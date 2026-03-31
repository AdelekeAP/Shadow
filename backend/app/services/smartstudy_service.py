"""
SmartStudy Service - AI Learning Intervention System
Handles GPT-4 chat, context loading, and personalized study plan generation
"""
import asyncio
import logging
from typing import Optional, Dict, List, Any, Generator
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
import json

from app.models.user import User
from app.models.task import Task
from app.models.course import UserCourse, Course
from app.models.mood import MoodLog
from app.models.smartstudy import ChatConversation, ChatMessage, StudyPlan
from app.services.openai_client import (
    get_openai_client,
    call_with_retry,
    OpenAIError,
    OpenAIErrorType,
    CHAT_MODELS,
)
from app.services.cache_service import cache_get, cache_set, cache_delete

logger = logging.getLogger(__name__)


def invalidate_student_context_cache(user_id: int):
    """Remove cached student context for a specific user."""
    cache_key = f"student_context:{user_id}"
    cache_delete(cache_key)


def load_student_context(db: Session, user_id: str) -> Dict[str, Any]:
    """
    Load comprehensive student context for SmartStudy AI

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        Dict with student info, courses, tasks, moods, CGPA status
    """
    cache_key = f"student_context:{user_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}

        # Get enrolled courses with grades
        user_courses = db.query(UserCourse, Course).join(
            Course, UserCourse.course_id == Course.id
        ).filter(UserCourse.user_id == user_id).all()

        courses_data = []
        for uc, course in user_courses:
            courses_data.append({
                "code": course.code,
                "title": course.title,
                "credits": course.credits,
                "ca_score": float(uc.ca_score) if uc.ca_score else 0,
                "predicted_grade": uc.predicted_letter_grade,
                "predicted_score": float(uc.predicted_score) if uc.predicted_score else None,
                "completion_rate": float(uc.completion_rate) if uc.completion_rate else 0
            })

        # Get recent tasks (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        tasks = db.query(Task).filter(
            Task.user_id == user_id,
            Task.created_at >= thirty_days_ago
        ).order_by(Task.due_date.desc()).limit(20).all()

        tasks_data = []
        for task in tasks:
            tasks_data.append({
                "title": task.title,
                "topic": task.topic,
                "task_type": task.task_type,
                "weight": float(task.weight) if task.weight else 0,
                "earned_marks": float(task.earned_marks) if task.earned_marks else None,
                "is_completed": task.is_completed,
                "is_late": task.is_late,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "priority_score": float(task.priority_score) if task.priority_score else None
            })

        # Get recent moods (last 14 days)
        two_weeks_ago = datetime.now(timezone.utc) - timedelta(days=14)
        moods = db.query(MoodLog).filter(
            MoodLog.user_id == user_id,
            MoodLog.logged_at >= two_weeks_ago
        ).order_by(MoodLog.logged_at.desc()).limit(10).all()

        moods_data = []
        for mood in moods:
            moods_data.append({
                "mood_type": mood.mood_type,
                "energy_level": mood.energy_level,
                "primary_emotion": mood.primary_emotion,
                "note": mood.note,
                "logged_at": mood.logged_at.isoformat() if mood.logged_at else None
            })

        # Compile context
        context = {
            "student_info": {
                "name": user.full_name,
                "target_cgpa": float(user.target_cgpa) if user.target_cgpa else None,
                "current_cgpa": float(user.current_cgpa) if user.current_cgpa else None,
                "learning_style": user.learning_style,
                "entry_level": user.entry_level
            },
            "courses": courses_data,
            "recent_tasks": tasks_data,
            "recent_moods": moods_data,
            "cgpa_gap": (
                float(user.target_cgpa - user.current_cgpa)
                if user.target_cgpa and user.current_cgpa
                else None
            )
        }

        cache_set(cache_key, context, ttl=120)  # 2 min TTL

        return context

    except Exception as e:
        logger.error(f"Error loading student context: {e}")
        return {}


