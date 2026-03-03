"""
Study Plan Generator Service - GPT-4 Powered Personalized Learning Plans
Generates day-by-day study plans based on student context and needs
"""
import os
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from openai import OpenAI

from app.models.user import User
from app.models.task import Task
from app.models.course import UserCourse, Course
from app.models.mood import MoodLog
from app.models.smartstudy import StudyPlan, StudyPlanResource
from app.services.smartstudy_service import load_student_context
from app.services.content_curator import get_content_curator
from app.services.resource_finder import get_resource_finder

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = None
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        client = OpenAI(api_key=api_key)
        logger.info("✅ OpenAI client initialized for study plan generation")
    else:
        logger.warning("⚠️ OPENAI_API_KEY not found")
except Exception as e:
    logger.error(f"❌ Failed to initialize OpenAI client: {e}")


def calculate_optimal_duration(student_context: Dict[str, Any], topic: str) -> int:
    """
    Calculate optimal study plan duration based on student's current state

    Args:
        student_context: Full student context from load_student_context()
        topic: Topic to study

    Returns:
        Optimal duration in days (5-14)
    """
    # Start with base duration
    duration = 7

    # Adjust based on CGPA gap (more urgent = shorter, intense plans)
    cgpa_gap = student_context.get("cgpa_gap", 0)
    if cgpa_gap and cgpa_gap > 0.5:
        duration = max(5, duration - 2)  # More urgent, shorter plan
    elif cgpa_gap and cgpa_gap < 0.2:
        duration = min(14, duration + 3)  # Less urgent, longer plan

    # Adjust based on recent mood/energy
    moods = student_context.get("recent_moods", [])
    if moods:
        recent_mood = moods[0]
        energy_level = recent_mood.get("energy_level", 3)

        if energy_level <= 2:
            duration = min(14, duration + 2)  # Low energy = longer, gentler plan
        elif energy_level >= 4:
            duration = max(5, duration - 1)  # High energy = shorter, intense plan

    # Adjust based on task load
    tasks = student_context.get("recent_tasks", [])
    incomplete_count = sum(1 for t in tasks if not t.get("is_completed"))

    if incomplete_count > 10:
        duration = max(5, duration - 2)  # Overloaded = quick plan
    elif incomplete_count < 3:
        duration = min(14, duration + 2)  # Light load = thorough plan

    return duration


