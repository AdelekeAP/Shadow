"""
Quiz Generator Service - AI-Powered Knowledge Testing
Generates quizzes from topics or document content using GPT-4
"""
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from openai import OpenAI
from sqlalchemy.orm import Session

from app.models.quiz import Quiz, QuizAttempt
from app.models.smartstudy import StudyPlan, UploadedDocument

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = None
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        client = OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized for quiz generation")
    else:
        logger.warning("OPENAI_API_KEY not set - quiz generation disabled")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")


# Default question counts by quiz type
QUIZ_DEFAULTS = {
    "quick_quiz": {"count": 8, "description": "Quick knowledge check"},
    "exam_style": {"count": 20, "description": "Comprehensive exam simulation"},
    "topic_review": {"count": 12, "description": "Focused topic review"},
}


def build_quiz_prompt(topic: str, quiz_type: str, question_count: int,
                      difficulty: str, slide_content: Optional[str] = None,
                      course_code: Optional[str] = None) -> str:
    prompt = f"""You are an expert academic quiz generator for Pan-Atlantic University (PAU).

Generate a quiz with exactly {question_count} questions on the topic: "{topic}"

Quiz Type: {quiz_type} ({QUIZ_DEFAULTS.get(quiz_type, {}).get('description', '')})
Difficulty: {difficulty}
"""

    if course_code:
        prompt += f"Course: {course_code}\n"

    if slide_content:
        prompt += f"""
=== SOURCE MATERIAL ===
{slide_content[:50000]}
=== END SOURCE MATERIAL ===

CRITICAL: Generate questions DIRECTLY from the source material above.
Test specific facts, definitions, concepts, and relationships from the content.
Do NOT generate generic questions — every question must be traceable to the material.
"""

    prompt += f"""
Question type distribution:
- About 60% multiple_choice (4 options labeled A, B, C, D)
- About 25% true_false
- About 15% short_answer

Requirements:
- Each question must have a unique "topic_tag" indicating the specific subtopic it tests
- Include an "explanation" for why the correct answer is correct
- Progressive difficulty: start easier, get harder
- For multiple_choice: correct_answer should be the letter (A, B, C, or D)
- For true_false: correct_answer should be "True" or "False"
- For short_answer: correct_answer should be the key points expected

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "title": "Quiz: {topic}",
  "questions": [
    {{
      "id": 1,
      "type": "multiple_choice",
      "question": "What is ...?",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct_answer": "B",
      "explanation": "The correct answer is B because...",
      "topic_tag": "Subtopic Name",
      "difficulty": "easy"
    }},
    {{
      "id": 2,
      "type": "true_false",
      "question": "Statement here...",
      "options": ["True", "False"],
      "correct_answer": "True",
      "explanation": "This is true because...",
      "topic_tag": "Subtopic Name",
      "difficulty": "medium"
    }},
    {{
      "id": 3,
      "type": "short_answer",
      "question": "Explain ...",
      "options": null,
      "correct_answer": "Key points: 1) ... 2) ...",
      "explanation": "A complete answer should cover...",
      "topic_tag": "Subtopic Name",
      "difficulty": "hard"
    }}
  ]
}}"""

    return prompt


def parse_quiz_json(response_text: str) -> dict:
    cleaned = response_text.strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)

    data = json.loads(cleaned)

    if "questions" not in data or not isinstance(data["questions"], list):
        raise ValueError("Response missing 'questions' array")

    if len(data["questions"]) == 0:
        raise ValueError("Questions array is empty")

    for i, q in enumerate(data["questions"]):
        for field in ["id", "type", "question", "correct_answer", "topic_tag"]:
            if field not in q:
                raise ValueError(f"Question {i+1} missing '{field}'")
        if q["type"] == "multiple_choice" and (not q.get("options") or len(q["options"]) < 2):
            raise ValueError(f"Question {i+1} is MCQ but has insufficient options")

    return data


def generate_quiz(
    db: Session,
    user_id: str,
    topic: str,
    quiz_type: str = "quick_quiz",
    question_count: Optional[int] = None,
    time_limit_minutes: Optional[int] = None,
    difficulty_level: str = "mixed",
    course_id: Optional[str] = None,
    study_plan_id: Optional[str] = None,
    slide_content: Optional[str] = None,
) -> dict:
    if not client:
        raise ValueError("OpenAI client not initialized. Set OPENAI_API_KEY.")

    # Determine question count
    if question_count is None:
        question_count = QUIZ_DEFAULTS.get(quiz_type, {}).get("count", 10)

    # Determine source type
    source_type = "topic"
    if slide_content:
        source_type = "document"
    elif study_plan_id:
        source_type = "study_plan"
        plan = db.query(StudyPlan).filter(StudyPlan.id == study_plan_id).first()
        if plan and not topic:
            topic = plan.topic

    # Get course code if course_id provided
    course_code = None
    if course_id:
        from app.models.course import Course
        course = db.query(Course).filter(Course.id == course_id).first()
        if course:
            course_code = course.code

    # Build prompt and call GPT-4
    prompt = build_quiz_prompt(topic, quiz_type, question_count, difficulty_level, slide_content, course_code)

    logger.info(f"Generating {quiz_type} quiz: {question_count} questions on '{topic}'")

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert academic quiz generator. Return ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000,
            timeout=60.0,
        )

        gpt_response = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if response.usage else 0

        # Parse response
        quiz_data = parse_quiz_json(gpt_response)
    except Exception as e:
        logger.error(f"Quiz generation failed: {type(e).__name__}: {str(e)}")
        raise ValueError(f"Failed to generate quiz: {str(e)}")

    # Create Quiz record
    from uuid import UUID
    quiz = Quiz(
        user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
        study_plan_id=UUID(study_plan_id) if study_plan_id else None,
        course_id=UUID(course_id) if course_id else None,
        title=quiz_data.get("title", f"Quiz: {topic}"),
        topic=topic,
        quiz_type=quiz_type,
        questions=quiz_data["questions"],
        question_count=len(quiz_data["questions"]),
        time_limit_minutes=time_limit_minutes,
        difficulty_level=difficulty_level,
        source_type=source_type,
        slide_content=slide_content,
    )

    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    logger.info(f"Quiz created: {quiz.id} with {len(quiz_data['questions'])} questions")

    result = quiz.to_dict(include_answers=False)
    result["tokens_used"] = tokens_used
    return result


