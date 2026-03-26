"""
Integration tests for Task API routes
backend/app/routes/tasks.py

Tests the full task lifecycle: create, list, complete, stats.
"""
import pytest
from datetime import datetime, timedelta, timezone


def create_course_and_enroll(client, auth_headers, code="CSC401"):
    """Helper: create a course and enroll the user, return enrollment ID"""
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
    """Helper: create a task"""
    data = {
        "user_course_id": user_course_id,
        "title": "Test Assignment",
        "task_type": "assignment",
        "weight": 15,
        "category": "CA",
    }
    data.update(overrides)
    return client.post("/api/v1/tasks/", json=data, headers=auth_headers)


# ===================================================================
# POST /api/v1/tasks/ - Create Task
# ===================================================================

class TestCreateTask:

    def test_create_ca_task(self, client, auth_headers):
        uc_id, _ = create_course_and_enroll(client, auth_headers)
        response = create_task(client, auth_headers, uc_id)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Assignment"
        assert data["weight"] == 15.0
        assert data["category"] == "CA"
        assert data["is_completed"] is False
        assert data["priority_score"] is not None

    def test_create_exam_task(self, client, auth_headers):
        uc_id, _ = create_course_and_enroll(client, auth_headers)
        response = create_task(client, auth_headers, uc_id,
                               title="Final Exam",
                               task_type="exam",
                               weight=65,
                               category="EXAM")
        assert response.status_code == 201
        assert response.json()["category"] == "EXAM"

    def test_ca_exceeds_30_rejected(self, client, auth_headers):
        uc_id, _ = create_course_and_enroll(client, auth_headers)
        # Create first task: 20 marks
        create_task(client, auth_headers, uc_id, weight=20)
        # Create second task: 15 marks (total 35 > 30)
        response = create_task(client, auth_headers, uc_id, title="Second Task", weight=15)
        assert response.status_code == 400
        assert "CA cannot exceed 30" in response.json()["detail"]

    def test_ca_exactly_30_allowed(self, client, auth_headers):
        uc_id, _ = create_course_and_enroll(client, auth_headers)
        create_task(client, auth_headers, uc_id, weight=15)
        response = create_task(client, auth_headers, uc_id, title="Task 2", weight=15)
        assert response.status_code == 201

    def test_task_with_due_date(self, client, auth_headers):
        uc_id, _ = create_course_and_enroll(client, auth_headers)
        due = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        response = create_task(client, auth_headers, uc_id, due_date=due)
        assert response.status_code == 201
        assert response.json()["due_date"] is not None

    def test_completed_task_with_marks(self, client, auth_headers):
        uc_id, _ = create_course_and_enroll(client, auth_headers)
        response = create_task(client, auth_headers, uc_id,
                               is_completed=True,
                               earned_marks=12)
        assert response.status_code == 201
        data = response.json()
        assert data["is_completed"] is True
        assert data["earned_marks"] == 12.0

    def test_invalid_task_type_rejected(self, client, auth_headers):
        uc_id, _ = create_course_and_enroll(client, auth_headers)
        response = create_task(client, auth_headers, uc_id, task_type="invalid_type")
        assert response.status_code == 422

    def test_invalid_category_rejected(self, client, auth_headers):
        uc_id, _ = create_course_and_enroll(client, auth_headers)
        response = create_task(client, auth_headers, uc_id, category="INVALID")
        assert response.status_code == 422

    def test_nonexistent_enrollment_rejected(self, client, auth_headers):
        response = create_task(client, auth_headers,
                               "00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    def test_no_auth_rejected(self, client):
        response = client.post("/api/v1/tasks/", json={
            "user_course_id": "fake-id",
            "title": "No Auth",
            "task_type": "test",
            "weight": 10,
        })
        assert response.status_code == 401  # Missing auth header


# ===================================================================
# GET /api/v1/tasks/ - List Tasks
# ===================================================================

class TestListTasks:

    def test_empty_task_list(self, client, auth_headers):
        response = client.get("/api/v1/tasks/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_after_creating(self, client, auth_headers):
        uc_id, _ = create_course_and_enroll(client, auth_headers)
        create_task(client, auth_headers, uc_id, title="Task 1")
        create_task(client, auth_headers, uc_id, title="Task 2", weight=10)
        response = client.get("/api/v1/tasks/", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_tasks_include_course_info(self, client, auth_headers):
        uc_id, _ = create_course_and_enroll(client, auth_headers, code="CSC401")
        create_task(client, auth_headers, uc_id)
        response = client.get("/api/v1/tasks/", headers=auth_headers)
        tasks = response.json()
        assert tasks[0]["course_code"] == "CSC401"


# ===================================================================
# PATCH /api/v1/tasks/{id}/complete - Mark Complete
# ===================================================================

class TestCompleteTask:

    def test_mark_task_complete(self, client, auth_headers):
        uc_id, _ = create_course_and_enroll(client, auth_headers)
        task = create_task(client, auth_headers, uc_id).json()
        response = client.patch(
            f"/api/v1/tasks/{task['id']}/complete",
            json={"earned_marks": 13, "actual_effort": 120},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_completed"] is True
        assert data["earned_marks"] == 13.0
        assert data["actual_effort"] == 120

    def test_complete_without_marks(self, client, auth_headers):
        uc_id, _ = create_course_and_enroll(client, auth_headers)
        task = create_task(client, auth_headers, uc_id).json()
        response = client.patch(
            f"/api/v1/tasks/{task['id']}/complete",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["is_completed"] is True

    def test_complete_nonexistent_task(self, client, auth_headers):
        response = client.patch(
            "/api/v1/tasks/00000000-0000-0000-0000-000000000000/complete",
            json={"earned_marks": 10},
            headers=auth_headers,
        )
        assert response.status_code == 404


# ===================================================================
# GET /api/v1/tasks/stats - Task Statistics
# ===================================================================

class TestTaskStats:

    def test_empty_stats(self, client, auth_headers):
        response = client.get("/api/v1/tasks/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_tasks"] == 0
        assert data["completed_tasks"] == 0
        assert data["completion_rate"] == 0.0

    def test_stats_after_tasks(self, client, auth_headers):
        uc_id, _ = create_course_and_enroll(client, auth_headers)
        # Create 3 tasks, complete 2
        t1 = create_task(client, auth_headers, uc_id, title="T1", weight=10).json()
        t2 = create_task(client, auth_headers, uc_id, title="T2", weight=10).json()
        create_task(client, auth_headers, uc_id, title="T3", weight=10)

        client.patch(f"/api/v1/tasks/{t1['id']}/complete",
                     json={"earned_marks": 8}, headers=auth_headers)
        client.patch(f"/api/v1/tasks/{t2['id']}/complete",
                     json={"earned_marks": 7}, headers=auth_headers)

        response = client.get("/api/v1/tasks/stats", headers=auth_headers)
        data = response.json()
        assert data["total_tasks"] == 3
        assert data["completed_tasks"] == 2
        assert data["pending_tasks"] == 1
        assert data["completion_rate"] == pytest.approx(66.67, abs=0.01)


# ===================================================================
# DELETE /api/v1/tasks/{id} - Delete Task
# ===================================================================

class TestDeleteTask:

    def test_delete_task(self, client, auth_headers):
        uc_id, _ = create_course_and_enroll(client, auth_headers)
        task = create_task(client, auth_headers, uc_id).json()
        response = client.delete(f"/api/v1/tasks/{task['id']}", headers=auth_headers)
        assert response.status_code == 204

        # Verify deleted
        tasks = client.get("/api/v1/tasks/", headers=auth_headers)
        assert len(tasks.json()) == 0

    def test_delete_nonexistent_task(self, client, auth_headers):
        response = client.delete(
            "/api/v1/tasks/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert response.status_code == 404
