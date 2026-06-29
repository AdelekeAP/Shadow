"""
Study Plan Generator Service - GPT-4 Powered Personalized Learning Plans
Generates day-by-day study plans based on student context and needs
"""
import asyncio
import logging
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.task import Task
from app.models.course import UserCourse, Course
from app.models.mood import MoodLog
from app.models.smartstudy import StudyPlan, StudyPlanResource
from app.services.smartstudy_service import load_student_context
from app.services.content_curator import get_content_curator
from app.services.resource_finder import get_resource_finder
from app.services.openai_client import (
    get_openai_client,
    call_with_retry,
    OpenAIError,
    PLAN_MODELS,
)

logger = logging.getLogger(__name__)

# Max characters of slide content to include in prompts (~5K tokens)
MAX_SLIDE_CONTENT_CHARS = 20000

# ── Central Learning Style Configuration ──
# All learning-style-specific tuning in one place.
# Change these values to adjust resource allocation without touching logic.
STYLE_CONFIG = {
    # Duration calculation thresholds
    "duration": {
        "base_days": 7,
        "min_days": 5,
        "max_days": 14,
        "cgpa_gap_urgent": 0.5,      # Above this → shorter plan
        "cgpa_gap_relaxed": 0.2,     # Below this → longer plan
        "energy_low_threshold": 2,    # At or below → gentler plan
        "energy_high_threshold": 4,   # At or above → intense plan
        "task_overload_threshold": 10, # More than this → quick plan
        "task_light_threshold": 3,     # Fewer than this → thorough plan
    },
    # Per-style resource allocation
    "resources": {
        "multiplier": 2,              # resources = max(num_days * multiplier, min_total)
        "min_total": 10,
        "min_quality_styled": 50.0,    # Quality threshold for styled plans
        "min_quality_default": 60.0,   # Quality threshold for default plans
        "default_max": 5,              # Max resources for unstyled plans
    },
    # Per-style video limits (max per plan-day)
    "videos_per_day": {
        "visual": 3,
        "audio": 1,
        "kinesthetic": 0,  # 0 = only as fallback
        "reading": 0,      # 0 = never assigned
        "default": 1,
    },
    # Slide assignment ratios (fraction of reading/review activities that get slides)
    "slide_ratio": {
        "reading": 0.8,    # Reading learners: 80% of activities get slides
        "default": 0.4,    # Other styles: 40% of activities get slides
    },
}


def calculate_optimal_duration(student_context: Dict[str, Any], topic: str) -> int:
    """
    Calculate optimal study plan duration based on student's current state.
    Thresholds are configured in STYLE_CONFIG["duration"].

    Args:
        student_context: Full student context from load_student_context()
        topic: Topic to study

    Returns:
        Optimal duration in days
    """
    cfg = STYLE_CONFIG["duration"]
    duration = cfg["base_days"]

    # Adjust based on CGPA gap (more urgent = shorter, intense plans)
    cgpa_gap = student_context.get("cgpa_gap", 0)
    if cgpa_gap and cgpa_gap > cfg["cgpa_gap_urgent"]:
        duration = max(cfg["min_days"], duration - 2)
    elif cgpa_gap and cgpa_gap < cfg["cgpa_gap_relaxed"]:
        duration = min(cfg["max_days"], duration + 3)

    # Adjust based on recent mood/energy
    moods = student_context.get("recent_moods", [])
    if moods:
        recent_mood = moods[0]
        energy_level = recent_mood.get("energy_level", 3)

        if energy_level <= cfg["energy_low_threshold"]:
            duration = min(cfg["max_days"], duration + 2)
        elif energy_level >= cfg["energy_high_threshold"]:
            duration = max(cfg["min_days"], duration - 1)

    # Adjust based on task load
    tasks = student_context.get("recent_tasks", [])
    incomplete_count = sum(1 for t in tasks if not t.get("is_completed"))

    if incomplete_count > cfg["task_overload_threshold"]:
        duration = max(cfg["min_days"], duration - 2)
    elif incomplete_count < cfg["task_light_threshold"]:
        duration = min(cfg["max_days"], duration + 2)

    return duration


