"""
Notification Scheduler - Background tasks for automatic notifications
Uses APScheduler for lightweight scheduling without Redis/Celery overhead
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.database import SessionLocal
from app.models.task import Task
from app.models.user import User
from app.models.mood import MoodLog
from app.models.notification import ScheduledReminder, NotificationPreference
from app.services.notification_service import NotificationService, get_notification_service
from app.services.email_service import send_task_overdue_email

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None


def get_db_session() -> Session:
    """Create a new database session for background tasks"""
    return SessionLocal()


async def process_task_reminders():
    """
    Check for tasks with upcoming deadlines and create reminders
    Runs every 15 minutes
    """
    db = get_db_session()
    try:
        logger.info("Processing task reminders...")

        now = datetime.now(timezone.utc)

        # Get all users with notification preferences
        users = db.query(User).filter(User.is_active == True).all()

        for user in users:
            try:
                service = get_notification_service(db)
                prefs = service.get_or_create_preferences(user.id)

                if not prefs.task_reminders:
                    continue

                reminder_hours = prefs.task_reminder_hours or 24

                # Find tasks due within the reminder window
                reminder_window = now + timedelta(hours=reminder_hours)

                upcoming_tasks = db.query(Task).filter(
                    Task.user_id == user.id,
                    Task.is_completed == False,
                    Task.due_date != None,
                    Task.due_date <= reminder_window,
                    Task.due_date > now
                ).all()

                for task in upcoming_tasks:
                    # Check if reminder already exists for this task
                    from app.models.notification import Notification, NotificationType

                    existing = db.query(Notification).filter(
                        Notification.user_id == user.id,
                        Notification.task_id == task.id,
                        Notification.notification_type == NotificationType.TASK_REMINDER.value,
                        Notification.created_at > now - timedelta(hours=24)
                    ).first()

                    if not existing:
                        service.create_task_reminder(user.id, task)
                        logger.info(f"Created reminder for task {task.id} for user {user.id}")

            except Exception as e:
                logger.error(f"Error processing reminders for user {user.id}: {e}")

        logger.info("Task reminder processing complete")

    except Exception as e:
        logger.error(f"Error in process_task_reminders: {e}")
    finally:
        db.close()


async def process_overdue_tasks():
    """
    Check for overdue tasks and create notifications
    Runs every hour
    """
    db = get_db_session()
    try:
        logger.info("Processing overdue task notifications...")

        now = datetime.now(timezone.utc)

        # Find overdue tasks
        overdue_tasks = db.query(Task).filter(
            Task.is_completed == False,
            Task.due_date != None,
            Task.due_date < now
        ).all()

        for task in overdue_tasks:
            try:
                service = get_notification_service(db)

                # Check user preferences
                prefs = service.get_or_create_preferences(task.user_id)
                if not prefs.task_overdue:
                    continue

                # Check if overdue notification already sent (within last 24 hours)
                from app.models.notification import Notification, NotificationType

                existing = db.query(Notification).filter(
                    Notification.user_id == task.user_id,
                    Notification.task_id == task.id,
                    Notification.notification_type == NotificationType.TASK_OVERDUE.value,
                    Notification.created_at > now - timedelta(hours=24)
                ).first()

                if not existing:
                    service.create_overdue_notification(task.user_id, task)
                    logger.info(f"Created overdue notification for task {task.id}")

                    # Send overdue email (best-effort)
                    try:
                        user = db.query(User).filter(User.id == task.user_id).first()
                        if user and user.email:
                            course_name = task.course.title if hasattr(task, 'course') and task.course else "Unknown Course"
                            due_str = task.due_date.strftime("%b %d, %Y") if task.due_date else "N/A"
                            send_task_overdue_email(
                                to=user.email,
                                name=user.full_name or "Student",
                                task_title=task.title or "Untitled Task",
                                course_name=course_name,
                                due_date=due_str,
                            )
                            logger.info(f"Sent overdue email for task {task.id} to {user.email}")
                    except Exception as email_err:
                        logger.warning(f"Failed to send overdue email for task {task.id}: {email_err}")

            except Exception as e:
                logger.error(f"Error processing overdue task {task.id}: {e}")

        logger.info("Overdue task processing complete")

    except Exception as e:
        logger.error(f"Error in process_overdue_tasks: {e}")
    finally:
        db.close()


async def process_mood_check_reminders():
    """
    Send mood check reminders to users based on their preferences
    Runs daily at 9 AM and 3 PM
    """
    db = get_db_session()
    try:
        logger.info("Processing mood check reminders...")

        now = datetime.now(timezone.utc)

        # Get users who want mood check reminders
        prefs = db.query(NotificationPreference).filter(
            NotificationPreference.mood_check_reminders == True
        ).all()

        for pref in prefs:
            try:
                # Check if user already logged mood today
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

                recent_mood = db.query(MoodLog).filter(
                    MoodLog.user_id == pref.user_id,
                    MoodLog.logged_at >= today_start
                ).first()

                if not recent_mood:
                    service = get_notification_service(db)
                    service.create_mood_check_reminder(pref.user_id)
                    logger.info(f"Created mood check reminder for user {pref.user_id}")

            except Exception as e:
                logger.error(f"Error processing mood reminder for user {pref.user_id}: {e}")

        logger.info("Mood check reminder processing complete")

    except Exception as e:
        logger.error(f"Error in process_mood_check_reminders: {e}")
    finally:
        db.close()


async def process_scheduled_reminders():
    """
    Process custom scheduled reminders
    Runs every 5 minutes
    """
    db = get_db_session()
    try:
        logger.info("Processing scheduled reminders...")

        now = datetime.now(timezone.utc)

        # Find due reminders
        due_reminders = db.query(ScheduledReminder).filter(
            ScheduledReminder.is_active == True,
            ScheduledReminder.is_sent == False,
            or_(
                ScheduledReminder.scheduled_time <= now,
                ScheduledReminder.next_run_at <= now
            )
        ).all()

        for reminder in due_reminders:
            try:
                service = get_notification_service(db)

                # Create notification from reminder
                title = reminder.custom_title or f"Reminder: {reminder.reminder_type}"
                message = reminder.custom_message or f"This is your scheduled {reminder.reminder_type} reminder."

                service.create_notification(
                    user_id=reminder.user_id,
                    title=title,
                    message=message,
                    notification_type="system",
                    check_preferences=True
                )

                # Update reminder status
                reminder.is_sent = True
                reminder.last_sent_at = now

                # Handle recurring reminders
                if reminder.is_recurring:
                    reminder.is_sent = False
                    reminder.next_run_at = calculate_next_run(reminder)

                db.commit()
                logger.info(f"Processed scheduled reminder {reminder.id}")

            except Exception as e:
                logger.error(f"Error processing reminder {reminder.id}: {e}")

        logger.info("Scheduled reminder processing complete")

    except Exception as e:
        logger.error(f"Error in process_scheduled_reminders: {e}")
    finally:
        db.close()


def calculate_next_run(reminder: ScheduledReminder) -> datetime:
    """Calculate the next run time for a recurring reminder"""
    now = datetime.now(timezone.utc)
    pattern = reminder.recurrence_pattern

    if pattern == "daily":
        return now + timedelta(days=1)
    elif pattern == "weekly":
        return now + timedelta(weeks=1)
    elif pattern == "hourly":
        return now + timedelta(hours=1)
    elif pattern == "custom" and reminder.recurrence_data:
        # Custom recurrence rules (e.g., {"interval_hours": 6})
        hours = reminder.recurrence_data.get("interval_hours", 24)
        return now + timedelta(hours=hours)
    else:
        return now + timedelta(days=1)


async def cleanup_old_notifications():
    """
    Clean up old read notifications
    Runs daily at midnight
    """
    db = get_db_session()
    try:
        logger.info("Cleaning up old notifications...")

        service = get_notification_service(db)
        deleted = service.delete_old_notifications(days_old=30)

        logger.info(f"Deleted {deleted} old notifications")

    except Exception as e:
        logger.error(f"Error in cleanup_old_notifications: {e}")
    finally:
        db.close()


def init_scheduler():
    """Initialize the notification scheduler with all jobs"""
    global scheduler

    scheduler = AsyncIOScheduler()

    # Task reminders - every 15 minutes
    scheduler.add_job(
        process_task_reminders,
        IntervalTrigger(minutes=15),
        id="task_reminders",
        name="Process Task Reminders",
        replace_existing=True
    )

    # Overdue tasks - every hour
    scheduler.add_job(
        process_overdue_tasks,
        IntervalTrigger(hours=1),
        id="overdue_tasks",
        name="Process Overdue Tasks",
        replace_existing=True
    )

    # Mood check reminders - at 9 AM and 3 PM
    scheduler.add_job(
        process_mood_check_reminders,
        CronTrigger(hour=9, minute=0),
        id="mood_check_morning",
        name="Morning Mood Check",
        replace_existing=True
    )
    scheduler.add_job(
        process_mood_check_reminders,
        CronTrigger(hour=15, minute=0),
        id="mood_check_afternoon",
        name="Afternoon Mood Check",
        replace_existing=True
    )

    # Scheduled reminders - every 5 minutes
    scheduler.add_job(
        process_scheduled_reminders,
        IntervalTrigger(minutes=5),
        id="scheduled_reminders",
        name="Process Scheduled Reminders",
        replace_existing=True
    )

    # Cleanup - daily at midnight
    scheduler.add_job(
        cleanup_old_notifications,
        CronTrigger(hour=0, minute=0),
        id="cleanup",
        name="Cleanup Old Notifications",
        replace_existing=True
    )

    logger.info("Notification scheduler initialized with all jobs")
    return scheduler


def start_scheduler():
    """Start the notification scheduler"""
    global scheduler

    if scheduler is None:
        scheduler = init_scheduler()

    if not scheduler.running:
        scheduler.start()
        logger.info("Notification scheduler started")


def stop_scheduler():
    """Stop the notification scheduler"""
    global scheduler

    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Notification scheduler stopped")


def get_scheduler_status():
    """Get the current status of the scheduler"""
    global scheduler

    if scheduler is None:
        return {"status": "not_initialized", "jobs": []}

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None
        })

    return {
        "status": "running" if scheduler.running else "stopped",
        "jobs": jobs
    }
