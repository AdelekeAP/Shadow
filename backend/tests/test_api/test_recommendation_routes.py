"""
Tests for app.routes.recommendations

Covers all 5 endpoints:
- GET /api/v1/recommendations/priority-tasks
- GET /api/v1/recommendations/urgent
- GET /api/v1/recommendations/goal-driven
- GET /api/v1/recommendations/recovery
- GET /api/v1/recommendations/summary

Each endpoint is tested for:
- 200 with auth + mocked PriorityCalculator
- 401 without auth
Plus specific data-shape assertions.
"""
import os

os.environ["DISABLE_ML_MODELS"] = "true"
os.environ["TESTING"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-for-integration-tests"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

from unittest.mock import patch

# Use fixtures from test_api/conftest.py (client, auth_headers, registered_user, etc.)

# ---------------------------------------------------------------------------
# Sample recommendation data used across tests
# ---------------------------------------------------------------------------

SAMPLE_RECOMMENDATIONS = [
    {"recommendation_type": "urgent", "task": "Submit essay", "score": 9.5},
    {"recommendation_type": "urgent", "task": "Quiz prep", "score": 8.2},
    {"recommendation_type": "goal_driven", "task": "Study chapter 5", "score": 7.0},
    {"recommendation_type": "mood_based", "task": "Light review", "score": 5.5},
    {"recommendation_type": "recovery", "task": "Redo assignment", "score": 6.0},
]

MOCK_PATH = "app.routes.recommendations.PriorityCalculator.get_priority_recommendations"


# ---------------------------------------------------------------------------
# priority-tasks endpoint
# ---------------------------------------------------------------------------

class TestPriorityTasks:

    def test_returns_200_with_auth(self, client, auth_headers):
        with patch(MOCK_PATH, return_value=SAMPLE_RECOMMENDATIONS):
            resp = client.get("/api/v1/recommendations/priority-tasks", headers=auth_headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["total_recommendations"] == 5

    def test_returns_401_without_auth(self, client):
        resp = client.get("/api/v1/recommendations/priority-tasks")
        assert resp.status_code == 401

    def test_empty_recommendations(self, client, auth_headers):
        with patch(MOCK_PATH, return_value=[]):
            resp = client.get("/api/v1/recommendations/priority-tasks", headers=auth_headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["total_recommendations"] == 0
            assert data["recommendations"] == []

    def test_grouped_by_type(self, client, auth_headers):
        with patch(MOCK_PATH, return_value=SAMPLE_RECOMMENDATIONS):
            resp = client.get("/api/v1/recommendations/priority-tasks", headers=auth_headers)
            data = resp.json()
            grouped = data["grouped_by_type"]
            assert len(grouped["urgent"]) == 2
            assert len(grouped["goal_driven"]) == 1
            assert len(grouped["mood_based"]) == 1
            assert len(grouped["recovery"]) == 1

    def test_summary_counts(self, client, auth_headers):
        with patch(MOCK_PATH, return_value=SAMPLE_RECOMMENDATIONS):
            resp = client.get("/api/v1/recommendations/priority-tasks", headers=auth_headers)
            summary = resp.json()["summary"]
            assert summary["urgent_count"] == 2
            assert summary["goal_driven_count"] == 1
            assert summary["mood_based_count"] == 1
            assert summary["recovery_count"] == 1


# ---------------------------------------------------------------------------
# urgent endpoint
# ---------------------------------------------------------------------------

class TestUrgentTasks:

    def test_returns_200_with_auth(self, client, auth_headers):
        with patch(MOCK_PATH, return_value=SAMPLE_RECOMMENDATIONS):
            resp = client.get("/api/v1/recommendations/urgent", headers=auth_headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["count"] == 2

    def test_returns_401_without_auth(self, client):
        resp = client.get("/api/v1/recommendations/urgent")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# goal-driven endpoint
# ---------------------------------------------------------------------------

class TestGoalDrivenTasks:

    def test_returns_200_with_auth(self, client, auth_headers):
        with patch(MOCK_PATH, return_value=SAMPLE_RECOMMENDATIONS):
            resp = client.get("/api/v1/recommendations/goal-driven", headers=auth_headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["count"] == 1

    def test_returns_401_without_auth(self, client):
        resp = client.get("/api/v1/recommendations/goal-driven")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# recovery endpoint
# ---------------------------------------------------------------------------

class TestRecoveryTasks:

    def test_returns_200_with_auth(self, client, auth_headers):
        with patch(MOCK_PATH, return_value=SAMPLE_RECOMMENDATIONS):
            resp = client.get("/api/v1/recommendations/recovery", headers=auth_headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["count"] == 1

    def test_returns_401_without_auth(self, client):
        resp = client.get("/api/v1/recommendations/recovery")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# summary endpoint
# ---------------------------------------------------------------------------

class TestSummary:

    def test_returns_200_with_auth(self, client, auth_headers):
        with patch(MOCK_PATH, return_value=SAMPLE_RECOMMENDATIONS):
            resp = client.get("/api/v1/recommendations/summary", headers=auth_headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["total_pending_tasks"] == 5
            assert data["has_urgent_tasks"] is True
            assert data["has_recovery_tasks"] is True

    def test_returns_401_without_auth(self, client):
        resp = client.get("/api/v1/recommendations/summary")
        assert resp.status_code == 401

    def test_summary_correct_counts(self, client, auth_headers):
        with patch(MOCK_PATH, return_value=SAMPLE_RECOMMENDATIONS):
            resp = client.get("/api/v1/recommendations/summary", headers=auth_headers)
            counts = resp.json()["counts_by_type"]
            assert counts["urgent"] == 2
            assert counts["goal_driven"] == 1
            assert counts["mood_based"] == 1
            assert counts["recovery"] == 1

    def test_top_3_priorities(self, client, auth_headers):
        with patch(MOCK_PATH, return_value=SAMPLE_RECOMMENDATIONS):
            resp = client.get("/api/v1/recommendations/summary", headers=auth_headers)
            top3 = resp.json()["top_3_priorities"]
            assert len(top3) == 3