def build_study_plan_prompt(
    student_context: Dict[str, Any],
    topic: str,
    course_code: Optional[str],
    duration_days: int,
    difficulty_level: str = "auto",
    slide_content: Optional[str] = None,
    learning_style: Optional[str] = None,
) -> str:
    """
    Build comprehensive GPT-4 prompt for study plan generation

    Args:
        student_context: Student's full academic context
        topic: Topic to create plan for
        course_code: Optional course code (e.g., "CSC401")
        duration_days: Plan duration (5-14 days)
        difficulty_level: "beginner", "intermediate", "advanced", or "auto"
        slide_content: Optional text extracted from uploaded slides

    Returns:
        Formatted prompt string for GPT-4
    """
    student_info = student_context.get("student_info", {})
    courses = student_context.get("courses", [])
    moods = student_context.get("recent_moods", [])
    cgpa_gap = student_context.get("cgpa_gap", 0)

    # Find relevant course if provided
    course_context = ""
    if course_code:
        course = next((c for c in courses if c["code"] == course_code), None)
        if course:
            course_context = f"""
**Relevant Course Context**:
- Course: {course['code']} - {course['title']}
- Current CA Score: {course['ca_score']}/35
- Predicted Grade: {course['predicted_grade']}
- Completion Rate: {course['completion_rate']}%

This study plan should help improve performance in this specific course.
"""

    # Assess student's current state
    mood_context = ""
    if moods:
        recent_mood = moods[0]
        mood_context = f"""
**Current Mental State**:
- Recent Mood: {recent_mood.get('mood_type', 'N/A')}
- Energy Level: {recent_mood.get('energy_level', 'N/A')}/5
- Primary Emotion: {recent_mood.get('primary_emotion', 'N/A')}

⚠️ IMPORTANT: Adapt plan difficulty and session length to student's energy level.
"""

    # Build the main prompt
    prompt = f"""You are an expert educational AI creating a personalized study plan for a Pan-Atlantic University student.

**Student Profile**:
- Name: {student_info.get('name', 'Student')}
- Current CGPA: {student_info.get('current_cgpa', 'N/A')}/5.0
- Target CGPA: {student_info.get('target_cgpa', 'N/A')}/5.0
- Gap to Target: {cgpa_gap if cgpa_gap else 'On track'}
- Learning Style: {learning_style or student_info.get('learning_style', 'Not specified')}
- Level: {student_info.get('entry_level', 'N/A')}

{course_context}

{mood_context}

**Topic to Master**: {topic}
**Duration**: {duration_days} days
**Difficulty Level**: {difficulty_level}

{"**STUDENT'S LECTURE SLIDES/NOTES**:" if slide_content else ""}
{f'''
The student has uploaded their actual lecture slides. This is the PRIMARY source material:
---
{slide_content[:MAX_SLIDE_CONTENT_CHARS] if slide_content else ""}
---
CRITICAL INSTRUCTIONS FOR SLIDE-BASED PLANS:
- Every activity MUST reference specific concepts, examples, formulas, or definitions from these slides
- Activity descriptions should say EXACTLY which pages/slides to focus on (e.g., "Study slides 5-9: Binary Trees and traversal algorithms")
- Do NOT create generic activities like "Set up your environment" or "Learn about class rules" unless the slides are specifically about that
- Do NOT create activities about topics NOT covered in the slides
- Each day should focus on a specific SECTION of the slides, progressing through the material
- The plan should follow the natural flow of the slides, not jump randomly between sections
- Activity titles must reference the SPECIFIC concept from the slides (e.g., "Practice Gradient Descent formula from Slide 12" NOT "Practice optimization")
''' if slide_content else ''}

{"**SELECTED LEARNING STYLE: " + learning_style.upper() + "**" + chr(10) + "⚠️ This student has specifically chosen " + learning_style + " learning mode. You MUST prioritize " + learning_style + "-style activities as described in the learning style guide below. At least 70% of activities must match this style." + chr(10) if learning_style else ""}
**Your Task**:
Create a detailed, actionable {duration_days}-day study plan to help this student master "{topic}".

**Requirements**:
1. **Day-by-Day Breakdown**: Each day should have 2-4 specific activities
2. **Progressive Difficulty**: Start easy, build to advanced concepts
3. **Varied Activities**: Mix theory, practice, projects, review
4. **Time Estimates**: Realistic time for each activity (30-120 minutes)
5. **Adaptive**: Match student's energy level and learning style
6. **Practical**: Include hands-on exercises, not just reading
7. **Measurable**: Clear objectives for each day

**Activity Types to Include**:
- 📚 Reading/Research (articles, documentation)
- 🎥 Video Learning (lecture recordings, tutorials)
- 💻 Hands-on Practice (coding exercises, problem-solving)
- 📝 Written Work (notes, summaries, explanations)
- 🧪 Projects (small builds, implementations)
- 🔄 Review (spaced repetition, quiz)

**Output Format** (STRICT JSON):
{{
  "title": "Master [Topic] in {duration_days} Days",
  "description": "Brief overview of what student will learn",
  "difficulty_level": "beginner|intermediate|advanced",
  "total_duration_days": {duration_days},
  "estimated_hours_total": "realistic total hours",
  "learning_objectives": [
    "Objective 1",
    "Objective 2",
    "Objective 3"
  ],
  "days": [
    {{
      "day_number": 1,
      "title": "Day 1: Foundation",
      "focus": "What this day focuses on",
      "activities": [
        {{
          "title": "Activity name — must reference a SPECIFIC concept",
          "description": "What to do in detail — reference specific slide content",
          "activity_type": "reading|video|practice|interactive|project|review",
          "estimated_minutes": 60,
          "difficulty": "easy|medium|hard",
          "page_range": "5-9",
          "resources_needed": ["Resource 1", "Resource 2"]
        }}
      ],
      "success_criteria": "How to know you've completed this day successfully"
    }}
  ],
  "final_assessment": "How to verify mastery of the topic",
  "next_steps": "What to study after completing this plan"
}}

**IMPORTANT GUIDELINES**:
- If student has LOW ENERGY (1-2/5): Shorter sessions (30-45 min), more breaks, easier start
- If student has HIGH ENERGY (4-5/5): Longer sessions (60-90 min), challenging projects
- If student is STRESSED: Include stress management tips, gentler pace
- If CGPA GAP is large: Focus on high-impact topics, exam-oriented practice
- Match LEARNING STYLE (ALL styles must be GROUNDED in slide content when slides are uploaded):
  - Visual learners: PRIORITIZE video-based activities and visual aids. Activity descriptions should specify WHAT concepts from the slides to look for in videos (e.g. "Watch a video on Decision Trees — compare with the classification examples from slides 8-12"). Include diagram-drawing and concept-mapping activities that reference specific slide content. Every video activity should specify the exact subtopic to search for, not just the broad topic.
  - Audio learners: PRIORITIZE audio-friendly activities — lecture-style explanations, discussion prompts, and content ideal for podcast-style summaries. Activity descriptions should specify WHICH slide pages to generate audio summaries from (e.g. "Listen to audio summary of slides 5-10: Regression Analysis"). Include activities that encourage verbal explanation and teaching concepts aloud. Each audio activity should reference the specific slide section it covers.
  - Reading learners: PRIORITIZE text-based, deep-reading activities — articles, documentation, written guides, and review activities. Every day should have at least one "reading" or "review" activity. Include activities that encourage note-taking, summarization, and comprehension checks. Use detailed descriptions that give reading learners enough context to engage deeply with the material. When the student uploaded slides, EVERY reading activity should reference SPECIFIC sections, pages, or concepts from the slides (e.g. "Read slides pages 5-9 on Binary Trees" NOT "Read about Binary Trees"). Activities should be grounded in the actual uploaded material, not generic web searches.
  - Kinesthetic learners: PRIORITIZE hands-on activities — coding challenges, worked examples, build-from-scratch projects, debugging exercises, and interactive labs. Every day should have at least one "practice" or "interactive" activity. Activity descriptions must reference SPECIFIC problems, formulas, or examples from the slides to practice (e.g. "Implement the sorting algorithm from Slide 15 from scratch" NOT "Practice sorting"). Include step-by-step exercises with clear success criteria grounded in the slide material.

**UNIVERSAL RULES (ALL LEARNING STYLES)**:
- NEVER generate activities about: setting up development environments, installing software, class attendance rules, course administration, or general study tips — UNLESS the slides are specifically about those topics
- Every activity title must name a SPECIFIC concept, not a generic category
- **page_range is REQUIRED** when slides are uploaded: Each activity must specify which slide/page numbers it covers (e.g. "5-9", "12-15", "1-3"). Activities should progress through the slides sequentially across days. If no slides uploaded, use null for page_range.
- Activity descriptions must tell the student EXACTLY what to focus on
- When slides are uploaded, at least 80% of activities must directly reference slide content

**Response**:
Return ONLY valid JSON. No markdown, no code blocks, just the JSON object.
"""

    return prompt


