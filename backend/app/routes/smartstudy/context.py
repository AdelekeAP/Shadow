"""
SmartStudy Context & Suggestions Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User
from app.services.cache_service import cache_get, cache_set, TTL_CONTEXT
from app.schemas.smartstudy import (
    SmartStudyContextResponse,
    SmartStudySuggestedPrompt,
    SmartStudyDashboardTrigger,
)
from app.services.smartstudy_service import (
    load_student_context,
    get_suggested_prompts,
    check_smartstudy_triggers,
)

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/context",
    response_model=SmartStudyContextResponse,
    operation_id="get_student_context",
    summary="Get comprehensive student context for SmartStudy",
)
async def get_student_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive student context for SmartStudy
    """
    try:
        # Check cache first
        cache_key = f"smartstudy:context:{current_user.id}"
        cached = cache_get(cache_key)
        if cached:
            return cached

        context = load_student_context(db, str(current_user.id))

        result = {
            "student_info": context.get("student_info", {}),
            "struggling_courses": [c for c in context.get("courses", []) if c.get("ca_score", 0) < 15],
            "recent_moods": context.get("recent_moods", []),
            "at_risk_tasks": [t for t in context.get("recent_tasks", []) if not t.get("is_completed") and t.get("is_late")],
            "cgpa_status": {
                "current": context.get("student_info", {}).get("current_cgpa"),
                "target": context.get("student_info", {}).get("target_cgpa"),
                "gap": context.get("cgpa_gap")
            }
        }

        cache_set(cache_key, result, TTL_CONTEXT)
        return result

    except Exception as e:
        logger.error(f"Error in get_student_context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/suggested-prompts",
    response_model=List[SmartStudySuggestedPrompt],
    operation_id="get_suggested_prompts",
    summary="Get contextual suggested prompts based on student state",
)
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


@router.get(
    "/triggers",
    operation_id="get_smartstudy_triggers",
    summary="Check all SmartStudy triggers for the current user",
)
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


@router.get(
    "/dashboard-trigger",
    response_model=SmartStudyDashboardTrigger,
    operation_id="check_dashboard_trigger",
    summary="Check if SmartStudy should be triggered on dashboard",
)
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
