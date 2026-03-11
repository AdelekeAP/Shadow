"""
Integration test fixtures - FastAPI TestClient with in-memory SQLite database.

This creates a fully isolated test environment:
- SQLite in-memory DB (no PostgreSQL needed)
- Fresh tables for every test
- FastAPI app with overridden DB dependency
"""
import pytest
import os

# Disable ML models, rate limiting, and set test env BEFORE importing app modules
os.environ["DISABLE_ML_MODELS"] = "true"
os.environ["TESTING"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-for-integration-tests"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ.setdefault("ADMIN_EMAILS", "*")

import uuid as _uuid_module

from sqlalchemy import create_engine, event, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from fastapi.testclient import TestClient

from app.database import Base, get_db


# Create in-memory SQLite engine
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Render PostgreSQL JSONB as plain JSON for SQLite compatibility
from sqlalchemy.ext.compiler import compiles

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

# Patch PostgreSQL UUID bind_processor so it accepts plain strings on SQLite.
# Routes that declare path parameters as `str` pass string UUIDs to
# SQLAlchemy UUID(as_uuid=True) columns.  PostgreSQL handles the cast
# implicitly, but the default SQLite adapter calls `value.hex` which
# fails on strings.  This wrapper converts strings to uuid.UUID first.
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

# Enable foreign key support in SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override the get_db dependency to use test database"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    # Import all models so they're registered with Base
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a TestClient with overridden DB dependency"""
    # Import app lazily to avoid startup side effects
    from app.main import app

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def registered_user(client):
    """Register a test user and return the response data"""
    user_data = {
        "email": "teststudent@pau.edu.ng",
        "password": "SecurePass123!",
        "full_name": "Test Student",
        "university_id": "PAU/2022/001",
        "entry_level": "400L",
        "target_cgpa": 4.5,
        "current_cgpa": 3.8,
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201, f"Registration failed: {response.text}"
    data = response.json()
    data["password"] = user_data["password"]  # Keep plain password for login tests
    return data


@pytest.fixture
def auth_headers(registered_user):
    """Return authorization headers for an authenticated user"""
    token = registered_user["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def course_in_db(db_session, registered_user):
    """Create a course and enroll the registered user"""
    from app.models.course import Course, UserCourse
    import uuid as _uuid
    course = Course(
        code="CSC401",
        title="Software Engineering",
        credits=3,
        level="400L"
    )
    db_session.add(course)
    db_session.flush()

    user_id = _uuid.UUID(registered_user["user"]["id"])
    enrollment = UserCourse(
        user_id=user_id,
        course_id=course.id,
        ca_score=25.0,
        exam_score=55.0,
    )
    db_session.add(enrollment)
    db_session.commit()
    return {"course": course, "course_id": str(course.id)}


@pytest.fixture
def study_plan_in_db(db_session, registered_user, course_in_db):
    """Create a study plan with resources"""
    from app.models.smartstudy import StudyPlan, StudyPlanResource
    import uuid as _uuid

    user_id = _uuid.UUID(registered_user["user"]["id"])
    plan = StudyPlan(
        user_id=user_id,
        course_id=course_in_db["course"].id,
        topic="Binary Search Trees",
        trigger_type="student_request",
        plan_data={"days": [{"day": 1, "activities": ["Read chapter 5"]}]},
        duration_days=7,
        completion_percentage=0,
        is_active=True,
    )
    db_session.add(plan)
    db_session.flush()

    resource = StudyPlanResource(
        study_plan_id=plan.id,
        resource_type="youtube_video",
        resource_url="https://www.youtube.com/watch?v=test123",
        resource_title="BST Tutorial",
        resource_description="Learn BST basics",
        day_number=1,
        order_in_day=1,
    )
    db_session.add(resource)
    db_session.commit()
    db_session.refresh(plan)
    db_session.refresh(resource)
    return {
        "plan": plan,
        "plan_id": str(plan.id),
        "resource": resource,
        "resource_id": str(resource.id),
    }


@pytest.fixture
def conversation_in_db(db_session, registered_user):
    """Create a chat conversation with messages"""
    from app.models.smartstudy import ChatConversation, ChatMessage
    import uuid as _uuid

    user_id = _uuid.UUID(registered_user["user"]["id"])
    conv = ChatConversation(
        user_id=user_id,
        title="Help with BSTs",
    )
    db_session.add(conv)
    db_session.flush()

    msg1 = ChatMessage(
        conversation_id=conv.id,
        role="user",
        content="Help me understand BSTs",
        tokens_used=50,
    )
    msg2 = ChatMessage(
        conversation_id=conv.id,
        role="assistant",
        content="A BST is a tree data structure...",
        tokens_used=150,
    )
    db_session.add_all([msg1, msg2])
    db_session.commit()
    db_session.refresh(conv)
    return {
        "conversation": conv,
        "conversation_id": str(conv.id),
        "messages": [msg1, msg2],
    }


@pytest.fixture
def library_document_in_db(db_session, registered_user, course_in_db):
    """Create a library document"""
    from app.models.library import LibraryDocument
    import hashlib
    import uuid as _uuid
    doc = LibraryDocument(
        course_id=course_in_db["course"].id,
        topic="Binary Search Trees",
        file_name="BST_lecture.pdf",
        file_path="/tmp/fake/BST_lecture.pdf",
        file_type="pdf",
        file_size=1024,
        content_hash=hashlib.sha256(b"fake content").hexdigest(),
        uploaded_by=_uuid.UUID(registered_user["user"]["id"]),
        is_public=True,
        helpful_votes=5,
        view_count=10,
        download_count=3,
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    return {"document": doc, "document_id": str(doc.id)}


@pytest.fixture
def notification_in_db(db_session, registered_user):
    """Create a notification for the test user"""
    from app.models.notification import Notification
    import uuid as _uuid
    notif = Notification(
        user_id=_uuid.UUID(registered_user["user"]["id"]),
        title="Test Notification",
        message="This is a test notification",
        notification_type="system",
        priority="medium",
        channel="in_app",
        is_read=False,
        is_dismissed=False,
    )
    db_session.add(notif)
    db_session.commit()
    db_session.refresh(notif)
    return {"notification": notif, "notification_id": str(notif.id)}