def parse_study_plan_json(gpt_response: str) -> Dict[str, Any]:
    """
    Parse and validate GPT-4 study plan JSON response

    Args:
        gpt_response: Raw GPT-4 response string

    Returns:
        Validated study plan dictionary

    Raises:
        ValueError: If JSON is invalid or missing required fields
    """
    try:
        # Remove markdown code blocks if present
        cleaned = gpt_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # Parse JSON
        plan_data = json.loads(cleaned)

        # Validate required fields
        required_fields = ["title", "description", "days"]
        for field in required_fields:
            if field not in plan_data:
                raise ValueError(f"Missing required field: {field}")

        # Validate days array
        if not isinstance(plan_data["days"], list) or len(plan_data["days"]) == 0:
            raise ValueError("Days array is empty or invalid")

        # Validate each day has required fields
        for day in plan_data["days"]:
            if "day_number" not in day or "activities" not in day:
                raise ValueError(f"Day {day.get('day_number', '?')} missing required fields")

        # Sanitize page_range formats in activities
        for day in plan_data["days"]:
            for activity in day.get("activities", []):
                pr = activity.get("page_range")
                if pr and isinstance(pr, str):
                    # Normalize formats like "pages 5-9" or "slides 1 to 3" to "5-9" / "1-3"
                    cleaned_pr = re.sub(r'^(?:pages?|slides?)\s*', '', pr.strip(), flags=re.IGNORECASE)
                    cleaned_pr = re.sub(r'\s*to\s*', '-', cleaned_pr)
                    # Validate it matches "N" or "N-M" pattern
                    if not re.match(r'^\d+(?:\s*-\s*\d+)?$', cleaned_pr.strip()):
                        activity["page_range"] = None
                    else:
                        activity["page_range"] = cleaned_pr.strip()

        logger.info(f"✅ Successfully parsed study plan with {len(plan_data['days'])} days")
        return plan_data

    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON parsing error: {e}")
        logger.error(f"Response: {gpt_response[:500]}")
        raise ValueError(f"Invalid JSON response from GPT-4: {e}")
    except Exception as e:
        logger.error(f"❌ Error parsing study plan: {e}")
        raise


def validate_slide_grounding(plan_data: dict, has_slides: bool) -> dict:
    """Validate that generated plan activities are grounded in slide content.

    Returns validation result with grounding score and warnings.
    """
    if not has_slides:
        return {"score": 1.0, "warnings": [], "grounded": True}

    days = plan_data.get("days", [])
    total_activities = 0
    grounded_activities = 0
    warnings = []

    slide_ref_patterns = [
        r'(?:slide|page)s?\s*\d',
        r'page[_\s]?range',
        r'from\s+(?:the\s+)?(?:slide|lecture|material)',
        r'(?:in|on|from)\s+(?:slide|page)',
    ]

    for day in days:
        for activity in day.get("activities", []):
            total_activities += 1

            # Check for slide grounding signals
            desc = (activity.get("description", "") + " " + activity.get("title", "")).lower()
            has_page_range = bool(activity.get("page_range"))
            has_slide_ref = any(re.search(p, desc, re.IGNORECASE) for p in slide_ref_patterns)

            if has_page_range or has_slide_ref:
                grounded_activities += 1
            else:
                act_type = activity.get("activity_type", "")
                title = activity.get("title", "")
                # Don't penalize video/quiz activities — those are inherently external
                if act_type not in ("video", "quiz"):
                    warnings.append(f"Day {day.get('day_number', '?')}: '{title}' — no slide reference or page_range")

    score = grounded_activities / total_activities if total_activities > 0 else 1.0

    if score < 0.8:
        logger.warning(
            f"Slide grounding below threshold: {score:.0%} "
            f"({grounded_activities}/{total_activities} activities reference slides). "
            f"Warnings: {warnings[:5]}"
        )
    else:
        logger.info(f"Slide grounding OK: {score:.0%} ({grounded_activities}/{total_activities})")

    result = {
        "score": round(score, 2),
        "grounded_count": grounded_activities,
        "total_count": total_activities,
        "warnings": warnings[:5],
        "grounded": score >= 0.8,
    }

    # Add user-facing warning when grounding is poor
    if score < 0.6:
        result["grounding_warning"] = (
            f"Only {score:.0%} of activities reference your uploaded slides. "
            "Some activities may use general knowledge instead of your specific material."
        )

    return result


