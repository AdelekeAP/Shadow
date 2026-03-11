"""
Integration tests for Authentication API routes
backend/app/routes/auth.py

Tests the full request/response cycle through FastAPI with a real
(in-memory SQLite) database.
"""
import pytest


# ===================================================================
# POST /api/v1/auth/register
# ===================================================================

class TestRegister:

    def test_successful_registration(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "newstudent@pau.edu.ng",
            "password": "SecurePass123!",
            "full_name": "New Student",
            "university_id": "PAU/2023/001",
            "entry_level": "300L",
            "target_cgpa": 4.0,
        })
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "newstudent@pau.edu.ng"
        assert data["user"]["full_name"] == "New Student"

    def test_registration_returns_token(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "tokentest@pau.edu.ng",
            "password": "ValidPass123",
            "full_name": "Token Test",
        })
        assert response.status_code == 201
        data = response.json()
        assert len(data["access_token"]) > 20  # JWT is long

    def test_duplicate_email_rejected(self, client, registered_user):
        response = client.post("/api/v1/auth/register", json={
            "email": "teststudent@pau.edu.ng",  # Same as registered_user
            "password": "AnotherPass123",
            "full_name": "Duplicate User",
        })
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_short_password_rejected(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "short@pau.edu.ng",
            "password": "short",  # < 8 chars
            "full_name": "Short Pass",
        })
        assert response.status_code == 422  # Validation error

    def test_invalid_email_rejected(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "ValidPass123",
            "full_name": "Invalid Email",
        })
        assert response.status_code == 422

    def test_missing_required_fields(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "missing@pau.edu.ng",
        })
        assert response.status_code == 422

    def test_invalid_entry_level_rejected(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "level@pau.edu.ng",
            "password": "ValidPass123",
            "full_name": "Bad Level",
            "entry_level": "500L",  # Not a valid PAU level
        })
        assert response.status_code == 422

    def test_valid_entry_levels_accepted(self, client):
        valid_levels = ["100L", "200L", "200L-DE", "300L", "400L"]
        for i, level in enumerate(valid_levels):
            response = client.post("/api/v1/auth/register", json={
                "email": f"level{i}@pau.edu.ng",
                "password": "ValidPass123",
                "full_name": f"Level {level}",
                "entry_level": level,
            })
            assert response.status_code == 201, f"Failed for entry_level={level}"

    def test_target_cgpa_out_of_range(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "cgpa@pau.edu.ng",
            "password": "ValidPass123",
            "full_name": "Bad CGPA",
            "target_cgpa": 6.0,  # Max is 5.0
        })
        assert response.status_code == 422

    def test_gpa_scale_defaults_to_5(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "scale@pau.edu.ng",
            "password": "ValidPass123",
            "full_name": "Scale Test",
        })
        assert response.status_code == 201
        assert response.json()["user"]["gpa_scale"] == 5.0


# ===================================================================
# POST /api/v1/auth/login
# ===================================================================

class TestLogin:

    def test_successful_login(self, client, registered_user):
        response = client.post("/api/v1/auth/login", json={
            "email": "teststudent@pau.edu.ng",
            "password": registered_user["password"],
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "teststudent@pau.edu.ng"

    def test_wrong_password(self, client, registered_user):
        response = client.post("/api/v1/auth/login", json={
            "email": "teststudent@pau.edu.ng",
            "password": "WrongPassword123",
        })
        assert response.status_code == 401

    def test_nonexistent_email(self, client):
        response = client.post("/api/v1/auth/login", json={
            "email": "nobody@pau.edu.ng",
            "password": "SomePass123",
        })
        assert response.status_code == 401

    def test_login_token_works_for_auth(self, client, registered_user):
        """Login token should allow accessing protected routes"""
        login_response = client.post("/api/v1/auth/login", json={
            "email": "teststudent@pau.edu.ng",
            "password": registered_user["password"],
        })
        token = login_response.json()["access_token"]
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_response.status_code == 200


# ===================================================================
# GET /api/v1/auth/me
# ===================================================================

class TestGetMe:

    def test_authenticated_user_gets_profile(self, client, auth_headers):
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "teststudent@pau.edu.ng"
        assert data["full_name"] == "Test Student"
        assert "password" not in data
        assert "password_hash" not in data

    def test_no_token_returns_401(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client):
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.jwt.token"},
        )
        assert response.status_code == 401

    def test_profile_contains_required_fields(self, client, auth_headers):
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        data = response.json()
        required_fields = ["id", "email", "full_name", "gpa_scale", "is_active"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"


# ===================================================================
# Root & Health endpoints
# ===================================================================

class TestRootEndpoints:

    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert "Shadow" in data["message"]

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


# ===================================================================
# Auth Security Tests
# ===================================================================

def test_logout_blacklists_token(client, auth_headers):
    """Logout should blacklist the access token"""
    # Verify we're authenticated
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200

    # Logout
    response = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert response.status_code == 200

    # Token should now be blacklisted
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 401


def test_refresh_token_rotation(client):
    """Refresh should return new tokens and invalidate old refresh token"""
    # Register and login
    client.post("/api/v1/auth/register", json={
        "email": "refresh@test.com",
        "password": "TestPass123!",
        "full_name": "Refresh Test",
        "entry_level": "100L"
    })
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "refresh@test.com",
        "password": "TestPass123!"
    })
    data = login_resp.json()
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        pytest.skip("Refresh tokens not enabled")

    # Use refresh token
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    new_refresh = resp.json().get("refresh_token")
    assert new_refresh != refresh_token  # Should be a new token

    # Old refresh token should be revoked
    resp2 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp2.status_code in [401, 400]


def test_change_password_invalidates_old_token(client, auth_headers):
    """Changing password should invalidate existing tokens via token_version"""
    # Change password — note: schema field is old_password (not current_password)
    response = client.post("/api/v1/auth/change-password", json={
        "old_password": "SecurePass123!",
        "new_password": "NewPassword456!"
    }, headers=auth_headers)
    # Accept 200 or check if the endpoint exists
    if response.status_code == 404:
        pytest.skip("Change password endpoint not available")
    assert response.status_code == 200

    # Old token should now be invalid
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 401
