"""
Notification Routes - API endpoints for Smart Reminders & Notifications
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User
from app.models.notification import Notification, NotificationPreference, ScheduledReminder
from app.services.notification_service import get_notification_service
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse,
    NotificationCountResponse,
    NotificationPreferenceUpdate,
    NotificationPreferenceResponse,
    ScheduledReminderCreate,
    ScheduledReminderUpdate,
    ScheduledReminderResponse,
    ScheduledReminderListResponse,
    MarkReadRequest,
    DismissRequest,
    ActionResult
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# ==================== NOTIFICATION ENDPOINTS ====================

@router.get(
    "",
    response_model=NotificationListResponse,
    operation_id="list_notifications",
    summary="Get user's notifications",
)
async def get_notifications(
    unread_only: bool = Query(False, description="Filter to unread only"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's notifications"""
    service = get_notification_service(db)

    notifications = service.get_user_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
        offset=offset
    )

    unread_count = service.get_unread_count(current_user.id)

    # Get total count
    total_count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_dismissed == False
    ).count()

    return NotificationListResponse(
        notifications=[NotificationResponse(**n.to_dict()) for n in notifications],
        total_count=total_count,
        unread_count=unread_count
    )


@router.get(
    "/count",
    response_model=NotificationCountResponse,
    operation_id="get_notification_count",
    summary="Get notification counts for badge display",
)
async def get_notification_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get notification counts for badge display"""
    service = get_notification_service(db)
    unread_count = service.get_unread_count(current_user.id)

    total_count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_dismissed == False
    ).count()

    return NotificationCountResponse(
        unread_count=unread_count,
        total_count=total_count
    )


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
    operation_id="get_notification",
    summary="Get a specific notification",
)
async def get_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific notification"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return NotificationResponse(**notification.to_dict())


@router.post(
    "/{notification_id}/read",
    response_model=ActionResult,
    operation_id="mark_notification_read",
    summary="Mark a notification as read",
)
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    service = get_notification_service(db)
    success = service.mark_as_read(notification_id, current_user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return ActionResult(
        success=True,
        message="Notification marked as read",
        affected_count=1
    )


@router.post(
    "/read-all",
    response_model=ActionResult,
    operation_id="mark_all_notifications_read",
    summary="Mark all notifications as read",
)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read"""
    service = get_notification_service(db)
    count = service.mark_all_as_read(current_user.id)

    return ActionResult(
        success=True,
        message=f"Marked {count} notification(s) as read",
        affected_count=count
    )


@router.post(
    "/{notification_id}/dismiss",
    response_model=ActionResult,
    operation_id="dismiss_notification",
    summary="Dismiss a notification",
)
async def dismiss_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Dismiss a notification"""
    service = get_notification_service(db)
    success = service.dismiss_notification(notification_id, current_user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return ActionResult(
        success=True,
        message="Notification dismissed",
        affected_count=1
    )


@router.post(
    "/dismiss-batch",
    response_model=ActionResult,
    operation_id="dismiss_notifications_batch",
    summary="Dismiss multiple notifications",
)
async def dismiss_notifications_batch(
    request: DismissRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Dismiss multiple notifications"""
    service = get_notification_service(db)
    count = 0

    for notification_id in request.notification_ids:
        if service.dismiss_notification(notification_id, current_user.id):
            count += 1

    return ActionResult(
        success=True,
        message=f"Dismissed {count} notification(s)",
        affected_count=count
    )


# ==================== PREFERENCE ENDPOINTS ====================

@router.get(
    "/preferences/me",
    response_model=NotificationPreferenceResponse,
    operation_id="get_notification_preferences",
    summary="Get current user's notification preferences",
)
async def get_my_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's notification preferences"""
    service = get_notification_service(db)
    prefs = service.get_or_create_preferences(current_user.id)
    return NotificationPreferenceResponse(**prefs.to_dict())


@router.put(
    "/preferences/me",
    response_model=NotificationPreferenceResponse,
    operation_id="update_notification_preferences",
    summary="Update current user's notification preferences",
)
async def update_my_preferences(
    updates: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's notification preferences"""
    service = get_notification_service(db)

    # Convert to dict, excluding None values
    update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}

    prefs = service.update_preferences(current_user.id, update_dict)
    return NotificationPreferenceResponse(**prefs.to_dict())


# ==================== SCHEDULED REMINDER ENDPOINTS ====================

