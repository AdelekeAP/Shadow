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
    ContentQualityScore
)

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
    "ContentQualityScore"
]
