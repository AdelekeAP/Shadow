"""
Tests for Notification Service
backend/app/services/notification_service.py

Tests CRUD operations, preferences, and edge cases using an in-memory SQLite DB.
"""
import uuid
import pytest
from unittest.mock import patch

from app.services.notification_service import NotificationService


class TestNotificationService:

    def test_create_notification(self, db_session, test_user):
        service = NotificationService(db_session)
        notif = service.create_notification(
            user_id=test_user.id,
            title="Test",
            message="Test message",
            notification_type="system",
            priority="medium",
            check_preferences=False,
        )
        assert notif is not None
        assert notif.title == "Test"
        assert notif.is_read is False

    def test_get_unread_count(self, db_session, test_user):
        service = NotificationService(db_session)
        service.create_notification(
            user_id=test_user.id, title="N1", message="M1",
            notification_type="system", check_preferences=False,
        )
        service.create_notification(
            user_id=test_user.id, title="N2", message="M2",
            notification_type="system", check_preferences=False,
        )
        assert service.get_unread_count(test_user.id) == 2

    def test_mark_as_read(self, db_session, test_user):
        service = NotificationService(db_session)
        notif = service.create_notification(
            user_id=test_user.id, title="N", message="M",
            notification_type="system", check_preferences=False,
        )
        result = service.mark_as_read(notif.id, test_user.id)
        assert result is True
        assert service.get_unread_count(test_user.id) == 0

    def test_mark_all_as_read(self, db_session, test_user):
        service = NotificationService(db_session)
        service.create_notification(
            user_id=test_user.id, title="N1", message="M1",
            notification_type="system", check_preferences=False,
        )
        service.create_notification(
            user_id=test_user.id, title="N2", message="M2",
            notification_type="system", check_preferences=False,
        )
        count = service.mark_all_as_read(test_user.id)
        assert count == 2
        assert service.get_unread_count(test_user.id) == 0

    def test_dismiss_notification(self, db_session, test_user):
        service = NotificationService(db_session)
        notif = service.create_notification(
            user_id=test_user.id, title="N", message="M",
            notification_type="system", check_preferences=False,
        )
        result = service.dismiss_notification(notif.id, test_user.id)
        assert result is True

    def test_get_user_notifications(self, db_session, test_user):
        service = NotificationService(db_session)
        service.create_notification(
            user_id=test_user.id, title="N1", message="M1",
            notification_type="system", check_preferences=False,
        )
        notifications = service.get_user_notifications(user_id=test_user.id, limit=10)
        assert len(notifications) >= 1

    def test_get_or_create_preferences(self, db_session, test_user):
        service = NotificationService(db_session)
        prefs = service.get_or_create_preferences(test_user.id)
        assert prefs is not None
        assert prefs.task_reminders is True  # default

    def test_get_or_create_preferences_idempotent(self, db_session, test_user):
        service = NotificationService(db_session)
        prefs1 = service.get_or_create_preferences(test_user.id)
        prefs2 = service.get_or_create_preferences(test_user.id)
        assert str(prefs1.id) == str(prefs2.id)

    def test_update_preferences(self, db_session, test_user):
        service = NotificationService(db_session)
        service.get_or_create_preferences(test_user.id)
        updated = service.update_preferences(test_user.id, {"task_reminders": False})
        assert updated.task_reminders is False

    def test_mark_as_read_wrong_user(self, db_session, test_user):
        service = NotificationService(db_session)
        notif = service.create_notification(
            user_id=test_user.id, title="N", message="M",
            notification_type="system", check_preferences=False,
        )
        result = service.mark_as_read(notif.id, uuid.uuid4())  # wrong user
        assert result is False

    def test_dismiss_nonexistent(self, db_session, test_user):
        service = NotificationService(db_session)
        result = service.dismiss_notification(uuid.uuid4(), test_user.id)
        assert result is False

    def test_dismissed_notification_not_in_list(self, db_session, test_user):
        """Dismissed notifications should not appear in get_user_notifications"""
        service = NotificationService(db_session)
        notif = service.create_notification(
            user_id=test_user.id, title="Hidden", message="Will be dismissed",
            notification_type="system", check_preferences=False,
        )
        service.dismiss_notification(notif.id, test_user.id)
        notifications = service.get_user_notifications(user_id=test_user.id)
        ids = [n.id for n in notifications]
        assert notif.id not in ids
