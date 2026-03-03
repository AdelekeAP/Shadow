"""
Tests for Usage Logging - UsageLog model and usage-summary endpoint.
"""
import uuid
from datetime import datetime, timedelta

import pytest

from app.models.usage_log import UsageLog


class TestUsageLogModel:
    """Unit tests for the UsageLog SQLAlchemy model."""

    def test_usage_log_model_creation(self, db_session, test_user):
        """Create a UsageLog entry with a user_id and verify all fields are stored."""
        log = UsageLog(
            user_id=test_user.id,
            endpoint_path="/api/v1/courses",
            http_method="GET",
            status_code=200,
            response_time_ms=45.12,
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)

        assert log.id is not None
        assert log.user_id == test_user.id
        assert log.endpoint_path == "/api/v1/courses"
        assert log.http_method == "GET"
        assert log.status_code == 200
        assert log.response_time_ms == 45.12
        assert log.timestamp is not None

    def test_usage_log_nullable_user_id(self, db_session):
        """Create a UsageLog with user_id=None (anonymous / unauthenticated request)."""
        log = UsageLog(
            user_id=None,
            endpoint_path="/api/v1/auth/login",
            http_method="POST",
            status_code=200,
            response_time_ms=120.5,
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)

        assert log.id is not None
        assert log.user_id is None
        assert log.endpoint_path == "/api/v1/auth/login"
        assert log.http_method == "POST"
        assert log.status_code == 200
        assert log.response_time_ms == 120.5
