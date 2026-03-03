"""
Tests for Cache Service
backend/app/services/cache_service.py

Tests Redis caching layer with mocked Redis client, covering round-trip
serialization, TTL handling, graceful fallback, and disabled-state behavior.
"""
import json
import pytest
from unittest.mock import patch, MagicMock, call


# ---------------------------------------------------------------------------
# 1. cache_get returns None when Redis is unavailable
# ---------------------------------------------------------------------------

class TestCacheGetUnavailable:

    def test_returns_none_when_redis_unavailable(self):
        """cache_get returns None when _get_redis() yields None."""
        with patch("app.services.cache_service._get_redis", return_value=None):
            from app.services.cache_service import cache_get
            result = cache_get("some:key")
            assert result is None


# ---------------------------------------------------------------------------
# 2. cache_set returns False when Redis is unavailable
# ---------------------------------------------------------------------------

class TestCacheSetUnavailable:

    def test_returns_false_when_redis_unavailable(self):
        """cache_set returns False when _get_redis() yields None."""
        with patch("app.services.cache_service._get_redis", return_value=None):
            from app.services.cache_service import cache_set
            result = cache_set("some:key", {"data": 1}, 300)
            assert result is False


# ---------------------------------------------------------------------------
# 3. Mocked Redis round-trip (set then get)
# ---------------------------------------------------------------------------

class TestCacheRoundTrip:

    def test_set_then_get_returns_original_value(self):
        """Values stored via cache_set can be retrieved via cache_get."""
        store = {}
        mock_redis = MagicMock()

        def fake_setex(key, ttl, value):
            store[key] = value

        def fake_get(key):
            return store.get(key)

        mock_redis.setex.side_effect = fake_setex
        mock_redis.get.side_effect = fake_get

        with patch("app.services.cache_service._get_redis", return_value=mock_redis):
            from app.services.cache_service import cache_set, cache_get

            payload = {"total": 42, "items": [1, 2, 3]}
            cache_set("test:roundtrip", payload, 600)
            retrieved = cache_get("test:roundtrip")

            assert retrieved == payload


# ---------------------------------------------------------------------------
# 4. TTL is passed correctly to Redis
# ---------------------------------------------------------------------------

class TestCacheTTL:

    def test_ttl_passed_to_setex(self):
        """cache_set forwards the TTL value to Redis SETEX."""
        mock_redis = MagicMock()
        with patch("app.services.cache_service._get_redis", return_value=mock_redis):
            from app.services.cache_service import cache_set

            cache_set("key:ttl", {"v": 1}, 120)
            mock_redis.setex.assert_called_once()
            args = mock_redis.setex.call_args
            # setex(key, ttl, value)
            assert args[0][0] == "key:ttl"
            assert args[0][1] == 120

    def test_default_ttl_is_analytics(self):
        """cache_set uses TTL_ANALYTICS (300) as the default TTL."""
        mock_redis = MagicMock()
        with patch("app.services.cache_service._get_redis", return_value=mock_redis):
            from app.services.cache_service import cache_set, TTL_ANALYTICS

            cache_set("key:default", {"v": 1})
            args = mock_redis.setex.call_args
            assert args[0][1] == TTL_ANALYTICS


# ---------------------------------------------------------------------------
# 5. cache_delete works
# ---------------------------------------------------------------------------

class TestCacheDelete:

    def test_delete_calls_redis_delete(self):
        """cache_delete invokes Redis DEL on the given key."""
        mock_redis = MagicMock()
        with patch("app.services.cache_service._get_redis", return_value=mock_redis):
            from app.services.cache_service import cache_delete

            result = cache_delete("key:to:remove")
            assert result is True
            mock_redis.delete.assert_called_once_with("key:to:remove")

    def test_delete_returns_false_when_unavailable(self):
        """cache_delete returns False when Redis is unavailable."""
        with patch("app.services.cache_service._get_redis", return_value=None):
            from app.services.cache_service import cache_delete

            result = cache_delete("key:to:remove")
            assert result is False


# ---------------------------------------------------------------------------
# 6. cache_delete_pattern works
# ---------------------------------------------------------------------------

class TestCacheDeletePattern:

    def test_delete_pattern_scans_and_deletes(self):
        """cache_delete_pattern uses SCAN + DELETE to remove matching keys."""
        mock_redis = MagicMock()
        # Simulate one SCAN pass that returns keys, then cursor=0
        mock_redis.scan.return_value = (0, ["analytics:user1:a", "analytics:user1:b"])

        with patch("app.services.cache_service._get_redis", return_value=mock_redis):
            from app.services.cache_service import cache_delete_pattern

            result = cache_delete_pattern("analytics:user1:*")
            assert result is True
            mock_redis.scan.assert_called_once_with(cursor=0, match="analytics:user1:*", count=100)
            mock_redis.delete.assert_called_once_with("analytics:user1:a", "analytics:user1:b")

    def test_delete_pattern_returns_false_when_unavailable(self):
        """cache_delete_pattern returns False when Redis is unavailable."""
        with patch("app.services.cache_service._get_redis", return_value=None):
            from app.services.cache_service import cache_delete_pattern

            result = cache_delete_pattern("some:*")
            assert result is False