@router.get(
    "/reminders",
    response_model=ScheduledReminderListResponse,
    operation_id="list_scheduled_reminders",
    summary="Get user's scheduled reminders",
)
async def get_scheduled_reminders(
    active_only: bool = Query(True, description="Filter to active reminders only"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's scheduled reminders"""
    query = db.query(ScheduledReminder).filter(
        ScheduledReminder.user_id == current_user.id
    )

    if active_only:
        query = query.filter(ScheduledReminder.is_active == True)

    total_count = query.count()
    reminders = query.order_by(
        ScheduledReminder.scheduled_time
    ).offset(offset).limit(limit).all()

    return ScheduledReminderListResponse(
        reminders=[ScheduledReminderResponse(**r.to_dict()) for r in reminders],
        total_count=total_count
    )


@router.post(
    "/reminders",
    response_model=ScheduledReminderResponse,
    operation_id="create_scheduled_reminder",
    summary="Create a new scheduled reminder",
)
async def create_scheduled_reminder(
    reminder: ScheduledReminderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new scheduled reminder"""
    new_reminder = ScheduledReminder(
        user_id=current_user.id,
        reminder_type=reminder.reminder_type,
        related_id=reminder.related_id,
        scheduled_time=reminder.scheduled_time,
        is_recurring=reminder.is_recurring,
        recurrence_pattern=reminder.recurrence_pattern,
        recurrence_data=reminder.recurrence_data,
        custom_title=reminder.custom_title,
        custom_message=reminder.custom_message,
        next_run_at=reminder.scheduled_time
    )

    db.add(new_reminder)
    db.commit()
    db.refresh(new_reminder)

    return ScheduledReminderResponse(**new_reminder.to_dict())


@router.get(
    "/reminders/{reminder_id}",
    response_model=ScheduledReminderResponse,
    operation_id="get_scheduled_reminder",
    summary="Get a specific scheduled reminder",
)
async def get_scheduled_reminder(
    reminder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific scheduled reminder"""
    reminder = db.query(ScheduledReminder).filter(
        ScheduledReminder.id == reminder_id,
        ScheduledReminder.user_id == current_user.id
    ).first()

    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    return ScheduledReminderResponse(**reminder.to_dict())


@router.put(
    "/reminders/{reminder_id}",
    response_model=ScheduledReminderResponse,
    operation_id="update_scheduled_reminder",
    summary="Update a scheduled reminder",
)
async def update_scheduled_reminder(
    reminder_id: UUID,
    updates: ScheduledReminderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a scheduled reminder"""
    reminder = db.query(ScheduledReminder).filter(
        ScheduledReminder.id == reminder_id,
        ScheduledReminder.user_id == current_user.id
    ).first()

    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}

    for key, value in update_dict.items():
        setattr(reminder, key, value)

    # Update next_run_at if scheduled_time changed
    if "scheduled_time" in update_dict:
        reminder.next_run_at = update_dict["scheduled_time"]

    db.commit()
    db.refresh(reminder)

    return ScheduledReminderResponse(**reminder.to_dict())


@router.delete(
    "/reminders/{reminder_id}",
    response_model=ActionResult,
    operation_id="delete_scheduled_reminder",
    summary="Delete a scheduled reminder",
)
async def delete_scheduled_reminder(
    reminder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a scheduled reminder"""
    reminder = db.query(ScheduledReminder).filter(
        ScheduledReminder.id == reminder_id,
        ScheduledReminder.user_id == current_user.id
    ).first()

    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    db.delete(reminder)
    db.commit()

    return ActionResult(
        success=True,
        message="Reminder deleted",
        affected_count=1
    )


# ==================== TASK REMINDER ENDPOINTS ====================

@router.post(
    "/task/{task_id}/remind",
    response_model=NotificationResponse,
    operation_id="create_task_reminder",
    summary="Create a reminder for a specific task",
)
async def create_task_reminder(
    task_id: UUID,
    hours_before: int = Query(24, ge=1, le=168, description="Hours before due date"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a reminder for a specific task"""
    from app.models.task import Task

    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not task.due_date:
        raise HTTPException(status_code=400, detail="Task has no due date")

    service = get_notification_service(db)
    notification = service.create_task_reminder(current_user.id, task, hours_before)

    if not notification:
        raise HTTPException(
            status_code=400,
            detail="Could not create reminder (may be past due or blocked by preferences)"
        )

    return NotificationResponse(**notification.to_dict())


# ==================== TEST ENDPOINTS (DEV ONLY) ====================

@router.post(
    "/test/mood-check",
    operation_id="test_mood_check_notification",
    summary="Create a test mood check notification",
)
async def test_mood_check_notification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a test mood check notification"""
    service = get_notification_service(db)
    notification = service.create_mood_check_reminder(current_user.id)

    if notification:
        return NotificationResponse(**notification.to_dict())
    else:
        raise HTTPException(status_code=400, detail="Notification blocked by preferences")


@router.post(
    "/test/achievement",
    operation_id="test_achievement_notification",
    summary="Create a test achievement notification",
)
async def test_achievement_notification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a test achievement notification"""
    service = get_notification_service(db)
    notification = service.create_achievement_notification(
        user_id=current_user.id,
        achievement_name="First Study Plan",
        achievement_description="You completed your first SmartStudy plan! Keep up the great work."
    )

    if notification:
        return NotificationResponse(**notification.to_dict())
    else:
        raise HTTPException(status_code=400, detail="Notification blocked by preferences")
