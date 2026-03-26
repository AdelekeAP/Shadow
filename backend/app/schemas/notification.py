"""
Notification Schemas - Pydantic models for notification API
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class NotificationTypeEnum(str, Enum):
    """Types of notifications"""
    TASK_REMINDER = "task_reminder"
    TASK_OVERDUE = "task_overdue"
    STUDY_PLAN = "study_plan"
    MOOD_CHECK = "mood_check"
    GOAL_PROGRESS = "goal_progress"
    ACHIEVEMENT = "achievement"
    SMART_STUDY = "smart_study"
    SYSTEM = "system"


class NotificationPriorityEnum(str, Enum):
    """Priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# ==================== NOTIFICATION SCHEMAS ====================

class NotificationBase(BaseModel):
    """Base notification fields"""
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1, max_length=1000)
    notification_type: NotificationTypeEnum = NotificationTypeEnum.SYSTEM
    priority: NotificationPriorityEnum = NotificationPriorityEnum.MEDIUM


class NotificationCreate(NotificationBase):
    """Schema for creating a notification"""
    task_id: Optional[UUID] = None
    course_id: Optional[UUID] = None
    study_plan_id: Optional[UUID] = None
    action_url: Optional[str] = None
    action_data: Optional[Dict[str, Any]] = None
    scheduled_for: Optional[datetime] = None


class NotificationResponse(BaseModel):
    """Schema for notification response"""
    id: UUID
    user_id: UUID
    title: str
    message: str
    notification_type: str
    priority: str
    task_id: Optional[UUID] = None
    course_id: Optional[UUID] = None
    study_plan_id: Optional[UUID] = None
    channel: str
    is_read: bool
    is_dismissed: bool
    read_at: Optional[datetime] = None
    action_url: Optional[str] = None
    action_data: Optional[Dict[str, Any]] = None
    scheduled_for: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    mood_context: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Response for list of notifications"""
    notifications: List[NotificationResponse]
    total_count: int
    unread_count: int


class NotificationCountResponse(BaseModel):
    """Response for notification counts"""
    unread_count: int
    total_count: int


# ==================== PREFERENCE SCHEMAS ====================

class NotificationPreferenceBase(BaseModel):
    """Base notification preference fields"""
    # Channel preferences
    email_enabled: bool = True
    in_app_enabled: bool = True
    push_enabled: bool = False

    # Type preferences
    task_reminders: bool = True
    task_overdue: bool = True
    study_plan_updates: bool = True
    mood_check_reminders: bool = True
    goal_progress: bool = True
    achievements: bool = True
    smart_study: bool = True
    system_announcements: bool = True


class NotificationPreferenceUpdate(BaseModel):
    """Schema for updating preferences"""
    # Channel preferences
    email_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None

    # Type preferences
    task_reminders: Optional[bool] = None
    task_overdue: Optional[bool] = None
    study_plan_updates: Optional[bool] = None
    mood_check_reminders: Optional[bool] = None
    goal_progress: Optional[bool] = None
    achievements: Optional[bool] = None
    smart_study: Optional[bool] = None
    system_announcements: Optional[bool] = None

    # Timing preferences
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    quiet_hours_end: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    timezone: Optional[str] = None

    # Reminder timing
    task_reminder_hours: Optional[int] = Field(None, ge=1, le=168)  # 1 hour to 1 week
    task_reminder_same_day: Optional[bool] = None
    mood_check_frequency: Optional[str] = None

    # Mood-aware preferences
    reduce_when_stressed: Optional[bool] = None
    motivate_when_low_energy: Optional[bool] = None

    # Digest preferences
    daily_digest: Optional[bool] = None
    weekly_digest: Optional[bool] = None
    digest_time: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")


class NotificationPreferenceResponse(BaseModel):
    """Schema for preference response"""
    id: UUID
    user_id: UUID
    email_enabled: bool
    in_app_enabled: bool
    push_enabled: bool
    task_reminders: bool
    task_overdue: bool
    study_plan_updates: bool
    mood_check_reminders: bool
    goal_progress: bool
    achievements: bool
    smart_study: bool
    system_announcements: bool
    quiet_hours_enabled: bool
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    timezone: str
    task_reminder_hours: int
    task_reminder_same_day: bool
    mood_check_frequency: str
    reduce_when_stressed: bool
    motivate_when_low_energy: bool
    daily_digest: bool
    weekly_digest: bool
    digest_time: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== SCHEDULED REMINDER SCHEMAS ====================

class ScheduledReminderCreate(BaseModel):
    """Schema for creating a scheduled reminder"""
    reminder_type: str = Field(..., min_length=1, max_length=50)
    related_id: Optional[UUID] = None
    scheduled_time: datetime
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    recurrence_data: Optional[Dict[str, Any]] = None
    custom_title: Optional[str] = Field(None, max_length=255)
    custom_message: Optional[str] = Field(None, max_length=500)


class ScheduledReminderUpdate(BaseModel):
    """Schema for updating a scheduled reminder"""
    scheduled_time: Optional[datetime] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None
    recurrence_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    custom_title: Optional[str] = Field(None, max_length=255)
    custom_message: Optional[str] = Field(None, max_length=500)


class ScheduledReminderResponse(BaseModel):
    """Schema for scheduled reminder response"""
    id: UUID
    user_id: UUID
    reminder_type: str
    related_id: Optional[UUID] = None
    scheduled_time: datetime
    is_recurring: bool
    recurrence_pattern: Optional[str] = None
    recurrence_data: Optional[Dict[str, Any]] = None
    is_active: bool
    is_sent: bool
    last_sent_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    custom_title: Optional[str] = None
    custom_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScheduledReminderListResponse(BaseModel):
    """Response for list of scheduled reminders"""
    reminders: List[ScheduledReminderResponse]
    total_count: int


# ==================== ACTION SCHEMAS ====================

class MarkReadRequest(BaseModel):
    """Request to mark notification(s) as read"""
    notification_ids: Optional[List[UUID]] = None  # If None, mark all as read


class DismissRequest(BaseModel):
    """Request to dismiss notification(s)"""
    notification_ids: List[UUID]


class ActionResult(BaseModel):
    """Result of a notification action"""
    success: bool
    message: str
    affected_count: int = 0
