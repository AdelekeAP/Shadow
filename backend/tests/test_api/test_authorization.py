"""
Tests for cross-user authorization (IDOR prevention).

Verifies that User A cannot access, modify, or delete resources
belonging to User B. Each test registers two separate users and
creates resources under User B, then attempts access with User A's token.
"""
import pytest
import uuid as _uuid
from datetime import datetime, timezone


# ===================================================================
# Helpers
# ===================================================================

def register_user(client, email, university_id):
    """Register a user and return (user_data_dict, auth_headers)."""
    user_data = {
        "email": email,
        "password": "SecurePass123!",
        "full_name": f"Test User {email}",
        "university_id": university_id,
        "entry_level": "400L",
        "target_cgpa": 4.5,
        "current_cgpa": 3.8,
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201, f"Registration failed for {email}: {response.text}"
    data = response.json()
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    return data, headers


def create_course_and_enroll(client, auth_headers, code="CSC401"):
    """Helper: create a course and enroll the user, return enrollment ID."""
    course = client.post("/api/v1/courses/", json={
        "code": code,
        "title": f"Course {code}",
        "credits": 3,
        "level": "400",
        "status": "C",
    }, headers=auth_headers).json()
    enrollment = client.post("/api/v1/courses/enroll", json={
        "course_id": course["id"],
    }, headers=auth_headers).json()
    return enrollment["id"], course["id"]


def create_task(client, auth_headers, user_course_id, **overrides):
    """Helper: create a task and return the response."""
    data = {
        "user_course_id": user_course_id,
        "title": "Test Assignment",
        "task_type": "assignment",
        "weight": 10,
        "category": "CA",
    }
    data.update(overrides)
    return client.post("/api/v1/tasks/", json=data, headers=auth_headers)


# ===================================================================
# Fixtures
# ===================================================================

@pytest.fixture
def user_a(client):
    """Register User A and return (data, headers)."""
    return register_user(client, "usera@pau.edu.ng", "PAU/2022/001")


@pytest.fixture
def user_b(client):
    """Register User B and return (data, headers)."""
    return register_user(client, "userb@pau.edu.ng", "PAU/2022/002")


@pytest.fixture
def user_a_headers(user_a):
    """Auth headers for User A."""
    return user_a[1]


@pytest.fixture
def user_b_headers(user_b):
    """Auth headers for User B."""
    return user_b[1]


@pytest.fixture
def user_b_task(client, user_b_headers):
    """Create a task owned by User B, return the task dict."""
    uc_id, _ = create_course_and_enroll(client, user_b_headers, code="CSC402")
    response = create_task(client, user_b_headers, uc_id, title="User B Task")
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def user_b_conversation(client, db_session, user_b):
    """Create a conversation owned by User B."""
    from app.models.smartstudy import ChatConversation, ChatMessage

    user_id = _uuid.UUID(user_b[0]["user"]["id"])
    conv = ChatConversation(user_id=user_id, title="User B Conversation")
    db_session.add(conv)
    db_session.flush()

    msg = ChatMessage(
        conversation_id=conv.id,
        role="user",
        content="Hello from User B",
        tokens_used=10,
    )
    db_session.add(msg)
    db_session.commit()
    db_session.refresh(conv)
    return {"conversation_id": str(conv.id)}


@pytest.fixture
def user_b_study_plan(client, db_session, user_b):
    """Create a study plan owned by User B."""
    from app.models.smartstudy import StudyPlan
    from app.models.course import Course, UserCourse

    user_id = _uuid.UUID(user_b[0]["user"]["id"])

    # Create course and enrollment for User B
    course = Course(code="CSC403", title="Algorithms", credits=3, level="400L")
    db_session.add(course)
    db_session.flush()

    enrollment = UserCourse(
        user_id=user_id,
        course_id=course.id,
        ca_score=20.0,
        exam_score=50.0,
    )
    db_session.add(enrollment)
    db_session.flush()

    plan = StudyPlan(
        user_id=user_id,
        course_id=course.id,
        topic="Graph Algorithms",
        trigger_type="student_request",
        plan_data={"days": [{"day": 1, "activities": ["Study graphs"]}]},
        duration_days=7,
        completion_percentage=0,
        is_active=True,
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    return {"plan_id": str(plan.id)}


@pytest.fixture
def user_b_notification(client, db_session, user_b):
    """Create a notification owned by User B."""
    from app.models.notification import Notification

    user_id = _uuid.UUID(user_b[0]["user"]["id"])
    notif = Notification(
        user_id=user_id,
        title="User B Notification",
        message="Private notification for User B",
        notification_type="system",
        priority="medium",
        channel="in_app",
        is_read=False,
        is_dismissed=False,
    )
    db_session.add(notif)
    db_session.commit()
    db_session.refresh(notif)
    return {"notification_id": str(notif.id)}


# ===================================================================
# Task IDOR Tests
# ===================================================================

class TestCrossUserTaskAuthorization:
    """Verify that users cannot access other users' tasks."""

    def test_cannot_get_other_users_task(self, client, user_a_headers, user_b_task):
        """User A should not be able to GET User B's task."""
        response = client.get(
            f"/api/v1/tasks/{user_b_task['id']}",
            headers=user_a_headers,
        )
        assert response.status_code in (403, 404)

    def test_cannot_update_other_users_task(self, client, user_a_headers, user_b_task):
        """User A should not be able to PATCH User B's task."""
        response = client.patch(
            f"/api/v1/tasks/{user_b_task['id']}",
            headers=user_a_headers,
            json={"title": "hacked"},
        )
        assert response.status_code in (403, 404)

    def test_cannot_delete_other_users_task(self, client, user_a_headers, user_b_task):
        """User A should not be able to DELETE User B's task."""
        response = client.delete(
            f"/api/v1/tasks/{user_b_task['id']}",
            headers=user_a_headers,
        )
        assert response.status_code in (403, 404)

    def test_cannot_complete_other_users_task(self, client, user_a_headers, user_b_task):
        """User A should not be able to mark User B's task as complete."""
        response = client.patch(
            f"/api/v1/tasks/{user_b_task['id']}/complete",
            headers=user_a_headers,
            json={"earned_marks": 10},
        )
        assert response.status_code in (403, 404)

    def test_task_list_only_returns_own_tasks(self, client, user_a_headers, user_b_task):
        """User A's task list should not include User B's tasks."""
        response = client.get("/api/v1/tasks/", headers=user_a_headers)
        assert response.status_code == 200
        task_ids = [t["id"] for t in response.json()]
        assert user_b_task["id"] not in task_ids


# ===================================================================
# Conversation IDOR Tests
# ===================================================================

class TestCrossUserConversationAuthorization:
    """Verify that users cannot access other users' conversations."""

    def test_cannot_get_other_users_conversation(self, client, user_a_headers, user_b_conversation):
        """User A should not be able to GET User B's conversation."""
        response = client.get(
            f"/api/v1/smartstudy/conversations/{user_b_conversation['conversation_id']}",
            headers=user_a_headers,
        )
        assert response.status_code in (403, 404)

    def test_cannot_delete_other_users_conversation(self, client, user_a_headers, user_b_conversation):
        """User A should not be able to DELETE User B's conversation."""
        response = client.delete(
            f"/api/v1/smartstudy/conversations/{user_b_conversation['conversation_id']}",
            headers=user_a_headers,
        )
        assert response.status_code in (403, 404)

    def test_conversation_list_only_returns_own(self, client, user_a_headers, user_b_conversation):
        """User A's conversation list should not include User B's conversations."""
        response = client.get(
            "/api/v1/smartstudy/conversations",
            headers=user_a_headers,
        )
        assert response.status_code == 200
        conv_ids = [c["id"] for c in response.json()]
        assert user_b_conversation["conversation_id"] not in conv_ids


# ===================================================================
# Study Plan IDOR Tests
# ===================================================================

class TestCrossUserStudyPlanAuthorization:
    """Verify that users cannot access other users' study plans."""

    def test_cannot_get_other_users_study_plan(self, client, user_a_headers, user_b_study_plan):
        """User A should not be able to GET User B's study plan."""
        response = client.get(
            f"/api/v1/smartstudy/study-plans/{user_b_study_plan['plan_id']}",
            headers=user_a_headers,
        )
        assert response.status_code in (403, 404)

    def test_cannot_update_other_users_study_plan(self, client, user_a_headers, user_b_study_plan):
        """User A should not be able to PATCH User B's study plan."""
        response = client.patch(
            f"/api/v1/smartstudy/study-plans/{user_b_study_plan['plan_id']}",
            headers=user_a_headers,
            json={"completion_percentage": 100},
        )
        assert response.status_code in (403, 404)

    def test_study_plan_list_only_returns_own(self, client, user_a_headers, user_b_study_plan):
        """User A's study plan list should not include User B's plans."""
        response = client.get(
            "/api/v1/smartstudy/study-plans",
            headers=user_a_headers,
        )
        assert response.status_code == 200
        plan_ids = [p["id"] for p in response.json()]
        assert user_b_study_plan["plan_id"] not in plan_ids


# ===================================================================
# Notification IDOR Tests
# ===================================================================

class TestCrossUserNotificationAuthorization:
    """Verify that users cannot access other users' notifications."""

    def test_cannot_get_other_users_notification(self, client, user_a_headers, user_b_notification):
        """User A should not be able to GET User B's notification."""
        response = client.get(
            f"/api/v1/notifications/{user_b_notification['notification_id']}",
            headers=user_a_headers,
        )
        assert response.status_code in (403, 404)

    def test_cannot_mark_other_users_notification_read(self, client, user_a_headers, user_b_notification):
        """User A should not be able to mark User B's notification as read."""
        response = client.post(
            f"/api/v1/notifications/{user_b_notification['notification_id']}/read",
            headers=user_a_headers,
        )
        assert response.status_code in (403, 404)

    def test_cannot_dismiss_other_users_notification(self, client, user_a_headers, user_b_notification):
        """User A should not be able to dismiss User B's notification."""
        response = client.post(
            f"/api/v1/notifications/{user_b_notification['notification_id']}/dismiss",
            headers=user_a_headers,
        )
        assert response.status_code in (403, 404)


# ===================================================================
# Mood Log IDOR Tests
# ===================================================================

class TestCrossUserMoodAuthorization:
    """Verify that mood endpoints only return the current user's data."""

    def test_mood_logs_only_returns_own_entries(self, client, user_a_headers, user_b_headers):
        """User A's mood logs should only contain their own entries."""
        # User B logs a mood
        client.post(
            "/api/v1/mood/log-mood",
            headers=user_b_headers,
            json={"mood_type": "focused", "energy_level": 4},
        )

        # User A should see an empty list (no moods logged by A)
        response = client.get("/api/v1/mood/moods", headers=user_a_headers)
        assert response.status_code == 200
        data = response.json()
        # The response may be a list or a dict with a list; handle both
        if isinstance(data, list):
            assert len(data) == 0
        elif isinstance(data, dict) and "logs" in data:
            assert len(data["logs"]) == 0