def grade_quiz(
    db: Session,
    user_id: str,
    quiz_id: str,
    answers: List[Dict[str, Any]],
    time_taken_seconds: Optional[int] = None,
    timed_out: bool = False,
) -> dict:
    from uuid import UUID

    quiz = db.query(Quiz).filter(
        Quiz.id == UUID(quiz_id),
        Quiz.user_id == UUID(user_id),
    ).first()

    if not quiz:
        raise ValueError("Quiz not found")

    questions = quiz.questions
    question_map = {q["id"]: q for q in questions}

    graded_answers = []
    correct_count = 0
    topic_results = {}  # topic_tag -> {correct: int, total: int}

    for answer in answers:
        q_id = answer.get("question_id")
        user_answer = answer.get("user_answer", "").strip()
        question = question_map.get(q_id)

        if not question:
            continue

        is_correct = False
        correct_answer = question["correct_answer"]

        if question["type"] in ("multiple_choice", "true_false"):
            is_correct = user_answer.upper().strip() == correct_answer.upper().strip()
        elif question["type"] == "short_answer":
            # For short answer, use GPT-4 to grade
            is_correct = grade_short_answer(question["question"], user_answer, correct_answer)

        if is_correct:
            correct_count += 1

        # Track per-topic performance
        tag = question.get("topic_tag", "General")
        if tag not in topic_results:
            topic_results[tag] = {"correct": 0, "total": 0}
        topic_results[tag]["total"] += 1
        if is_correct:
            topic_results[tag]["correct"] += 1

        graded_answers.append({
            "question_id": q_id,
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "explanation": question.get("explanation", ""),
            "topic_tag": tag,
        })

    total = len(graded_answers)
    score = round((correct_count / total) * 100, 2) if total > 0 else 0

    # Generate knowledge gap analysis
    knowledge_gaps = generate_knowledge_gaps(topic_results, score)

    # Create attempt record
    attempt = QuizAttempt(
        quiz_id=UUID(quiz_id),
        user_id=UUID(user_id),
        answers=graded_answers,
        score=score,
        correct_count=correct_count,
        total_questions=total,
        time_taken_seconds=time_taken_seconds,
        was_timed=quiz.time_limit_minutes is not None,
        timed_out=timed_out,
        knowledge_gaps=knowledge_gaps,
        completed_at=datetime.now(timezone.utc),
    )

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    logger.info(f"Quiz graded: {quiz_id} - Score: {score}% ({correct_count}/{total})")

    return attempt.to_dict()


def grade_short_answer(question: str, user_answer: str, correct_answer: str) -> bool:
    if not client or not user_answer:
        return False

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a strict academic grader. Return ONLY 'CORRECT' or 'INCORRECT'."},
                {"role": "user", "content": f"Question: {question}\nExpected answer: {correct_answer}\nStudent answer: {user_answer}\n\nIs the student's answer substantially correct? Reply ONLY with CORRECT or INCORRECT."}
            ],
            temperature=0,
            max_tokens=10,
            timeout=30.0,
        )
        result = response.choices[0].message.content.strip().upper()
        return "CORRECT" in result
    except Exception as e:
        logger.error(f"Error grading short answer: {e}")
        return False


def generate_knowledge_gaps(topic_results: dict, overall_score: float) -> dict:
    weak_topics = []
    strong_topics = []

    for tag, data in topic_results.items():
        pct = round((data["correct"] / data["total"]) * 100) if data["total"] > 0 else 0
        entry = {"topic": tag, "score_pct": pct, "correct": data["correct"], "total": data["total"]}
        if pct < 70:
            weak_topics.append(entry)
        else:
            strong_topics.append(entry)

    weak_topics.sort(key=lambda x: x["score_pct"])
    strong_topics.sort(key=lambda x: x["score_pct"], reverse=True)

    if overall_score >= 80:
        assessment = "Strong understanding overall. Focus on the few weak areas identified."
    elif overall_score >= 60:
        assessment = "Decent foundation but significant gaps remain. Review weak topics thoroughly."
    else:
        assessment = "Substantial knowledge gaps detected. Consider creating a focused study plan."

    recommendations = []
    for w in weak_topics[:3]:
        recommendations.append(f"Review '{w['topic']}' — scored {w['score_pct']}%")
    if overall_score < 70:
        recommendations.append("Consider creating a study plan targeting your weak areas")

    return {
        "weak_topics": weak_topics,
        "strong_topics": strong_topics,
        "overall_assessment": assessment,
        "study_recommendations": recommendations,
    }