def build_system_prompt(context: Dict[str, Any]) -> str:
    """
    Build comprehensive system prompt for SmartStudy AI

    Args:
        context: Student context from load_student_context()

    Returns:
        System prompt string for GPT-4
    """
    student_info = context.get("student_info", {})
    courses = context.get("courses", [])
    moods = context.get("recent_moods", [])
    cgpa_gap = context.get("cgpa_gap")

    prompt = f"""You are SmartStudy, an AI learning coach integrated into Shadow, a goal-driven academic system for Pan-Atlantic University students.

**Student Profile:**
- Name: {student_info.get('name', 'Student')}
- Current CGPA: {student_info.get('current_cgpa', 'N/A')}/5.0
- Target CGPA: {student_info.get('target_cgpa', 'N/A')}/5.0
- Gap to target: {cgpa_gap if cgpa_gap else 'On track'}
- Learning style: {student_info.get('learning_style', 'Not specified')}
- Level: {student_info.get('entry_level', 'N/A')}

**Enrolled Courses ({len(courses)}):**
"""

    for course in courses[:5]:  # Show top 5
        prompt += f"- {course['code']}: {course['title']} | CA: {course['ca_score']}/35 | Predicted: {course['predicted_grade']}\n"

    if moods:
        recent_mood = moods[0]
        prompt += f"\n**Recent Mood:** {recent_mood.get('mood_type')} (Energy: {recent_mood.get('energy_level')}/5)\n"
        if recent_mood.get('primary_emotion'):
            prompt += f"Emotion detected: {recent_mood.get('primary_emotion')}\n"

    prompt += """
**Your Role:**
1. **Empathetic Coach**: Recognize student's emotional state and adapt your tone
2. **Topic Expert**: Provide clear explanations for CS topics (algorithms, data structures, web dev, ML, etc.)
3. **Strategic Advisor**: Help prioritize tasks based on CGPA impact
4. **Motivator**: Encourage without being patronizing
5. **Practical Helper**: Give actionable steps, not just theory

**Guidelines:**
- Be conversational but professional
- If student is struggling, offer supportive guidance and break down concepts
- If student is anxious/stressed, keep responses concise and reassuring
- If student is motivated/confident, provide deeper insights and challenges
- Always relate advice to their CGPA goal
- Use PAU grading scale (5.0 max, A=70+, B=60-69, C=50-59)
- Suggest specific topics to review based on their course progress
- When appropriate, recommend creating a study plan

**Avoid:**
- Being overly formal or academic
- Giving up on struggling students
- Ignoring their emotional state
- Overwhelming with too much information at once
"""

    return prompt


