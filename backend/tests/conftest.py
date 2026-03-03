"""
Shared test fixtures for Shadow backend tests
"""
import pytest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Mock objects that mirror SQLAlchemy model attributes without needing a DB
# ---------------------------------------------------------------------------

class MockTask:
    """Lightweight mock of app.models.task.Task"""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.user_id = kwargs.get("user_id", uuid.uuid4())
        self.user_course_id = kwargs.get("user_course_id", uuid.uuid4())
        self.title = kwargs.get("title", "Test Task")
        self.description = kwargs.get("description", "")
        self.task_type = kwargs.get("task_type", "assignment")
        self.topic = kwargs.get("topic", None)
        self.weight = kwargs.get("weight", 10)
        self.max_marks = kwargs.get("max_marks", None)
        self.earned_marks = kwargs.get("earned_marks", None)
        self.category = kwargs.get("category", "CA")
        self.due_date = kwargs.get("due_date", None)
        self.completed_at = kwargs.get("completed_at", None)
        self.is_completed = kwargs.get("is_completed", False)
        self.is_late = kwargs.get("is_late", False)
        self.effort_estimate = kwargs.get("effort_estimate", None)
        self.actual_effort = kwargs.get("actual_effort", None)
        self.priority_score = kwargs.get("priority_score", None)
        self.is_urgent = kwargs.get("is_urgent", False)


class MockUser:
    """Lightweight mock of app.models.user.User"""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.email = kwargs.get("email", "test@pau.edu.ng")
        self.password_hash = kwargs.get("password_hash", "")
        self.full_name = kwargs.get("full_name", "Test Student")
        self.university_id = kwargs.get("university_id", "PAU/2022/001")
        self.entry_level = kwargs.get("entry_level", "300L")
        self.gpa_scale = kwargs.get("gpa_scale", 5.0)
        self.target_cgpa = kwargs.get("target_cgpa", 4.5)
        self.current_cgpa = kwargs.get("current_cgpa", 3.8)
        self.total_credits_completed = kwargs.get("total_credits_completed", 60)
        self.learning_style = kwargs.get("learning_style", None)
        self.is_active = kwargs.get("is_active", True)


class MockMoodLog:
    """Lightweight mock of app.models.mood.MoodLog"""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.user_id = kwargs.get("user_id", uuid.uuid4())
        self.mood_type = kwargs.get("mood_type", "focused")
        self.energy_level = kwargs.get("energy_level", 3)
        self.note = kwargs.get("note", None)
        self.sentiment_score = kwargs.get("sentiment_score", None)
        self.primary_emotion = kwargs.get("primary_emotion", None)
        self.emotion_confidence = kwargs.get("emotion_confidence", None)
        self.emotion_scores = kwargs.get("emotion_scores", None)
        self.logged_at = kwargs.get("logged_at", datetime.now(timezone.utc))


class MockCourse:
    """Lightweight mock of app.models.course.Course"""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.code = kwargs.get("code", "CSC401")
        self.title = kwargs.get("title", "Software Engineering")
        self.credits = kwargs.get("credits", 3)


class MockUserCourse:
    """Lightweight mock of app.models.course.UserCourse"""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.user_id = kwargs.get("user_id", uuid.uuid4())
        self.course_id = kwargs.get("course_id", uuid.uuid4())
        self.course = kwargs.get("course", MockCourse())
        self.is_priority = kwargs.get("is_priority", False)
        self.is_carryover = kwargs.get("is_carryover", False)


# ---------------------------------------------------------------------------
# Reusable fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_user():
    return MockUser()


@pytest.fixture
def sample_task():
    return MockTask(
        due_date=datetime.utcnow() + timedelta(days=3),
        weight=15,
        category="CA",
    )


@pytest.fixture
def overdue_task():
    return MockTask(
        title="Overdue Assignment",
        due_date=datetime.utcnow() - timedelta(days=2),
        weight=20,
        category="CA",
    )


@pytest.fixture
def exam_task():
    return MockTask(
        title="Final Exam",
        due_date=datetime.utcnow() + timedelta(days=14),
        weight=65,
        category="EXAM",
        task_type="exam",
    )


@pytest.fixture
def high_energy_mood():
    return MockMoodLog(energy_level=5, mood_type="motivated")


@pytest.fixture
def low_energy_mood():
    return MockMoodLog(energy_level=1, mood_type="tired")


@pytest.fixture
def stressed_mood():
    return MockMoodLog(energy_level=3, mood_type="stressed")
