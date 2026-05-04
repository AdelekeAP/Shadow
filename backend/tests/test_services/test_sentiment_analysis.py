"""
Tests for app.services.sentiment_analysis (j-hartmann 7-class emotion model)

Covers:
- analyze_sentiment with disabled model (DISABLE_ML_MODELS=true)
- analyze_sentiment with mocked model (various dominant emotions / confidences)
- get_sentiment_description for every known key + unknown
- batch_analyze_sentiments with disabled and mocked model
"""
import os

os.environ["DISABLE_ML_MODELS"] = "true"
os.environ["TESTING"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

from unittest.mock import patch

from app.services.sentiment_analysis import (
    analyze_sentiment,
    get_sentiment_description,
    batch_analyze_sentiments,
    _model_ready,
)

_model_ready.set()


def _full_distribution(top_label: str, top_score: float):
    """Build a 7-emotion distribution where one label dominates."""
    others = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]
    others.remove(top_label)
    remainder = round((1.0 - top_score) / len(others), 4)
    return [{"label": top_label, "score": top_score}] + [
        {"label": label, "score": remainder} for label in others
    ]


# ---------------------------------------------------------------------------
# analyze_sentiment -- model disabled
# ---------------------------------------------------------------------------

class TestAnalyzeSentimentDisabled:
    def test_empty_string_returns_none(self):
        assert analyze_sentiment("") is None

    def test_whitespace_only_returns_none(self):
        assert analyze_sentiment("   ") is None

    def test_none_input_returns_none(self):
        assert analyze_sentiment(None) is None

    def test_normal_text_returns_none_when_model_disabled(self):
        assert analyze_sentiment("I am feeling great today") is None


# ---------------------------------------------------------------------------
# analyze_sentiment -- model mocked
# ---------------------------------------------------------------------------

