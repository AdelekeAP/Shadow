"""
Tests for Token Blacklist Utilities
backend/app/utils/token_blacklist.py

Tests the in-memory blacklist fallback: adding tokens, checking status,
and automatic cleanup of expired entries.
"""
import pytest
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("TESTING", "true")

from app.utils.token_blacklist import (
    blacklist_token,
    is_blacklisted,
    _blacklist,
    _cleanup,
)


@pytest.fixture(autouse=True)
def clear_blacklist():
    """Clear the in-memory blacklist before and after each test."""
    _blacklist.clear()
    yield
    _blacklist.clear()


# ===================================================================
# blacklist_token
# ===================================================================

class TestBlacklistToken:

    @patch("app.utils.token_blacklist._get_redis", return_value=None)
    def test_blacklist_token_adds_to_memory(self, mock_redis):
        """A blacklisted token should be stored in the in-memory dict."""
        token = "test-token-abc"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        blacklist_token(token, expires_at)

        assert len(_blacklist) == 1

    @patch("app.utils.token_blacklist._get_redis", return_value=None)
    def test_blacklist_already_expired_token_is_ignored(self, mock_redis):
        """A token whose expiry is in the past should not be added."""
        token = "expired-token"
        expires_at = datetime.now(timezone.utc) - timedelta(seconds=10)

        blacklist_token(token, expires_at)

        assert len(_blacklist) == 0

    @patch("app.utils.token_blacklist._get_redis", return_value=None)
    def test_blacklist_multiple_tokens(self, mock_redis):
        """Multiple different tokens can be blacklisted independently."""
        expires = datetime.now(timezone.utc) + timedelta(hours=1)

        blacklist_token("token-1", expires)
        blacklist_token("token-2", expires)
        blacklist_token("token-3", expires)

        assert len(_blacklist) == 3

    @patch("app.utils.token_blacklist._get_redis", return_value=None)
    def test_blacklist_same_token_twice_is_idempotent(self, mock_redis):
        """Blacklisting the same token twice should only store one entry."""
        expires = datetime.now(timezone.utc) + timedelta(hours=1)

        blacklist_token("same-token", expires)
        blacklist_token("same-token", expires)

        # Same hash -> same key, so still 1 entry
        assert len(_blacklist) == 1


# ===================================================================
# is_blacklisted
# ===================================================================

class TestIsBlacklisted:

    @patch("app.utils.token_blacklist._get_redis", return_value=None)
    def test_blacklisted_token_is_detected(self, mock_redis):
        """A blacklisted token should be reported as blacklisted."""
        token = "revoked-token"
        expires = datetime.now(timezone.utc) + timedelta(hours=1)

        blacklist_token(token, expires)

        assert is_blacklisted(token) is True

    @patch("app.utils.token_blacklist._get_redis", return_value=None)
    def test_non_blacklisted_token_is_not_detected(self, mock_redis):
        """A token that was never blacklisted should return False."""
        assert is_blacklisted("never-blacklisted") is False

    @patch("app.utils.token_blacklist._get_redis", return_value=None)
    def test_expired_blacklist_entry_is_not_detected(self, mock_redis):
        """A blacklist entry whose expiry has passed should return False."""
        import hashlib

        token = "soon-expired-token"
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Manually insert an already-expired entry
        _blacklist[token_hash] = datetime.now(timezone.utc) - timedelta(seconds=1)

        assert is_blacklisted(token) is False

    @patch("app.utils.token_blacklist._get_redis", return_value=None)
    def test_different_token_not_affected(self, mock_redis):
        """Blacklisting token A should not affect token B."""
        expires = datetime.now(timezone.utc) + timedelta(hours=1)

        blacklist_token("token-a", expires)

        assert is_blacklisted("token-a") is True
        assert is_blacklisted("token-b") is False


# ===================================================================
# _cleanup
# ===================================================================

class TestCleanup:

    def test_cleanup_removes_expired_entries(self):
        """Expired entries should be removed by _cleanup."""
        import hashlib

        # Add one expired and one valid entry
        expired_hash = hashlib.sha256(b"expired").hexdigest()
        valid_hash = hashlib.sha256(b"valid").hexdigest()

        _blacklist[expired_hash] = datetime.now(timezone.utc) - timedelta(hours=1)
        _blacklist[valid_hash] = datetime.now(timezone.utc) + timedelta(hours=1)

        assert len(_blacklist) == 2

        _cleanup()

        assert len(_blacklist) == 1
        assert valid_hash in _blacklist
        assert expired_hash not in _blacklist

    def test_cleanup_on_empty_blacklist(self):
        """Cleanup on an empty blacklist should not raise."""
        _cleanup()
        assert len(_blacklist) == 0

    def test_cleanup_removes_all_when_all_expired(self):
        """If all entries are expired, cleanup should empty the dict."""
        import hashlib

        for i in range(5):
            h = hashlib.sha256(f"token-{i}".encode()).hexdigest()
            _blacklist[h] = datetime.now(timezone.utc) - timedelta(minutes=i + 1)

        assert len(_blacklist) == 5

        _cleanup()

        assert len(_blacklist) == 0

    @patch("app.utils.token_blacklist._get_redis", return_value=None)
    def test_cleanup_triggered_on_blacklist_add(self, mock_redis):
        """Adding a token via blacklist_token should trigger cleanup of expired entries."""
        import hashlib

        # Pre-seed an expired entry
        expired_hash = hashlib.sha256(b"old-token").hexdigest()
        _blacklist[expired_hash] = datetime.now(timezone.utc) - timedelta(hours=1)

        # Adding a new token should trigger _cleanup internally
        blacklist_token("new-token", datetime.now(timezone.utc) + timedelta(hours=1))

        # The expired entry should have been cleaned up
        assert expired_hash not in _blacklist
        # The new entry should be present
        assert len(_blacklist) == 1
