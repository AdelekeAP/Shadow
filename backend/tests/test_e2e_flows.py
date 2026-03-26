"""
End-to-End Integration Tests for Shadow Academic Achievement System

Tests complete user journeys that span multiple API endpoints, verifying
that the system works correctly as a whole rather than in isolation.

Each test class represents a critical user flow:
1. Registration -> Login -> Dashboard data
2. Course enrollment -> Task creation -> Completion -> CGPA update
3. Mood logging -> Trends aggregation
4. Library browsing and filtering
"""
import pytest
import uuid
import hashlib
from datetime import datetime, timedelta, timezone

# Re-use the integration test fixtures from tests/test_api/conftest.py
# by importing the same conftest setup (pytest automatically discovers it).
# The conftest at tests/test_api/ sets TESTING=true, DISABLE_ML_MODELS=true,
# creates an in-memory SQLite DB, and provides client/db_session/auth_headers.


# ===================================================================
# FLOW 1: Registration -> Login -> Dashboard Data
# ===================================================================

class TestRegistrationLoginDashboardFlow:
    """
    Tests the most fundamental user journey: a new student registers,
    logs in with those credentials, and then accesses their profile
    and dashboard data.
    """

    def test_full_registration_login_profile_flow(self, client):
        """Register a new user, login, and verify the profile endpoint works."""
        # Step 1: Register a new user
        registration_payload = {
            "email": "e2e_flow1@pau.edu.ng",
            "password": "FlowTest1!",
            "full_name": "Flow Test Student",
            "university_id": "PAU/2025/E2E",
            "entry_level": "400L",
            "target_cgpa": 4.5,
            "current_cgpa": 3.2,
        }
        reg_response = client.post("/api/v1/auth/register", json=registration_payload)
        assert reg_response.status_code == 201, f"Registration failed: {reg_response.text}"
        reg_data = reg_response.json()

        assert "access_token" in reg_data
        assert reg_data["token_type"] == "bearer"
        assert reg_data["user"]["email"] == "e2e_flow1@pau.edu.ng"
        assert reg_data["user"]["full_name"] == "Flow Test Student"
        assert reg_data["user"]["gpa_scale"] == 5.0
        assert reg_data["user"]["is_active"] is True

        reg_token = reg_data["access_token"]
        user_id = reg_data["user"]["id"]

        # Step 2: Login with the same credentials
        login_response = client.post("/api/v1/auth/login", json={
            "email": "e2e_flow1@pau.edu.ng",
            "password": "FlowTest1!",
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        login_data = login_response.json()

        assert "access_token" in login_data
        login_token = login_data["access_token"]
        assert login_data["user"]["id"] == user_id
        assert login_data["user"]["last_login"] is not None  # Updated on login

        # Step 3: Use the login token to access protected profile endpoint
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {login_token}"},
        )
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["email"] == "e2e_flow1@pau.edu.ng"
        assert me_data["full_name"] == "Flow Test Student"
        assert me_data["entry_level"] == "400L"
        assert "password" not in me_data
        assert "password_hash" not in me_data

    def test_registration_token_also_works(self, client):
        """The token returned at registration should also be valid for auth."""
        reg_response = client.post("/api/v1/auth/register", json={
            "email": "e2e_regtoken@pau.edu.ng",
            "password": "RegToken1!",
            "full_name": "Reg Token Test",
        })
        assert reg_response.status_code == 201
        token = reg_response.json()["access_token"]

        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "e2e_regtoken@pau.edu.ng"

    def test_register_login_access_cgpa_dashboard(self, client):
        """
        Full flow: register -> login -> access CGPA dashboard.
        A fresh user with no courses should still get a valid response.
        """
        # Register
        reg_response = client.post("/api/v1/auth/register", json={
            "email": "e2e_cgpa@pau.edu.ng",
            "password": "CgpaTest1!",
            "full_name": "CGPA Test Student",
            "target_cgpa": 4.0,
        })
        assert reg_response.status_code == 201
        token = reg_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Access CGPA dashboard (no courses yet)
        dashboard_response = client.get("/api/v1/cgpa/dashboard", headers=headers)
        assert dashboard_response.status_code == 200
        dashboard_data = dashboard_response.json()
        assert dashboard_data["success"] is True
        assert "data" in dashboard_data
        assert dashboard_data["data"]["total_courses"] == 0

    def test_register_login_access_task_stats(self, client):
        """
        Full flow: register -> login -> access task statistics.
        A fresh user with no tasks should get zeroed-out stats.
        """
        reg_response = client.post("/api/v1/auth/register", json={
            "email": "e2e_taskstats@pau.edu.ng",
            "password": "TaskStats1!",
            "full_name": "TaskStats Test",
        })
        assert reg_response.status_code == 201
        token = reg_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        stats_response = client.get("/api/v1/tasks/stats", headers=headers)
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["total_tasks"] == 0
        assert stats["completed_tasks"] == 0
        assert stats["pending_tasks"] == 0
        assert stats["completion_rate"] == 0.0

    def test_wrong_password_after_registration(self, client):
        """After registration, login with wrong password must fail."""
        client.post("/api/v1/auth/register", json={
            "email": "e2e_wrongpw@pau.edu.ng",
            "password": "CorrectPass1!",
            "full_name": "Wrong PW Test",
        })

        login_response = client.post("/api/v1/auth/login", json={
            "email": "e2e_wrongpw@pau.edu.ng",
            "password": "WrongPassword1!",
        })
        assert login_response.status_code == 401


# ===================================================================
# FLOW 2: Course Enrollment -> Task Creation -> Completion -> CGPA
# ===================================================================

class TestCourseTaskCompletionCGPAFlow:
    """
    Tests the core academic workflow: a student enrolls in a course,
    creates tasks (CA assessments), completes them with marks,
    and verifies that scores and CGPA data update accordingly.
    """

    def _setup_user_and_course(self, client, db_session):
        """
        Helper: register a user, create a course, and enroll.
        Returns (headers, user_id, course_id, enrollment_id).
        """
        # Register user
        reg = client.post("/api/v1/auth/register", json={
            "email": "e2e_course@pau.edu.ng",
            "password": "CourseTest1!",
            "full_name": "Course Flow Student",
            "entry_level": "400L",
            "target_cgpa": 4.5,
            "current_cgpa": 3.5,
        })
        assert reg.status_code == 201
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        user_id = reg.json()["user"]["id"]

        # Create a course via API
        course_resp = client.post("/api/v1/courses/", json={
            "code": "CSC499",
            "title": "Advanced Algorithms",
            "credits": 3,
            "level": "400",
            "status": "C",
            "department": "Computer Science",
        }, headers=headers)
        assert course_resp.status_code == 201, f"Course creation failed: {course_resp.text}"
        course_id = course_resp.json()["id"]

        # Enroll in the course
        enroll_resp = client.post(
            "/api/v1/courses/enroll",
            json={"course_id": course_id},
            headers=headers,
        )
        assert enroll_resp.status_code == 201, f"Enrollment failed: {enroll_resp.text}"
        enrollment_id = enroll_resp.json()["id"]

        return headers, user_id, course_id, enrollment_id

    def test_enroll_create_task_complete_verify_scores(self, client, db_session):
        """
        Full flow: enroll -> create CA task -> complete with marks ->
        verify the course CA score is updated.
        """
        headers, user_id, course_id, enrollment_id = self._setup_user_and_course(client, db_session)

        # Create a CA task (Test 1, worth 15 marks)
        task_resp = client.post("/api/v1/tasks/", json={
            "user_course_id": enrollment_id,
            "title": "Test 1 - Sorting Algorithms",
            "task_type": "test",
            "weight": 15,
            "category": "CA",
            "due_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        }, headers=headers)
        assert task_resp.status_code == 201, f"Task creation failed: {task_resp.text}"
        task_id = task_resp.json()["id"]
        assert task_resp.json()["is_completed"] is False
        assert task_resp.json()["category"] == "CA"

        # Complete the task with earned marks
        complete_resp = client.patch(
            f"/api/v1/tasks/{task_id}/complete",
            json={"earned_marks": 12, "actual_effort": 120},
            headers=headers,
        )
        assert complete_resp.status_code == 200, f"Task completion failed: {complete_resp.text}"
        complete_data = complete_resp.json()
        assert complete_data["is_completed"] is True
        assert complete_data["earned_marks"] == 12.0

        # Verify the enrollment now reflects the updated CA score
        enrollment_resp = client.get(
            f"/api/v1/courses/my-courses/{enrollment_id}",
            headers=headers,
        )
        assert enrollment_resp.status_code == 200
        enrollment_data = enrollment_resp.json()
        assert enrollment_data["ca_score"] == 12.0

    def test_multiple_tasks_accumulate_ca_score(self, client, db_session):
        """
        Create two CA tasks, complete both, and verify the CA scores accumulate.
        """
        headers, user_id, course_id, enrollment_id = self._setup_user_and_course(client, db_session)

        # Task 1: Assignment worth 10 marks, earned 8
        task1 = client.post("/api/v1/tasks/", json={
            "user_course_id": enrollment_id,
            "title": "Assignment 1",
            "task_type": "assignment",
            "weight": 10,
            "category": "CA",
        }, headers=headers)
        assert task1.status_code == 201
        task1_id = task1.json()["id"]

        client.patch(
            f"/api/v1/tasks/{task1_id}/complete",
            json={"earned_marks": 8},
            headers=headers,
        )

        # Task 2: Quiz worth 10 marks, earned 7
        task2 = client.post("/api/v1/tasks/", json={
            "user_course_id": enrollment_id,
            "title": "Quiz 1",
            "task_type": "quiz",
            "weight": 10,
            "category": "CA",
        }, headers=headers)
        assert task2.status_code == 201
        task2_id = task2.json()["id"]

        client.patch(
            f"/api/v1/tasks/{task2_id}/complete",
            json={"earned_marks": 7},
            headers=headers,
        )

        # Verify accumulated CA score = 8 + 7 = 15
        enrollment_resp = client.get(
            f"/api/v1/courses/my-courses/{enrollment_id}",
            headers=headers,
        )
        assert enrollment_resp.status_code == 200
        assert enrollment_resp.json()["ca_score"] == 15.0

    def test_task_stats_reflect_completion(self, client, db_session):
        """
        After creating and completing tasks, the stats endpoint should
        reflect the correct counts and completion rate.
        """
        headers, user_id, course_id, enrollment_id = self._setup_user_and_course(client, db_session)

        # Create 3 tasks
        task_ids = []
        for i in range(3):
            resp = client.post("/api/v1/tasks/", json={
                "user_course_id": enrollment_id,
                "title": f"Task {i+1}",
                "task_type": "assignment",
                "weight": 10,
                "category": "CA",
            }, headers=headers)
            assert resp.status_code == 201
            task_ids.append(resp.json()["id"])

        # Complete 2 of 3
        for tid in task_ids[:2]:
            client.patch(
                f"/api/v1/tasks/{tid}/complete",
                json={"earned_marks": 8},
                headers=headers,
            )

        # Check stats
        stats = client.get("/api/v1/tasks/stats", headers=headers)
        assert stats.status_code == 200
        stats_data = stats.json()
        assert stats_data["total_tasks"] == 3
        assert stats_data["completed_tasks"] == 2
        assert stats_data["pending_tasks"] == 1
        # Completion rate should be 2/3 * 100 = 66.67
        assert 66.0 <= stats_data["completion_rate"] <= 67.0

    def test_cgpa_dashboard_reflects_enrolled_course(self, client, db_session):
        """
        After enrolling in a course, the CGPA dashboard should reflect
        the enrollment and provide predictions.
        """
        headers, user_id, course_id, enrollment_id = self._setup_user_and_course(client, db_session)

        # Create and complete a task so there is data to work with
        task_resp = client.post("/api/v1/tasks/", json={
            "user_course_id": enrollment_id,
            "title": "Final Test",
            "task_type": "test",
            "weight": 15,
            "category": "CA",
            "is_completed": True,
            "earned_marks": 12,
        }, headers=headers)
        assert task_resp.status_code == 201

        # Check CGPA dashboard
        dashboard_resp = client.get("/api/v1/cgpa/dashboard", headers=headers)
        assert dashboard_resp.status_code == 200
        dashboard = dashboard_resp.json()
        assert dashboard["success"] is True
        assert dashboard["data"]["total_courses"] >= 1

    def test_low_score_triggers_intervention_suggestion(self, client, db_session):
        """
        When a task is completed with a score below 60%, the response
        should include a SmartStudy intervention suggestion.
        """
        headers, user_id, course_id, enrollment_id = self._setup_user_and_course(client, db_session)

        # Create a task worth 15 marks
        task_resp = client.post("/api/v1/tasks/", json={
            "user_course_id": enrollment_id,
            "title": "Hard Test",
            "task_type": "test",
            "weight": 15,
            "category": "CA",
        }, headers=headers)
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        # Complete with only 5/15 marks (33%) -- below 60%
        complete_resp = client.patch(
            f"/api/v1/tasks/{task_id}/complete",
            json={"earned_marks": 5},
            headers=headers,
        )
        assert complete_resp.status_code == 200
        complete_data = complete_resp.json()

        # Should have intervention suggestion
        assert "intervention" in complete_data
        assert complete_data["intervention"]["suggested"] is True
        assert complete_data["intervention"]["reason"] == "low_score"
        assert complete_data["intervention"]["score_percentage"] < 60

    def test_ca_weight_limit_enforcement(self, client, db_session):
        """
        Total CA weight for a course cannot exceed 30 marks
        (5 marks reserved for participation).
        """
        headers, user_id, course_id, enrollment_id = self._setup_user_and_course(client, db_session)

        # Create a 25-mark CA task (ok)
        resp1 = client.post("/api/v1/tasks/", json={
            "user_course_id": enrollment_id,
            "title": "Big Test",
            "task_type": "test",
            "weight": 25,
            "category": "CA",
        }, headers=headers)
        assert resp1.status_code == 201

        # Try to create another 10-mark CA task (would total 35, exceeding 30)
        resp2 = client.post("/api/v1/tasks/", json={
            "user_course_id": enrollment_id,
            "title": "Another Test",
            "task_type": "test",
            "weight": 10,
            "category": "CA",
        }, headers=headers)
        assert resp2.status_code == 400
        assert "CA" in resp2.json()["detail"]


# ===================================================================
# FLOW 3: Mood Logging -> History -> Trends
# ===================================================================

class TestMoodLoggingTrendsFlow:
    """
    Tests the wellness monitoring flow: a student logs multiple moods
    over time, then checks history and trend aggregations.
    """

    def _get_auth(self, client):
        """Helper: register and return auth headers."""
        reg = client.post("/api/v1/auth/register", json={
            "email": f"e2e_mood_{uuid.uuid4().hex[:8]}@pau.edu.ng",
            "password": "MoodTest1!",
            "full_name": "Mood Flow Student",
        })
        assert reg.status_code == 201
        token = reg.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_log_single_mood_and_retrieve(self, client):
        """Log a single mood and verify it appears in history."""
        headers = self._get_auth(client)

        # Log a mood
        log_resp = client.post("/api/v1/mood/log-mood", json={
            "mood_type": "focused",
            "energy_level": 4,
            "note": "Feeling productive today",
        }, headers=headers)
        assert log_resp.status_code == 200, f"Mood log failed: {log_resp.text}"
        log_data = log_resp.json()
        assert log_data["success"] is True
        assert log_data["mood_log"]["mood_type"] == "focused"
        assert log_data["mood_log"]["energy_level"] == 4

        # Retrieve mood history
        history_resp = client.get("/api/v1/mood/moods", headers=headers)
        assert history_resp.status_code == 200
        history = history_resp.json()
        assert history["success"] is True
        assert history["total"] == 1
        assert history["moods"][0]["mood_type"] == "focused"

    def test_multiple_moods_and_trends(self, client):
        """
        Log several moods of different types and verify the trends
        endpoint returns correct aggregations.
        """
        headers = self._get_auth(client)

        # Log multiple moods
        moods_to_log = [
            {"mood_type": "focused", "energy_level": 4},
            {"mood_type": "focused", "energy_level": 5},
            {"mood_type": "stressed", "energy_level": 2},
            {"mood_type": "motivated", "energy_level": 4},
            {"mood_type": "tired", "energy_level": 1},
        ]

        for mood in moods_to_log:
            resp = client.post("/api/v1/mood/log-mood", json=mood, headers=headers)
            assert resp.status_code == 200, f"Mood log failed: {resp.text}"

        # Check history count
        history_resp = client.get("/api/v1/mood/moods?limit=50", headers=headers)
        assert history_resp.status_code == 200
        assert history_resp.json()["total"] == 5

        # Check trends
        trends_resp = client.get("/api/v1/mood/mood-trends?days=7", headers=headers)
        assert trends_resp.status_code == 200
        trends = trends_resp.json()
        assert trends["success"] is True
        assert trends["trends"]["total_logs"] == 5

        # Average energy: (4+5+2+4+1) / 5 = 3.2
        assert trends["trends"]["avg_energy"] == 3.2

        # Most common mood should be "focused" (appears 2 times)
        assert trends["trends"]["most_common_mood"] == "focused"

        # Mood distribution
        dist = trends["trends"]["mood_distribution"]
        assert dist["focused"] == 2
        assert dist["stressed"] == 1
        assert dist["motivated"] == 1
        assert dist["tired"] == 1

    def test_mood_with_invalid_type_rejected(self, client):
        """Invalid mood types should be rejected."""
        headers = self._get_auth(client)

        resp = client.post("/api/v1/mood/log-mood", json={
            "mood_type": "ecstatic",  # Not in valid list
            "energy_level": 5,
        }, headers=headers)
        assert resp.status_code == 400

    def test_energy_level_boundaries(self, client):
        """Energy level must be between 1 and 5."""
        headers = self._get_auth(client)

        # Too low
        resp_low = client.post("/api/v1/mood/log-mood", json={
            "mood_type": "calm",
            "energy_level": 0,
        }, headers=headers)
        assert resp_low.status_code == 422

        # Too high
        resp_high = client.post("/api/v1/mood/log-mood", json={
            "mood_type": "calm",
            "energy_level": 6,
        }, headers=headers)
        assert resp_high.status_code == 422

    def test_recent_energy_endpoint(self, client):
        """
        After logging moods, the recent-energy endpoint should return
        the correct average energy.
        """
        headers = self._get_auth(client)

        for energy in [3, 4, 5]:
            client.post("/api/v1/mood/log-mood", json={
                "mood_type": "focused",
                "energy_level": energy,
            }, headers=headers)

        energy_resp = client.get("/api/v1/mood/recent-energy?limit=5", headers=headers)
        assert energy_resp.status_code == 200
        energy_data = energy_resp.json()
        assert energy_data["success"] is True
        assert energy_data["avg_energy"] == 4.0  # (3+4+5)/3
        assert len(energy_data["recent_moods"]) == 3

    def test_empty_trends_for_new_user(self, client):
        """A new user with no moods should get empty trends without errors."""
        headers = self._get_auth(client)

        trends_resp = client.get("/api/v1/mood/mood-trends?days=7", headers=headers)
        assert trends_resp.status_code == 200
        trends = trends_resp.json()
        assert trends["success"] is True
        assert trends["trends"]["total_logs"] == 0
        assert trends["trends"]["avg_energy"] == 0
        assert trends["trends"]["most_common_mood"] is None


# ===================================================================
# FLOW 4: Library Browsing and Filtering
# ===================================================================

class TestLibraryBrowsingFlow:
    """
    Tests the learning library system: browsing documents, filtering
    by course, and accessing document metadata. Documents are created
    directly in the DB since the upload flow involves file processing.
    """

    def _setup_library(self, client, db_session):
        """
        Helper: register a user, create a course, and insert library
        documents directly into the DB. Returns (headers, course_id, doc_ids).
        """
        # Register user
        reg = client.post("/api/v1/auth/register", json={
            "email": f"e2e_lib_{uuid.uuid4().hex[:8]}@pau.edu.ng",
            "password": "LibTest1!",
            "full_name": "Library Flow Student",
        })
        assert reg.status_code == 201
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        user_id = reg.json()["user"]["id"]

        # Create a course
        course_resp = client.post("/api/v1/courses/", json={
            "code": f"LIB{uuid.uuid4().hex[:4].upper()}",
            "title": "Data Structures",
            "credits": 3,
        }, headers=headers)
        assert course_resp.status_code == 201
        course_id = course_resp.json()["id"]

        # Insert documents directly into DB
        from app.models.library import LibraryDocument
        doc_ids = []
        docs_data = [
            {
                "topic": "Binary Search Trees",
                "file_name": "BST_lecture.pdf",
                "week_number": 5,
                "helpful_votes": 10,
                "view_count": 50,
            },
            {
                "topic": "Hash Tables",
                "file_name": "hash_tables_slides.pdf",
                "week_number": 7,
                "helpful_votes": 5,
                "view_count": 30,
            },
            {
                "topic": "Graph Algorithms",
                "file_name": "graphs_notes.pdf",
                "week_number": 10,
                "helpful_votes": 15,
                "view_count": 80,
            },
        ]

        for dd in docs_data:
            doc = LibraryDocument(
                course_id=course_id,
                topic=dd["topic"],
                file_name=dd["file_name"],
                file_path=f"/tmp/fake/{dd['file_name']}",
                file_type="pdf",
                file_size=2048,
                content_hash=hashlib.sha256(dd["file_name"].encode()).hexdigest(),
                uploaded_by=user_id,
                is_public=True,
                helpful_votes=dd["helpful_votes"],
                view_count=dd["view_count"],
                download_count=0,
                week_number=dd["week_number"],
            )
            db_session.add(doc)

        db_session.commit()

        # Retrieve the IDs
        docs = db_session.query(LibraryDocument).filter(
            LibraryDocument.course_id == course_id
        ).all()
        doc_ids = [str(d.id) for d in docs]

        return headers, course_id, doc_ids, user_id

    def test_browse_all_library_documents(self, client, db_session):
        """Browse the library without filters and verify documents appear."""
        headers, course_id, doc_ids, _ = self._setup_library(client, db_session)

        browse_resp = client.get("/api/v1/library/browse", headers=headers)
        assert browse_resp.status_code == 200
        browse_data = browse_resp.json()
        assert browse_data["total"] >= 3
        assert len(browse_data["documents"]) >= 3

    def test_browse_filter_by_course(self, client, db_session):
        """Filter library documents by course_id."""
        headers, course_id, doc_ids, _ = self._setup_library(client, db_session)

        browse_resp = client.get(
            f"/api/v1/library/browse?course_id={course_id}",
            headers=headers,
        )
        assert browse_resp.status_code == 200
        browse_data = browse_resp.json()
        assert browse_data["total"] == 3
        # All documents should belong to this course
        for doc in browse_data["documents"]:
            assert doc["course_id"] == course_id

    def test_browse_filter_by_week(self, client, db_session):
        """Filter library documents by week_number."""
        headers, course_id, doc_ids, _ = self._setup_library(client, db_session)

        browse_resp = client.get(
            f"/api/v1/library/browse?course_id={course_id}&week_number=5",
            headers=headers,
        )
        assert browse_resp.status_code == 200
        browse_data = browse_resp.json()
        assert browse_data["total"] == 1
        assert browse_data["documents"][0]["topic"] == "Binary Search Trees"

    def test_browse_search_by_topic(self, client, db_session):
        """Search library documents by topic keyword."""
        headers, course_id, doc_ids, _ = self._setup_library(client, db_session)

        browse_resp = client.get(
            f"/api/v1/library/browse?search=Graph",
            headers=headers,
        )
        assert browse_resp.status_code == 200
        browse_data = browse_resp.json()
        assert browse_data["total"] >= 1
        topics = [d["topic"] for d in browse_data["documents"]]
        assert any("Graph" in t for t in topics)

    def test_browse_sorted_by_helpfulness(self, client, db_session):
        """Documents should be sorted by helpful_votes descending."""
        headers, course_id, doc_ids, _ = self._setup_library(client, db_session)

        browse_resp = client.get(
            f"/api/v1/library/browse?course_id={course_id}",
            headers=headers,
        )
        assert browse_resp.status_code == 200
        docs = browse_resp.json()["documents"]
        # Verify descending order by helpful_votes
        votes = [d["helpful_votes"] for d in docs]
        assert votes == sorted(votes, reverse=True)

    def test_browse_pagination(self, client, db_session):
        """Test that pagination works with limit and offset."""
        headers, course_id, doc_ids, _ = self._setup_library(client, db_session)

        # Get first 2
        resp1 = client.get(
            f"/api/v1/library/browse?course_id={course_id}&limit=2&offset=0",
            headers=headers,
        )
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert len(data1["documents"]) == 2
        assert data1["total"] == 3
        assert data1["has_more"] is True

        # Get next page
        resp2 = client.get(
            f"/api/v1/library/browse?course_id={course_id}&limit=2&offset=2",
            headers=headers,
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert len(data2["documents"]) == 1
        assert data2["has_more"] is False

    def test_get_single_document(self, client, db_session):
        """Retrieve a single library document by its ID."""
        headers, course_id, doc_ids, _ = self._setup_library(client, db_session)

        doc_id = doc_ids[0]
        doc_resp = client.get(
            f"/api/v1/library/documents/{doc_id}",
            headers=headers,
        )
        assert doc_resp.status_code == 200
        doc_data = doc_resp.json()
        assert doc_data["id"] == doc_id
        assert doc_data["is_public"] is True

    def test_get_nonexistent_document_returns_404(self, client, db_session):
        """Requesting a non-existent document should return 404."""
        headers, _, _, _ = self._setup_library(client, db_session)

        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/library/documents/{fake_id}",
            headers=headers,
        )
        assert resp.status_code == 404

    def test_library_stats_endpoint(self, client, db_session):
        """The library stats endpoint should return aggregate data."""
        headers, course_id, doc_ids, _ = self._setup_library(client, db_session)

        stats_resp = client.get("/api/v1/library/stats", headers=headers)
        assert stats_resp.status_code == 200
        stats = stats_resp.json()
        assert stats["total_documents"] >= 3
        assert stats["total_contributors"] >= 1

    def test_my_contributions(self, client, db_session):
        """A user who uploaded documents should see them in contributions."""
        headers, course_id, doc_ids, user_id = self._setup_library(client, db_session)

        contrib_resp = client.get("/api/v1/library/my-contributions", headers=headers)
        assert contrib_resp.status_code == 200
        contrib = contrib_resp.json()
        assert contrib["total_documents"] == 3
        assert contrib["total_views"] == 50 + 30 + 80  # Sum of view counts
        assert len(contrib["documents"]) == 3


# ===================================================================
# FLOW 5: Cross-cutting - Complete student session
# ===================================================================

class TestFullStudentSessionFlow:
    """
    A comprehensive test simulating a full student session:
    register, create a course, enroll, add tasks, complete some,
    log moods, and check dashboard data -- all in one flow.
    """

    def test_complete_student_session(self, client, db_session):
        """
        Simulate a complete student session touching all major endpoints.
        """
        # 1. Register
        reg = client.post("/api/v1/auth/register", json={
            "email": "e2e_full@pau.edu.ng",
            "password": "FullFlow1!",
            "full_name": "Full Flow Student",
            "entry_level": "400L",
            "target_cgpa": 4.5,
            "current_cgpa": 3.8,
        })
        assert reg.status_code == 201
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Create course
        course = client.post("/api/v1/courses/", json={
            "code": "CSC410",
            "title": "Software Engineering",
            "credits": 3,
        }, headers=headers)
        assert course.status_code == 201
        course_id = course.json()["id"]

        # 3. Enroll
        enroll = client.post("/api/v1/courses/enroll", json={
            "course_id": course_id,
        }, headers=headers)
        assert enroll.status_code == 201
        enrollment_id = enroll.json()["id"]

        # 4. Verify my-courses includes the enrollment
        my_courses = client.get("/api/v1/courses/my-courses/", headers=headers)
        assert my_courses.status_code == 200
        enrolled_ids = [c["id"] for c in my_courses.json()]
        assert enrollment_id in enrolled_ids

        # 5. Create tasks
        task1 = client.post("/api/v1/tasks/", json={
            "user_course_id": enrollment_id,
            "title": "Lab Report 1",
            "task_type": "assignment",
            "weight": 10,
            "category": "CA",
            "due_date": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
        }, headers=headers)
        assert task1.status_code == 201
        task1_id = task1.json()["id"]

        task2 = client.post("/api/v1/tasks/", json={
            "user_course_id": enrollment_id,
            "title": "Mid-term Test",
            "task_type": "test",
            "weight": 15,
            "category": "CA",
            "due_date": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
        }, headers=headers)
        assert task2.status_code == 201
        task2_id = task2.json()["id"]

        # 6. List tasks -- should have 2
        tasks = client.get("/api/v1/tasks/", headers=headers)
        assert tasks.status_code == 200
        assert len(tasks.json()) == 2

        # 7. Complete task1
        complete1 = client.patch(
            f"/api/v1/tasks/{task1_id}/complete",
            json={"earned_marks": 8, "actual_effort": 60},
            headers=headers,
        )
        assert complete1.status_code == 200

        # 8. Check task stats
        stats = client.get("/api/v1/tasks/stats", headers=headers)
        assert stats.status_code == 200
        stats_data = stats.json()
        assert stats_data["total_tasks"] == 2
        assert stats_data["completed_tasks"] == 1
        assert stats_data["pending_tasks"] == 1

        # 9. Log some moods
        client.post("/api/v1/mood/log-mood", json={
            "mood_type": "focused",
            "energy_level": 4,
        }, headers=headers)

        client.post("/api/v1/mood/log-mood", json={
            "mood_type": "stressed",
            "energy_level": 2,
            "note": "Worried about mid-term",
        }, headers=headers)

        # 10. Check mood history
        history = client.get("/api/v1/mood/moods", headers=headers)
        assert history.status_code == 200
        assert history.json()["total"] == 2

        # 11. Check CGPA dashboard
        dashboard = client.get("/api/v1/cgpa/dashboard", headers=headers)
        assert dashboard.status_code == 200
        assert dashboard.json()["success"] is True
        assert dashboard.json()["data"]["total_courses"] == 1

        # 12. Update preferences
        prefs = client.patch("/api/v1/auth/me/preferences", json={
            "learning_style": "visual",
            "target_cgpa": 4.8,
        }, headers=headers)
        assert prefs.status_code == 200
        assert prefs.json()["learning_style"] == "visual"
        assert prefs.json()["target_cgpa"] == 4.8

        # 13. Verify profile reflects updated preferences
        me = client.get("/api/v1/auth/me", headers=headers)
        assert me.status_code == 200
        assert me.json()["target_cgpa"] == 4.8


# ===================================================================
# FLOW 6: Notification System — Preferences, CRUD, Mark as Read
# ===================================================================

class TestNotificationSystemFlow:
    """
    Tests the notification lifecycle: preferences, retrieval,
    mark-as-read, and dismiss operations.
    """

    def _get_auth(self, client):
        """Helper: register and return auth headers."""
        reg = client.post("/api/v1/auth/register", json={
            "email": f"e2e_notif_{uuid.uuid4().hex[:8]}@pau.edu.ng",
            "password": "NotifTest1!",
            "full_name": "Notification Flow Student",
        })
        assert reg.status_code == 201
        return {"Authorization": f"Bearer {reg.json()['access_token']}"}

    def test_new_user_has_empty_notifications(self, client):
        """A fresh user should have zero notifications."""
        headers = self._get_auth(client)

        resp = client.get("/api/v1/notifications", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_count"] == 0
        assert data["unread_count"] == 0
        assert data["notifications"] == []

    def test_notification_count_endpoint(self, client):
        """Count endpoint should match list totals."""
        headers = self._get_auth(client)

        count_resp = client.get("/api/v1/notifications/count", headers=headers)
        assert count_resp.status_code == 200
        count_data = count_resp.json()
        assert count_data["unread_count"] == 0
        assert count_data["total_count"] == 0

    def test_preferences_get_and_update(self, client):
        """Get default preferences, update them, verify persistence."""
        headers = self._get_auth(client)

        # Get defaults
        prefs_resp = client.get("/api/v1/notifications/preferences/me", headers=headers)
        assert prefs_resp.status_code == 200
        prefs = prefs_resp.json()
        assert prefs["task_reminders"] is True  # default on
        assert prefs["smart_study"] is True

        # Update: disable smart_study and set quiet hours
        update_resp = client.put("/api/v1/notifications/preferences/me", json={
            "smart_study": False,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "07:00",
        }, headers=headers)
        assert update_resp.status_code == 200
        updated = update_resp.json()
        assert updated["smart_study"] is False
        assert updated["quiet_hours_start"] == "22:00"
        assert updated["quiet_hours_end"] == "07:00"

        # Verify persistence
        prefs2 = client.get("/api/v1/notifications/preferences/me", headers=headers)
        assert prefs2.json()["smart_study"] is False
        assert prefs2.json()["quiet_hours_start"] == "22:00"

    def test_mark_all_as_read(self, client):
        """Mark-all-read should succeed even with no notifications."""
        headers = self._get_auth(client)

        resp = client.post("/api/v1/notifications/read-all", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_scheduled_reminders_list(self, client):
        """A fresh user should have empty scheduled reminders."""
        headers = self._get_auth(client)

        resp = client.get("/api/v1/notifications/reminders", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_count"] == 0
        assert data["reminders"] == []


# ===================================================================
# FLOW 7: Semester Management — Create, List, Activate
# ===================================================================

class TestSemesterManagementFlow:
    """
    Tests the academic year lifecycle: create academic year,
    list semesters, activate specific semester, and assign courses.
    """

    def _get_auth(self, client):
        """Helper: register and return auth headers."""
        reg = client.post("/api/v1/auth/register", json={
            "email": f"e2e_sem_{uuid.uuid4().hex[:8]}@pau.edu.ng",
            "password": "SemTest1!",
            "full_name": "Semester Flow Student",
        })
        assert reg.status_code == 201
        return {"Authorization": f"Bearer {reg.json()['access_token']}"}

    def test_create_academic_year_and_list_semesters(self, client):
        """Create academic year → 2 semesters auto-generated → list them."""
        headers = self._get_auth(client)

        # Create academic year
        create_resp = client.post("/api/v1/semesters/academic-year", json={
            "academic_year": "2025/2026",
        }, headers=headers)
        assert create_resp.status_code == 200, f"Create failed: {create_resp.text}"
        data = create_resp.json()
        assert data["success"] is True
        assert data["academic_year"] == "2025/2026"
        assert len(data["semesters"]) == 2

        first_sem = data["semesters"][0]
        second_sem = data["semesters"][1]
        assert "First Semester" in first_sem["name"]
        assert "Second Semester" in second_sem["name"]

        # List semesters
        list_resp = client.get("/api/v1/semesters/", headers=headers)
        assert list_resp.status_code == 200
        semesters = list_resp.json()
        assert len(semesters) == 2

    def test_activate_semester(self, client):
        """Create year, then manually activate a specific semester."""
        headers = self._get_auth(client)

        # Create year
        create_resp = client.post("/api/v1/semesters/academic-year", json={
            "academic_year": "2024/2025",
        }, headers=headers)
        assert create_resp.status_code == 200
        semesters = create_resp.json()["semesters"]

        # Activate the second semester specifically
        second_id = semesters[1]["id"]
        activate_resp = client.patch(
            f"/api/v1/semesters/{second_id}/activate",
            headers=headers,
        )
        assert activate_resp.status_code == 200
        assert activate_resp.json()["success"] is True
        assert activate_resp.json()["semester"]["is_active"] is True

        # Verify via active endpoint
        active_resp = client.get("/api/v1/semesters/active", headers=headers)
        assert active_resp.status_code == 200
        active_data = active_resp.json()
        assert active_data["semester"]["id"] == second_id
        assert active_data["semester"]["is_active"] is True

    def test_duplicate_academic_year_rejected(self, client):
        """Creating the same academic year twice should fail."""
        headers = self._get_auth(client)

        # First creation succeeds
        resp1 = client.post("/api/v1/semesters/academic-year", json={
            "academic_year": "2023/2024",
        }, headers=headers)
        assert resp1.status_code == 200

        # Second creation fails
        resp2 = client.post("/api/v1/semesters/academic-year", json={
            "academic_year": "2023/2024",
        }, headers=headers)
        assert resp2.status_code == 400

    def test_invalid_year_format_rejected(self, client):
        """Invalid academic year format should be rejected."""
        headers = self._get_auth(client)

        resp = client.post("/api/v1/semesters/academic-year", json={
            "academic_year": "2025-2026",  # Wrong format
        }, headers=headers)
        assert resp.status_code == 422

    def test_no_active_semester_for_new_user(self, client):
        """A new user with no semesters should get null active semester."""
        headers = self._get_auth(client)

        resp = client.get("/api/v1/semesters/active", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["semester"] is None


# ===================================================================
# FLOW 8: Cross-System — Task Completion → CGPA Cache Invalidation
# ===================================================================

class TestCrossSystemIntegrationFlow:
    """
    Tests that operations in one subsystem correctly trigger
    updates in related subsystems.
    """

    def _setup_full_env(self, client, db_session):
        """
        Helper: register user, create academic year, create course,
        enroll with semester assignment. Returns everything needed.
        """
        reg = client.post("/api/v1/auth/register", json={
            "email": f"e2e_cross_{uuid.uuid4().hex[:8]}@pau.edu.ng",
            "password": "CrossTest1!",
            "full_name": "Cross System Student",
            "target_cgpa": 4.5,
        })
        assert reg.status_code == 201
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create course
        course = client.post("/api/v1/courses/", json={
            "code": f"CSC{uuid.uuid4().hex[:3].upper()}",
            "title": "Test Course",
            "credits": 3,
        }, headers=headers)
        assert course.status_code == 201
        course_id = course.json()["id"]

        # Enroll
        enroll = client.post("/api/v1/courses/enroll", json={
            "course_id": course_id,
        }, headers=headers)
        assert enroll.status_code == 201
        enrollment_id = enroll.json()["id"]

        return headers, course_id, enrollment_id

    def test_task_completion_updates_cgpa_data(self, client, db_session):
        """
        Complete a task → verify CGPA dashboard reflects updated scores.
        Tests the Task → CGPA integration pipeline.
        """
        headers, course_id, enrollment_id = self._setup_full_env(client, db_session)

        # Get initial CGPA (no completed tasks)
        cgpa_before = client.get("/api/v1/cgpa/dashboard", headers=headers)
        assert cgpa_before.status_code == 200

        # Create and complete a CA task
        task = client.post("/api/v1/tasks/", json={
            "user_course_id": enrollment_id,
            "title": "Integration Test CA",
            "task_type": "test",
            "weight": 15,
            "category": "CA",
        }, headers=headers)
        assert task.status_code == 201
        task_id = task.json()["id"]

        complete = client.patch(
            f"/api/v1/tasks/{task_id}/complete",
            json={"earned_marks": 12},
            headers=headers,
        )
        assert complete.status_code == 200

        # CGPA should now reflect the score
        cgpa_after = client.get("/api/v1/cgpa/dashboard", headers=headers)
        assert cgpa_after.status_code == 200
        assert cgpa_after.json()["data"]["total_courses"] >= 1

    def test_mood_then_recommendations(self, client, db_session):
        """
        Log mood → get recommendations. Recommendations should
        return without errors regardless of mood state.
        """
        headers, course_id, enrollment_id = self._setup_full_env(client, db_session)

        # Create a pending task first
        client.post("/api/v1/tasks/", json={
            "user_course_id": enrollment_id,
            "title": "Upcoming Assignment",
            "task_type": "assignment",
            "weight": 10,
            "category": "CA",
            "due_date": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        }, headers=headers)

        # Log a low-energy mood
        mood_resp = client.post("/api/v1/mood/log-mood", json={
            "mood_type": "tired",
            "energy_level": 1,
            "note": "Very exhausted today",
        }, headers=headers)
        assert mood_resp.status_code == 200

        # Get recommendations (should work even with low energy)
        recs = client.get("/api/v1/recommendations/priority-tasks", headers=headers)
        assert recs.status_code == 200
        recs_data = recs.json()
        assert "recommendations" in recs_data

    def test_enrollment_update_scores_recalculates_grades(self, client, db_session):
        """
        Update CA/exam scores on enrollment → verify grades recalculated.
        Tests the Courses → CGPA grade recalculation pipeline.
        """
        headers, course_id, enrollment_id = self._setup_full_env(client, db_session)

        # Update CA score directly on enrollment
        update_resp = client.patch(
            f"/api/v1/courses/my-courses/{enrollment_id}",
            json={"ca_score": 25.0, "participation_score": 4.0},
            headers=headers,
        )
        assert update_resp.status_code == 200
        updated = update_resp.json()
        assert updated["ca_score"] == 25.0
        assert updated["participation_score"] == 4.0

    def test_task_pagination_works(self, client, db_session):
        """
        Create multiple tasks and verify pagination params work.
        """
        headers, course_id, enrollment_id = self._setup_full_env(client, db_session)

        # Create 5 tasks
        for i in range(5):
            resp = client.post("/api/v1/tasks/", json={
                "user_course_id": enrollment_id,
                "title": f"Paginated Task {i+1}",
                "task_type": "assignment",
                "weight": 5,
                "category": "CA",
            }, headers=headers)
            assert resp.status_code == 201

        # Get first 2
        page1 = client.get("/api/v1/tasks/?limit=2&offset=0", headers=headers)
        assert page1.status_code == 200
        assert len(page1.json()) == 2

        # Get next 2
        page2 = client.get("/api/v1/tasks/?limit=2&offset=2", headers=headers)
        assert page2.status_code == 200
        assert len(page2.json()) == 2

        # Get last page
        page3 = client.get("/api/v1/tasks/?limit=2&offset=4", headers=headers)
        assert page3.status_code == 200
        assert len(page3.json()) == 1

        # Get all
        all_tasks = client.get("/api/v1/tasks/?limit=50", headers=headers)
        assert all_tasks.status_code == 200
        assert len(all_tasks.json()) == 5

    def test_health_check_endpoints(self, client):
        """Both health check endpoints should respond."""
        # Basic health (no auth required)
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

        # Detailed health (requires auth)
        reg = client.post("/api/v1/auth/register", json={
            "email": f"e2e_health_{uuid.uuid4().hex[:8]}@pau.edu.ng",
            "password": "HealthTest1!",
            "full_name": "Health Check User",
            "target_cgpa": 4.0,
        })
        headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
        resp_detailed = client.get("/health/detailed", headers=headers)
        assert resp_detailed.status_code == 200
        data = resp_detailed.json()
        assert "services" in data
        assert "database" in data["services"]
        assert "redis" in data["services"]
        assert "clamav" in data["services"]