def build_study_plan_prompt(
    student_context: Dict[str, Any],
    topic: str,
    course_code: Optional[str],
    duration_days: int,
    difficulty_level: str = "auto",
    slide_content: Optional[str] = None
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
- Learning Style: {student_info.get('learning_style', 'Not specified')}
- Level: {student_info.get('entry_level', 'N/A')}

{course_context}

{mood_context}

**Topic to Master**: {topic}
**Duration**: {duration_days} days
**Difficulty Level**: {difficulty_level}

{"**STUDENT'S LECTURE SLIDES/NOTES**:" if slide_content else ""}
{f'''
The student has uploaded their lecture slides. Use this content to personalize the plan:
---
{slide_content[:50000] if slide_content else ""}
---
IMPORTANT: Reference concepts from these slides, use slide examples, and fill knowledge gaps not covered in slides.
''' if slide_content else ''}

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
          "title": "Activity name",
          "description": "What to do in detail",
          "activity_type": "reading|video|practice|interactive|project|review",
          "estimated_minutes": 60,
          "difficulty": "easy|medium|hard",
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
- Match LEARNING STYLE: Visual learners get more videos/diagrams, hands-on learners get more coding

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

        logger.info(f"✅ Successfully parsed study plan with {len(plan_data['days'])} days")
        return plan_data

    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON parsing error: {e}")
        logger.error(f"Response: {gpt_response[:500]}")
        raise ValueError(f"Invalid JSON response from GPT-4: {e}")
    except Exception as e:
        logger.error(f"❌ Error parsing study plan: {e}")
        raise


def generate_study_plan(
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
    if not client:
        return {
            "error": "OpenAI client not initialized. Please check OPENAI_API_KEY."
        }

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

        # Build GPT-4 prompt
        prompt = build_study_plan_prompt(
            context, topic, course_code, duration_days, difficulty_level, slide_content
        )

        # Call GPT-4 Turbo (128K context window - handles large slide content)
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",  # Upgraded to handle large prompts with slide content
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
            temperature=0.7,
            max_tokens=4000  # Sufficient with 128K context window
        )

        gpt_response = response.choices[0].message.content
        tokens_used = response.usage.total_tokens

        logger.info(f"📊 GPT-4 response received ({tokens_used} tokens)")

        # Parse GPT-4 response
        plan_data = parse_study_plan_json(gpt_response)

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
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=duration_days)).date(),
            completion_percentage=0,
            is_active=True,
            learning_style_used=learning_style,
            completed_days=[]
        )

        db.add(study_plan)
        db.commit()
        db.refresh(study_plan)

        logger.info(f"✅ Study plan created with ID: {study_plan.id}")

        # Create StudyPlanResource entries with curated YouTube/Reddit resources
        logger.info(f"🔍 Curating resources for '{topic}' (learning style: {learning_style or 'balanced'})")

        try:
            curator = get_content_curator()
            resource_finder = get_resource_finder()

            # Determine how many resources to fetch based on learning style
            # Visual learners get more videos, spread across all days
            is_visual_learner = learning_style == "visual"
            is_kinesthetic_learner = learning_style == "kinesthetic"
            is_reading_learner = learning_style == "reading"
            num_days = len(plan_data.get("days", []))

            # For visual learners: at least 1-2 videos per day
            # For others: 5 total resources
            max_resources = max(num_days * 2, 10) if is_visual_learner else 5
            min_quality = 50.0 if is_visual_learner else 60.0  # Lower threshold for more results

            # Curate resources for the main topic
            curated_resources = curator.curate_resources(
                topic=topic,
                learning_style=learning_style or "balanced",
                max_results=max_resources,
                min_quality_score=min_quality
            )

            # Get combined recommendations (best of both YouTube and Reddit)
            recommendations = curated_resources.get("combined_recommendations", [])

            # Separate YouTube videos for easier distribution
            youtube_videos = [r for r in recommendations if r.get("type") == "youtube_video"]
            other_resources = [r for r in recommendations if r.get("type") != "youtube_video"]

            # Get additional resources from resource finder
            found_resources = resource_finder.find_all_resources(
                topic=topic,
                resource_types=['documentation', 'articles', 'practice', 'interactive'],
                max_per_type=num_days,  # Get enough for all days
                db=db  # Enable Brave Search caching
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

            # Cap how many reading/review activities get the uploaded slides (~40%)
            total_reading_review = sum(
                1 for d in plan_data.get("days", [])
                for a in d.get("activities", [])
                if a.get("activity_type", "reading").lower().strip()
                in ("reading", "review", "tutorial", "listen")
            )
            max_slide_assignments = max(1, total_reading_review * 2 // 5)
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
                        "listen": "reading",
                        "discussion": "review",
                    }
                    activity_type = type_normalization.get(activity_type, activity_type)

                    # ── Title-based type correction ──
                    # If GPT labelled something "video" but the title says
                    # interactive / hands-on / practice, override to practice
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

                    # Determine if this activity should get a video
                    should_assign_video = False

                    if is_visual_learner:
                        # For visual learners: assign videos to explicit video activities
                        # and activities with "watch"/"video" in the title
                        if activity_type == "video":
                            should_assign_video = True
                        elif videos_assigned_this_day < 1 and video_idx < len(youtube_videos):
                            if "watch" in activity_title or "video" in activity_title:
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

                    # For reading activities - assign documentation or articles
                    elif activity_type == "reading":
                        # Prefer uploaded slides for slide/lecture/review activities
                        slide_keywords = ['slide', 'lecture', 'notes', 'review', 'material', 'course']
                        if (uploaded_doc_resource
                                and slide_assignments_used < max_slide_assignments
                                and any(kw in activity_title for kw in slide_keywords)):
                            matched_resource = uploaded_doc_resource
                            resource_type_override = 'uploaded_slides'
                            slide_assignments_used += 1

                        # Check for specific keywords to determine resource type
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

                        # Last resort: uploaded slides if nothing else matched and still under cap
                        if not matched_resource and uploaded_doc_resource and slide_assignments_used < max_slide_assignments:
                            matched_resource = uploaded_doc_resource
                            resource_type_override = 'uploaded_slides'
                            slide_assignments_used += 1

                    # For practice/interactive activities - assign practice platforms
                    elif activity_type in ("practice", "interactive"):
                        if practice_idx < len(practice_resources):
                            matched_resource = practice_resources[practice_idx]
                            resource_type_override = 'practice'
                            practice_idx += 1
                        elif interactive_idx < len(interactive_resources):
                            matched_resource = interactive_resources[interactive_idx]
                            resource_type_override = 'interactive'
                            interactive_idx += 1

                    # For project activities - assign interactive tutorials or practice
                    elif activity_type == "project":
                        if is_kinesthetic_learner and interactive_idx < len(interactive_resources):
                            matched_resource = interactive_resources[interactive_idx]
                            resource_type_override = 'interactive'
                            interactive_idx += 1
                        elif practice_idx < len(practice_resources):
                            matched_resource = practice_resources[practice_idx]
                            resource_type_override = 'practice'
                            practice_idx += 1

                    # For quiz/assessment/review activities
                    elif activity_type in ["quiz", "assessment", "review"]:
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
            db.commit()

        return {
            "study_plan_id": str(study_plan.id),
            "topic": topic,
            "duration_days": duration_days,
            "plan_data": plan_data,
            "tokens_used": tokens_used,
            "created_at": study_plan.created_at.isoformat()
        }

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
            plan.completed_at = datetime.now()

        db.commit()
        logger.info(f"✅ Updated study plan progress: {completion}%")
        return True

    except Exception as e:
        logger.error(f"❌ Error updating study plan progress: {e}")
        db.rollback()
        return False
