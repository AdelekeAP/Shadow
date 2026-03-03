"""
Tests for Emotion Analysis Service
backend/app/services/emotion_analysis.py

Tests the helper functions that DON'T require the ML model.
The analyze_emotion() and batch functions are tested with mocking.
"""
import pytest
from unittest.mock import patch, MagicMock
import os

# Ensure ML models are disabled for testing
os.environ["DISABLE_ML_MODELS"] = "true"

from app.services.emotion_analysis import (
    get_mood_based_recommendation,
    convert_emotion_to_legacy_sentiment,
    get_emotion_emoji,
    get_emotion_color,
    analyze_emotion,
    batch_analyze_emotions,
)


# ===================================================================
# get_mood_based_recommendation
# ===================================================================

class TestGetMoodBasedRecommendation:

    def test_joy_returns_normal_intensity(self):
        analysis = {"primary_emotion": "joy", "confidence": 0.9}
        result = get_mood_based_recommendation(analysis)
        assert result["intensity"] == "normal"
        assert result["session_length"] == 30

    def test_sadness_returns_light_intensity(self):
        analysis = {"primary_emotion": "sadness", "confidence": 0.8}
        result = get_mood_based_recommendation(analysis)
        assert result["intensity"] == "light"
        assert result["session_length"] == 10

    def test_anxiety_returns_light_short_session(self):
        analysis = {"primary_emotion": "anxiety", "confidence": 0.7}
        result = get_mood_based_recommendation(analysis)
        assert result["intensity"] == "light"
        assert result["session_length"] == 15

    def test_fear_returns_supportive(self):
        analysis = {"primary_emotion": "fear", "confidence": 0.6}
        result = get_mood_based_recommendation(analysis)
        assert result["intensity"] == "supportive"
        assert result["session_length"] == 20

    def test_anger_returns_productive(self):
        analysis = {"primary_emotion": "anger", "confidence": 0.85}
        result = get_mood_based_recommendation(analysis)
        assert result["intensity"] == "productive"
        assert result["session_length"] == 25

    def test_surprise_returns_normal(self):
        analysis = {"primary_emotion": "surprise", "confidence": 0.5}
        result = get_mood_based_recommendation(analysis)
        assert result["intensity"] == "normal"
        assert result["session_length"] == 30

    def test_disgust_returns_break(self):
        analysis = {"primary_emotion": "disgust", "confidence": 0.7}
        result = get_mood_based_recommendation(analysis)
        assert result["intensity"] == "break"
        assert result["session_length"] == 0

    def test_none_analysis_returns_none(self):
        assert get_mood_based_recommendation(None) is None

    def test_all_emotions_have_messages(self):
        """Every recommendation must include a supportive message"""
        emotions = ["joy", "sadness", "anxiety", "fear", "anger", "surprise", "disgust"]
        for emotion in emotions:
            analysis = {"primary_emotion": emotion, "confidence": 0.8}
            result = get_mood_based_recommendation(analysis)
            assert result["message"], f"Missing message for {emotion}"
            assert len(result["message"]) > 10, f"Message too short for {emotion}"

    def test_unknown_emotion_defaults_to_joy(self):
        analysis = {"primary_emotion": "unknown_emotion", "confidence": 0.5}
        result = get_mood_based_recommendation(analysis)
        assert result["intensity"] == "normal"  # Joy default


# ===================================================================
# convert_emotion_to_legacy_sentiment
# ===================================================================

class TestConvertEmotionToLegacySentiment:

    def test_joy_is_positive(self):
        assert convert_emotion_to_legacy_sentiment("joy") == 1

    def test_surprise_is_neutral(self):
        assert convert_emotion_to_legacy_sentiment("surprise") == 0

    def test_sadness_is_negative(self):
        assert convert_emotion_to_legacy_sentiment("sadness") == -1

    def test_anxiety_is_negative(self):
        assert convert_emotion_to_legacy_sentiment("anxiety") == -1

    def test_fear_is_negative(self):
        assert convert_emotion_to_legacy_sentiment("fear") == -1

    def test_anger_is_negative(self):
        assert convert_emotion_to_legacy_sentiment("anger") == -1

    def test_disgust_is_negative(self):
        assert convert_emotion_to_legacy_sentiment("disgust") == -1

    def test_unknown_emotion_is_neutral(self):
        assert convert_emotion_to_legacy_sentiment("confused") == 0


# ===================================================================
# get_emotion_emoji
# ===================================================================

class TestGetEmotionEmoji:

    def test_all_seven_emotions_have_emojis(self):
        emotions = ["joy", "sadness", "anxiety", "fear", "anger", "disgust", "surprise"]
        for emotion in emotions:
            emoji = get_emotion_emoji(emotion)
            assert emoji, f"No emoji for {emotion}"
            assert len(emoji) > 0

    def test_joy_emoji(self):
        assert get_emotion_emoji("joy") == "\U0001f60a"  # smiling face

    def test_unknown_emotion_default(self):
        assert get_emotion_emoji("boredom") == "\U0001f610"  # neutral face


# ===================================================================
# get_emotion_color
# ===================================================================

class TestGetEmotionColor:

    def test_all_seven_emotions_have_colors(self):
        emotions = ["joy", "sadness", "anxiety", "fear", "anger", "disgust", "surprise"]
        for emotion in emotions:
            color = get_emotion_color(emotion)
            assert color.startswith("#"), f"Invalid color for {emotion}"
            assert len(color) == 7, f"Color should be hex format for {emotion}"

    def test_joy_is_green(self):
        assert get_emotion_color("joy") == "#10B981"

    def test_anger_is_red(self):
        assert get_emotion_color("anger") == "#EF4444"

    def test_unknown_emotion_default_color(self):
        color = get_emotion_color("unknown")
        assert color.startswith("#")


# ===================================================================
# analyze_emotion (with disabled model)
# ===================================================================

class TestAnalyzeEmotionDisabled:

    def test_returns_none_when_model_disabled(self):
        assert analyze_emotion("I'm feeling great today!") is None

    def test_empty_text_returns_none(self):
        assert analyze_emotion("") is None

    def test_whitespace_text_returns_none(self):
        assert analyze_emotion("   ") is None

    def test_none_text_returns_none(self):
        assert analyze_emotion(None) is None


# ===================================================================
# batch_analyze_emotions (with disabled model)
# ===================================================================

class TestBatchAnalyzeEmotionsDisabled:

    def test_returns_none_list_when_disabled(self):
        texts = ["Hello", "World", "Test"]
        results = batch_analyze_emotions(texts)
        assert len(results) == 3
        assert all(r is None for r in results)

    def test_empty_list(self):
        results = batch_analyze_emotions([])
        assert results == []


# ===================================================================
# analyze_emotion with mocked model
# ===================================================================

class TestAnalyzeEmotionMocked:

    def test_successful_analysis(self):
        mock_result = [[
            {"label": "joy", "score": 0.892},
            {"label": "surprise", "score": 0.045},
            {"label": "sadness", "score": 0.023},
            {"label": "anger", "score": 0.015},
            {"label": "fear", "score": 0.012},
            {"label": "anxiety", "score": 0.008},
            {"label": "disgust", "score": 0.005},
        ]]

        with patch("app.services.emotion_analysis.emotion_analyzer", return_value=mock_result):
            result = analyze_emotion("I'm so happy today!")
            assert result is not None
            assert result["primary_emotion"] == "joy"
            assert result["confidence"] == 0.892
            assert "all_emotions" in result
            assert len(result["all_emotions"]) == 7
