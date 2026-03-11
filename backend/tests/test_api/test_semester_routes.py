"""Tests for semester management routes."""
import pytest


class TestSemesterRoutes:
    """Test semester CRUD operations."""

    def test_create_academic_year(self, client, auth_headers):
        """Should create a new academic year with two semesters."""
        response = client.post("/api/v1/semesters/academic-year", json={
            "academic_year": "2025/2026"
        }, headers=auth_headers)
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["success"] is True
        assert data["academic_year"] == "2025/2026"
        assert len(data["semesters"]) == 2

    def test_create_academic_year_generates_two_semesters(self, client, auth_headers):
        """Creating an academic year should auto-generate first and second semester."""
        response = client.post("/api/v1/semesters/academic-year", json={
            "academic_year": "2024/2025"
        }, headers=auth_headers)
        assert response.status_code in [200, 201]
        semesters = response.json()["semesters"]
        semester_numbers = {s["semester_number"] for s in semesters}
        assert semester_numbers == {1, 2}

    def test_list_semesters(self, client, auth_headers):
        """Should list user's semesters after creating one."""
        # Create one first
        client.post("/api/v1/semesters/academic-year", json={
            "academic_year": "2025/2026"
        }, headers=auth_headers)

        response = client.get("/api/v1/semesters/", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 2  # academic year creates 2 semesters

    def test_list_semesters_empty(self, client, auth_headers):
        """Should return empty list when no semesters exist."""
        response = client.get("/api/v1/semesters/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_create_duplicate_academic_year_rejected(self, client, auth_headers):
        """Should reject creating the same academic year twice."""
        client.post("/api/v1/semesters/academic-year", json={
            "academic_year": "2025/2026"
        }, headers=auth_headers)

        response = client.post("/api/v1/semesters/academic-year", json={
            "academic_year": "2025/2026"
        }, headers=auth_headers)
        assert response.status_code == 400

    def test_create_academic_year_invalid_format(self, client, auth_headers):
        """Should reject academic year with invalid format."""
        response = client.post("/api/v1/semesters/academic-year", json={
            "academic_year": "2025-2026"
        }, headers=auth_headers)
        assert response.status_code == 422

    def test_create_academic_year_non_consecutive_years(self, client, auth_headers):
        """Should reject academic year where second year is not first year + 1."""
        response = client.post("/api/v1/semesters/academic-year", json={
            "academic_year": "2025/2027"
        }, headers=auth_headers)
        assert response.status_code == 422

    def test_get_active_semester(self, client, auth_headers):
        """Should return the active semester (or null if none)."""
        response = client.get("/api/v1/semesters/active", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "semester" in data

    def test_activate_semester(self, client, auth_headers):
        """Should activate a specific semester."""
        # Create an academic year first
        create_resp = client.post("/api/v1/semesters/academic-year", json={
            "academic_year": "2025/2026"
        }, headers=auth_headers)
        semesters = create_resp.json()["semesters"]
        second_sem = next(s for s in semesters if s["semester_number"] == 2)
        semester_id = second_sem["id"]

        response = client.patch(
            f"/api/v1/semesters/{semester_id}/activate",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["semester"]["id"] == semester_id
        assert data["semester"]["is_active"] is True

    def test_create_academic_year_unauthenticated(self, client):
        """Should reject unauthenticated requests."""
        response = client.post("/api/v1/semesters/academic-year", json={
            "academic_year": "2025/2026"
        })
        assert response.status_code == 401

    def test_list_semesters_unauthenticated(self, client):
        """Should reject unauthenticated list requests."""
        response = client.get("/api/v1/semesters/")
        assert response.status_code == 401

    def test_delete_semester(self, client, auth_headers):
        """Should delete a semester."""
        create_resp = client.post("/api/v1/semesters/academic-year", json={
            "academic_year": "2025/2026"
        }, headers=auth_headers)
        semesters = create_resp.json()["semesters"]
        sem_id = semesters[0]["id"]

        response = client.delete(
            f"/api/v1/semesters/{sem_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_delete_nonexistent_semester(self, client, auth_headers):
        """Should return 404 for nonexistent semester."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(
            f"/api/v1/semesters/{fake_id}",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_semesters_isolated_per_user(self, client):
        """Each user should only see their own semesters."""
        # Register and login as user A
        client.post("/api/v1/auth/register", json={
            "email": "usera@pau.edu.ng",
            "password": "UserAPass123!",
            "full_name": "User A",
        })
        login_a = client.post("/api/v1/auth/login", json={
            "email": "usera@pau.edu.ng",
            "password": "UserAPass123!"
        })
        headers_a = {"Authorization": f"Bearer {login_a.json()['access_token']}"}

        # Register and login as user B
        client.post("/api/v1/auth/register", json={
            "email": "userb@pau.edu.ng",
            "password": "UserBPass123!",
            "full_name": "User B",
        })
        login_b = client.post("/api/v1/auth/login", json={
            "email": "userb@pau.edu.ng",
            "password": "UserBPass123!"
        })
        headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

        # User A creates an academic year
        client.post("/api/v1/semesters/academic-year", json={
            "academic_year": "2025/2026"
        }, headers=headers_a)

        # User B should see no semesters
        resp_b = client.get("/api/v1/semesters/", headers=headers_b)
        assert resp_b.status_code == 200
        assert resp_b.json() == []
