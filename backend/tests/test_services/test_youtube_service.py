"""
Tests for YouTube Service
backend/app/services/youtube_service.py

Tests initialization, disabled-state behavior, and the pure _parse_video_data method.
"""
import os
import pytest
from unittest.mock import patch

from app.services.youtube_service import YouTubeService


def _no_key_service():
    """Create a YouTubeService with no API key, regardless of env vars."""
    with patch.dict(os.environ, {}, clear=False):
        # Remove YOUTUBE_API_KEY from env if present
        env_copy = os.environ.copy()
        env_copy.pop("YOUTUBE_API_KEY", None)
        with patch.dict(os.environ, env_copy, clear=True):
            return YouTubeService(api_key=None)


class TestYouTubeServiceInit:

    def test_init_without_api_key(self):
        service = _no_key_service()
        assert service.youtube is None

    def test_search_returns_empty_without_api_key(self):
        service = _no_key_service()
        result = service.search_videos("python tutorial")
        assert result == []

    def test_get_comments_returns_empty_without_api_key(self):
        service = _no_key_service()
        result = service.get_video_comments("dQw4w9WgXcQ")
        assert result == []


class TestParseVideoData:

    def _make_service(self):
        """Create service for parse tests (no API key needed for _parse_video_data)."""
        return _no_key_service()

    def test_full_video_data(self):
        service = self._make_service()
        item = {
            "id": "abc123",
            "snippet": {
                "title": "Learn BST",
                "description": "BST tutorial",
                "channelTitle": "CS Channel",
                "publishedAt": "2025-01-01T00:00:00Z",
                "thumbnails": {"high": {"url": "https://img.youtube.com/vi/abc123/hqdefault.jpg"}},
            },
            "statistics": {"viewCount": "1000", "likeCount": "100", "commentCount": "10"},
            "contentDetails": {"duration": "PT10M30S"},
        }
        result = service._parse_video_data(item)
        assert result["video_id"] == "abc123"
        assert result["title"] == "Learn BST"
        assert result["view_count"] == 1000
        assert result["like_count"] == 100
        assert result["like_view_ratio"] == 10.0
        assert result["url"] == "https://www.youtube.com/watch?v=abc123"

    def test_zero_views(self):
        service = self._make_service()
        item = {
            "id": "xyz789",
            "snippet": {"title": "New Video", "description": "", "channelTitle": "", "publishedAt": "", "thumbnails": {}},
            "statistics": {"viewCount": "0", "likeCount": "0", "commentCount": "0"},
            "contentDetails": {},
        }
        result = service._parse_video_data(item)
        assert result["like_view_ratio"] == 0
        assert result["comment_view_ratio"] == 0

    def test_missing_statistics(self):
        service = self._make_service()
        item = {
            "id": "test1",
            "snippet": {"title": "Test", "description": "", "channelTitle": "", "publishedAt": "", "thumbnails": {}},
        }
        result = service._parse_video_data(item)
        assert result["view_count"] == 0
        assert result["like_count"] == 0

    def test_comment_view_ratio_calculation(self):
        service = self._make_service()
        item = {
            "id": "ratio1",
            "snippet": {"title": "Ratio", "description": "", "channelTitle": "", "publishedAt": "", "thumbnails": {}},
            "statistics": {"viewCount": "200", "likeCount": "10", "commentCount": "4"},
            "contentDetails": {},
        }
        result = service._parse_video_data(item)
        assert result["comment_view_ratio"] == 2.0  # 4/200 * 100

    def test_thumbnail_url_extracted(self):
        service = self._make_service()
        item = {
            "id": "thumb1",
            "snippet": {
                "title": "T", "description": "", "channelTitle": "", "publishedAt": "",
                "thumbnails": {"high": {"url": "https://example.com/thumb.jpg"}},
            },
            "statistics": {},
            "contentDetails": {},
        }
        result = service._parse_video_data(item)
        assert result["thumbnail_url"] == "https://example.com/thumb.jpg"


class TestAnalyzeCommentSentiment:

    def _make_service(self):
        return _no_key_service()

    def test_empty_comments(self):
        service = self._make_service()
        result = service.analyze_comment_sentiment([])
        assert result["positive_count"] == 0
        assert result["quality_score"] == 0

    def test_positive_comments(self):
        service = self._make_service()
        comments = [
            {"text": "This is a great tutorial!"},
            {"text": "Excellent explanation, thank you!"},
        ]
        result = service.analyze_comment_sentiment(comments)
        assert result["positive_count"] == 2
        assert result["positive_percentage"] == 100.0

    def test_negative_comments(self):
        service = self._make_service()
        comments = [
            {"text": "This is terrible and confusing"},
            {"text": "Waste of time"},
        ]
        result = service.analyze_comment_sentiment(comments)
        assert result["negative_count"] == 2
        assert result["positive_count"] == 0

    def test_mixed_comments(self):
        service = self._make_service()
        comments = [
            {"text": "Great video!"},
            {"text": "This is terrible"},
            {"text": "Just a normal comment"},
        ]
        result = service.analyze_comment_sentiment(comments)
        assert result["positive_count"] == 1
        assert result["negative_count"] == 1
        assert result["neutral_count"] == 1
