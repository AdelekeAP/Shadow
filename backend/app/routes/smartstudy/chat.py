"""
SmartStudy Chat Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.utils.auth import get_current_user
from app.middleware.rate_limiter import limiter
from app.models.user import User
from app.models.smartstudy import ChatConversation, ChatMessage
from app.schemas.smartstudy import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatConversationResponse,
    ChatConversationList,
)
from app.services.smartstudy_service import chat_with_smartstudy

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/chat",
    response_model=dict,
    operation_id="send_chat_message",
    summary="Send a message to SmartStudy AI and get a response",
)
@limiter.limit("10/minute")
async def create_chat_message(
    request: Request,
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


@router.get(
    "/conversations",
    response_model=List[ChatConversationList],
    operation_id="list_conversations",
    summary="Get all chat conversations for current user",
)
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


@router.get(
    "/conversations/{conversation_id}",
    response_model=ChatConversationResponse,
    operation_id="get_conversation",
    summary="Get a specific conversation with all messages",
)
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


@router.delete(
    "/conversations/{conversation_id}",
    operation_id="delete_conversation",
    summary="Delete a conversation and all its messages",
)
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
