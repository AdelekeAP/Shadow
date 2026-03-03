"""
Notification Models - Smart Reminders & Notification System
Handles notifications, user preferences, and scheduled reminders
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from app.database import Base


class NotificationType(str, enum.Enum):
    """Types of notifications"""
    TASK_REMINDER = "task_reminder"        # Upcoming task deadline
    TASK_OVERDUE = "task_overdue"          # Task past due date
    STUDY_PLAN = "study_plan"              # Study plan recommendation
    MOOD_CHECK = "mood_check"              # Mood check-in reminder
    GOAL_PROGRESS = "goal_progress"        # CGPA goal progress update
    ACHIEVEMENT = "achievement"            # Achievement unlocked
    SMART_STUDY = "smart_study"            # SmartStudy recommendations
    SYSTEM = "system"                      # System announcements


class NotificationPriority(str, enum.Enum):
    """Priority levels for notifications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class DeliveryChannel(str, enum.Enum):
    """Notification delivery channels"""
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"  # For future mobile app


class Notification(Base):
    """
    Notification Model - Individual notification records
    """
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Notification content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False, default=NotificationType.SYSTEM.value)
    priority = Column(String(20), nullable=False, default=NotificationPriority.MEDIUM.value)

    # Related entities (optional)
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey('courses.id', ondelete='SET NULL'), nullable=True)
    study_plan_id = Column(UUID(as_uuid=True), ForeignKey('study_plans.id', ondelete='SET NULL'), nullable=True)

    # Delivery tracking
    channel = Column(String(20), nullable=False, default=DeliveryChannel.IN_APP.value)
    is_read = Column(Boolean, default=False, index=True)
    is_dismissed = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Action handling
    action_url = Column(String(500), nullable=True)  # Deep link for the notification
    action_data = Column(JSONB, nullable=True)  # Additional data for actions

    # Scheduling
    scheduled_for = Column(DateTime(timezone=True), nullable=True)  # When to send
    sent_at = Column(DateTime(timezone=True), nullable=True)  # When actually sent
    expires_at = Column(DateTime(timezone=True), nullable=True)  # When notification expires

    # Mood-aware context
    mood_context = Column(JSONB, nullable=True)  # Mood state when notification was created

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.notification_type}, user={self.user_id})>"

    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "message": self.message,
            "notification_type": self.notification_type,
            "priority": self.priority,
            "task_id": str(self.task_id) if self.task_id else None,
            "course_id": str(self.course_id) if self.course_id else None,
            "study_plan_id": str(self.study_plan_id) if self.study_plan_id else None,
            "channel": self.channel,
            "is_read": self.is_read,
            "is_dismissed": self.is_dismissed,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "action_url": self.action_url,
            "action_data": self.action_data,
            "scheduled_for": self.scheduled_for.isoformat() if self.scheduled_for else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "mood_context": self.mood_context,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class NotificationPreference(Base):
    """
    User Notification Preferences - Controls what notifications users receive
    """
    __tablename__ = "notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)

    # Channel preferences
    email_enabled = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=False)  # For future

    # Notification type preferences (per type)
    task_reminders = Column(Boolean, default=True)
    task_overdue = Column(Boolean, default=True)
    study_plan_updates = Column(Boolean, default=True)
    mood_check_reminders = Column(Boolean, default=True)
    goal_progress = Column(Boolean, default=True)
    achievements = Column(Boolean, default=True)
    smart_study = Column(Boolean, default=True)
    system_announcements = Column(Boolean, default=True)

    # Timing preferences
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String(5), nullable=True)  # HH:MM format (e.g., "22:00")
    quiet_hours_end = Column(String(5), nullable=True)    # HH:MM format (e.g., "08:00")
    timezone = Column(String(50), default="Africa/Lagos")  # User's timezone

    # Reminder timing preferences
    task_reminder_hours = Column(Integer, default=24)  # Hours before due date
    task_reminder_same_day = Column(Boolean, default=True)  # Remind on due day
    mood_check_frequency = Column(String(20), default="daily")  # 'daily', 'twice_daily', 'weekly'

    # Mood-aware preferences
    reduce_when_stressed = Column(Boolean, default=True)  # Reduce notifications when stressed
    motivate_when_low_energy = Column(Boolean, default=True)  # Send motivational when low energy

    # Email digest preferences
    daily_digest = Column(Boolean, default=False)
    weekly_digest = Column(Boolean, default=True)
    digest_time = Column(String(5), default="09:00")  # When to send digest

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<NotificationPreference(user_id={self.user_id})>"

    def to_dict(self):
        """Convert preferences to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "email_enabled": self.email_enabled,
            "in_app_enabled": self.in_app_enabled,
            "push_enabled": self.push_enabled,
            "task_reminders": self.task_reminders,
            "task_overdue": self.task_overdue,
            "study_plan_updates": self.study_plan_updates,
            "mood_check_reminders": self.mood_check_reminders,
            "goal_progress": self.goal_progress,
            "achievements": self.achievements,
            "smart_study": self.smart_study,
            "system_announcements": self.system_announcements,
            "quiet_hours_enabled": self.quiet_hours_enabled,
            "quiet_hours_start": self.quiet_hours_start,
            "quiet_hours_end": self.quiet_hours_end,
            "timezone": self.timezone,
            "task_reminder_hours": self.task_reminder_hours,
            "task_reminder_same_day": self.task_reminder_same_day,
            "mood_check_frequency": self.mood_check_frequency,
            "reduce_when_stressed": self.reduce_when_stressed,
            "motivate_when_low_energy": self.motivate_when_low_energy,
            "daily_digest": self.daily_digest,
            "weekly_digest": self.weekly_digest,
            "digest_time": self.digest_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def should_send_notification(self, notification_type: str) -> bool:
        """Check if a notification type should be sent based on preferences"""
        type_mapping = {
            NotificationType.TASK_REMINDER.value: self.task_reminders,
            NotificationType.TASK_OVERDUE.value: self.task_overdue,
            NotificationType.STUDY_PLAN.value: self.study_plan_updates,
            NotificationType.MOOD_CHECK.value: self.mood_check_reminders,
            NotificationType.GOAL_PROGRESS.value: self.goal_progress,
            NotificationType.ACHIEVEMENT.value: self.achievements,
            NotificationType.SMART_STUDY.value: self.smart_study,
            NotificationType.SYSTEM.value: self.system_announcements,
        }
        return type_mapping.get(notification_type, True)


class ScheduledReminder(Base):
    """
    Scheduled Reminder - For recurring and scheduled notifications
    """
    __tablename__ = "scheduled_reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # What to remind about
    reminder_type = Column(String(50), nullable=False)  # 'task', 'mood_check', 'study_session', 'goal_review'
    related_id = Column(UUID(as_uuid=True), nullable=True)  # Task ID, Study Plan ID, etc.

    # Schedule
    scheduled_time = Column(DateTime(timezone=True), nullable=False, index=True)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(50), nullable=True)  # 'daily', 'weekly', 'custom'
    recurrence_data = Column(JSONB, nullable=True)  # Custom recurrence rules

    # Status
    is_active = Column(Boolean, default=True)
    is_sent = Column(Boolean, default=False)
    last_sent_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)

    # Content customization
    custom_title = Column(String(255), nullable=True)
    custom_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ScheduledReminder(id={self.id}, type={self.reminder_type}, scheduled={self.scheduled_time})>"

    def to_dict(self):
        """Convert scheduled reminder to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "reminder_type": self.reminder_type,
            "related_id": str(self.related_id) if self.related_id else None,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "is_recurring": self.is_recurring,
            "recurrence_pattern": self.recurrence_pattern,
            "recurrence_data": self.recurrence_data,
            "is_active": self.is_active,
            "is_sent": self.is_sent,
            "last_sent_at": self.last_sent_at.isoformat() if self.last_sent_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "custom_title": self.custom_title,
            "custom_message": self.custom_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
