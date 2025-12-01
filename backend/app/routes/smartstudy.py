"""
SmartStudy API Routes - AI Learning Intervention System
Handles chat, study plans, and contextual recommendations
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User
from app.models.smartstudy import ChatConversation, ChatMessage, StudyPlan, StudyPlanResource
from app.schemas.smartstudy import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatConversationResponse,
    ChatConversationList,
    StudyPlanCreate,
    StudyPlanResponse,
    StudyPlanUpdate,
    ResourceClickUpdate,
    ResourceCompletionUpdate,
    SmartStudyContextResponse,
    SmartStudySuggestedPrompt,
    SmartStudyDashboardTrigger
)
from app.services.smartstudy_service import (
    chat_with_smartstudy,
    load_student_context,
    get_suggested_prompts,
    check_smartstudy_triggers
)

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/smartstudy", tags=["SmartStudy"])


# ============================================================================
# Chat Endpoints
# ============================================================================

@router.post("/chat", response_model=dict)
async def create_chat_message(
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a message to SmartStudy AI and get a response

    - **content**: User's message
    - **conversation_id**: Optional - continue existing conversation
    """
    try:
        result = chat_with_smartstudy(
            db=db,
            user_id=str(current_user.id),
            message=message_data.content,
            conversation_id=str(message_data.conversation_id) if message_data.conversation_id else None
        )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )

        return result

    except Exception as e:
        logger.error(f"Error in create_chat_message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/conversations", response_model=List[ChatConversationList])
async def get_user_conversations(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all chat conversations for current user

    - **limit**: Number of conversations to return (default 20)
    """
    try:
        conversations = db.query(ChatConversation).filter(
            ChatConversation.user_id == current_user.id
        ).order_by(ChatConversation.updated_at.desc()).limit(limit).all()

        result = []
        for conv in conversations:
            message_count = db.query(ChatMessage).filter(
                ChatMessage.conversation_id == conv.id
            ).count()

            result.append(ChatConversationList(
                id=conv.id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=message_count
            ))

        return result

    except Exception as e:
        logger.error(f"Error in get_user_conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/conversations/{conversation_id}", response_model=ChatConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific conversation with all messages
    """
    try:
        conversation = db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id,
            ChatConversation.user_id == current_user.id
        ).first()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        # Get messages
        messages = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation.id
        ).order_by(ChatMessage.created_at.asc()).all()

        return ChatConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=[ChatMessageResponse.from_orm(msg) for msg in messages]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a conversation and all its messages
    """
    try:
        conversation = db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id,
            ChatConversation.user_id == current_user.id
        ).first()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        db.delete(conversation)
        db.commit()

        return {"message": "Conversation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_conversation: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# Context & Suggestions Endpoints
# ============================================================================

@router.get("/context", response_model=SmartStudyContextResponse)
async def get_student_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive student context for SmartStudy
    """
    try:
        context = load_student_context(db, str(current_user.id))

        return SmartStudyContextResponse(
            student_info=context.get("student_info", {}),
            struggling_courses=[c for c in context.get("courses", []) if c.get("ca_score", 0) < 15],
            recent_moods=context.get("recent_moods", []),
            at_risk_tasks=[t for t in context.get("recent_tasks", []) if not t.get("is_completed") and t.get("is_late")],
            cgpa_status={
                "current": context.get("student_info", {}).get("current_cgpa"),
                "target": context.get("student_info", {}).get("target_cgpa"),
                "gap": context.get("cgpa_gap")
            }
        )

    except Exception as e:
        logger.error(f"Error in get_student_context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/suggested-prompts", response_model=List[SmartStudySuggestedPrompt])
async def get_suggested_chat_prompts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get contextual suggested prompts based on student's current state
    """
    try:
        prompts = get_suggested_prompts(db, str(current_user.id))
        return [SmartStudySuggestedPrompt(**p) for p in prompts]

    except Exception as e:
        logger.error(f"Error in get_suggested_chat_prompts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/triggers")
async def get_smartstudy_triggers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check all SmartStudy triggers for the current user
    Returns detailed trigger information with urgency levels
    """
    try:
        trigger_data = check_smartstudy_triggers(db, str(current_user.id))
        return trigger_data

    except Exception as e:
        logger.error(f"Error in get_smartstudy_triggers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/dashboard-trigger", response_model=SmartStudyDashboardTrigger)
async def check_dashboard_trigger(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if SmartStudy should be triggered on dashboard
    Shows prompt when student is struggling (legacy endpoint - use /triggers for full data)
    """
    try:
        trigger_data = check_smartstudy_triggers(db, str(current_user.id))

        # If any triggers, return the primary one
        if trigger_data["should_trigger"] and trigger_data["primary_trigger"]:
            primary = trigger_data["primary_trigger"]
            return SmartStudyDashboardTrigger(
                show_trigger=True,
                trigger_type=primary["type"],
                trigger_message=primary["title"],
                suggested_action=primary["message"]
            )

        # No trigger needed
        return SmartStudyDashboardTrigger(
            show_trigger=False,
            trigger_type="none",
            trigger_message="",
            suggested_action=""
        )

    except Exception as e:
        logger.error(f"Error in check_dashboard_trigger: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# Study Plan Endpoints (Phase 2 - Future)
# ============================================================================

@router.get("/study-plans", response_model=List[StudyPlanResponse])
async def get_user_study_plans(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all study plans for current user
    """
    try:
        query = db.query(StudyPlan).filter(StudyPlan.user_id == current_user.id)

        if active_only:
            query = query.filter(StudyPlan.is_active == True)

        plans = query.order_by(StudyPlan.created_at.desc()).all()
        return plans

    except Exception as e:
        logger.error(f"Error in get_user_study_plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
