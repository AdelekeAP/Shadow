"""
Integration tests for Mood API routes
backend/app/routes/mood.py

Tests mood logging, history, trends, and energy endpoints.
"""
import pytest


# ===================================================================
# Helper
# ===================================================================

def log_mood(client, auth_headers, mood_type="focused", energy_level=4, **overrides):
    """Helper to log a mood"""
    data = {
        "mood_type": mood_type,
        "energy_level": energy_level,
    }
    data.update(overrides)
    return client.post("/api/v1/mood/log-mood", json=data, headers=auth_headers)


# ===================================================================
# POST /api/v1/mood/log-mood
# ===================================================================

class TestLogMood:

    def test_log_valid_mood(self, client, auth_headers):
        response = log_mood(client, auth_headers, mood_type="focused", energy_level=4)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["mood_log"]["mood_type"] == "focused"
        assert data["mood_log"]["energy_level"] == 4

    def test_all_valid_mood_types(self, client, auth_headers):
        valid_moods = ['focused', 'tired', 'stressed', 'motivated',
                       'anxious', 'confident', 'overwhelmed', 'calm']
        for mood in valid_moods:
            response = log_mood(client, auth_headers, mood_type=mood, energy_level=3)
            assert response.status_code == 200, f"Failed for mood: {mood}"

    def test_invalid_mood_type(self, client, auth_headers):
        response = log_mood(client, auth_headers, mood_type="happy")
        assert response.status_code == 400
        assert "Invalid mood type" in response.json()["detail"]

    def test_energy_level_bounds(self, client, auth_headers):
        # Min energy
        r1 = log_mood(client, auth_headers, energy_level=1)
        assert r1.status_code == 200
        assert r1.json()["mood_log"]["energy_level"] == 1

        # Max energy
        r2 = log_mood(client, auth_headers, mood_type="motivated", energy_level=5)
        assert r2.status_code == 200
        assert r2.json()["mood_log"]["energy_level"] == 5

    def test_energy_below_min_rejected(self, client, auth_headers):
        response = log_mood(client, auth_headers, energy_level=0)
        assert response.status_code == 422

    def test_energy_above_max_rejected(self, client, auth_headers):
        response = log_mood(client, auth_headers, energy_level=6)
        assert response.status_code == 422

    def test_mood_with_note(self, client, auth_headers):
        response = log_mood(client, auth_headers, note="Feeling great today!")
        assert response.status_code == 200
        data = response.json()
        assert data["mood_log"]["note"] == "Feeling great today!"

    def test_mood_without_note(self, client, auth_headers):
        response = log_mood(client, auth_headers)
        assert response.status_code == 200
        assert response.json()["mood_log"]["note"] is None

    def test_mood_case_insensitive(self, client, auth_headers):
        response = log_mood(client, auth_headers, mood_type="FOCUSED")
        assert response.status_code == 200
        assert response.json()["mood_log"]["mood_type"] == "focused"

    def test_mood_without_auth(self, client):
        response = client.post("/api/v1/mood/log-mood", json={
            "mood_type": "focused",
            "energy_level": 3,
        })
        assert response.status_code in [401, 422]

    def test_mood_log_has_timestamp(self, client, auth_headers):
        response = log_mood(client, auth_headers)
        assert response.status_code == 200
        assert response.json()["mood_log"]["logged_at"] is not None

    def test_mood_log_has_user_id(self, client, auth_headers):
        response = log_mood(client, auth_headers)
        assert response.status_code == 200
        assert response.json()["mood_log"]["user_id"] is not None


# ===================================================================
# GET /api/v1/mood/moods
# ===================================================================

class TestMoodHistory:

    def test_empty_mood_history(self, client, auth_headers):
        response = client.get("/api/v1/mood/moods", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 0
        assert data["moods"] == []

    def test_history_after_logging(self, client, auth_headers):
        log_mood(client, auth_headers, mood_type="focused", energy_level=4)
        log_mood(client, auth_headers, mood_type="tired", energy_level=2)
        log_mood(client, auth_headers, mood_type="stressed", energy_level=1)

        response = client.get("/api/v1/mood/moods", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["moods"]) == 3

    def test_history_returns_all_logged_moods(self, client, auth_headers):
        log_mood(client, auth_headers, mood_type="focused", energy_level=4)
        log_mood(client, auth_headers, mood_type="tired", energy_level=2)

        response = client.get("/api/v1/mood/moods", headers=auth_headers)
        moods = response.json()["moods"]
        mood_types = {m["mood_type"] for m in moods}
        assert mood_types == {"focused", "tired"}

    def test_history_without_auth(self, client):
        response = client.get("/api/v1/mood/moods")
        assert response.status_code in [401, 422]


# ===================================================================
# GET /api/v1/mood/mood-trends
# ===================================================================

class TestMoodTrends:

    def test_trends_no_data(self, client, auth_headers):
        response = client.get("/api/v1/mood/mood-trends", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["trends"]["total_logs"] == 0
        assert data["trends"]["avg_energy"] == 0

    def test_trends_with_data(self, client, auth_headers):
        log_mood(client, auth_headers, mood_type="focused", energy_level=4)
        log_mood(client, auth_headers, mood_type="focused", energy_level=5)
        log_mood(client, auth_headers, mood_type="tired", energy_level=2)

        response = client.get("/api/v1/mood/mood-trends", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        trends = data["trends"]
        assert trends["total_logs"] == 3
        assert trends["avg_energy"] == pytest.approx(3.67, abs=0.01)
        assert trends["most_common_mood"] == "focused"
        assert "mood_distribution" in trends
        assert trends["mood_distribution"]["focused"] == 2
        assert trends["mood_distribution"]["tired"] == 1

    def test_trends_without_auth(self, client):
        response = client.get("/api/v1/mood/mood-trends")
        assert response.status_code in [401, 422]


# ===================================================================
# GET /api/v1/mood/recent-energy
# ===================================================================

class TestRecentEnergy:

    def test_recent_energy_no_data(self, client, auth_headers):
        response = client.get("/api/v1/mood/recent-energy", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["avg_energy"] == 3.0  # Default neutral
        assert data["recent_moods"] == []

    def test_recent_energy_with_data(self, client, auth_headers):
        log_mood(client, auth_headers, mood_type="focused", energy_level=5)
        log_mood(client, auth_headers, mood_type="tired", energy_level=1)

        response = client.get("/api/v1/mood/recent-energy", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["avg_energy"] == 3.0  # (5+1)/2
        assert len(data["recent_moods"]) == 2

    def test_recent_energy_without_auth(self, client):
        response = client.get("/api/v1/mood/recent-energy")
        assert response.status_code in [401, 422]
