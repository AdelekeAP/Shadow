"""
Shared test fixtures for Shadow backend tests
"""
import pytest
import os
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Integration test fixtures (in-memory SQLite + FastAPI TestClient)
# These are used by tests/test_e2e_flows.py and can be used by any test
# under tests/ that needs a real HTTP client with a fresh database.
# ---------------------------------------------------------------------------

# Set test environment BEFORE importing app modules
os.environ.setdefault("DISABLE_ML_MODELS", "true")
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-integration-tests")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")

import uuid as _uuid_module

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from fastapi.testclient import TestClient

from app.database import Base, get_db

# ---------------------------------------------------------------------------
# SQLite dialect patches (run once at import time)
# ---------------------------------------------------------------------------

# Render PostgreSQL JSONB as plain JSON for SQLite compatibility
from sqlalchemy.ext.compiler import compiles

@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

# Patch PostgreSQL UUID bind_processor for SQLite compatibility
_original_uuid_bind_processor = PG_UUID.bind_processor

def _patched_uuid_bind_processor(self, dialect):
    original = _original_uuid_bind_processor(self, dialect)
    if original is None:
        return None

    def process(value):
        if isinstance(value, str):
            value = _uuid_module.UUID(value)
        return original(value)

    return process

PG_UUID.bind_processor = _patched_uuid_bind_processor


# ---------------------------------------------------------------------------
# Session-scoped engine — created once per test session for performance.
# Function-scoped db_session ensures each test starts with a clean slate.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def _test_engine():
    """Session-scoped SQLite engine (created once, reused across all tests)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable foreign key support in SQLite
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


# Module-level fallback engine for tests that don't use the fixture directly
# (needed by _override_get_db and legacy code paths)
_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@event.listens_for(_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _override_get_db():
    """Override the get_db dependency to use test database"""
    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test.

    Uses the module-level engine with StaticPool so every session in the same
    test (including the FastAPI dependency override) shares the same in-memory
    database while still getting a clean schema per test function.
    """
    import app.models  # noqa: F401 — register all models with Base

    Base.metadata.create_all(bind=_engine)
    session = _TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a TestClient with overridden DB dependency"""
    from app.main import app

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


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
        due_date=datetime.now(timezone.utc) + timedelta(days=3),
        weight=15,
        category="CA",
    )


@pytest.fixture
def overdue_task():
    return MockTask(
        title="Overdue Assignment",
        due_date=datetime.now(timezone.utc) - timedelta(days=2),
        weight=20,
        category="CA",
    )


@pytest.fixture
def exam_task():
    return MockTask(
        title="Final Exam",
        due_date=datetime.now(timezone.utc) + timedelta(days=14),
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