# ---------------------------------------------------------------------------
# 7. Graceful error handling on connection failure
# ---------------------------------------------------------------------------

class TestGracefulErrorHandling:

    def test_cache_get_handles_exception(self):
        """cache_get returns None when Redis raises an exception."""
        mock_redis = MagicMock()
        mock_redis.get.side_effect = ConnectionError("Connection refused")

        with patch("app.services.cache_service._get_redis", return_value=mock_redis):
            from app.services.cache_service import cache_get

            result = cache_get("broken:key")
            assert result is None

    def test_cache_set_handles_exception(self):
        """cache_set returns False when Redis raises an exception."""
        mock_redis = MagicMock()
        mock_redis.setex.side_effect = ConnectionError("Connection refused")

        with patch("app.services.cache_service._get_redis", return_value=mock_redis):
            from app.services.cache_service import cache_set

            result = cache_set("broken:key", {"v": 1}, 60)
            assert result is False

    def test_cache_delete_handles_exception(self):
        """cache_delete returns False when Redis raises an exception."""
        mock_redis = MagicMock()
        mock_redis.delete.side_effect = ConnectionError("Connection refused")

        with patch("app.services.cache_service._get_redis", return_value=mock_redis):
            from app.services.cache_service import cache_delete

            result = cache_delete("broken:key")
            assert result is False

    def test_cache_delete_pattern_handles_exception(self):
        """cache_delete_pattern returns False when Redis raises an exception."""
        mock_redis = MagicMock()
        mock_redis.scan.side_effect = ConnectionError("Connection refused")

        with patch("app.services.cache_service._get_redis", return_value=mock_redis):
            from app.services.cache_service import cache_delete_pattern

            result = cache_delete_pattern("broken:*")
            assert result is False


# ---------------------------------------------------------------------------
# 8. REDIS_ENABLED=false disables caching
# ---------------------------------------------------------------------------

class TestRedisDisabled:

    def test_get_redis_returns_none_when_disabled(self):
        """_get_redis returns None when REDIS_ENABLED is 'false'."""
        with patch("app.services.cache_service.REDIS_ENABLED", False):
            from app.services.cache_service import _get_redis

            result = _get_redis()
            assert result is None

    def test_cache_set_returns_false_when_disabled(self):
        """cache_set returns False when Redis is disabled via flag."""
        with patch("app.services.cache_service.REDIS_ENABLED", False), \
             patch("app.services.cache_service._redis_client", None):
            from app.services.cache_service import cache_set

            result = cache_set("key", {"data": 1}, 300)
            assert result is False

    def test_cache_get_returns_none_when_disabled(self):
        """cache_get returns None when Redis is disabled via flag."""
        with patch("app.services.cache_service.REDIS_ENABLED", False), \
             patch("app.services.cache_service._redis_client", None):
            from app.services.cache_service import cache_get

            result = cache_get("key")
            assert result is None


# ---------------------------------------------------------------------------
# 9. cache_get returns None for missing keys
# ---------------------------------------------------------------------------

class TestCacheMiss:

    def test_returns_none_for_missing_key(self):
        """cache_get returns None when the key does not exist in Redis."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        with patch("app.services.cache_service._get_redis", return_value=mock_redis):
            from app.services.cache_service import cache_get

            result = cache_get("nonexistent:key")
            assert result is None
            mock_redis.get.assert_called_once_with("nonexistent:key")


# ---------------------------------------------------------------------------
# 10. JSON serialization round-trip
# ---------------------------------------------------------------------------

class TestJSONSerialization:

    def test_complex_data_survives_serialization(self):
        """Nested dicts, lists, and numeric types survive JSON round-trip."""
        store = {}
        mock_redis = MagicMock()

        def fake_setex(key, ttl, value):
            store[key] = value

        def fake_get(key):
            return store.get(key)

        mock_redis.setex.side_effect = fake_setex
        mock_redis.get.side_effect = fake_get

        with patch("app.services.cache_service._get_redis", return_value=mock_redis):
            from app.services.cache_service import cache_set, cache_get

            payload = {
                "summary": {
                    "total_study_plans": 12,
                    "average_improvement": 8.45,
                    "positive_improvements": 6,
                },
                "engagement": {
                    "engagement_rate": 72.9,
                    "items": [1, 2, 3],
                },
                "nullable_field": None,
                "flag": True,
            }

            cache_set("json:test", payload, 300)
            retrieved = cache_get("json:test")

            assert retrieved == payload
            assert isinstance(retrieved["summary"]["total_study_plans"], int)
            assert isinstance(retrieved["summary"]["average_improvement"], float)
            assert retrieved["nullable_field"] is None
            assert retrieved["flag"] is True

    def test_stored_value_is_valid_json(self):
        """Verify the value stored in Redis is valid JSON."""
        mock_redis = MagicMock()
        with patch("app.services.cache_service._get_redis", return_value=mock_redis):
            from app.services.cache_service import cache_set

            data = {"key": "value", "num": 42}
            cache_set("json:valid", data, 60)

            stored_value = mock_redis.setex.call_args[0][2]
            parsed = json.loads(stored_value)
            assert parsed == data
