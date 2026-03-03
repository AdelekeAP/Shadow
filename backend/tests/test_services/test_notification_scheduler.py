"""
Tests for Notification Scheduler - Background tasks for automatic notifications
backend/app/services/notification_scheduler.py

Tests calculate_next_run (pure function), scheduler management, and async background tasks.
"""
import pytest
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock, AsyncMock

os.environ["DISABLE_ML_MODELS"] = "true"
os.environ["TESTING"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

from app.services.notification_scheduler import (
    calculate_next_run,
    init_scheduler,
    start_scheduler,
    stop_scheduler,
    get_scheduler_status,
    process_task_reminders,
    process_overdue_tasks,
    process_mood_check_reminders,
    process_scheduled_reminders,
    cleanup_old_notifications,
)


# ==================== calculate_next_run ====================


class TestCalculateNextRun:
    """Tests for the calculate_next_run pure function."""

    def test_daily_pattern(self):
        """Daily recurrence should return approximately 1 day ahead."""
        mock_reminder = MagicMock()
        mock_reminder.recurrence_pattern = "daily"
        mock_reminder.recurrence_data = None

        before = datetime.now(timezone.utc)
        result = calculate_next_run(mock_reminder)
        after = datetime.now(timezone.utc)

        expected_min = before + timedelta(days=1)
        expected_max = after + timedelta(days=1)
        assert expected_min <= result <= expected_max

    def test_weekly_pattern(self):
        """Weekly recurrence should return approximately 7 days ahead."""
        mock_reminder = MagicMock()
        mock_reminder.recurrence_pattern = "weekly"
        mock_reminder.recurrence_data = None

        before = datetime.now(timezone.utc)
        result = calculate_next_run(mock_reminder)
        after = datetime.now(timezone.utc)

        expected_min = before + timedelta(weeks=1)
        expected_max = after + timedelta(weeks=1)
        assert expected_min <= result <= expected_max

    def test_hourly_pattern(self):
        """Hourly recurrence should return approximately 1 hour ahead."""
        mock_reminder = MagicMock()
        mock_reminder.recurrence_pattern = "hourly"
        mock_reminder.recurrence_data = None

        before = datetime.now(timezone.utc)
        result = calculate_next_run(mock_reminder)
        after = datetime.now(timezone.utc)

        expected_min = before + timedelta(hours=1)
        expected_max = after + timedelta(hours=1)
        assert expected_min <= result <= expected_max

    def test_custom_with_interval_hours(self):
        """Custom recurrence with interval_hours should use that value."""
        mock_reminder = MagicMock()
        mock_reminder.recurrence_pattern = "custom"
        mock_reminder.recurrence_data = {"interval_hours": 6}

        before = datetime.now(timezone.utc)
        result = calculate_next_run(mock_reminder)
        after = datetime.now(timezone.utc)

        expected_min = before + timedelta(hours=6)
        expected_max = after + timedelta(hours=6)
        assert expected_min <= result <= expected_max

    def test_custom_without_recurrence_data(self):
        """Custom pattern without recurrence_data should default to 1 day."""
        mock_reminder = MagicMock()
        mock_reminder.recurrence_pattern = "custom"
        mock_reminder.recurrence_data = None

        before = datetime.now(timezone.utc)
        result = calculate_next_run(mock_reminder)
        after = datetime.now(timezone.utc)

        # Falls through to the else branch -> 1 day
        expected_min = before + timedelta(days=1)
        expected_max = after + timedelta(days=1)
        assert expected_min <= result <= expected_max

    def test_unknown_pattern_defaults_to_daily(self):
        """An unrecognized pattern should default to 1 day ahead."""
        mock_reminder = MagicMock()
        mock_reminder.recurrence_pattern = "biweekly"
        mock_reminder.recurrence_data = None

        before = datetime.now(timezone.utc)
        result = calculate_next_run(mock_reminder)
        after = datetime.now(timezone.utc)

        expected_min = before + timedelta(days=1)
        expected_max = after + timedelta(days=1)
        assert expected_min <= result <= expected_max

    def test_custom_with_large_interval(self):
        """Custom with a large interval_hours value."""
        mock_reminder = MagicMock()
        mock_reminder.recurrence_pattern = "custom"
        mock_reminder.recurrence_data = {"interval_hours": 72}

        before = datetime.now(timezone.utc)
        result = calculate_next_run(mock_reminder)
        after = datetime.now(timezone.utc)

        expected_min = before + timedelta(hours=72)
        expected_max = after + timedelta(hours=72)
        assert expected_min <= result <= expected_max

    def test_custom_with_missing_interval_key(self):
        """Custom with recurrence_data but no interval_hours key should default to 24 hours."""
        mock_reminder = MagicMock()
        mock_reminder.recurrence_pattern = "custom"
        mock_reminder.recurrence_data = {"some_other_key": 10}

        before = datetime.now(timezone.utc)
        result = calculate_next_run(mock_reminder)
        after = datetime.now(timezone.utc)

        expected_min = before + timedelta(hours=24)
        expected_max = after + timedelta(hours=24)
        assert expected_min <= result <= expected_max


# ==================== Scheduler Management ====================


class TestSchedulerManagement:
    """Tests for init_scheduler, start_scheduler, stop_scheduler, get_scheduler_status."""

    def test_init_scheduler_returns_scheduler_with_six_jobs(self):
        """init_scheduler should return a scheduler with 6 configured jobs."""
        import app.services.notification_scheduler as ns_module

        old_scheduler = ns_module.scheduler
        try:
            sched = init_scheduler()
            assert sched is not None
            jobs = sched.get_jobs()
            assert len(jobs) == 6

            job_ids = {j.id for j in jobs}
            expected_ids = {
                "task_reminders",
                "overdue_tasks",
                "mood_check_morning",
                "mood_check_afternoon",
                "scheduled_reminders",
                "cleanup",
            }
            assert job_ids == expected_ids
        finally:
            # Shut down if running and restore
            if sched.running:
                sched.shutdown(wait=False)
            ns_module.scheduler = old_scheduler

    def test_get_scheduler_status_when_none(self):
        """get_scheduler_status should return not_initialized when scheduler is None."""
        import app.services.notification_scheduler as ns_module

        old_scheduler = ns_module.scheduler
        try:
            ns_module.scheduler = None
            status = get_scheduler_status()
            assert status["status"] == "not_initialized"
            assert status["jobs"] == []
        finally:
            ns_module.scheduler = old_scheduler

    def test_get_scheduler_status_with_mock_scheduler(self):
        """get_scheduler_status should reflect the mock scheduler's state."""
        import app.services.notification_scheduler as ns_module

        old_scheduler = ns_module.scheduler

        mock_job = MagicMock()
        mock_job.id = "test_job"
        mock_job.name = "Test Job"
        mock_job.next_run_time = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)

        mock_sched = MagicMock()
        mock_sched.running = True
        mock_sched.get_jobs.return_value = [mock_job]

        try:
            ns_module.scheduler = mock_sched
            status = get_scheduler_status()
            assert status["status"] == "running"
            assert len(status["jobs"]) == 1
            assert status["jobs"][0]["id"] == "test_job"
            assert status["jobs"][0]["name"] == "Test Job"
            assert status["jobs"][0]["next_run"] is not None
        finally:
            ns_module.scheduler = old_scheduler

    def test_get_scheduler_status_stopped(self):
        """get_scheduler_status should show 'stopped' when scheduler exists but is not running."""
        import app.services.notification_scheduler as ns_module

        old_scheduler = ns_module.scheduler

        mock_sched = MagicMock()
        mock_sched.running = False
        mock_sched.get_jobs.return_value = []

        try:
            ns_module.scheduler = mock_sched
            status = get_scheduler_status()
            assert status["status"] == "stopped"
            assert status["jobs"] == []
        finally:
            ns_module.scheduler = old_scheduler

    @patch("app.services.notification_scheduler.AsyncIOScheduler")
    def test_start_scheduler_creates_and_starts(self, mock_scheduler_cls):
        """start_scheduler should create scheduler if None and start it."""
        import app.services.notification_scheduler as ns_module

        old_scheduler = ns_module.scheduler

        mock_instance = MagicMock()
        mock_instance.running = False
        mock_scheduler_cls.return_value = mock_instance

        try:
            ns_module.scheduler = None
            start_scheduler()
            # It should have initialized (creating a real scheduler via init_scheduler)
            # and then called start
            assert ns_module.scheduler is not None
        finally:
            # Clean up - shut down if a real scheduler was created
            if ns_module.scheduler and hasattr(ns_module.scheduler, 'running'):
                try:
                    if ns_module.scheduler.running:
                        ns_module.scheduler.shutdown(wait=False)
                except Exception:
                    pass
            ns_module.scheduler = old_scheduler

    def test_stop_scheduler_when_running(self):
        """stop_scheduler should call shutdown when scheduler is running."""
        import app.services.notification_scheduler as ns_module

        old_scheduler = ns_module.scheduler

        mock_sched = MagicMock()
        mock_sched.running = True

        try:
            ns_module.scheduler = mock_sched
            stop_scheduler()
            mock_sched.shutdown.assert_called_once()
        finally:
            ns_module.scheduler = old_scheduler

    def test_stop_scheduler_when_not_running(self):
        """stop_scheduler should not call shutdown when scheduler is not running."""
        import app.services.notification_scheduler as ns_module

        old_scheduler = ns_module.scheduler

        mock_sched = MagicMock()
        mock_sched.running = False

        try:
            ns_module.scheduler = mock_sched
            stop_scheduler()
            mock_sched.shutdown.assert_not_called()
        finally:
            ns_module.scheduler = old_scheduler

    def test_stop_scheduler_when_none(self):
        """stop_scheduler should handle None scheduler gracefully."""
        import app.services.notification_scheduler as ns_module

        old_scheduler = ns_module.scheduler
        try:
            ns_module.scheduler = None
            # Should not raise
            stop_scheduler()
        finally:
            ns_module.scheduler = old_scheduler


