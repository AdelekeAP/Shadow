"""
Integration tests for Notification API routes
backend/app/routes/notifications.py

Tests notification listing, counts, read/dismiss actions, preferences,
and scheduled reminders.
"""
import pytest


# ===================================================================
# GET /api/v1/notifications
# ===================================================================

class TestGetNotifications:

    def test_get_notifications_empty(self, client, auth_headers):
        """Empty notification list for a new user"""
        response = client.get("/api/v1/notifications", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["notifications"] == []
        assert data["total_count"] == 0
        assert data["unread_count"] == 0

    def test_get_notifications_with_data(self, client, auth_headers, notification_in_db):
        """Notifications list includes the seeded notification"""
        response = client.get("/api/v1/notifications", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert data["unread_count"] == 1
        assert len(data["notifications"]) == 1
        notif = data["notifications"][0]
        assert notif["title"] == "Test Notification"
        assert notif["message"] == "This is a test notification"
        assert notif["notification_type"] == "system"
        assert notif["priority"] == "medium"
        assert notif["is_read"] is False
        assert notif["is_dismissed"] is False

    def test_get_notifications_unauthenticated(self, client):
        """Listing notifications without auth is rejected"""
        response = client.get("/api/v1/notifications")
        assert response.status_code in [401, 403]


# ===================================================================
# GET /api/v1/notifications/count
# ===================================================================

class TestNotificationCount:

    def test_get_notification_count_empty(self, client, auth_headers):
        """Counts are zero for a new user"""
        response = client.get("/api/v1/notifications/count", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["unread_count"] == 0
        assert data["total_count"] == 0

    def test_get_notification_count_with_data(self, client, auth_headers, notification_in_db):
        """Counts reflect the seeded notification"""
        response = client.get("/api/v1/notifications/count", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["unread_count"] == 1
        assert data["total_count"] == 1


# ===================================================================
# GET /api/v1/notifications/{notification_id}
# ===================================================================

class TestGetSingleNotification:

    def test_get_single_notification(self, client, auth_headers, notification_in_db):
        """Retrieve a single notification by ID"""
        notif_id = notification_in_db["notification_id"]
        response = client.get(
            f"/api/v1/notifications/{notif_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == notif_id
        assert data["title"] == "Test Notification"

    def test_get_notification_not_found(self, client, auth_headers):
        """Request for non-existent notification returns 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(
            f"/api/v1/notifications/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


# ===================================================================
# POST /api/v1/notifications/{notification_id}/read
# ===================================================================

class TestMarkNotificationRead:

    def test_mark_notification_read(self, client, auth_headers, notification_in_db):
        """Mark a notification as read"""
        notif_id = notification_in_db["notification_id"]
        response = client.post(
            f"/api/v1/notifications/{notif_id}/read",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["affected_count"] == 1

        # Verify it is now read
        get_resp = client.get(
            f"/api/v1/notifications/{notif_id}",
            headers=auth_headers,
        )
        assert get_resp.json()["is_read"] is True


# ===================================================================
# POST /api/v1/notifications/read-all
# ===================================================================

class TestMarkAllRead:

    def test_mark_all_read(self, client, auth_headers, notification_in_db):
        """Mark all notifications as read"""
        response = client.post(
            "/api/v1/notifications/read-all",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["affected_count"] >= 1

    def test_mark_all_read_empty(self, client, auth_headers):
        """Mark-all-read on empty inbox still succeeds"""
        response = client.post(
            "/api/v1/notifications/read-all",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["affected_count"] == 0


# ===================================================================
# POST /api/v1/notifications/{notification_id}/dismiss
# ===================================================================

class TestDismissNotification:

    def test_dismiss_notification(self, client, auth_headers, notification_in_db):
        """Dismiss a notification"""
        notif_id = notification_in_db["notification_id"]
        response = client.post(
            f"/api/v1/notifications/{notif_id}/dismiss",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["affected_count"] == 1

    def test_dismiss_not_found(self, client, auth_headers):
        """Dismissing a non-existent notification returns 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.post(
            f"/api/v1/notifications/{fake_id}/dismiss",
            headers=auth_headers,
        )
        assert response.status_code == 404


# ===================================================================
# GET /api/v1/notifications/preferences/me
# ===================================================================

class TestPreferences:

    def test_get_preferences(self, client, auth_headers):
        """Get (or create default) preferences for the current user"""
        response = client.get(
            "/api/v1/notifications/preferences/me",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        # Verify default preference values
        assert data["email_enabled"] is True
        assert data["in_app_enabled"] is True
        assert data["task_reminders"] is True
        assert data["mood_check_reminders"] is True
        assert data["timezone"] == "Africa/Lagos"
        assert "user_id" in data
        assert "id" in data


# ===================================================================
# POST /api/v1/notifications/reminders
# ===================================================================

class TestScheduledReminders:

    def test_create_scheduled_reminder(self, client, auth_headers):
        """Create a new scheduled reminder"""
        payload = {
            "reminder_type": "study",
            "scheduled_time": "2026-03-01T10:00:00Z",
        }
        response = client.post(
            "/api/v1/notifications/reminders",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["reminder_type"] == "study"
        assert data["is_active"] is True
        assert data["is_sent"] is False
        assert "id" in data
        assert "user_id" in data
