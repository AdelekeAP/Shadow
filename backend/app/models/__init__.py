"""
SQLAlchemy Models for Shadow
"""
from app.models.user import User
from app.models.course import Course, UserCourse, Semester
from app.models.task import Task
from app.models.mood import MoodLog
from app.models.smartstudy import (
    ChatConversation,
    ChatMessage,
    StudyPlan,
    StudyPlanResource,
    UploadedDocument,
    InterventionOutcome,
    ContentQualityScore,
    VideoNote
)
from app.models.quiz import Quiz, QuizAttempt
from app.models.library import LibraryDocument, LibraryVote
from app.models.content_curation import CuratedResource, ContentCurationQuery
from app.models.notification import (
    Notification,
    NotificationPreference,
    ScheduledReminder,
    NotificationType,
    NotificationPriority,
    DeliveryChannel
)
from app.models.usage_log import UsageLog

__all__ = [
    "User",
    "Course",
    "UserCourse",
    "Semester",
    "Task",
    "MoodLog",
    "ChatConversation",
    "ChatMessage",
    "StudyPlan",
    "StudyPlanResource",
    "UploadedDocument",
    "InterventionOutcome",
    "ContentQualityScore",
    "VideoNote",
    "LibraryDocument",
    "LibraryVote",
    "CuratedResource",
    "ContentCurationQuery",
    "Notification",
    "NotificationPreference",
    "ScheduledReminder",
    "NotificationType",
    "NotificationPriority",
    "DeliveryChannel",
    "UsageLog",
    "Quiz",
    "QuizAttempt"
]
