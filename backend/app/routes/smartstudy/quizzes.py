"""
Quiz Routes - AI-Powered Knowledge Testing
"""
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.models.quiz import Quiz, QuizAttempt
from app.models.smartstudy import StudyPlan
from app.schemas.smartstudy import QuizCreate, QuizSubmission
from app.utils.auth import get_current_user
from app.middleware.rate_limiter import limiter
from app.utils.ai_guard import require_ai_feature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quizzes", tags=["SmartStudy"])


@router.post("/")
@limiter.limit("10/minute")
async def create_quiz(
    request: Request,
    quiz_data: QuizCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _ai_check=Depends(require_ai_feature("ai_quizzes")),
):
    """Generate a quiz from a topic"""
    from app.services.quiz_generator import generate_quiz

    try:
        result = await generate_quiz(
            db=db,
            user_id=str(current_user.id),
            topic=quiz_data.topic,
            quiz_type=quiz_data.quiz_type,
            question_count=quiz_data.question_count,
            time_limit_minutes=quiz_data.time_limit_minutes,
            difficulty_level=quiz_data.difficulty_level or "mixed",
            course_id=quiz_data.course_id,
            study_plan_id=quiz_data.study_plan_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Quiz generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate quiz")


@router.post("/upload")
@limiter.limit("10/minute")
async def create_quiz_with_upload(
    request: Request,
    topic: str = Form(None),
    uploaded_file: UploadFile = File(None),
    quiz_type: str = Form("quick_quiz"),
    question_count: int = Form(None),
    time_limit_minutes: int = Form(None),
    difficulty_level: str = Form("mixed"),
    course_id: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _ai_check=Depends(require_ai_feature("ai_quizzes")),
):
    """Generate a quiz from an uploaded document"""
    import tempfile
    import os
    from app.services.quiz_generator import generate_quiz
    from app.services.document_processor import extract_text_from_file, extract_topics_with_gpt4

    if not uploaded_file and not topic:
        raise HTTPException(status_code=400, detail="Provide a topic or upload a document")

    slide_content = None
    extracted_topic = topic

    if uploaded_file:
        # Validate extension first (cheapest check)
        file_ext = uploaded_file.filename.split(".")[-1].lower() if uploaded_file.filename else ""
        if file_ext not in ("pdf", "pptx"):
            raise HTTPException(status_code=400, detail="Only PDF and PPTX files are supported")

        # Pre-validate file size if available (avoids reading entire file into memory)
        if uploaded_file.size is not None and uploaded_file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")

        # Read file bytes
        try:
            file_bytes = await uploaded_file.read()
        except Exception:
            raise HTTPException(status_code=400, detail="Failed to read uploaded file")

        # Validate size after reading (uploaded_file.size can be None on some servers)
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        if len(file_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")

        # Validate magic bytes to prevent file type spoofing
        MAGIC_BYTES = {"pdf": b"%PDF", "pptx": b"PK\x03\x04"}
        expected = MAGIC_BYTES[file_ext]
        if file_bytes[:len(expected)] != expected:
            raise HTTPException(status_code=400, detail=f"File content does not match {file_ext.upper()} format")

        # Write to temp file and extract text (run blocking I/O off event loop)
        def _process_document(data: bytes, ext: str):
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
                    tmp.write(data)
                    tmp_path = tmp.name
                return extract_text_from_file(tmp_path)
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        try:
            slide_content = await asyncio.to_thread(_process_document, file_bytes, file_ext)

            if not extracted_topic and slide_content:
                topics = await asyncio.to_thread(extract_topics_with_gpt4, slide_content[:3000])
                extracted_topic = topics.get("main_topic")
        except Exception as e:
            logger.error(f"Document processing failed: {e}", exc_info=True)
            raise HTTPException(status_code=422, detail=f"Could not extract content from {file_ext.upper()} file. The file may be corrupted or password-protected.")

    if not extracted_topic:
        extracted_topic = "General Knowledge"

    try:
        quiz_result = await generate_quiz(
            db=db,
            user_id=str(current_user.id),
            topic=extracted_topic,
            quiz_type=quiz_type,
            question_count=question_count,
            time_limit_minutes=time_limit_minutes,
            difficulty_level=difficulty_level,
            course_id=course_id,
            slide_content=slide_content,
        )
        quiz_result["extracted_topic"] = extracted_topic
        return quiz_result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Quiz generation with upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate quiz")


@router.post("/from-plan/{plan_id}")
@limiter.limit("10/minute")
async def create_quiz_from_plan(
    request: Request,
    plan_id: str,
    quiz_type: str = "topic_review",
    question_count: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _ai_check=Depends(require_ai_feature("ai_quizzes")),
):
    """Generate a quiz from an existing study plan"""
    from app.services.quiz_generator import generate_quiz

    plan_uuid = UUID(plan_id)
    plan = db.query(StudyPlan).filter(
        StudyPlan.id == plan_uuid,
        StudyPlan.user_id == current_user.id,
    ).first()

    if not plan:
        raise HTTPException(status_code=404, detail="Study plan not found")

    # Extract slide content from plan for grounded quiz generation
    slide_content = None
    if plan.plan_data and isinstance(plan.plan_data, dict):
        slide_content = plan.plan_data.get("_slide_content", "") or None

    try:
        result = await generate_quiz(
            db=db,
            user_id=str(current_user.id),
            topic=plan.topic,
            quiz_type=quiz_type,
            question_count=question_count,
            course_id=str(plan.course_id) if plan.course_id else None,
            study_plan_id=str(plan.id),
            slide_content=slide_content,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Quiz from plan failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate quiz from study plan")


@router.post("/from-plan/{plan_id}/section")
@limiter.limit("10/minute")
async def create_section_quiz(
    request: Request,
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _ai_check=Depends(require_ai_feature("ai_quizzes")),
):
    """Generate a quiz for a specific section (page range) of a study plan's slides"""
    from app.services.quiz_generator import generate_quiz
    from app.routes.smartstudy.study_plans import extract_relevant_slides

    body = await request.json()
    page_range = body.get("page_range")
    activity_description = body.get("activity_description", "")
    question_count = body.get("question_count", 5)

    if not page_range and not activity_description:
        raise HTTPException(status_code=400, detail="Provide page_range or activity_description")

    plan_uuid = UUID(plan_id)
    plan = db.query(StudyPlan).filter(
        StudyPlan.id == plan_uuid,
        StudyPlan.user_id == current_user.id,
    ).first()

    if not plan:
        raise HTTPException(status_code=404, detail="Study plan not found")

    # Extract slide content from plan
    full_slide_content = ""
    if plan.plan_data and isinstance(plan.plan_data, dict):
        full_slide_content = plan.plan_data.get("_slide_content", "")

    if not full_slide_content:
        raise HTTPException(status_code=400, detail="No slide content available for this plan. Section quizzes require uploaded slides.")

    # Extract only the relevant section
    section_content = extract_relevant_slides(full_slide_content, activity_description, page_range=page_range)

    section_label = f"pages {page_range}" if page_range else "selected section"
    section_topic = f"{plan.topic} — {section_label}"

    try:
        result = await generate_quiz(
            db=db,
            user_id=str(current_user.id),
            topic=section_topic,
            quiz_type="section_review",
            question_count=min(question_count, 10),
            course_id=str(plan.course_id) if plan.course_id else None,
            study_plan_id=str(plan.id),
            slide_content=section_content,
        )
        result["section_page_range"] = page_range
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Section quiz generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate section quiz")


@router.get("/")
async def list_quizzes(
    topic: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List user's quizzes"""
    query = db.query(Quiz).filter(Quiz.user_id == current_user.id)
    if topic:
        query = query.filter(Quiz.topic.ilike(f"%{topic}%"))
    quizzes = query.order_by(Quiz.created_at.desc()).all()

    results = []
    for q in quizzes:
        d = q.to_dict(include_answers=False)
        d["attempts_count"] = db.query(QuizAttempt).filter(QuizAttempt.quiz_id == q.id).count()
        best = db.query(QuizAttempt).filter(QuizAttempt.quiz_id == q.id).order_by(QuizAttempt.score.desc()).first()
        d["best_score"] = float(best.score) if best else None
        results.append(d)

    return results


@router.get("/{quiz_id}")
async def get_quiz(
    quiz_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a quiz for taking (answers stripped)"""
    quiz = db.query(Quiz).filter(
        Quiz.id == UUID(quiz_id),
        Quiz.user_id == current_user.id,
    ).first()

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    result = quiz.to_dict(include_answers=False)
    attempt_count = db.query(QuizAttempt).filter(
        QuizAttempt.quiz_id == quiz.id,
        QuizAttempt.user_id == current_user.id,
    ).count()
    result["attempts_count"] = attempt_count
    result["remaining_attempts"] = max(0, 5 - attempt_count)
    return result


@router.post("/{quiz_id}/submit")
@limiter.limit("10/minute")
async def submit_quiz(
    request: Request,
    quiz_id: str,
    submission: QuizSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit quiz answers and get graded results"""
    from app.services.quiz_generator import grade_quiz

    MAX_ATTEMPTS = 5

    # Check attempt limit
    attempt_count = db.query(QuizAttempt).filter(
        QuizAttempt.quiz_id == UUID(quiz_id),
        QuizAttempt.user_id == current_user.id,
    ).count()

    if attempt_count >= MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Maximum of {MAX_ATTEMPTS} attempts reached for this quiz. Generate a new quiz to continue practicing."
        )

    try:
        result = await grade_quiz(
            db=db,
            user_id=str(current_user.id),
            quiz_id=quiz_id,
            answers=[a.model_dump() for a in submission.answers],
            time_taken_seconds=submission.time_taken_seconds,
            timed_out=submission.timed_out,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Quiz submission failed for quiz {quiz_id}: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to grade quiz")


@router.get("/{quiz_id}/attempts")
async def get_quiz_attempts(
    quiz_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all attempts for a specific quiz"""
    attempts = db.query(QuizAttempt).filter(
        QuizAttempt.quiz_id == UUID(quiz_id),
        QuizAttempt.user_id == current_user.id,
    ).order_by(QuizAttempt.started_at.desc()).all()

    return [a.to_dict() for a in attempts]


@router.post("/{quiz_id}/study-weak-topics")
@limiter.limit("5/minute")
async def create_study_plan_from_quiz_gaps(
    request: Request,
    quiz_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a study plan targeting weak topics identified in a quiz attempt.
    Uses the original document content (if quiz was from an upload) to focus
    the study plan on the specific areas where the student struggled."""
    from app.services.study_plan_generator import generate_study_plan

    quiz = db.query(Quiz).filter(
        Quiz.id == UUID(quiz_id),
        Quiz.user_id == current_user.id,
    ).first()

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Get the latest attempt with knowledge gaps
    latest_attempt = db.query(QuizAttempt).filter(
        QuizAttempt.quiz_id == quiz.id,
        QuizAttempt.user_id == current_user.id,
    ).order_by(QuizAttempt.completed_at.desc()).first()

    if not latest_attempt or not latest_attempt.knowledge_gaps:
        raise HTTPException(status_code=400, detail="No quiz attempt with knowledge gaps found. Take the quiz first.")

    gaps = latest_attempt.knowledge_gaps
    weak_topics = gaps.get("weak_topics", [])

    if not weak_topics:
        raise HTTPException(status_code=400, detail="No weak topics found — you scored well! No study plan needed.")

    # Build a focused topic string from weak areas
    weak_names = [w["topic"] if isinstance(w, dict) else str(w) for w in weak_topics[:5]]
    focused_topic = f"{quiz.topic} — focusing on: {', '.join(weak_names)}"

    try:
        result = await generate_study_plan(
            db=db,
            user_id=str(current_user.id),
            topic=focused_topic,
            course_id=str(quiz.course_id) if quiz.course_id else None,
            trigger_type="quiz_gap_analysis",
            trigger_score=float(latest_attempt.score),
            slide_content=quiz.slide_content,
        )
        result["source"] = "quiz_gap_analysis"
        result["weak_topics"] = weak_names
        result["quiz_score"] = float(latest_attempt.score)
        return result
    except Exception as e:
        logger.error(f"Study plan from quiz gaps failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate study plan from quiz gaps")
