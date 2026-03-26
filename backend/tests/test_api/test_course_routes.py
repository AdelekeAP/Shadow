"""
Integration tests for Course API routes
backend/app/routes/courses.py

Tests course creation, enrollment, listing, and the full enrollment lifecycle.
"""
import pytest


# ===================================================================
# Helper to create a course
# ===================================================================

def create_course(client, code="CSC401", title="Software Engineering", credits=3, headers=None):
    """Helper to create a course via API"""
    return client.post("/api/v1/courses/", json={
        "code": code,
        "title": title,
        "credits": credits,
        "level": "400",
        "status": "C",
        "department": "Computer Science",
    }, headers=headers)


# ===================================================================
# POST /api/v1/courses/ - Create Course
# ===================================================================

class TestCreateCourse:

    def test_create_course_success(self, client, auth_headers):
        response = create_course(client, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "CSC401"
        assert data["title"] == "Software Engineering"
        assert data["credits"] == 3
        assert data["is_approved"] is True

    def test_duplicate_course_code_rejected(self, client, auth_headers):
        create_course(client, code="CSC401", headers=auth_headers)
        response = create_course(client, code="CSC401", title="Different Title", headers=auth_headers)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_course_with_different_codes(self, client, auth_headers):
        r1 = create_course(client, code="CSC401", title="Software Engineering", headers=auth_headers)
        r2 = create_course(client, code="CSC403", title="Artificial Intelligence", headers=auth_headers)
        assert r1.status_code == 201
        assert r2.status_code == 201

    def test_invalid_credits_rejected(self, client, auth_headers):
        response = client.post("/api/v1/courses/", json={
            "code": "CSC999",
            "title": "Bad Course",
            "credits": 0,  # Must be >= 1
        }, headers=auth_headers)
        assert response.status_code == 422

    def test_credits_max_6(self, client, auth_headers):
        response = client.post("/api/v1/courses/", json={
            "code": "CSC999",
            "title": "Bad Course",
            "credits": 7,  # Must be <= 6
        }, headers=auth_headers)
        assert response.status_code == 422

    def test_invalid_status_rejected(self, client, auth_headers):
        response = client.post("/api/v1/courses/", json={
            "code": "CSC999",
            "title": "Bad Status",
            "credits": 3,
            "status": "X",  # Must be C, E, or R
        }, headers=auth_headers)
        assert response.status_code == 422


# ===================================================================
# GET /api/v1/courses/ - List Courses
# ===================================================================

class TestListCourses:

    def test_list_empty_courses(self, client, auth_headers):
        response = client.get("/api/v1/courses/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_after_creating(self, client, auth_headers):
        create_course(client, code="CSC401", title="Software Engineering", headers=auth_headers)
        create_course(client, code="CSC403", title="Artificial Intelligence", headers=auth_headers)
        response = client.get("/api/v1/courses/", headers=auth_headers)
        assert response.status_code == 200
        courses = response.json()
        assert len(courses) == 2

    def test_list_courses_sorted_by_code(self, client, auth_headers):
        create_course(client, code="MTH401", title="Maths", headers=auth_headers)
        create_course(client, code="CSC401", title="SE", headers=auth_headers)
        response = client.get("/api/v1/courses/", headers=auth_headers)
        codes = [c["code"] for c in response.json()]
        assert codes == sorted(codes)


# ===================================================================
# GET /api/v1/courses/{id} - Get Single Course
# ===================================================================

class TestGetCourse:

    def test_get_existing_course(self, client, auth_headers):
        create_resp = create_course(client, headers=auth_headers)
        course_id = create_resp.json()["id"]
        response = client.get(f"/api/v1/courses/{course_id}")
        assert response.status_code == 200
        assert response.json()["code"] == "CSC401"

    def test_get_nonexistent_course(self, client):
        response = client.get("/api/v1/courses/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    def test_get_invalid_uuid(self, client):
        response = client.get("/api/v1/courses/not-a-uuid")
        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]


# ===================================================================
# POST /api/v1/courses/enroll - Enroll in Course
# ===================================================================

class TestEnrollInCourse:

    def test_successful_enrollment(self, client, auth_headers):
        course = create_course(client, headers=auth_headers).json()
        response = client.post("/api/v1/courses/enroll", json={
            "course_id": course["id"],
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["course_id"] == course["id"]
        assert data["is_carryover"] is False
        assert data["is_priority"] is False

    def test_enrollment_with_priority(self, client, auth_headers):
        course = create_course(client, headers=auth_headers).json()
        response = client.post("/api/v1/courses/enroll", json={
            "course_id": course["id"],
            "is_priority": True,
            "is_carryover": True,
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["is_priority"] is True
        assert data["is_carryover"] is True

    def test_duplicate_enrollment_rejected(self, client, auth_headers):
        course = create_course(client, headers=auth_headers).json()
        client.post("/api/v1/courses/enroll", json={
            "course_id": course["id"],
        }, headers=auth_headers)
        response = client.post("/api/v1/courses/enroll", json={
            "course_id": course["id"],
        }, headers=auth_headers)
        assert response.status_code == 400
        assert "Already enrolled" in response.json()["detail"]

    def test_enroll_nonexistent_course(self, client, auth_headers):
        response = client.post("/api/v1/courses/enroll", json={
            "course_id": "00000000-0000-0000-0000-000000000000",
        }, headers=auth_headers)
        assert response.status_code == 404

    def test_enroll_without_auth(self, client, auth_headers):
        course = create_course(client, headers=auth_headers).json()
        response = client.post("/api/v1/courses/enroll", json={
            "course_id": course["id"],
        })
        assert response.status_code == 401  # Missing Authorization header


# ===================================================================
# GET /api/v1/courses/my-courses/ - My Courses
# ===================================================================

class TestMyCourses:

    def test_empty_my_courses(self, client, auth_headers):
        response = client.get("/api/v1/courses/my-courses/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_my_courses_after_enrollment(self, client, auth_headers):
        course = create_course(client, headers=auth_headers).json()
        client.post("/api/v1/courses/enroll", json={
            "course_id": course["id"],
        }, headers=auth_headers)
        response = client.get("/api/v1/courses/my-courses/", headers=auth_headers)
        assert response.status_code == 200
        enrollments = response.json()
        assert len(enrollments) == 1
        assert enrollments[0]["course"]["code"] == "CSC401"


# ===================================================================
# DELETE /api/v1/courses/my-courses/{id} - Unenroll
# ===================================================================

class TestUnenroll:

    def test_successful_unenroll(self, client, auth_headers):
        course = create_course(client, headers=auth_headers).json()
        enroll_resp = client.post("/api/v1/courses/enroll", json={
            "course_id": course["id"],
        }, headers=auth_headers)
        enrollment_id = enroll_resp.json()["id"]

        response = client.delete(
            f"/api/v1/courses/my-courses/{enrollment_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify removed
        my_courses = client.get("/api/v1/courses/my-courses/", headers=auth_headers)
        assert len(my_courses.json()) == 0

    def test_unenroll_nonexistent(self, client, auth_headers):
        response = client.delete(
            "/api/v1/courses/my-courses/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert response.status_code == 404
