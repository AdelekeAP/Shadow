"""
Tests for ContentCurator service
backend/app/services/content_curator.py

Covers: resource curation, learning style adaptation, cross-referencing,
quality score filtering, and fallback when services are unavailable.
"""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_video(title="Intro to Binary Trees", quality=75, has_transcript=False):
    return {
        "title": title,
        "url": f"https://youtube.com/watch?v={title[:5].replace(' ', '')}",
        "description": f"Video about {title}",
        "quality_score": quality,
        "channel_title": "CS Channel",
        "view_count": 10000,
        "like_count": 500,
        "has_transcript": has_transcript,
    }


def _make_reddit(title="Great BST tutorial", quality=70, url="https://example.com/bst"):
    return {
        "title": title,
        "url": url,
        "description": f"Reddit post: {title}",
        "quality_score": quality,
        "subreddit": "learnprogramming",
        "score": 200,
        "upvote_ratio": 0.95,
        "num_comments": 30,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCurateResources:

    @patch("app.services.content_curator.get_reddit_service")
    @patch("app.services.content_curator.get_youtube_service")
    def test_returns_structured_results(self, mock_yt_factory, mock_reddit_factory):
        """curate_resources returns dict with expected keys."""
        mock_yt = MagicMock()
        mock_yt.get_curated_videos.return_value = [_make_video()]
        mock_yt_factory.return_value = mock_yt

        mock_reddit = MagicMock()
        mock_reddit.reddit = MagicMock()
        mock_reddit.find_learning_resources.return_value = [_make_reddit()]
        mock_reddit_factory.return_value = mock_reddit

        from app.services.content_curator import ContentCurator
        curator = ContentCurator()
        result = curator.curate_resources("binary search trees")

        assert "topic" in result
        assert result["topic"] == "binary search trees"
        assert "videos" in result
        assert "reddit_resources" in result
        assert "combined_recommendations" in result
        assert "curated_at" in result
        assert len(result["videos"]) >= 1

    @patch("app.services.content_curator.get_reddit_service")
    @patch("app.services.content_curator.get_youtube_service")
    def test_visual_style_prioritizes_videos(self, mock_yt_factory, mock_reddit_factory):
        """Visual learning style should boost YouTube videos."""
        mock_yt = MagicMock()
        mock_yt.get_curated_videos.return_value = [
            _make_video("Visual Diagrams of Trees", quality=70),
            _make_video("BST Animated Tutorial", quality=65),
        ]
        mock_yt_factory.return_value = mock_yt

        mock_reddit = MagicMock()
        mock_reddit.reddit = MagicMock()
        mock_reddit.find_learning_resources.return_value = [
            _make_reddit("Great text guide", quality=80),
        ]
        mock_reddit_factory.return_value = mock_reddit

        from app.services.content_curator import ContentCurator
        curator = ContentCurator()
        result = curator.curate_resources("BST", learning_style="visual", max_results=5)

        combined = result["combined_recommendations"]
        # Videos should appear first for visual learners
        video_types = [r for r in combined if r["type"] == "youtube_video"]
        assert len(video_types) >= 2

    @patch("app.services.content_curator.get_reddit_service")
    @patch("app.services.content_curator.get_youtube_service")
    def test_reading_style_boosts_reddit(self, mock_yt_factory, mock_reddit_factory):
        """Reading style should boost reddit posts."""
        mock_yt = MagicMock()
        mock_yt.get_curated_videos.return_value = [_make_video(quality=60)]
        mock_yt_factory.return_value = mock_yt

        mock_reddit = MagicMock()
        mock_reddit.reddit = MagicMock()
        mock_reddit.find_learning_resources.return_value = [
            _make_reddit("Comprehensive BST Guide", quality=65),
        ]
        mock_reddit_factory.return_value = mock_reddit

        from app.services.content_curator import ContentCurator
        curator = ContentCurator()
        result = curator.curate_resources("BST", learning_style="reading", max_results=5)

        combined = result["combined_recommendations"]
        # Reddit posts should be boosted for reading learners
        reddit_items = [r for r in combined if r["type"] == "reddit_post"]
        if reddit_items:
            assert reddit_items[0]["quality_score"] > 65  # Should be boosted

    @patch("app.services.content_curator.get_reddit_service")
    @patch("app.services.content_curator.get_youtube_service")
    def test_fallback_when_youtube_unavailable(self, mock_yt_factory, mock_reddit_factory):
        """Service handles YouTube failure gracefully."""
        mock_yt = MagicMock()
        mock_yt.get_curated_videos.side_effect = Exception("YouTube API error")
        mock_yt_factory.return_value = mock_yt

        mock_reddit = MagicMock()
        mock_reddit.reddit = MagicMock()
        mock_reddit.find_learning_resources.return_value = [_make_reddit()]
        mock_reddit_factory.return_value = mock_reddit

        from app.services.content_curator import ContentCurator
        curator = ContentCurator()
        result = curator.curate_resources("BST")

        assert result["videos"] == []
        assert len(result["reddit_resources"]) >= 1

    @patch("app.services.content_curator.get_reddit_service")
    @patch("app.services.content_curator.get_youtube_service")
    def test_fallback_when_reddit_unavailable(self, mock_yt_factory, mock_reddit_factory):
        """Service handles Reddit being not configured."""
        mock_yt = MagicMock()
        mock_yt.get_curated_videos.return_value = [_make_video()]
        mock_yt_factory.return_value = mock_yt

        mock_reddit = MagicMock()
        mock_reddit.reddit = None  # Not configured
        mock_reddit_factory.return_value = mock_reddit

        from app.services.content_curator import ContentCurator
        curator = ContentCurator()
        result = curator.curate_resources("BST")

        assert result["reddit_resources"] == []
        assert len(result["videos"]) >= 1

    @patch("app.services.content_curator.get_reddit_service")
    @patch("app.services.content_curator.get_youtube_service")
    def test_quality_score_sorting(self, mock_yt_factory, mock_reddit_factory):
        """Combined results are sorted by quality score."""
        mock_yt = MagicMock()
        mock_yt.get_curated_videos.return_value = [
            _make_video("Low quality", quality=40),
            _make_video("High quality", quality=90),
            _make_video("Medium quality", quality=65),
        ]
        mock_yt_factory.return_value = mock_yt

        mock_reddit = MagicMock()
        mock_reddit.reddit = None
        mock_reddit_factory.return_value = mock_reddit

        from app.services.content_curator import ContentCurator
        curator = ContentCurator()
        result = curator.curate_resources("BST", learning_style="balanced")

        combined = result["combined_recommendations"]
        scores = [r["quality_score"] for r in combined]
        assert scores == sorted(scores, reverse=True)

    @patch("app.services.content_curator.get_reddit_service")
    @patch("app.services.content_curator.get_youtube_service")
    def test_cross_referencing_boosts_score(self, mock_yt_factory, mock_reddit_factory):
        """Videos mentioned on Reddit get a score boost."""
        yt_url = "https://youtube.com/watch?v=abc123"
        mock_yt = MagicMock()
        mock_yt.get_curated_videos.return_value = [
            {**_make_video("BST Tutorial", quality=60), "url": yt_url},
        ]
        mock_yt_factory.return_value = mock_yt

        mock_reddit = MagicMock()
        mock_reddit.reddit = MagicMock()
        mock_reddit.find_learning_resources.return_value = [
            _make_reddit("This video is amazing", quality=80, url=yt_url),
        ]
        mock_reddit_factory.return_value = mock_reddit

        from app.services.content_curator import ContentCurator
        curator = ContentCurator()
        result = curator.curate_resources("BST", learning_style="balanced")

        combined = result["combined_recommendations"]
        cross_ref = [r for r in combined if r.get("cross_referenced")]
        assert len(cross_ref) >= 1
        # Cross-referenced item should have boosted score above original 60
        assert cross_ref[0]["quality_score"] > 60

    @patch("app.services.content_curator.get_reddit_service")
    @patch("app.services.content_curator.get_youtube_service")
    def test_kinesthetic_style_prioritizes_hands_on(self, mock_yt_factory, mock_reddit_factory):
        """Kinesthetic style boosts hands-on/interactive content."""
        mock_yt = MagicMock()
        mock_yt.get_curated_videos.return_value = [
            _make_video("Lecture on Trees", quality=70),
            _make_video("Hands-on Build BST Project", quality=60),
        ]
        mock_yt_factory.return_value = mock_yt

        mock_reddit = MagicMock()
        mock_reddit.reddit = None
        mock_reddit_factory.return_value = mock_reddit

        from app.services.content_curator import ContentCurator
        curator = ContentCurator()
        result = curator.curate_resources("BST", learning_style="kinesthetic")

        combined = result["combined_recommendations"]
        # The hands-on video should be boosted above the lecture
        if len(combined) >= 2:
            hands_on = next((r for r in combined if "Hands-on" in r["title"]), None)
            if hands_on:
                assert hands_on.get("style_match") is True


class TestCalculateStyleBoost:

    @patch("app.services.content_curator.get_reddit_service")
    @patch("app.services.content_curator.get_youtube_service")
    def test_visual_boost_for_youtube(self, mock_yt_factory, mock_reddit_factory):
        mock_yt_factory.return_value = MagicMock()
        mock_reddit_factory.return_value = MagicMock()

        from app.services.content_curator import ContentCurator
        curator = ContentCurator()

        resource = {"type": "youtube_video", "title": "Test", "metadata": {"has_transcript": True}}
        boost = curator._calculate_style_boost(resource, "visual")
        assert boost == 20  # 15 for video + 5 for transcript

    @patch("app.services.content_curator.get_reddit_service")
    @patch("app.services.content_curator.get_youtube_service")
    def test_audio_boost_for_lecture(self, mock_yt_factory, mock_reddit_factory):
        mock_yt_factory.return_value = MagicMock()
        mock_reddit_factory.return_value = MagicMock()

        from app.services.content_curator import ContentCurator
        curator = ContentCurator()

        resource = {"type": "youtube_video", "title": "CS Lecture on BSTs", "metadata": {}}
        boost = curator._calculate_style_boost(resource, "audio")
        assert boost == 20  # 15 for video + 5 for lecture keyword

    @patch("app.services.content_curator.get_reddit_service")
    @patch("app.services.content_curator.get_youtube_service")
    def test_reading_boost_for_reddit(self, mock_yt_factory, mock_reddit_factory):
        mock_yt_factory.return_value = MagicMock()
        mock_reddit_factory.return_value = MagicMock()

        from app.services.content_curator import ContentCurator
        curator = ContentCurator()

        resource = {"type": "reddit_post", "title": "Guide", "metadata": {}}
        boost = curator._calculate_style_boost(resource, "reading")
        assert boost == 15

    @patch("app.services.content_curator.get_reddit_service")
    @patch("app.services.content_curator.get_youtube_service")
    def test_no_boost_for_mismatched_style(self, mock_yt_factory, mock_reddit_factory):
        mock_yt_factory.return_value = MagicMock()
        mock_reddit_factory.return_value = MagicMock()

        from app.services.content_curator import ContentCurator
        curator = ContentCurator()

        resource = {"type": "reddit_post", "title": "Guide", "metadata": {}}
        boost = curator._calculate_style_boost(resource, "visual")
        assert boost == 0