# ==================== Async Background Tasks ====================


class TestAsyncBackgroundTasks:
    """Tests for async background task functions with mocked DB."""

    @pytest.mark.asyncio
    @patch("app.services.notification_scheduler.get_db_session")
    async def test_process_task_reminders_no_users(self, mock_get_db):
        """process_task_reminders completes when no active users found."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        await process_task_reminders()
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.notification_scheduler.get_db_session")
    async def test_process_overdue_tasks_no_overdue(self, mock_get_db):
        """process_overdue_tasks completes when no overdue tasks found."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        await process_overdue_tasks()
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.notification_scheduler.get_db_session")
    async def test_process_mood_check_reminders_no_prefs(self, mock_get_db):
        """process_mood_check_reminders completes when no preferences found."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        await process_mood_check_reminders()
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.notification_scheduler.get_db_session")
    async def test_process_scheduled_reminders_no_due(self, mock_get_db):
        """process_scheduled_reminders completes when no due reminders found."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        await process_scheduled_reminders()
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.notification_scheduler.get_notification_service")
    @patch("app.services.notification_scheduler.get_db_session")
    async def test_cleanup_old_notifications(self, mock_get_db, mock_get_service):
        """cleanup_old_notifications should call delete_old_notifications on the service."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_service = MagicMock()
        mock_service.delete_old_notifications.return_value = 5
        mock_get_service.return_value = mock_service

        await cleanup_old_notifications()

        mock_service.delete_old_notifications.assert_called_once_with(days_old=30)
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.notification_scheduler.get_db_session")
    async def test_process_task_reminders_handles_exception(self, mock_get_db):
        """process_task_reminders should handle exceptions gracefully and close DB."""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("DB error")
        mock_get_db.return_value = mock_db

        # Should not raise
        await process_task_reminders()
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.notification_scheduler.get_db_session")
    async def test_process_overdue_tasks_handles_exception(self, mock_get_db):
        """process_overdue_tasks should handle exceptions gracefully and close DB."""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("DB error")
        mock_get_db.return_value = mock_db

        await process_overdue_tasks()
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.notification_scheduler.get_db_session")
    async def test_process_mood_check_reminders_handles_exception(self, mock_get_db):
        """process_mood_check_reminders should handle exceptions and close DB."""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("DB error")
        mock_get_db.return_value = mock_db

        await process_mood_check_reminders()
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.notification_scheduler.get_notification_service")
    @patch("app.services.notification_scheduler.get_db_session")
    async def test_cleanup_handles_exception(self, mock_get_db, mock_get_service):
        """cleanup_old_notifications should handle exceptions and close DB."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_service.side_effect = Exception("Service error")

        await cleanup_old_notifications()
        mock_db.close.assert_called_once()
