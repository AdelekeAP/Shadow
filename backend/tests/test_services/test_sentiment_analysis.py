"""
Tests for app.services.sentiment_analysis

Covers:
- analyze_sentiment with disabled model (DISABLE_ML_MODELS=true)
- analyze_sentiment with mocked model (various confidence / label combos)
- get_sentiment_description for every known key + unknown
- batch_analyze_sentiments with disabled and mocked model
"""
import os

os.environ["DISABLE_ML_MODELS"] = "true"
os.environ["TESTING"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

from unittest.mock import patch, MagicMock

from app.services.sentiment_analysis import (
    analyze_sentiment,
    get_sentiment_description,
    batch_analyze_sentiments,
)


# ---------------------------------------------------------------------------
# analyze_sentiment -- model disabled (sentiment_analyzer is None)
# ---------------------------------------------------------------------------

class TestAnalyzeSentimentDisabled:
    """When DISABLE_ML_MODELS=true the module-level sentiment_analyzer is None."""

    def test_empty_string_returns_none(self):
        assert analyze_sentiment("") is None

    def test_whitespace_only_returns_none(self):
        assert analyze_sentiment("   ") is None

    def test_none_input_returns_none(self):
        assert analyze_sentiment(None) is None

    def test_normal_text_returns_none_when_model_disabled(self):
        result = analyze_sentiment("I am feeling great today")
        assert result is None


# ---------------------------------------------------------------------------
# analyze_sentiment -- model mocked
# ---------------------------------------------------------------------------

class TestAnalyzeSentimentMocked:
    """Mock the module-level sentiment_analyzer to simulate a loaded model."""

    def test_high_confidence_positive(self):
        with patch("app.services.sentiment_analysis.sentiment_analyzer") as mock_analyzer:
            mock_analyzer.return_value = [{"label": "POSITIVE", "score": 0.95}]
            result = analyze_sentiment("I love this course!")
            assert result is not None
            assert result["sentiment_score"] == 1
            assert result["confidence"] == 0.95
            assert result["label"] == "POSITIVE"

    def test_low_confidence_positive_returns_neutral(self):
        with patch("app.services.sentiment_analysis.sentiment_analyzer") as mock_analyzer:
            mock_analyzer.return_value = [{"label": "POSITIVE", "score": 0.55}]
            result = analyze_sentiment("It was okay I guess")
            assert result is not None
            assert result["sentiment_score"] == 0
            assert result["confidence"] == 0.55
            assert result["label"] == "POSITIVE"

    def test_high_confidence_negative(self):
        with patch("app.services.sentiment_analysis.sentiment_analyzer") as mock_analyzer:
            mock_analyzer.return_value = [{"label": "NEGATIVE", "score": 0.92}]
            result = analyze_sentiment("This is terrible")
            assert result is not None
            assert result["sentiment_score"] == -1
            assert result["confidence"] == 0.92
            assert result["label"] == "NEGATIVE"

    def test_low_confidence_negative_returns_neutral(self):
        with patch("app.services.sentiment_analysis.sentiment_analyzer") as mock_analyzer:
            mock_analyzer.return_value = [{"label": "NEGATIVE", "score": 0.6}]
            result = analyze_sentiment("Meh, not the best")
            assert result is not None
            assert result["sentiment_score"] == 0
            assert result["confidence"] == 0.6
            assert result["label"] == "NEGATIVE"

    def test_exception_in_model_returns_none(self):
        with patch("app.services.sentiment_analysis.sentiment_analyzer") as mock_analyzer:
            mock_analyzer.side_effect = RuntimeError("Model crashed")
            result = analyze_sentiment("Some text here")
            assert result is None

    def test_long_text_is_truncated_before_model_call(self):
        """The function slices text to 512 chars; verify the model is still called."""
        long_text = "x" * 1000
        with patch("app.services.sentiment_analysis.sentiment_analyzer") as mock_analyzer:
            mock_analyzer.return_value = [{"label": "POSITIVE", "score": 0.8}]
            result = analyze_sentiment(long_text)
            # Model should have been called with truncated text (512 chars)
            mock_analyzer.assert_called_once()
            call_arg = mock_analyzer.call_args[0][0]
            assert len(call_arg) == 512
            assert result is not None

    def test_boundary_confidence_exactly_0_7_is_neutral(self):
        """Confidence == 0.7 is NOT > 0.7, so score should be 0 (neutral)."""
        with patch("app.services.sentiment_analysis.sentiment_analyzer") as mock_analyzer:
            mock_analyzer.return_value = [{"label": "POSITIVE", "score": 0.7}]
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
        texts = ["hello", "world", "test"]
        results = batch_analyze_sentiments(texts)
        assert results == [None, None, None]
        assert len(results) == 3

    def test_mocked_model_processes_each_text(self):
        with patch("app.services.sentiment_analysis.sentiment_analyzer") as mock_analyzer:
            mock_analyzer.return_value = [{"label": "POSITIVE", "score": 0.9}]
            texts = ["great", "awesome"]
            results = batch_analyze_sentiments(texts)
            assert len(results) == 2
            for r in results:
                assert r is not None
                assert r["sentiment_score"] == 1
                assert r["label"] == "POSITIVE"

    def test_empty_list_returns_empty(self):
        results = batch_analyze_sentiments([])
        assert results == []
