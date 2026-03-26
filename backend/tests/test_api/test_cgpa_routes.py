"""
Integration tests for CGPA API routes
backend/app/routes/cgpa.py

Tests the CGPA dashboard, target calculation, and prediction endpoints.
These are key defense demonstration endpoints.
"""
import pytest


# ===================================================================
# Helper
# ===================================================================

def setup_user_with_courses(client, auth_headers):
    """Create courses, enroll, and add some completed tasks with marks"""
    # Create courses
    c1 = client.post("/api/v1/courses/", json={
        "code": "CSC401", "title": "Software Engineering", "credits": 3,
        "level": "400", "status": "C",
    }, headers=auth_headers).json()
    c2 = client.post("/api/v1/courses/", json={
        "code": "CSC403", "title": "Artificial Intelligence", "credits": 3,
        "level": "400", "status": "C",
    }, headers=auth_headers).json()

    # Enroll
    e1 = client.post("/api/v1/courses/enroll", json={
        "course_id": c1["id"],
    }, headers=auth_headers).json()
    e2 = client.post("/api/v1/courses/enroll", json={
        "course_id": c2["id"],
    }, headers=auth_headers).json()

    # Add completed CA tasks with marks for course 1
    t1 = client.post("/api/v1/tasks/", json={
        "user_course_id": e1["id"],
        "title": "Test 1", "task_type": "test",
        "weight": 15, "category": "CA",
        "is_completed": True, "earned_marks": 12,
    }, headers=auth_headers).json()

    # Add completed CA task for course 2
    t2 = client.post("/api/v1/tasks/", json={
        "user_course_id": e2["id"],
        "title": "Assignment 1", "task_type": "assignment",
        "weight": 10, "category": "CA",
        "is_completed": True, "earned_marks": 8,
    }, headers=auth_headers).json()

    return e1, e2, c1, c2


# ===================================================================
# GET /api/v1/cgpa/dashboard
# ===================================================================

class TestCGPADashboard:

    def test_dashboard_with_no_courses(self, client, auth_headers):
        response = client.get("/api/v1/cgpa/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_courses"] == 0

    def test_dashboard_with_courses(self, client, auth_headers):
        setup_user_with_courses(client, auth_headers)
        response = client.get("/api/v1/cgpa/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_courses"] == 2
        assert "current" in data["data"]
        assert "predictions" in data["data"]
        assert "target_analysis" in data["data"]

    def test_dashboard_without_auth(self, client):
        response = client.get("/api/v1/cgpa/dashboard")
        assert response.status_code == 401


# ===================================================================
# GET /api/v1/cgpa/current
# ===================================================================

class TestCurrentCGPA:

    def test_current_cgpa_no_courses(self, client, auth_headers):
        response = client.get("/api/v1/cgpa/current", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["cgpa"] == 0.0
        assert data["total_courses"] == 0

    def test_current_cgpa_with_data(self, client, auth_headers):
        setup_user_with_courses(client, auth_headers)
        response = client.get("/api/v1/cgpa/current", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_courses"] == 2


# ===================================================================
# POST /api/v1/cgpa/target
# ===================================================================

class TestTargetCGPA:

    def test_target_calculation(self, client, auth_headers):
        setup_user_with_courses(client, auth_headers)
        response = client.post("/api/v1/cgpa/target", json={
            "target_cgpa": 4.5,
            "semester_credits": 18,
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "required_gpa" in data["data"]
        assert "is_achievable" in data["data"]
        assert "difficulty" in data["data"]

    def test_target_without_auth(self, client):
        response = client.post("/api/v1/cgpa/target", json={
            "target_cgpa": 4.5,
            "semester_credits": 18,
        })
        assert response.status_code == 401


# ===================================================================
# POST /api/v1/cgpa/predict
# ===================================================================

class TestPredictCGPA:

    def test_prediction_endpoint(self, client, auth_headers):
        setup_user_with_courses(client, auth_headers)
        response = client.post("/api/v1/cgpa/predict", json={
            "predicted_courses": [
                {"credits": 3, "predicted_score": 75},
                {"credits": 3, "predicted_score": 65},
            ],
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "predicted_cgpa" in data["data"]

    def test_prediction_empty_courses(self, client, auth_headers):
        response = client.post("/api/v1/cgpa/predict", json={
            "predicted_courses": [],
        }, headers=auth_headers)
        assert response.status_code == 200


# ===================================================================
# GET /api/v1/cgpa/breakdown
# ===================================================================

class TestCGPABreakdown:

    def test_breakdown_endpoint(self, client, auth_headers):
        setup_user_with_courses(client, auth_headers)
        response = client.get("/api/v1/cgpa/breakdown", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "semesters" in data
        assert "cumulative_cgpa" in data


# ===================================================================
# GET /api/v1/cgpa/analytics
# ===================================================================

class TestCGPAAnalytics:

    def test_analytics_no_data(self, client, auth_headers):
        response = client.get("/api/v1/cgpa/analytics", headers=auth_headers)
        assert response.status_code == 200

    def test_analytics_with_data(self, client, auth_headers):
        setup_user_with_courses(client, auth_headers)
        response = client.get("/api/v1/cgpa/analytics", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
