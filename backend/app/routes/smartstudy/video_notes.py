"""
SmartStudy Video Notes Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User
from app.models.smartstudy import StudyPlan, StudyPlanResource, VideoNote
from app.schemas.smartstudy import (
    VideoNoteCreate,
    VideoNoteUpdate,
    VideoNoteResponse,
    VideoNotesListResponse,
)

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/video-notes",
    response_model=VideoNoteResponse,
    operation_id="create_video_note",
    summary="Create a new note for a video resource",
)
async def create_video_note(
    note_data: VideoNoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new note for a video resource

    - **resource_id**: The study plan resource ID (YouTube video)
    - **content**: Note content (required)
    - **timestamp_seconds**: Optional video timestamp in seconds
    - **note_type**: Type of note (note, highlight, question, summary)
    - **color**: Color for visual organization (yellow, green, blue, pink, orange)
    """
    try:
        # Verify resource exists and belongs to user's study plan
        resource = db.query(StudyPlanResource).filter(
            StudyPlanResource.id == note_data.resource_id
        ).first()

        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )

        # Verify the study plan belongs to the current user
        plan = db.query(StudyPlan).filter(
            StudyPlan.id == resource.study_plan_id,
            StudyPlan.user_id == current_user.id
        ).first()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this resource"
            )

        # Create the note
        note = VideoNote(
            user_id=current_user.id,
            resource_id=note_data.resource_id,
            content=note_data.content,
            timestamp_seconds=note_data.timestamp_seconds,
            note_type=note_data.note_type or "note",
            color=note_data.color or "yellow"
        )

        db.add(note)
        db.commit()
        db.refresh(note)

        logger.info(f"📝 Created video note for resource {resource.id}")

        return VideoNoteResponse(
            id=note.id,
            user_id=note.user_id,
            resource_id=note.resource_id,
            content=note.content,
            timestamp_seconds=note.timestamp_seconds,
            formatted_timestamp=note.format_timestamp(),
            note_type=note.note_type,
            color=note.color,
            created_at=note.created_at,
            updated_at=note.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating video note: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/video-notes/resource/{resource_id}",
    response_model=VideoNotesListResponse,
    operation_id="get_video_notes_for_resource",
    summary="Get all notes for a specific video resource",
)
async def get_notes_for_resource(
    resource_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all notes for a specific video resource
    """
    try:
        # Verify resource exists and user has access
        resource = db.query(StudyPlanResource).filter(
            StudyPlanResource.id == resource_id
        ).first()

        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )

        # Verify study plan belongs to user
        plan = db.query(StudyPlan).filter(
            StudyPlan.id == resource.study_plan_id,
            StudyPlan.user_id == current_user.id
        ).first()

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this resource"
            )

        # Get all notes for this resource
        notes = db.query(VideoNote).filter(
            VideoNote.resource_id == resource_id,
            VideoNote.user_id == current_user.id
        ).order_by(VideoNote.timestamp_seconds.asc().nullsfirst(), VideoNote.created_at.asc()).all()

        return VideoNotesListResponse(
            notes=[
                VideoNoteResponse(
                    id=note.id,
                    user_id=note.user_id,
                    resource_id=note.resource_id,
                    content=note.content,
                    timestamp_seconds=note.timestamp_seconds,
                    formatted_timestamp=note.format_timestamp(),
                    note_type=note.note_type,
                    color=note.color,
                    created_at=note.created_at,
                    updated_at=note.updated_at
                )
                for note in notes
            ],
            total_count=len(notes),
            resource_id=resource_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video notes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put(
    "/video-notes/{note_id}",
    response_model=VideoNoteResponse,
    operation_id="update_video_note",
    summary="Update an existing video note",
)
async def update_video_note(
    note_id: UUID,
    update_data: VideoNoteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing video note
    """
    try:
        note = db.query(VideoNote).filter(
            VideoNote.id == note_id,
            VideoNote.user_id == current_user.id
        ).first()

        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )

        # Update fields if provided
        if update_data.content is not None:
            note.content = update_data.content
        if update_data.timestamp_seconds is not None:
            note.timestamp_seconds = update_data.timestamp_seconds
        if update_data.note_type is not None:
            note.note_type = update_data.note_type
        if update_data.color is not None:
            note.color = update_data.color

        db.commit()
        db.refresh(note)

        return VideoNoteResponse(
            id=note.id,
            user_id=note.user_id,
            resource_id=note.resource_id,
            content=note.content,
            timestamp_seconds=note.timestamp_seconds,
            formatted_timestamp=note.format_timestamp(),
            note_type=note.note_type,
            color=note.color,
            created_at=note.created_at,
            updated_at=note.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating video note: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete(
    "/video-notes/{note_id}",
    operation_id="delete_video_note",
    summary="Delete a video note",
)
async def delete_video_note(
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a video note
    """
    try:
        note = db.query(VideoNote).filter(
            VideoNote.id == note_id,
            VideoNote.user_id == current_user.id
        ).first()

        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )

        db.delete(note)
        db.commit()

        return {"message": "Note deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting video note: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