async def generate_study_plan(
    db: Session,
    user_id: str,
    topic: str,
    course_id: Optional[str] = None,
    duration_days: Optional[int] = None,
    difficulty_level: str = "auto",
    trigger_type: Optional[str] = None,
    trigger_task_id: Optional[str] = None,
    trigger_score: Optional[float] = None,
    learning_style: Optional[str] = None,
    slide_content: Optional[str] = None,
    document_filename: Optional[str] = None,
    document_view_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a personalized study plan using GPT-4

    Args:
        db: Database session
        user_id: User UUID
        topic: Topic to create study plan for
        course_id: Optional course UUID
        duration_days: Optional duration (auto-calculated if not provided)
        difficulty_level: "beginner", "intermediate", "advanced", or "auto"
        trigger_type: What triggered this plan (e.g., "low_score", "student_request")
        trigger_task_id: Task that triggered the plan (if applicable)
        trigger_score: Score that triggered intervention (if applicable)
        learning_style: "visual", "audio", "reading", "kinesthetic", or None (auto)
        slide_content: Optional text extracted from uploaded slides/PDF
        document_filename: Original filename of uploaded slides (for display)
        document_view_url: URL to view the document (library docs only, None for transient uploads)

    Returns:
        Dict with study plan details and database ID
    """
    try:
        # Load student context
        context = load_student_context(db, user_id)

        # Get course code if course_id provided
        course_code = None
        if course_id:
            course = db.query(Course).filter(Course.id == course_id).first()
            if course:
                course_code = course.code

        # Calculate optimal duration if not provided
        if not duration_days:
            duration_days = calculate_optimal_duration(context, topic)

        # Ensure duration is in valid range
        duration_days = max(5, min(14, duration_days))

        logger.info(f"🎯 Generating {duration_days}-day study plan for '{topic}'")
        if slide_content:
            logger.info(f"📄 Using uploaded slide content ({len(slide_content)} characters)")

        # Track style recommendation for mismatch warnings
        style_recommendation = None
        user_selected_style = learning_style  # Capture what user originally picked

        # Normalize the stored profile value "auditory" to the generator's internal
        # "audio" so the audio-specific resource handling fires instead of falling
        # through to the generic else branch. (Profile column is left unchanged.)
        if learning_style == "auditory":
            learning_style = "audio"

        # Smart auto: when learning_style is None and we have slide content,
        # use content analysis to pick the best default style
        if learning_style is None and slide_content:
            try:
                from app.services.document_processor import analyze_content_type
                content_analysis = analyze_content_type(slide_content)
                recommended = content_analysis.get("recommended_styles", [])
                if recommended:
                    learning_style = recommended[0]
                    logger.info(
                        f"Smart auto: detected {content_analysis['content_type']} content, "
                        f"auto-selected '{learning_style}' learning style"
                    )
            except Exception as auto_err:
                logger.warning(f"Smart auto detection failed (non-fatal): {auto_err}")

        # Check for style mismatch: user picked a style but content analysis suggests different
        if user_selected_style and slide_content:
            try:
                from app.services.document_processor import analyze_content_type
                content_analysis = analyze_content_type(slide_content)
                recommended = content_analysis.get("recommended_styles", [])
                if recommended and user_selected_style not in recommended:
                    style_recommendation = {
                        "warning": f"Your content appears to be {content_analysis.get('content_type', 'general')} material. "
                                   f"Consider trying '{recommended[0]}' mode for better results with this type of content.",
                        "selected_style": user_selected_style,
                        "recommended_styles": recommended,
                        "content_type": content_analysis.get("content_type", "general"),
                    }
            except Exception:
                pass  # Non-fatal

        # Sanitize slide content — remove non-printable characters that cause OpenAI BadRequestError
        if slide_content:
            # Keep printable ASCII, common unicode, and whitespace; strip control chars
            slide_content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', slide_content)
            # Collapse excessive whitespace/newlines from PDF extraction artifacts
            slide_content = re.sub(r'\n{4,}', '\n\n\n', slide_content)
            slide_content = re.sub(r' {4,}', '   ', slide_content)

        # Build GPT-4 prompt
        prompt = build_study_plan_prompt(
            context, topic, course_code, duration_days, difficulty_level, slide_content,
            learning_style=learning_style,
        )

        # Call GPT-4 Turbo with retry/fallback (offload to thread to avoid blocking event loop)
        response = await asyncio.to_thread(
            call_with_retry,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert educational planner. Generate detailed, personalized study plans in strict JSON format. IMPORTANT: Complete the entire JSON response without truncation."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            models=PLAN_MODELS,
            temperature=0.7,
            max_tokens=4000,
            timeout=60.0,
            stream=False,
        )

        gpt_response = response.choices[0].message.content
        tokens_used = response.usage.total_tokens

        logger.info(f"📊 GPT-4 response received ({tokens_used} tokens)")

        # Parse GPT-4 response
        plan_data = parse_study_plan_json(gpt_response)

        # Validate slide grounding
        grounding_result = validate_slide_grounding(plan_data, bool(slide_content))

        # Persist grounding validation result for frontend display
        plan_data["_slide_grounding"] = grounding_result

        # Store the learning style used for frontend display
        if learning_style:
            plan_data["_learning_style"] = learning_style

        # Preserve slide content for downstream audio generation
        if slide_content:
            plan_data["_slide_content"] = slide_content[:MAX_SLIDE_CONTENT_CHARS]

        # Create StudyPlan in database
        study_plan = StudyPlan(
            user_id=user_id,
            course_id=course_id,
            topic=topic,
            trigger_type=trigger_type,
            trigger_task_id=trigger_task_id,
            trigger_score=trigger_score,
            plan_data=plan_data,
            duration_days=duration_days,
            start_date=datetime.now(timezone.utc).date(),
            end_date=(datetime.now(timezone.utc) + timedelta(days=duration_days)).date(),
            completion_percentage=0,
            is_active=True,
            learning_style_used=learning_style,
            completed_days=[]
        )

        db.add(study_plan)
        db.flush()  # Get plan.id for FK references without committing
        db.refresh(study_plan)

        logger.info(f"✅ Study plan created with ID: {study_plan.id}")

        # Send notification for new study plan
        try:
            from app.services.notification_service import NotificationService
            from app.models.notification import NotificationType, NotificationPriority
            ns = NotificationService(db)
            ns.create_notification(
                user_id=study_plan.user_id,
                title=f"New Study Plan: {topic}",
                message=f"Your {duration_days}-day plan for \"{topic}\" is ready. Start Day 1 now!",
                notification_type=NotificationType.STUDY_PLAN.value if hasattr(NotificationType, 'STUDY_PLAN') else NotificationType.SYSTEM.value,
                priority=NotificationPriority.HIGH.value,
                study_plan_id=study_plan.id,
                action_url="/smartstudy",
            )
        except Exception as notif_err:
            logger.warning(f"Failed to send study plan notification: {notif_err}")

        # Create StudyPlanResource entries with curated YouTube/Reddit resources
        logger.info(f"🔍 Curating resources for '{topic}' (learning style: {learning_style or 'balanced'})")

        try:
            curator = get_content_curator()
            resource_finder = get_resource_finder()

            # Determine how many resources to fetch based on learning style
            # Visual learners get more videos, spread across all days
            is_visual_learner = learning_style == "visual"
            is_audio_learner = learning_style == "audio"
            is_kinesthetic_learner = learning_style == "kinesthetic"
            is_reading_learner = learning_style == "reading"
            num_days = len(plan_data.get("days", []))

            # Resource allocation driven by STYLE_CONFIG
            res_cfg = STYLE_CONFIG["resources"]
            if is_visual_learner or is_audio_learner or is_kinesthetic_learner or is_reading_learner:
                max_resources = max(num_days * res_cfg["multiplier"], res_cfg["min_total"])
                min_quality = res_cfg["min_quality_styled"]
            else:
                max_resources = res_cfg["default_max"]
                min_quality = res_cfg["min_quality_default"]

            # Extract specific subtopics from GPT plan for targeted resource search
            # Use DAY FOCUS only (short concept names like "Linear Regression")
            # NOT activity titles (which are too long/specific for YouTube search)
            plan_subtopics = []
            for day in plan_data.get("days", []):
                day_focus = day.get("focus", "")
                if day_focus and day_focus != topic:
                    # Extract the specific concept from the day focus
                    clean_focus = day_focus.replace(f"Day {day.get('day_number', '')}", "").strip(": -")
                    if clean_focus and len(clean_focus) > 3 and len(clean_focus) < 80:
                        plan_subtopics.append(clean_focus)

            # Deduplicate and take top 5 unique subtopics
            seen = set()
            unique_subtopics = []
            for st in plan_subtopics:
                st_lower = st.lower()
                if st_lower not in seen and topic.lower() not in st_lower[:10]:
                    seen.add(st_lower)
                    unique_subtopics.append(st)
                    if len(unique_subtopics) >= 5:
                        break

            if unique_subtopics:
                logger.info(f"📋 Extracted subtopics for resource search: {unique_subtopics[:3]}")

            # Curate resources using subtopics for more specific YouTube searches
            curated_resources = curator.curate_resources(
                topic=topic,
                learning_style=learning_style or "balanced",
                max_results=max_resources,
                min_quality_score=min_quality,
                subtopics=unique_subtopics
            )

            # Get combined recommendations (best of both YouTube and Reddit)
            recommendations = curated_resources.get("combined_recommendations", [])

            # Separate YouTube videos for easier distribution
            youtube_videos = [r for r in recommendations if r.get("type") == "youtube_video"]
            other_resources = [r for r in recommendations if r.get("type") != "youtube_video"]

            # Get additional resources from resource finder (offload to thread — find_all_resources
            # calls classify_topic which calls call_with_retry with a blocking time.sleep)
            found_resources = await asyncio.to_thread(
                resource_finder.find_all_resources,
                topic,
                ['documentation', 'articles', 'practice', 'interactive'],  # resource_types
                num_days,  # max_per_type — get enough for all days
                db,  # Enable Brave Search caching
                unique_subtopics,  # subtopics
            )

            # Separate by type for easier assignment
            documentation_resources = found_resources.get('resources', {}).get('documentation', [])
            article_resources = found_resources.get('resources', {}).get('articles', [])
            practice_resources = found_resources.get('resources', {}).get('practice', [])
            interactive_resources = found_resources.get('resources', {}).get('interactive', [])

            logger.info(f"📊 Found {len(recommendations)} curated resources ({len(youtube_videos)} videos)")
            logger.info(f"📚 Found {len(documentation_resources)} docs, {len(article_resources)} articles, {len(practice_resources)} practice, {len(interactive_resources)} interactive")

            # Build uploaded_slides resource if student provided slides
            uploaded_doc_resource = None
            if slide_content:
                uploaded_doc_resource = {
                    'type': 'uploaded_slides',
                    'title': document_filename or f'{topic} - Lecture Slides',
                    'url': document_view_url,  # None for transient uploads
                    'description': f'Your uploaded lecture slides for {topic}',
                    'quality_score': 95,
                }
                logger.info(f"📄 Uploaded slides resource created: {uploaded_doc_resource['title']}")

            # Cap how many reading/review activities get the uploaded slides
            # Reading learners: slides are the PRIMARY resource (~80%)
            # Other styles: slides supplement external resources (~40%)
            total_reading_review = sum(
                1 for d in plan_data.get("days", [])
                for a in d.get("activities", [])
                if a.get("activity_type", "reading").lower().strip()
                in ("reading", "review", "tutorial", "listen", "audio", "written")
            )
            slide_cfg = STYLE_CONFIG["slide_ratio"]
            slide_ratio = slide_cfg["reading"] if is_reading_learner else slide_cfg["default"]
            if is_reading_learner:
                max_slide_assignments = max(2, int(total_reading_review * slide_ratio))
            else:
                max_slide_assignments = max(1, int(total_reading_review * slide_ratio))
            slide_assignments_used = 0

            # Create resource entries for each day's activities
            video_idx = 0
            other_idx = 0
            doc_idx = 0
            article_idx = 0
            practice_idx = 0
            interactive_idx = 0
            videos_assigned_this_day = 0
            current_day = 0

            # Track assigned video URLs to prevent duplicates
            assigned_video_urls = set()

            for day in plan_data.get("days", []):
                day_num = day.get("day_number", 0)

                # Reset video counter for new day
                if day_num != current_day:
                    current_day = day_num
                    videos_assigned_this_day = 0

                for idx, activity in enumerate(day.get("activities", [])):
                    activity_type = activity.get("activity_type", "reading").lower().strip()
                    activity_title = activity.get("title", "").lower()

                    # ── Normalize activity type ──
                    # GPT sometimes generates types outside the allowed set
                    type_normalization = {
                        "interactive": "practice",
                        "tutorial": "reading",
                        "exercise": "practice",
                        "hands-on": "practice",
                        "watch": "video",
                        "listen": "audio",
                        "discussion": "review",
                        "written": "reading",
                        "audio": "audio",
                    }
                    activity_type = type_normalization.get(activity_type, activity_type)

                    # ── Title-based type correction ──
                    # If GPT labelled something "video" but the title says
                    # interactive / hands-on / practice, override to practice
                    # SKIP for visual learners — they WANT video content for all activities
                    if not is_visual_learner:
                        practice_keywords = ['interactive', 'hands-on', 'exercise', 'practice',
                                             'sandbox', 'lab', 'drill', 'coding challenge']
                        if activity_type == "video" and any(kw in activity_title for kw in practice_keywords):
                            activity_type = "practice"

                        # If title says "read" or "article" but type is video, override to reading
                        reading_keywords = ['read', 'article', 'documentation', 'docs', 'textbook']
                        if activity_type == "video" and any(kw in activity_title for kw in reading_keywords):
                            activity_type = "reading"

                    # Try to match curated resources to activity type
                    matched_resource = None
                    resource_type_override = None  # For overriding the type

                    # Reading override: for "video" activities,
                    # ALWAYS prefer text resources — reading learners should never get videos
                    if is_reading_learner and activity_type == "video":
                        if uploaded_doc_resource and slide_assignments_used < max_slide_assignments:
                            matched_resource = uploaded_doc_resource
                            resource_type_override = 'uploaded_slides'
                            slide_assignments_used += 1
                        elif doc_idx < len(documentation_resources):
                            matched_resource = documentation_resources[doc_idx]
                            resource_type_override = 'documentation'
                            doc_idx += 1
                        elif article_idx < len(article_resources):
                            matched_resource = article_resources[article_idx]
                            resource_type_override = 'article'
                            article_idx += 1
                        # No fall-through to video — reading learners skip video resources entirely

                    # Kinesthetic override: for "video" or "reading" activities,
                    # prefer practice/interactive resources if available
                    if not matched_resource and is_kinesthetic_learner and activity_type in ("video", "reading"):
                        if interactive_idx < len(interactive_resources):
                            matched_resource = interactive_resources[interactive_idx]
                            resource_type_override = 'interactive'
                            interactive_idx += 1
                        elif practice_idx < len(practice_resources):
                            matched_resource = practice_resources[practice_idx]
                            resource_type_override = 'practice'
                            practice_idx += 1
                        # Fall through to normal assignment if no practice resources left

                    # Determine if this activity should get a video
                    # (skip if style override already matched, or reading learners)
                    should_assign_video = False

                    if not matched_resource and not is_reading_learner:
                        vid_cfg = STYLE_CONFIG["videos_per_day"]
                        style_key = learning_style or "default"
                        max_vids = vid_cfg.get(style_key, vid_cfg["default"])

                        if is_visual_learner:
                            # Visual learners: videos are their PRIMARY learning mode
                            if activity_type == "video":
                                should_assign_video = True
                            elif video_idx < len(youtube_videos) and videos_assigned_this_day < max_vids:
                                should_assign_video = True
                        elif is_audio_learner:
                            # Audio learners: YouTube videos supplement podcast content
                            if activity_type in ("video", "audio") and videos_assigned_this_day < max_vids:
                                should_assign_video = True
                        else:
                            # For other learning styles: only video activities
                            should_assign_video = activity_type == "video"

                    # Assign YouTube video (skip duplicates)
                    if should_assign_video:
                        while video_idx < len(youtube_videos):
                            candidate_url = youtube_videos[video_idx].get("url", "")
                            if candidate_url not in assigned_video_urls:
                                break
                            video_idx += 1
                        if video_idx < len(youtube_videos):
                            matched_resource = youtube_videos[video_idx]
                            assigned_video_urls.add(matched_resource.get("url", ""))
                            video_idx += 1
                            videos_assigned_this_day += 1

                    # Fallback for video activities when YouTube is unavailable
                    # Assign docs/articles/interactive so they're not empty ai_generated
                    if not matched_resource and activity_type == "video":
                        if interactive_idx < len(interactive_resources):
                            matched_resource = interactive_resources[interactive_idx]
                            resource_type_override = 'interactive'
                            interactive_idx += 1
                        elif doc_idx < len(documentation_resources):
                            matched_resource = documentation_resources[doc_idx]
                            resource_type_override = 'documentation'
                            doc_idx += 1
                        elif article_idx < len(article_resources):
                            matched_resource = article_resources[article_idx]
                            resource_type_override = 'article'
                            article_idx += 1

                    # For audio activities without a video — assign docs/articles
                    # AudioPlayer generates audio summaries from these on the frontend
                    if not matched_resource and activity_type == "audio":
                        if doc_idx < len(documentation_resources) and (article_idx >= len(article_resources) or doc_idx <= article_idx):
                            matched_resource = documentation_resources[doc_idx]
                            resource_type_override = 'documentation'
                            doc_idx += 1
                        elif article_idx < len(article_resources):
                            matched_resource = article_resources[article_idx]
                            resource_type_override = 'article'
                            article_idx += 1

                    # For reading activities - assign documentation or articles
                    if not matched_resource and activity_type == "reading":
                        # Reading learners: uploaded slides are the PRIMARY resource
                        # Other styles: slides only for keyword-matched activities
                        if is_reading_learner and uploaded_doc_resource and slide_assignments_used < max_slide_assignments:
                            # Reading learners get slides by default for reading activities
                            matched_resource = uploaded_doc_resource
                            resource_type_override = 'uploaded_slides'
                            slide_assignments_used += 1
                        elif not is_reading_learner:
                            # Other styles: only assign slides for keyword-matched activities
                            slide_keywords = ['slide', 'lecture', 'notes', 'review', 'material', 'course']
                            if (uploaded_doc_resource
                                    and slide_assignments_used < max_slide_assignments
                                    and any(kw in activity_title for kw in slide_keywords)):
                                matched_resource = uploaded_doc_resource
                                resource_type_override = 'uploaded_slides'
                                slide_assignments_used += 1

                        # External resources as supplement (or primary for non-reading styles)
                        if not matched_resource and any(word in activity_title for word in ['documentation', 'docs', 'reference', 'official']):
                            if doc_idx < len(documentation_resources):
                                matched_resource = documentation_resources[doc_idx]
                                resource_type_override = 'documentation'
                                doc_idx += 1
                        elif not matched_resource and any(word in activity_title for word in ['article', 'blog', 'tutorial', 'guide']):
                            if article_idx < len(article_resources):
                                matched_resource = article_resources[article_idx]
                                resource_type_override = 'article'
                                article_idx += 1

                        # Fallback: alternate between docs and articles
                        if not matched_resource:
                            if doc_idx < len(documentation_resources) and (article_idx >= len(article_resources) or doc_idx <= article_idx):
                                matched_resource = documentation_resources[doc_idx]
                                resource_type_override = 'documentation'
                                doc_idx += 1
                            elif article_idx < len(article_resources):
                                matched_resource = article_resources[article_idx]
                                resource_type_override = 'article'
                                article_idx += 1

                        # Last resort: uploaded slides if nothing else matched
                        if not matched_resource and uploaded_doc_resource and slide_assignments_used < max_slide_assignments:
                            matched_resource = uploaded_doc_resource
                            resource_type_override = 'uploaded_slides'
                            slide_assignments_used += 1

                    # For practice/interactive activities - assign practice platforms
                    if not matched_resource and activity_type in ("practice", "interactive"):
                        if practice_idx < len(practice_resources):
                            matched_resource = practice_resources[practice_idx]
                            resource_type_override = 'practice'
                            practice_idx += 1
                        elif interactive_idx < len(interactive_resources):
                            matched_resource = interactive_resources[interactive_idx]
                            resource_type_override = 'interactive'
                            interactive_idx += 1
                        # Kinesthetic fallback: YouTube tutorials for hands-on follow-along
                        elif is_kinesthetic_learner and video_idx < len(youtube_videos):
                            while video_idx < len(youtube_videos):
                                candidate_url = youtube_videos[video_idx].get("url", "")
                                if candidate_url not in assigned_video_urls:
                                    break
                                video_idx += 1
                            if video_idx < len(youtube_videos):
                                matched_resource = youtube_videos[video_idx]
                                assigned_video_urls.add(matched_resource.get("url", ""))
                                video_idx += 1
                        # Further fallback: docs/articles for reference material
                        elif not matched_resource and doc_idx < len(documentation_resources):
                            matched_resource = documentation_resources[doc_idx]
                            resource_type_override = 'documentation'
                            doc_idx += 1
                        elif not matched_resource and article_idx < len(article_resources):
                            matched_resource = article_resources[article_idx]
                            resource_type_override = 'article'
                            article_idx += 1

                    # For project activities - assign interactive tutorials or practice
                    if not matched_resource and activity_type == "project":
                        if is_kinesthetic_learner and interactive_idx < len(interactive_resources):
                            matched_resource = interactive_resources[interactive_idx]
                            resource_type_override = 'interactive'
                            interactive_idx += 1
                        elif practice_idx < len(practice_resources):
                            matched_resource = practice_resources[practice_idx]
                            resource_type_override = 'practice'
                            practice_idx += 1

                    # For quiz/assessment/review activities
                    if not matched_resource and activity_type in ["quiz", "assessment", "review"]:
                        # Prefer uploaded slides for review activities
                        if (uploaded_doc_resource
                                and activity_type == "review"
                                and slide_assignments_used < max_slide_assignments):
                            matched_resource = uploaded_doc_resource
                            resource_type_override = 'uploaded_slides'
                            slide_assignments_used += 1
                        elif practice_idx < len(practice_resources):
                            matched_resource = practice_resources[practice_idx]
                            resource_type_override = 'practice'
                            practice_idx += 1

                    # Create StudyPlanResource entry
                    if matched_resource:
                        # Determine resource type (use override if set, otherwise from resource)
                        res_type = resource_type_override or matched_resource.get("type", "youtube_video")

                        # Create with curated resource data
                        resource = StudyPlanResource(
                            study_plan_id=study_plan.id,
                            resource_type=res_type,
                            resource_url=matched_resource.get("url"),
                            resource_title=matched_resource.get("title"),
                            resource_description=matched_resource.get("description", activity.get("description")),
                            quality_score=matched_resource.get("quality_score"),
                            day_number=day.get("day_number"),
                            order_in_day=idx,
                            clicked=False,
                            completed=False
                        )
                    else:
                        # Fallback: Create AI-generated placeholder
                        logger.info(
                            f"No curated resource matched for activity '{activity.get('title')}' "
                            f"(type={activity_type}, day={day.get('day_number')}) — using ai_generated fallback"
                        )
                        resource = StudyPlanResource(
                            study_plan_id=study_plan.id,
                            resource_type="ai_generated",
                            resource_title=activity.get("title"),
                            resource_description=activity.get("description"),
                            day_number=day.get("day_number"),
                            order_in_day=idx,
                            clicked=False,
                            completed=False
                        )

                    db.add(resource)

            db.commit()
            total_resources = sum(
                len(day.get("activities", []))
                for day in plan_data.get("days", [])
            )
            logger.info(f"✅ Created {total_resources} curated resources for study plan")

        except Exception as e:
            logger.error(f"⚠️ Error curating resources, using placeholder resources: {e}")
            # Fallback to basic resources on error
            for day in plan_data.get("days", []):
                for idx, activity in enumerate(day.get("activities", [])):
                    resource = StudyPlanResource(
                        study_plan_id=study_plan.id,
                        resource_type="ai_generated",
                        resource_title=activity.get("title"),
                        resource_description=activity.get("description"),
                        day_number=day.get("day_number"),
                        order_in_day=idx,
                        clicked=False,
                        completed=False
                    )
                    db.add(resource)

        # Single atomic commit for plan + all resources
        db.commit()

        result = {
            "study_plan_id": str(study_plan.id),
            "topic": topic,
            "duration_days": duration_days,
            "plan_data": plan_data,
            "tokens_used": tokens_used,
            "created_at": study_plan.created_at.isoformat(),
            "slide_grounding": grounding_result if slide_content else None,
        }
        if style_recommendation:
            result["style_recommendation"] = style_recommendation
        return result

    except OpenAIError as e:
        logger.error(f"❌ OpenAI error generating study plan: {e.error_type.value}")
        logger.error(f"   Original error: {e.original_error}")
        db.rollback()
        return {"error": e.user_message}
    except Exception as e:
        logger.error(f"❌ Error generating study plan: {e}")
        db.rollback()
        return {"error": str(e)}


def get_study_plan(db: Session, user_id: str, plan_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific study plan by ID

    Args:
        db: Database session
        user_id: User UUID (for auth)
        plan_id: StudyPlan UUID

    Returns:
        Study plan dict or None
    """
    try:
        plan = db.query(StudyPlan).filter(
            StudyPlan.id == plan_id,
            StudyPlan.user_id == user_id
        ).first()

        if not plan:
            return None

        # Get resources
        resources = db.query(StudyPlanResource).filter(
            StudyPlanResource.study_plan_id == plan.id
        ).order_by(
            StudyPlanResource.day_number,
            StudyPlanResource.order_in_day
        ).all()

        return {
            **plan.to_dict(),
            "resources": [r.to_dict() for r in resources]
        }

    except Exception as e:
        logger.error(f"❌ Error getting study plan: {e}")
        return None


def update_study_plan_progress(
    db: Session,
    user_id: str,
    plan_id: str,
    completed_days: List[int]
) -> bool:
    """
    Update study plan progress

    Args:
        db: Database session
        user_id: User UUID
        plan_id: StudyPlan UUID
        completed_days: List of completed day numbers

    Returns:
        True if successful
    """
    try:
        plan = db.query(StudyPlan).filter(
            StudyPlan.id == plan_id,
            StudyPlan.user_id == user_id
        ).first()

        if not plan:
            return False

        # Calculate completion percentage
        total_days = len(plan.plan_data.get("days", []))
        completion = (len(completed_days) / total_days * 100) if total_days > 0 else 0

        plan.completion_percentage = completion

        # Mark as completed if 100%
        if completion >= 100:
            plan.is_active = False
            plan.completed_at = datetime.now(timezone.utc)

        db.commit()
        logger.info(f"✅ Updated study plan progress: {completion}%")
        return True

    except Exception as e:
        logger.error(f"❌ Error updating study plan progress: {e}")
        db.rollback()
        return False