async def chat_with_smartstudy(
    db: Session,
    user_id: str,
    message: str,
    conversation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Handle chat interaction with SmartStudy AI

    Args:
        db: Database session
        user_id: User UUID
        message: User's message
        conversation_id: Optional existing conversation ID

    Returns:
        Dict with conversation_id, user_message, ai_response, tokens_used
    """
    try:
        # Load or create conversation
        if conversation_id:
            conversation = db.query(ChatConversation).filter(
                ChatConversation.id == conversation_id,
                ChatConversation.user_id == user_id
            ).first()
            if not conversation:
                return {"error": "Conversation not found"}
        else:
            # Create new conversation (flush to get ID, commit with first message)
            conversation = ChatConversation(user_id=user_id)
            db.add(conversation)
            db.flush()
            db.refresh(conversation)

        # Load student context
        context = load_student_context(db, user_id)
        system_prompt = build_system_prompt(context)

        # Get conversation history
        messages_history = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation.id
        ).order_by(ChatMessage.created_at.desc()).limit(10).all()

        # Reverse to chronological order (we fetched desc to limit efficiently)
        messages_history = list(reversed(messages_history))

        # Build messages for GPT-4
        gpt_messages = [
            {"role": "system", "content": system_prompt}
        ]

        # Add conversation history (last 10 messages to avoid token limit)
        for msg in messages_history:
            gpt_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # Add current user message
        gpt_messages.append({
            "role": "user",
            "content": message
        })

        # Call GPT-4 with retry/fallback (offload to thread to avoid blocking event loop)
        response = await asyncio.to_thread(
            call_with_retry,
            messages=gpt_messages,
            models=CHAT_MODELS,
            max_tokens=1024,
            temperature=0.7,
            timeout=60.0,
            stream=False,
        )

        ai_message = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        actual_model = str(response.model) if response.model else "unknown"

        # Save user message
        user_msg = ChatMessage(
            conversation_id=conversation.id,
            role="user",
            content=message,
            model_used=actual_model
        )
        db.add(user_msg)

        # Save AI response
        ai_msg = ChatMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=ai_message,
            tokens_used=tokens_used,
            model_used=actual_model
        )
        db.add(ai_msg)

        # Update conversation title if first message
        if not conversation.title:
            # Generate title from first message (first 50 chars)
            conversation.title = message[:50] + ("..." if len(message) > 50 else "")

        conversation.updated_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "conversation_id": str(conversation.id),
            "user_message": message,
            "ai_response": ai_message,
            "tokens_used": tokens_used,
            "created_at": ai_msg.created_at.isoformat()
        }

    except OpenAIError as e:
        logger.error(f"OpenAI error in chat_with_smartstudy: {e.error_type.value}")
        db.rollback()
        return {"error": e.user_message, "error_type": e.error_type.value}
    except Exception as e:
        logger.error(f"Error in chat_with_smartstudy: {e}")
        db.rollback()
        return {"error": str(e)}


def stream_chat_with_smartstudy(
    db: Session,
    user_id: str,
    message: str,
    conversation_id: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    Streaming version of chat_with_smartstudy.
    Yields SSE-formatted events: meta, token, done, error.
    """
    try:
        # Load or create conversation
        if conversation_id:
            conversation = db.query(ChatConversation).filter(
                ChatConversation.id == conversation_id,
                ChatConversation.user_id == user_id
            ).first()
            if not conversation:
                yield f'data: {json.dumps({"type": "error", "error_type": "invalid_request", "message": "Conversation not found"})}\n\n'
                return
        else:
            # Create new conversation (flush to get ID, commit with first message)
            conversation = ChatConversation(user_id=user_id)
            db.add(conversation)
            db.flush()
            db.refresh(conversation)

        # Send meta event with conversation_id immediately
        yield f'data: {json.dumps({"type": "meta", "conversation_id": str(conversation.id)})}\n\n'

        # Load student context + build system prompt
        context = load_student_context(db, user_id)
        system_prompt = build_system_prompt(context)

        # Get conversation history (last 10 only to avoid loading entire history)
        messages_history = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation.id
        ).order_by(ChatMessage.created_at.desc()).limit(10).all()
        messages_history = list(reversed(messages_history))

        gpt_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages_history:
            gpt_messages.append({"role": msg.role, "content": msg.content})
        gpt_messages.append({"role": "user", "content": message})

        # Call GPT-4 with streaming
        stream = call_with_retry(
            messages=gpt_messages,
            models=CHAT_MODELS,
            max_tokens=1024,
            temperature=0.7,
            timeout=60.0,
            stream=True,
        )

        # Iterate over streamed chunks
        full_content = ""
        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                full_content += delta.content
                yield f'data: {json.dumps({"type": "token", "content": delta.content})}\n\n'

        # Streaming responses don't reliably expose .model; use first model in chain
        stream_model = CHAT_MODELS[0] if CHAT_MODELS else "unknown"

        # Save user message
        user_msg = ChatMessage(
            conversation_id=conversation.id,
            role="user",
            content=message,
            model_used=stream_model,
        )
        db.add(user_msg)

        # Save AI response
        ai_msg = ChatMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=full_content,
            model_used=stream_model,
        )
        db.add(ai_msg)

        # Update conversation title if first message
        if not conversation.title:
            conversation.title = message[:50] + ("..." if len(message) > 50 else "")

        conversation.updated_at = datetime.now(timezone.utc)
        db.commit()

        # Send done event
        yield f'data: {json.dumps({"type": "done", "conversation_id": str(conversation.id), "created_at": ai_msg.created_at.isoformat()})}\n\n'

    except OpenAIError as e:
        logger.error(f"OpenAI error in stream_chat: {e.error_type.value}")
        db.rollback()
        yield f'data: {json.dumps({"type": "error", "error_type": e.error_type.value, "message": e.user_message})}\n\n'
    except Exception as e:
        logger.error(f"Error in stream_chat: {e}")
        db.rollback()
        yield f'data: {json.dumps({"type": "error", "error_type": "unknown", "message": "An unexpected error occurred. Please try again."})}\n\n'
    finally:
        db.close()  # Explicitly close session — generators outlive FastAPI's dependency scope