class TestAnalyzeSentimentMocked:

    def test_high_confidence_joy_is_positive(self):
        with patch("app.services.sentiment_analysis._sentiment_analyzer") as mock_analyzer, \
             patch("app.services.sentiment_analysis._model_disabled", False):
            mock_analyzer.return_value = _full_distribution("joy", 0.95)
            result = analyze_sentiment("I love this course!")
            assert result is not None
            assert result["primary_emotion"] == "joy"
            assert result["emotion_confidence"] == 0.95
            assert result["sentiment_score"] == 1
            assert result["label"] == "POSITIVE"
            assert "joy" in result["emotion_scores"]
            assert len(result["emotion_scores"]) == 7

    def test_low_confidence_joy_is_neutral_score(self):
        with patch("app.services.sentiment_analysis._sentiment_analyzer") as mock_analyzer, \
             patch("app.services.sentiment_analysis._model_disabled", False):
            mock_analyzer.return_value = _full_distribution("joy", 0.55)
            result = analyze_sentiment("It was okay I guess")
            assert result["primary_emotion"] == "joy"
            assert result["sentiment_score"] == 0  # below 0.7 threshold
            assert result["label"] == "POSITIVE"

    def test_high_confidence_sadness_is_negative(self):
        with patch("app.services.sentiment_analysis._sentiment_analyzer") as mock_analyzer, \
             patch("app.services.sentiment_analysis._model_disabled", False):
            mock_analyzer.return_value = _full_distribution("sadness", 0.92)
            result = analyze_sentiment("This is terrible")
            assert result["primary_emotion"] == "sadness"
            assert result["sentiment_score"] == -1
            assert result["label"] == "NEGATIVE"

    def test_high_confidence_fear_is_negative(self):
        with patch("app.services.sentiment_analysis._sentiment_analyzer") as mock_analyzer, \
             patch("app.services.sentiment_analysis._model_disabled", False):
            mock_analyzer.return_value = _full_distribution("fear", 0.85)
            result = analyze_sentiment("I'm worried about my exam")
            assert result["primary_emotion"] == "fear"
            assert result["sentiment_score"] == -1
            assert result["label"] == "NEGATIVE"

    def test_high_confidence_neutral_returns_neutral_label(self):
        with patch("app.services.sentiment_analysis._sentiment_analyzer") as mock_analyzer, \
             patch("app.services.sentiment_analysis._model_disabled", False):
            mock_analyzer.return_value = _full_distribution("neutral", 0.88)
            result = analyze_sentiment("Just another day")
            assert result["primary_emotion"] == "neutral"
            assert result["sentiment_score"] == 0
            assert result["label"] == "NEUTRAL"

    def test_surprise_is_treated_as_neutral(self):
        with patch("app.services.sentiment_analysis._sentiment_analyzer") as mock_analyzer, \
             patch("app.services.sentiment_analysis._model_disabled", False):
            mock_analyzer.return_value = _full_distribution("surprise", 0.9)
            result = analyze_sentiment("Wow, did not expect that")
            assert result["primary_emotion"] == "surprise"
            assert result["sentiment_score"] == 0
            assert result["label"] == "NEUTRAL"

    def test_emotion_scores_contains_all_seven_labels(self):
        with patch("app.services.sentiment_analysis._sentiment_analyzer") as mock_analyzer, \
             patch("app.services.sentiment_analysis._model_disabled", False):
            mock_analyzer.return_value = _full_distribution("anger", 0.8)
            result = analyze_sentiment("I'm furious")
            expected = {"anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"}
            assert set(result["emotion_scores"].keys()) == expected

    def test_pipeline_returning_batched_list_is_unwrapped(self):
        """Some transformers versions wrap the per-input list in another list."""
        with patch("app.services.sentiment_analysis._sentiment_analyzer") as mock_analyzer, \
             patch("app.services.sentiment_analysis._model_disabled", False):
            mock_analyzer.return_value = [_full_distribution("joy", 0.9)]
            result = analyze_sentiment("Happy day")
            assert result is not None
            assert result["primary_emotion"] == "joy"

    def test_exception_in_model_returns_none(self):
        with patch("app.services.sentiment_analysis._sentiment_analyzer") as mock_analyzer, \
             patch("app.services.sentiment_analysis._model_disabled", False):
            mock_analyzer.side_effect = RuntimeError("Model crashed")
            assert analyze_sentiment("Some text here") is None

    def test_long_text_is_truncated_before_model_call(self):
        long_text = "x" * 1000
        with patch("app.services.sentiment_analysis._sentiment_analyzer") as mock_analyzer, \
             patch("app.services.sentiment_analysis._model_disabled", False):
            mock_analyzer.return_value = _full_distribution("joy", 0.8)
            analyze_sentiment(long_text)
            mock_analyzer.assert_called_once()
            call_arg = mock_analyzer.call_args[0][0]
            assert len(call_arg) == 512

    def test_boundary_confidence_exactly_0_7_is_neutral(self):
        """Confidence == 0.7 is NOT > 0.7, so score should be 0 (neutral)."""
        with patch("app.services.sentiment_analysis._sentiment_analyzer") as mock_analyzer, \
             patch("app.services.sentiment_analysis._model_disabled", False):
            mock_analyzer.return_value = _full_distribution("joy", 0.7)
            result = analyze_sentiment("boundary test")
            assert result["sentiment_score"] == 0


# ---------------------------------------------------------------------------
# get_sentiment_description
# ---------------------------------------------------------------------------

class TestGetSentimentDescription:

    def test_negative(self):
        assert get_sentiment_description(-1) == "Negative sentiment detected"

    def test_neutral(self):
        assert get_sentiment_description(0) == "Neutral sentiment"

    def test_positive(self):
        assert get_sentiment_description(1) == "Positive sentiment detected"

    def test_unknown_value(self):
        assert get_sentiment_description(42) == "Unknown sentiment"


# ---------------------------------------------------------------------------
# batch_analyze_sentiments
# ---------------------------------------------------------------------------

class TestBatchAnalyzeSentiments:

    def test_disabled_model_returns_list_of_nones(self):
        results = batch_analyze_sentiments(["hello", "world", "test"])
        assert results == [None, None, None]

    def test_mocked_model_processes_each_text(self):
        with patch("app.services.sentiment_analysis._sentiment_analyzer") as mock_analyzer, \
             patch("app.services.sentiment_analysis._model_disabled", False):
            mock_analyzer.return_value = _full_distribution("joy", 0.9)
            results = batch_analyze_sentiments(["great", "awesome"])
            assert len(results) == 2
            for r in results:
                assert r is not None
                assert r["primary_emotion"] == "joy"
                assert r["sentiment_score"] == 1

    def test_empty_list_returns_empty(self):
        assert batch_analyze_sentiments([]) == []
