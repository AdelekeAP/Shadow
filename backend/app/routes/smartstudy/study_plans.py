"""
SmartStudy Study Plan Endpoints (Phase 2)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import os
import tempfile
from datetime import datetime

from app.database import get_db
from app.utils.auth import get_current_user
from app.middleware.rate_limiter import limiter
from app.models.user import User
from app.models.course import Course
from app.models.smartstudy import StudyPlan, StudyPlanResource
from app.schemas.smartstudy import (
    StudyPlanCreate,
    StudyPlanResponse,
    StudyPlanUpdate,
    ResourceClickUpdate,
    ResourceCompletionUpdate,
    ResourceReportCreate,
)
from app.services.study_plan_generator import (
    generate_study_plan,
    get_study_plan,
    update_study_plan_progress,
)
from app.services.document_processor import (
    process_document_for_study_plan,
    validate_file,
)
from app.services.library_service import contribute_to_library
from app.services.cache_service import cache_delete_pattern

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/study-plans",
    response_model=dict,
    operation_id="generate_study_plan",
    summary="Generate a new AI-powered study plan",
)
@limiter.limit("5/minute")
async def create_study_plan(
    request: Request,
    plan_data: StudyPlanCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a new AI-powered study plan

    - **topic**: Topic to study (e.g., "Binary Search Trees")
    - **course_id**: Optional - link to specific course
    - **duration_days**: Optional - auto-calculated if not provided (5-14 days)
    - **trigger_type**: reactive, proactive, preventive, or exploratory
    """
    try:
        result = generate_study_plan(
            db=db,
            user_id=str(current_user.id),
            topic=plan_data.topic,
            course_id=str(plan_data.course_id) if plan_data.course_id else None,
            duration_days=plan_data.duration_days,
            difficulty_level=plan_data.difficulty_level or "auto",
            trigger_type=plan_data.trigger_type,
            trigger_task_id=str(plan_data.trigger_task_id) if plan_data.trigger_task_id else None,
            trigger_score=plan_data.trigger_score,
            learning_style=plan_data.learning_style
        )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_study_plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/study-plans/upload",
    response_model=dict,
    operation_id="upload_document_for_study_plan",
    summary="Generate study plan with optional document upload",
)
@limiter.limit("5/minute")
async def create_study_plan_with_upload(
    request: Request,
    topic: str = Form(None),
    uploaded_file: UploadFile = File(None),
    course_id: str = Form(None),
    duration_days: int = Form(None),
    difficulty_level: str = Form("auto"),
    learning_style: str = Form(None),
    trigger_type: str = Form("student_request"),
    is_school_material: bool = Form(False),
    week_number: int = Form(None),
    library_document_id: str = Form(None),  # NEW: Use existing library document
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate study plan with optional document upload (PDF/PPTX)

    - **topic**: Optional - topic to study (can be extracted from file)
    - **uploaded_file**: Optional - PDF or PPTX file
    - **course_id**: Optional - link to specific course
    - **duration_days**: Optional - auto-calculated if not provided
    - **difficulty_level**: Optional - beginner/intermediate/advanced/auto
    - **learning_style**: Optional - visual/audio/reading/kinesthetic
    - **trigger_type**: Optional - student_request (default)
    - **is_school_material**: If true, contributes document to learning library
    - **week_number**: Optional week (1-15) for library organization
    - **library_document_id**: Optional - use existing library document instead of uploading

    Note: Must provide either topic OR uploaded_file OR library_document_id
    """
    try:
        slide_content = None
        extracted_topic = None
        file_info = None
        file_content_bytes = None  # Store file content for library contribution
        library_doc = None  # Hoisted to outer scope for reuse

        # Validate: Must provide either topic, file, or library document
        if not topic and not uploaded_file and not library_document_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please provide either a topic, upload a document, or select from library"
            )

        # Handle library document selection
        if library_document_id and not uploaded_file:
            # Validate UUID format before using in query
            try:
                library_document_uuid = UUID(library_document_id)
            except (ValueError, AttributeError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid library_document_id format"
                )

            logger.info(f"📚 Using library document: {library_document_id}")

            # Fetch library document
            from app.models.library import LibraryDocument
            library_doc = db.query(LibraryDocument).filter(
                LibraryDocument.id == library_document_uuid
            ).first()

            if not library_doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Library document not found"
                )

            # Check access (must be public or owned by user)
            if not library_doc.is_public and str(library_doc.uploaded_by) != str(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this document"
                )

            # Use extracted text from library document
            slide_content = library_doc.extracted_text or ""
            extracted_topic = library_doc.topic
            file_info = {
                "name": library_doc.file_name,
                "size_mb": round(library_doc.file_size / (1024 * 1024), 2),
                "type": library_doc.file_type
            }

            # Use library document's course if not specified
            if not course_id:
                course_id = str(library_doc.course_id)

            # Use topic from library if not provided
            if not topic:
                topic = extracted_topic

            logger.info(f"✅ Loaded library document: {library_doc.file_name}")
            logger.info(f"   Using {len(slide_content)} characters of content")

        # Process uploaded file if provided
        if uploaded_file:
            logger.info(f"📄 Processing uploaded file: {uploaded_file.filename}")

            # Validate file type
            file_ext = uploaded_file.filename.lower().split('.')[-1]
            if file_ext not in ['pdf', 'pptx', 'ppt']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file type: .{file_ext}. Only PDF and PPTX are supported."
                )

            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as temp_file:
                # Read and write file content
                content = await uploaded_file.read()
                file_content_bytes = content  # Store for library contribution
                temp_file.write(content)
                temp_file_path = temp_file.name

            try:
                # Process document
                result = process_document_for_study_plan(
                    file_path=temp_file_path,
                    topic_hint=topic  # Use provided topic as hint
                )

                if not result["success"]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=result["error"]
                    )

                slide_content = result["extracted_text"]
                extracted_topic = result["main_topic"]
                file_info = result.get("file_info")

                logger.info(f"✅ Extracted {len(slide_content)} characters from {uploaded_file.filename}")
                logger.info(f"   Detected topic: {extracted_topic}")

                # Use extracted topic if no topic provided
                if not topic:
                    topic = extracted_topic

            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file: {e}")

        # Build document metadata for resource injection (reuse library_doc from above)
        doc_filename = None
        doc_view_url = None
        if uploaded_file:
            doc_filename = uploaded_file.filename
        elif library_doc:
            doc_filename = library_doc.file_name
            doc_view_url = f"/api/v1/library/documents/{str(library_doc.id)}/view"

        # Generate study plan
        plan_result = generate_study_plan(
            db=db,
            user_id=str(current_user.id),
            topic=topic,
            course_id=course_id,
            duration_days=duration_days,
            difficulty_level=difficulty_level,
            trigger_type=trigger_type,
            learning_style=learning_style,
            slide_content=slide_content,  # Pass extracted content
            document_filename=doc_filename,
            document_view_url=doc_view_url,
        )

        if "error" in plan_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=plan_result["error"]
            )

        # Always save uploaded files to library so slides remain viewable.
        # Public if marked as school material, private otherwise.
        library_result = None
        if uploaded_file and course_id:
            logger.info(f"📚 Saving document to library (public={is_school_material})...")

            library_result = contribute_to_library(
                db=db,
                user_id=str(current_user.id),
                course_id=course_id,
                topic=topic or extracted_topic or "Study Material",
                file_content=file_content_bytes,
                file_name=uploaded_file.filename,
                file_type=file_ext,
                extracted_text=slide_content or "",
                week_number=week_number,
                key_topics=[],  # Could extract from AI analysis later
                is_public=is_school_material  # Private unless explicitly shared
            )

            if library_result.get("success"):
                lib_doc_id = library_result.get('library_document_id')
                logger.info(f"✅ Document added to library: {lib_doc_id}")
                cache_delete_pattern("library:browse:*")
                cache_delete_pattern("library:stats*")
                cache_delete_pattern(f"library:contributions:{current_user.id}")

                # Backfill uploaded_slides resources with the library view URL
                if lib_doc_id and plan_result.get("study_plan_id"):
                    from app.models.smartstudy import StudyPlanResource
                    view_url = f"/api/v1/library/documents/{lib_doc_id}/view"
                    db.query(StudyPlanResource).filter(
                        StudyPlanResource.study_plan_id == plan_result["study_plan_id"],
                        StudyPlanResource.resource_type == "uploaded_slides",
                        StudyPlanResource.resource_url.is_(None),
                    ).update({"resource_url": view_url}, synchronize_session="fetch")
                    db.commit()
                    logger.info(f"📎 Backfilled uploaded_slides resources with library URL: {view_url}")

            elif library_result.get("is_duplicate"):
                logger.info(f"📋 Document already exists in library (duplicate detected)")

        # Add file info to response
        return {
            **plan_result,
            "document_processed": uploaded_file is not None,
            "extracted_topic": extracted_topic,
            "file_info": file_info,
            "library_contribution": library_result if library_result else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_study_plan_with_upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/study-plans",
    response_model=List[StudyPlanResponse],
    operation_id="list_study_plans",
    summary="List all study plans for current user",
)
async def get_user_study_plans(
    active_only: bool = True,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all study plans for current user

    - **active_only**: If true, only return active (incomplete) plans
    - **limit**: Max plans per page (1-100, default 20)
    - **offset**: Number of plans to skip (default 0)
    """
    try:
        query = db.query(StudyPlan).filter(StudyPlan.user_id == current_user.id)

        if active_only:
            query = query.filter(StudyPlan.is_active == True)

        plans = query.order_by(StudyPlan.created_at.desc()).limit(limit).offset(offset).all()

        # Enrich with resources
        result = []
        for plan in plans:
            resources = db.query(StudyPlanResource).filter(
                StudyPlanResource.study_plan_id == plan.id
            ).order_by(
                StudyPlanResource.day_number,
                StudyPlanResource.order_in_day
            ).all()

            plan_dict = plan.to_dict()
            plan_dict["resources"] = [r.to_dict() for r in resources]
            result.append(plan_dict)

        return result

    except Exception as e:
        logger.error(f"Error in get_user_study_plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/study-plans/{plan_id}",
    response_model=dict,
    operation_id="get_study_plan",
    summary="Get a specific study plan by ID",
)
async def get_single_study_plan(
    plan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific study plan by ID with all resources
    """
    try:
        plan_data = get_study_plan(db, str(current_user.id), str(plan_id))

        if not plan_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study plan not found"
            )

        return plan_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_single_study_plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.patch(
    "/study-plans/{plan_id}",
    response_model=dict,
    operation_id="update_study_plan",
    summary="Update study plan progress",
)
async def update_study_plan(
    plan_id: UUID,
    update_data: StudyPlanUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update study plan progress

    - **completion_percentage**: Progress (0-100)
    - **is_active**: Mark as inactive when completed
    - **after_score**: Score after intervention (for effectiveness tracking)
    """
    try:
        plan = db.query(StudyPlan).filter(
            StudyPlan.id == plan_id,
            StudyPlan.user_id == current_user.id
        ).first()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study plan not found"
            )

        # Update fields
        if update_data.completion_percentage is not None:
            plan.completion_percentage = update_data.completion_percentage

            # Auto-complete if 100%
            if update_data.completion_percentage >= 100:
                plan.is_active = False
                plan.completed_at = datetime.now()

        if update_data.is_active is not None:
            plan.is_active = update_data.is_active

            if not update_data.is_active and not plan.completed_at:
                plan.completed_at = datetime.now()

        if update_data.before_score is not None:
            plan.before_score = update_data.before_score

        if update_data.after_score is not None:
            plan.after_score = update_data.after_score

            # Calculate effectiveness if we have before score
            if plan.before_score is not None:
                plan.effectiveness_score = update_data.after_score - float(plan.before_score)

        if update_data.completed_days is not None:
            plan.completed_days = update_data.completed_days

        db.commit()
        db.refresh(plan)

        # Invalidate analytics cache on plan completion or score updates
        if (update_data.is_active is not None and not update_data.is_active) or \
           update_data.after_score is not None or \
           (update_data.completion_percentage is not None and update_data.completion_percentage >= 100):
            cache_delete_pattern("analytics:*")

        # Send notification on plan completion
        if plan.completion_percentage >= 100 and plan.after_score is None:
            try:
                from app.services.notification_service import NotificationService
                from app.models.notification import NotificationType, NotificationPriority
                ns = NotificationService(db)
                ns.create_notification(
                    user_id=plan.user_id,
                    title="Study Plan Complete!",
                    message=f"You finished your plan for \"{plan.topic}\". Rate your knowledge now to track improvement.",
                    notification_type=NotificationType.STUDY_PLAN.value if hasattr(NotificationType, 'STUDY_PLAN') else NotificationType.SYSTEM.value,
                    priority=NotificationPriority.MEDIUM.value,
                    study_plan_id=plan.id,
                    action_url="/smartstudy",
                )
            except Exception as notif_err:
                logger.warning(f"Failed to send completion notification: {notif_err}")

        return {
            "message": "Study plan updated successfully",
            "study_plan_id": str(plan.id),
            "completion_percentage": float(plan.completion_percentage),
            "is_active": plan.is_active
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_study_plan: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/study-plans/{plan_id}/resources/{resource_id}/click",
    operation_id="click_resource",
    summary="Track when a student clicks on a resource link",
)
async def track_resource_click(
    plan_id: UUID,
    resource_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Track when a student clicks on a resource link
    """
    try:
        # Verify plan belongs to user
        plan = db.query(StudyPlan).filter(
            StudyPlan.id == plan_id,
            StudyPlan.user_id == current_user.id
        ).first()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study plan not found"
            )

        # Update resource
        resource = db.query(StudyPlanResource).filter(
            StudyPlanResource.id == resource_id,
            StudyPlanResource.study_plan_id == plan_id
        ).first()

        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )

        resource.clicked = True
        resource.clicked_at = datetime.now()

        db.commit()

        return {"message": "Resource click tracked"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in track_resource_click: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/study-plans/{plan_id}/resources/{resource_id}/complete",
    operation_id="complete_resource",
    summary="Mark a resource as completed and optionally rate it",
)
async def mark_resource_complete(
    plan_id: UUID,
    resource_id: UUID,
    completion_data: ResourceCompletionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a resource as completed and optionally rate it

    - **completed**: Set to true
    - **helpful_rating**: 1-5 stars (optional)
    """
    try:
        # Verify plan belongs to user
        plan = db.query(StudyPlan).filter(
            StudyPlan.id == plan_id,
            StudyPlan.user_id == current_user.id
        ).first()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study plan not found"
            )

        # Update resource
        resource = db.query(StudyPlanResource).filter(
            StudyPlanResource.id == resource_id,
            StudyPlanResource.study_plan_id == plan_id
        ).first()

        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )

        resource.completed = completion_data.completed

        if completion_data.helpful_rating:
            resource.helpful_rating = completion_data.helpful_rating

        db.commit()

        # Invalidate analytics cache on resource completion
        if completion_data.completed:
            cache_delete_pattern("analytics:*")

        return {"message": "Resource marked as complete"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in mark_resource_complete: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# Report Broken Resource Endpoint
# ============================================================================

@router.post(
    "/study-plans/{plan_id}/resources/{resource_id}/report",
    operation_id="report_resource",
    summary="Report a broken or irrelevant resource",
)
async def report_resource(
    plan_id: UUID,
    resource_id: UUID,
    report_data: ResourceReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Report a resource as broken, irrelevant, or outdated.

    - **reason**: broken_link | irrelevant | outdated
    """
    try:
        plan = db.query(StudyPlan).filter(
            StudyPlan.id == plan_id,
            StudyPlan.user_id == current_user.id
        ).first()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study plan not found"
            )

        resource = db.query(StudyPlanResource).filter(
            StudyPlanResource.id == resource_id,
            StudyPlanResource.study_plan_id == plan_id
        ).first()

        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )

        resource.helpful_rating = 0
        resource.report_reason = report_data.reason
        resource.reported_at = datetime.now()

        db.commit()

        # Invalidate article cache for this URL
        if resource.resource_url:
            try:
                from app.services.article_search_service import invalidate_article_cache
                invalidate_article_cache(resource.resource_url, db=db)
            except Exception as e:
                logger.warning(f"Cache invalidation failed: {e}")

        return {"message": "Resource reported successfully", "reason": report_data.reason}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in report_resource: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


def _estimate_duration(script: str) -> str:
    """Estimate audio duration from script word count (~150 WPM)."""
    if not script:
        return "3-5 minutes"
    words = len(script.split())
    minutes = max(1, round(words / 150))
    return f"~{minutes} minute{'s' if minutes != 1 else ''}"


# ============================================================================
# Audio Summary Endpoints
# ============================================================================

@router.post(
    "/study-plans/{plan_id}/resources/{resource_id}/audio",
    operation_id="generate_audio_summary",
    summary="Generate an audio summary for a resource",
)
@limiter.limit("10/minute")
async def generate_audio(
    request: Request,
    plan_id: UUID,
    resource_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a podcast-style audio summary for a study plan resource.
    Audio is lazily generated on first request and cached.
    """
    try:
        plan = db.query(StudyPlan).filter(
            StudyPlan.id == plan_id,
            StudyPlan.user_id == current_user.id
        ).first()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study plan not found"
            )

        resource = db.query(StudyPlanResource).filter(
            StudyPlanResource.id == resource_id,
            StudyPlanResource.study_plan_id == plan_id
        ).first()

        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )

        # Return cached audio if available
        if resource.audio_file_path:
            return {
                "audio_url": f"/api/v1/smartstudy/audio/{resource.audio_file_path}",
                "script": resource.audio_script,
                "duration_estimate": _estimate_duration(resource.audio_script),
                "cached": True,
            }

        # Generate new audio
        from app.services.audio_summary_service import get_audio_summary_service
        audio_service = get_audio_summary_service()

        if not audio_service.is_available:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Audio generation not configured. Use NotebookLM as an alternative."
            )

        result = audio_service.get_or_generate(
            resource_id=str(resource.id),
            topic=plan.topic,
            title=resource.resource_title or "Study Activity",
            description=resource.resource_description or "",
        )

        script = result.get("script")

        # TTS failed — return script as fallback (no audio file)
        if result.get("tts_failed"):
            # Save script even without audio so it can be shown
            if script:
                resource.audio_script = script
                db.commit()

            return {
                "audio_url": None,
                "script": script,
                "duration_estimate": _estimate_duration(script),
                "cached": False,
                "script_only": True,
                "tts_error": result.get("tts_error", "Audio synthesis unavailable"),
            }

        # Store just the filename, not the full path
        filename = os.path.basename(result["filepath"])

        resource.audio_file_path = filename
        resource.audio_script = script
        resource.audio_generated_at = datetime.now()
        db.commit()

        return {
            "audio_url": f"/api/v1/smartstudy/audio/{filename}",
            "script": script,
            "duration_estimate": _estimate_duration(script),
            "cached": False,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# Library Upload Endpoint
# ============================================================================

@router.post(
    "/library/upload",
    response_model=dict,
    operation_id="upload_document_to_library",
    summary="Upload a document directly to the learning library",
)
@limiter.limit("10/hour")
async def upload_to_library(
    request: Request,
    file: UploadFile = File(...),
    topic: str = Form(...),
    course_id: str = Form(...),
    week_number: Optional[int] = Form(None),
    is_public: bool = Form(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a document directly to the learning library

    **Purpose**: Students can share course materials with classmates

    - **file**: PDF or PPTX file (max 10MB)
    - **topic**: Document topic/title
    - **course_id**: Course UUID this document belongs to
    - **week_number**: Optional week number (1-15)
    - **is_public**: Make document accessible to other students (default: true)

    **Returns**: Upload result with document ID or duplicate notification
    """
    try:
        logger.info(f"📤 Library upload from {current_user.full_name}: {file.filename}")

        # Validate file type
        file_ext = file.filename.lower().split('.')[-1]
        if file_ext not in ['pdf', 'pptx', 'ppt']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: .{file_ext}. Only PDF and PPTX are supported."
            )

        # Read file in chunks with size limit to prevent OOM on oversized uploads
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        chunks = []
        total_size = 0
        while True:
            chunk = await file.read(8192)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File too large. Maximum size is 10MB."
                )
            chunks.append(chunk)
        file_content = b"".join(chunks)
        file_size = total_size

        # Verify course exists
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )

        # Verify user is enrolled in this course
        from app.models.course import UserCourse
        enrollment = db.query(UserCourse).filter(
            UserCourse.user_id == current_user.id,
            UserCourse.course_id == course_id
        ).first()
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be enrolled in this course to upload documents"
            )

        # Extract text from document
        extracted_text = ""
        try:
            # Save temporarily for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name

            try:
                result = process_document_for_study_plan(
                    file_path=temp_file_path,
                    topic_hint=topic
                )
                if result["success"]:
                    extracted_text = result["extracted_text"]
                    logger.info(f"✅ Extracted {len(extracted_text)} characters")
            finally:
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file: {e}")
        except Exception as e:
            logger.warning(f"⚠️ Text extraction failed: {e}, continuing without text")

        # Contribute to library
        library_result = contribute_to_library(
            db=db,
            user_id=str(current_user.id),
            course_id=course_id,
            topic=topic,
            file_content=file_content,
            file_name=file.filename,
            file_type=file_ext,
            extracted_text=extracted_text,
            week_number=week_number,
            key_topics=[],  # Could add AI topic extraction later
            is_public=is_public
        )

        if library_result.get("is_duplicate"):
            return {
                "success": True,
                "message": "This document already exists in the library",
                "is_duplicate": True,
                "existing_document_id": library_result.get("existing_document_id")
            }

        if library_result.get("success"):
            logger.info(f"✅ Document uploaded to library: {library_result.get('library_document_id')}")
            cache_delete_pattern("library:browse:*")
            cache_delete_pattern("library:stats*")
            cache_delete_pattern(f"library:contributions:{current_user.id}")

            doc = library_result.get("document", {})
            scan_status = doc.get("scan_status", "clean")

            if scan_status == "clean":
                msg = f"Document uploaded successfully! {('It is now available to other students.' if is_public else 'It is saved as private.')}"
            else:
                msg = "Document uploaded successfully! It is pending security review and will be available to other students once verified."

            response = {
                "success": True,
                "message": msg,
                "document_id": library_result.get("library_document_id"),
                "is_duplicate": False,
                "scan_status": scan_status
            }
            if library_result.get("relevance_warning"):
                response["relevance_warning"] = library_result["relevance_warning"]
            return response
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload document to library"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in upload_to_library: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