def check_smartstudy_triggers(db: Session, user_id: str) -> Dict[str, Any]:
    """
    Check if user meets criteria for SmartStudy recommendation

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        Dict with triggered status, reasons, and urgency level
    """
    context = load_student_context(db, user_id)
    triggers = []
    urgency = "none"  # none, low, medium, high, critical

    # Get user info
    student_info = context.get("student_info", {})
    cgpa_gap = context.get("cgpa_gap")
    tasks = context.get("recent_tasks", [])
    moods = context.get("recent_moods", [])
    courses = context.get("courses", [])

    # TRIGGER 1: Overdue tasks (High urgency)
    now = datetime.now(timezone.utc)

    def _parse_due_date(due_date_str: str) -> datetime:
        """Parse ISO datetime string; attach UTC if naive."""
        dt = datetime.fromisoformat(due_date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    overdue_tasks = [t for t in tasks if t.get("due_date") and
                     _parse_due_date(t["due_date"]) < now and
                     not t.get("is_completed")]

    if len(overdue_tasks) >= 2:
        triggers.append({
            "type": "overdue_tasks",
            "title": f"You have {len(overdue_tasks)} overdue tasks",
            "message": f"Let SmartStudy help you prioritize and catch up on your {len(overdue_tasks)} overdue assignments.",
            "urgency": "high",
            "icon": "⚠️",
            "suggested_prompt": f"I have {len(overdue_tasks)} overdue tasks. How should I tackle them?"
        })
        if urgency in ["none", "low", "medium"]:
            urgency = "high"

    # TRIGGER 2: CGPA gap (Medium to Critical urgency)
    if cgpa_gap and cgpa_gap > 0.1:
        urgency_level = "critical" if cgpa_gap > 0.5 else "high" if cgpa_gap > 0.3 else "medium"
        triggers.append({
            "type": "cgpa_gap",
            "title": f"You're {cgpa_gap:.2f} points below your target CGPA",
            "message": f"SmartStudy can help create a personalized plan to reach your {student_info.get('target_cgpa', 'target')} CGPA goal.",
            "urgency": urgency_level,
            "icon": "📉",
            "suggested_prompt": "I'm behind on my CGPA goal. What's the best strategy to improve?"
        })
        if urgency_level == "critical" or (urgency_level == "high" and urgency != "critical"):
            urgency = urgency_level

    # TRIGGER 3: Negative mood patterns (High urgency)
    if moods:
        recent_negative = sum(1 for m in moods[:3] if m.get("primary_emotion") in
                            ["anxiety", "fear", "sadness", "stress", "overwhelm"])
        if recent_negative >= 2:
            triggers.append({
                "type": "negative_mood",
                "title": "You seem to be feeling stressed lately",
                "message": "SmartStudy can provide personalized support and help you manage academic pressure.",
                "urgency": "high",
                "icon": "😰",
                "suggested_prompt": "I'm feeling overwhelmed with my workload. Can you help?"
            })
            if urgency in ["none", "low", "medium"]:
                urgency = "high"

    # TRIGGER 4: Low energy levels (Medium urgency)
    if moods:
        recent_low_energy = sum(1 for m in moods[:3] if m.get("energy_level", 5) <= 2)
        if recent_low_energy >= 2:
            triggers.append({
                "type": "low_energy",
                "title": "Your energy levels have been low",
                "message": "Let SmartStudy suggest study techniques optimized for when you're feeling tired.",
                "urgency": "medium",
                "icon": "🔋",
                "suggested_prompt": "I'm low on energy. How can I study effectively?"
            })
            if urgency in ["none", "low"]:
                urgency = "medium"

    # TRIGGER 5: Many incomplete tasks (Medium urgency)
    incomplete_count = sum(1 for t in tasks if not t.get("is_completed"))
    if incomplete_count >= 8:
        triggers.append({
            "type": "task_overload",
            "title": f"{incomplete_count} pending tasks detected",
            "message": "SmartStudy can help you prioritize based on deadlines, weights, and CGPA impact.",
            "urgency": "medium",
            "icon": "📚",
            "suggested_prompt": f"I have {incomplete_count} tasks. What should I focus on first?"
        })
        if urgency in ["none", "low"]:
            urgency = "medium"

    # TRIGGER 6: Failing/low-performing courses (High urgency)
    low_performing_courses = [c for c in courses if
                             (c.get("predicted_grade") in ["D", "E", "F"]) or
                             (c.get("ca_score", 0) < 15)]  # Less than 15/35 CA

    if low_performing_courses:
        course_names = ", ".join([c["code"] for c in low_performing_courses[:2]])
        triggers.append({
            "type": "low_grades",
            "title": f"Struggling in {len(low_performing_courses)} course(s)",
            "message": f"Get targeted help for {course_names} and improve your understanding.",
            "urgency": "high",
            "icon": "📕",
            "suggested_prompt": f"I'm struggling with {course_names}. What should I do?"
        })
        if urgency in ["none", "low", "medium"]:
            urgency = "high"

    # TRIGGER 7: Recent late submissions (Medium urgency)
    late_tasks = sum(1 for t in tasks if t.get("is_late"))
    if late_tasks >= 3:
        triggers.append({
            "type": "late_pattern",
            "title": f"{late_tasks} late submissions detected",
            "message": "SmartStudy can help you build better time management habits.",
            "urgency": "medium",
            "icon": "⏰",
            "suggested_prompt": "I keep submitting tasks late. How can I improve my time management?"
        })
        if urgency in ["none", "low"]:
            urgency = "medium"

    # TRIGGER 8: First-time user with no chat history (Low urgency)
    chat_count = db.query(ChatConversation).filter(
        ChatConversation.user_id == user_id
    ).count()

    if chat_count == 0 and (incomplete_count > 3 or (cgpa_gap and cgpa_gap > 0)):
        triggers.append({
            "type": "new_user",
            "title": "Welcome to SmartStudy!",
            "message": "Get AI-powered help with your courses, tasks, and study planning.",
            "urgency": "low",
            "icon": "🎓",
            "suggested_prompt": "What can SmartStudy help me with?"
        })
        if urgency == "none":
            urgency = "low"

    return {
        "should_trigger": len(triggers) > 0,
        "urgency": urgency,
        "triggers": triggers,
        "trigger_count": len(triggers),
        "primary_trigger": triggers[0] if triggers else None
    }


def get_suggested_prompts(db: Session, user_id: str) -> List[Dict[str, str]]:
    """
    Generate contextual suggested prompts based on student's current state

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        List of suggested prompts
    """
    context = load_student_context(db, user_id)
    prompts = []

    # Check if student is struggling
    cgpa_gap = context.get("cgpa_gap")
    if cgpa_gap and cgpa_gap > 0.2:
        prompts.append({
            "prompt": "I'm behind on my CGPA goal. How can I catch up?",
            "category": "struggling",
            "icon": "⚠️"
        })

    # Check recent mood
    moods = context.get("recent_moods", [])
    if moods and moods[0].get("primary_emotion") in ["anxiety", "fear", "sadness"]:
        prompts.append({
            "prompt": "I'm feeling overwhelmed. Can you help me prioritize?",
            "category": "struggling",
            "icon": "😰"
        })

    # Check for incomplete tasks
    tasks = context.get("recent_tasks", [])
    incomplete_count = sum(1 for t in tasks if not t.get("is_completed"))
    if incomplete_count > 5:
        prompts.append({
            "prompt": f"I have {incomplete_count} pending tasks. What should I focus on?",
            "category": "planning",
            "icon": "📝"
        })

    # Always include general prompts
    prompts.extend([
        {
            "prompt": "Can you explain [topic] in simple terms?",
            "category": "clarification",
            "icon": "💡"
        },
        {
            "prompt": "Help me create a study plan for [course]",
            "category": "planning",
            "icon": "📅"
        },
        {
            "prompt": "I just failed a test. What should I do?",
            "category": "struggling",
            "icon": "😔"
        }
    ])

    return prompts[:5]  # Return top 5
