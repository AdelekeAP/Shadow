"""
Notification Service - Smart Reminders with Mood-Aware Logic
Handles creating, scheduling, and sending notifications
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.notification import (
    Notification,
    NotificationPreference,
    ScheduledReminder,
    NotificationType,
    NotificationPriority,
    DeliveryChannel
)
from app.models.mood import MoodLog
from app.models.task import Task
from app.models.user import User

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications with mood-aware intelligence"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== NOTIFICATION CRUD ====================

    def create_notification(
        self,
        user_id: UUID,
        title: str,
        message: str,
        notification_type: str = NotificationType.SYSTEM.value,
        priority: str = NotificationPriority.MEDIUM.value,
        task_id: UUID = None,
        course_id: UUID = None,
        study_plan_id: UUID = None,
        action_url: str = None,
        action_data: dict = None,
        scheduled_for: datetime = None,
        check_preferences: bool = True
    ) -> Optional[Notification]:
        """
        Create a new notification for a user

        Args:
            user_id: User to notify
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            priority: Priority level
            task_id: Related task (optional)
            course_id: Related course (optional)
            study_plan_id: Related study plan (optional)
            action_url: Deep link URL (optional)
            action_data: Additional action data (optional)
            scheduled_for: When to send (optional, immediate if None)
            check_preferences: Whether to check user preferences

        Returns:
            Created notification or None if blocked by preferences
        """
        try:
            # Check user preferences
            if check_preferences:
                prefs = self.get_or_create_preferences(user_id)
                if not prefs.should_send_notification(notification_type):
                    logger.info(f"Notification blocked by user preferences: {notification_type}")
                    return None

                # Check quiet hours
                if prefs.quiet_hours_enabled and self._is_quiet_hours(prefs):
                    # Schedule for after quiet hours instead of blocking
                    scheduled_for = self._get_next_active_time(prefs)
                    logger.info(f"Notification scheduled for after quiet hours: {scheduled_for}")

            # Get mood context for mood-aware adjustments
            mood_context = self._get_current_mood_context(user_id)

            # Adjust notification based on mood if applicable
            if mood_context:
                title, message, priority = self._adjust_for_mood(
                    title, message, priority, mood_context, notification_type
                )

            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
                task_id=task_id,
                course_id=course_id,
                study_plan_id=study_plan_id,
                channel=DeliveryChannel.IN_APP.value,
                action_url=action_url,
                action_data=action_data,
                scheduled_for=scheduled_for,
                sent_at=datetime.now(timezone.utc) if not scheduled_for else None,
                mood_context=mood_context
            )

            self.db.add(notification)
            self.db.commit()
            self.db.refresh(notification)

            logger.info(f"Created notification {notification.id} for user {user_id}")
            return notification

        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            self.db.rollback()
            return None

    def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """Get notifications for a user"""
        query = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_dismissed == False
        )

        if unread_only:
            query = query.filter(Notification.is_read == False)

        # Only show sent notifications (not scheduled for future)
        query = query.filter(
            or_(
                Notification.scheduled_for == None,
                Notification.scheduled_for <= datetime.now(timezone.utc)
            )
        )

        return query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()

    def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications"""
        return self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
            Notification.is_dismissed == False,
            or_(
                Notification.scheduled_for == None,
                Notification.scheduled_for <= datetime.now(timezone.utc)
            )
        ).count()

    def mark_as_read(self, notification_id: UUID, user_id: UUID) -> bool:
        """Mark a notification as read"""
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()

        if notification:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            self.db.commit()
            return True
        return False

    def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user"""
        result = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({
            "is_read": True,
            "read_at": datetime.now(timezone.utc)
        })
        self.db.commit()
        return result

    def dismiss_notification(self, notification_id: UUID, user_id: UUID) -> bool:
        """Dismiss a notification"""
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()

        if notification:
            notification.is_dismissed = True
            self.db.commit()
            return True
        return False

    def delete_old_notifications(self, days_old: int = 30) -> int:
        """Delete notifications older than specified days"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_old)
        result = self.db.query(Notification).filter(
            Notification.created_at < cutoff,
            Notification.is_read == True
        ).delete()
        self.db.commit()
        return result

    # ==================== PREFERENCES ====================

    def get_or_create_preferences(self, user_id: UUID) -> NotificationPreference:
        """Get user preferences or create default ones"""
        prefs = self.db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()

        if not prefs:
            prefs = NotificationPreference(user_id=user_id)
            self.db.add(prefs)
            self.db.commit()
            self.db.refresh(prefs)

        return prefs

    def update_preferences(self, user_id: UUID, updates: Dict) -> NotificationPreference:
        """Update user notification preferences"""
        prefs = self.get_or_create_preferences(user_id)

        for key, value in updates.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)

        self.db.commit()
        self.db.refresh(prefs)
        return prefs

    # ==================== TASK REMINDERS ====================

    def create_task_reminder(
        self,
        user_id: UUID,
        task: Task,
        hours_before: int = None
    ) -> Optional[Notification]:
        """Create a reminder for an upcoming task"""
        if not task.due_date:
            return None

        prefs = self.get_or_create_preferences(user_id)
        hours_before = hours_before or prefs.task_reminder_hours

        # Calculate reminder time
        reminder_time = task.due_date - timedelta(hours=hours_before)

        # Don't create reminders for past tasks
        if reminder_time < datetime.now(timezone.utc):
            return None

        # Determine priority based on task weight and deadline proximity
        priority = NotificationPriority.MEDIUM.value
        if task.is_urgent or (task.weight and float(task.weight) >= 20):
            priority = NotificationPriority.HIGH.value

        days_until = (task.due_date - datetime.now(timezone.utc)).days
        if days_until <= 1:
            priority = NotificationPriority.URGENT.value

        # Create action URL
        action_url = f"/tasks/{task.id}"

        return self.create_notification(
            user_id=user_id,
            title=f"Upcoming: {task.title}",
            message=self._generate_task_reminder_message(task, hours_before),
            notification_type=NotificationType.TASK_REMINDER.value,
            priority=priority,
            task_id=task.id,
            action_url=action_url,
            scheduled_for=reminder_time
        )

    def create_overdue_notification(self, user_id: UUID, task: Task) -> Optional[Notification]:
        """Create notification for an overdue task"""
        if task.is_completed or not task.due_date:
            return None

        return self.create_notification(
            user_id=user_id,
            title=f"Overdue: {task.title}",
            message=f"This task was due {self._format_time_ago(task.due_date)}. Would you like help prioritizing your tasks?",
            notification_type=NotificationType.TASK_OVERDUE.value,
            priority=NotificationPriority.HIGH.value,
            task_id=task.id,
            action_url=f"/tasks/{task.id}",
            action_data={"show_reschedule": True}
        )

    def _generate_task_reminder_message(self, task: Task, hours_before: int) -> str:
        """Generate a contextual reminder message for a task"""
        if hours_before >= 24:
            time_str = f"in {hours_before // 24} day(s)"
        else:
            time_str = f"in {hours_before} hour(s)"

        weight_info = ""
        if task.weight:
            weight_info = f" This is worth {task.weight} marks."

        return f"'{task.title}' is due {time_str}.{weight_info} Start preparing now to do your best!"

    # ==================== MOOD-AWARE LOGIC ====================

    def _get_current_mood_context(self, user_id: UUID) -> Optional[Dict]:
        """Get the user's current mood context from recent mood logs"""
        recent_mood = self.db.query(MoodLog).filter(
            MoodLog.user_id == user_id
        ).order_by(MoodLog.logged_at.desc()).first()

        if not recent_mood:
            return None

        # Only use mood if logged within last 12 hours
        if recent_mood.logged_at:
            hours_ago = (datetime.now(timezone.utc) - recent_mood.logged_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
            if hours_ago > 12:
                return None

        return {
            "mood_type": recent_mood.mood_type,
            "energy_level": recent_mood.energy_level,
            "primary_emotion": recent_mood.primary_emotion,
            "emotion_scores": recent_mood.emotion_scores
        }

    def _adjust_for_mood(
        self,
        title: str,
        message: str,
        priority: str,
        mood_context: Dict,
        notification_type: str
    ) -> tuple:
        """Adjust notification content and priority based on user's mood"""
        mood_type = mood_context.get("mood_type", "neutral")
        energy_level = mood_context.get("energy_level", 3)
        primary_emotion = mood_context.get("primary_emotion")

        # For stressed users - be gentler, reduce urgency
        if mood_type == "stressed" or primary_emotion == "anxiety":
            if priority == NotificationPriority.HIGH.value:
                priority = NotificationPriority.MEDIUM.value
            message = self._add_supportive_tone(message, "stressed")

        # For tired/low energy users - add motivation
        elif mood_type == "tired" or energy_level <= 2:
            message = self._add_supportive_tone(message, "tired")

        # For anxious users - provide reassurance
        elif primary_emotion == "fear" or mood_type == "anxious":
            message = self._add_supportive_tone(message, "anxious")

        # For motivated/confident users - can be more direct
        elif mood_type in ["motivated", "confident", "focused"]:
            # Keep original tone, possibly increase urgency for task reminders
            if notification_type == NotificationType.TASK_REMINDER.value:
                message = f"{message} You've got this - stay focused!"

        return title, message, priority

    def _add_supportive_tone(self, message: str, mood_type: str) -> str:
        """Add supportive messaging based on mood"""
        supportive_prefixes = {
            "stressed": "Take a breath. ",
            "tired": "When you're ready, ",
            "anxious": "No pressure, but "
        }

        supportive_suffixes = {
            "stressed": " Remember, one step at a time.",
            "tired": " Consider taking breaks when needed.",
            "anxious": " You're more prepared than you think."
        }

        prefix = supportive_prefixes.get(mood_type, "")
        suffix = supportive_suffixes.get(mood_type, "")

        return f"{prefix}{message}{suffix}"

    # ==================== MOOD CHECK REMINDERS ====================

    def create_mood_check_reminder(self, user_id: UUID) -> Optional[Notification]:
        """Create a reminder to log mood"""
        prefs = self.get_or_create_preferences(user_id)

        if not prefs.mood_check_reminders:
            return None

        messages = [
            "How are you feeling today? Taking a moment to check in with yourself can help you study more effectively.",
            "Quick mood check! Understanding your energy levels helps us give you better study recommendations.",
            "Time for a brief check-in. How's your mood and energy right now?",
            "Remember to log your mood - it helps us personalize your learning experience!"
        ]

        import random
        message = random.choice(messages)

        return self.create_notification(
            user_id=user_id,
            title="Mood Check-In",
            message=message,
            notification_type=NotificationType.MOOD_CHECK.value,
            priority=NotificationPriority.LOW.value,
            action_url="/mood",
            action_data={"open_mood_logger": True}
        )

    # ==================== STUDY PLAN NOTIFICATIONS ====================

    def create_study_plan_notification(
        self,
        user_id: UUID,
        study_plan_id: UUID,
        topic: str
    ) -> Optional[Notification]:
        """Notify user about a new study plan"""
        return self.create_notification(
            user_id=user_id,
            title=f"New Study Plan: {topic}",
            message=f"Your personalized study plan for '{topic}' is ready! Start learning with curated videos, articles, and practice resources.",
            notification_type=NotificationType.STUDY_PLAN.value,
            priority=NotificationPriority.MEDIUM.value,
            study_plan_id=study_plan_id,
            action_url=f"/smartstudy/plan/{study_plan_id}",
            action_data={"show_plan": True}
        )

    def create_study_session_reminder(
        self,
        user_id: UUID,
        study_plan_id: UUID,
        day_number: int,
        topic: str
    ) -> Optional[Notification]:
        """Remind user about their study session"""
        return self.create_notification(
            user_id=user_id,
            title=f"Study Session Day {day_number}",
            message=f"Time for your {topic} study session! Today's activities are waiting for you.",
            notification_type=NotificationType.STUDY_PLAN.value,
            priority=NotificationPriority.MEDIUM.value,
            study_plan_id=study_plan_id,
            action_url=f"/smartstudy/plan/{study_plan_id}",
            action_data={"highlight_day": day_number}
        )

    # ==================== GOAL PROGRESS NOTIFICATIONS ====================

    def create_goal_progress_notification(
        self,
        user_id: UUID,
        current_cgpa: float,
        target_cgpa: float,
        change: float
    ) -> Optional[Notification]:
        """Notify about CGPA goal progress"""
        gap = target_cgpa - current_cgpa

        if change > 0:
            title = "CGPA Improved!"
            if gap <= 0:
                message = f"Congratulations! You've reached your target CGPA of {target_cgpa}! Your current CGPA is {current_cgpa:.2f}."
                priority = NotificationPriority.HIGH.value
            else:
                message = f"Your CGPA improved by {change:.2f}! You're now at {current_cgpa:.2f}, just {gap:.2f} away from your target of {target_cgpa}."
                priority = NotificationPriority.MEDIUM.value
        else:
            title = "CGPA Update"
            message = f"Your current CGPA is {current_cgpa:.2f}. You need to improve by {gap:.2f} to reach your target of {target_cgpa}. Let's create a plan!"
            priority = NotificationPriority.MEDIUM.value

        return self.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=NotificationType.GOAL_PROGRESS.value,
            priority=priority,
            action_url="/gpa",
            action_data={"show_progress": True}
        )

    # ==================== ACHIEVEMENT NOTIFICATIONS ====================

    def create_achievement_notification(
        self,
        user_id: UUID,
        achievement_name: str,
        achievement_description: str
    ) -> Optional[Notification]:
        """Notify user about an achievement"""
        return self.create_notification(
            user_id=user_id,
            title=f"Achievement Unlocked: {achievement_name}",
            message=achievement_description,
            notification_type=NotificationType.ACHIEVEMENT.value,
            priority=NotificationPriority.MEDIUM.value,
            action_url="/achievements",
            action_data={"new_achievement": achievement_name}
        )

    # ==================== HELPER METHODS ====================

    def _is_quiet_hours(self, prefs: NotificationPreference) -> bool:
        """Check if current time is within quiet hours"""
        if not prefs.quiet_hours_start or not prefs.quiet_hours_end:
            return False

        try:
            import pytz
            tz = pytz.timezone(prefs.timezone or "Africa/Lagos")
            now = datetime.now(tz)
            current_time = now.strftime("%H:%M")

            start = prefs.quiet_hours_start
            end = prefs.quiet_hours_end

            # Handle overnight quiet hours (e.g., 22:00 to 08:00)
            if start > end:
                return current_time >= start or current_time < end
            else:
                return start <= current_time < end
        except Exception:
            return False

    def _get_next_active_time(self, prefs: NotificationPreference) -> datetime:
        """Get the next time notifications should be sent (after quiet hours)"""
        try:
            import pytz
            tz = pytz.timezone(prefs.timezone or "Africa/Lagos")
            now = datetime.now(tz)

            end_hour, end_min = map(int, prefs.quiet_hours_end.split(":"))
            next_active = now.replace(hour=end_hour, minute=end_min, second=0, microsecond=0)

            if next_active <= now:
                next_active += timedelta(days=1)

            return next_active.astimezone(timezone.utc)
        except Exception:
            return datetime.now(timezone.utc) + timedelta(hours=8)

    def _format_time_ago(self, dt: datetime) -> str:
        """Format a datetime as 'X hours/days ago'"""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        diff = datetime.now(timezone.utc) - dt

        if diff.days > 0:
            return f"{diff.days} day(s) ago"

        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours} hour(s) ago"

        minutes = diff.seconds // 60
        return f"{minutes} minute(s) ago"


# ==================== SINGLETON ACCESSOR ====================

def get_notification_service(db: Session) -> NotificationService:
    """Get notification service instance"""
    return NotificationService(db)
