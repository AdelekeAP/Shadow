"""
Emotion Classification Service
Uses Hugging Face j-hartmann/emotion-english-distilroberta-base for 7-class
emotion detection on mood notes (anger, disgust, fear, joy, neutral, sadness,
surprise). Model loads in a background thread so it never blocks app startup
or requests.

Backward compatibility: still returns `sentiment_score` (-1/0/1) and `label`
(POSITIVE/NEGATIVE/NEUTRAL) derived from the dominant emotion, so legacy
mismatch-detection logic in routes/mood.py keeps working.
"""
from typing import Optional, Dict, List
import logging
import os
import threading

logger = logging.getLogger(__name__)

EMOTION_MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"

# j-hartmann label set
EMOTION_LABELS = {"anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"}

# Map each emotion to a binary-sentiment polarity for backward-compatible
# mismatch detection. Surprise is treated as neutral because it can be
# positive or negative depending on context.
POSITIVE_EMOTIONS = {"joy"}
NEGATIVE_EMOTIONS = {"anger", "disgust", "fear", "sadness"}
NEUTRAL_EMOTIONS = {"neutral", "surprise"}

# Confidence threshold below which we report the score as neutral (0)
CONFIDENCE_THRESHOLD = 0.7

_sentiment_analyzer = None
_model_ready = threading.Event()
_model_disabled = os.getenv("DISABLE_ML_MODELS", "").lower() == "true"


def _load_model():
    """Load the emotion model in a background thread. Imports transformers lazily."""
    global _sentiment_analyzer
    try:
        import importlib
        transformers = importlib.import_module("transformers")
        _sentiment_analyzer = transformers.pipeline(
            "text-classification",
            model=EMOTION_MODEL_NAME,
            top_k=None,  # return all 7 emotion scores
        )
        logger.info("Emotion model loaded: %s", EMOTION_MODEL_NAME)
    except Exception as e:
        logger.error(f"Failed to load emotion model: {e}")
        _sentiment_analyzer = None
    finally:
        _model_ready.set()


if not _model_disabled:
    def _deferred_load():
        import time
        time.sleep(2)  # Let the worker finish startup first
        _load_model()

    _loader = threading.Thread(target=_deferred_load, daemon=True)
    _loader.start()
    logger.info("Emotion model will load in background")
else:
    _model_ready.set()
    logger.info("Emotion classification disabled via DISABLE_ML_MODELS")


def _polarity_for(emotion: str) -> str:
    """Return POSITIVE / NEGATIVE / NEUTRAL for an emotion label."""
    if emotion in POSITIVE_EMOTIONS:
        return "POSITIVE"
    if emotion in NEGATIVE_EMOTIONS:
        return "NEGATIVE"
    return "NEUTRAL"


def _normalize_scores(raw) -> List[Dict]:
    """Normalize the pipeline output to a flat list of {label, score} dicts.

    Different transformers versions return either:
      [{"label": ..., "score": ...}, ...]              # single-input + top_k=None
      [[{"label": ..., "score": ...}, ...]]            # batched output
    """
    if not raw:
        return []
    # Unwrap if batched
    if isinstance(raw[0], list):
        raw = raw[0]
    return [item for item in raw if "label" in item and "score" in item]


def analyze_sentiment(text: str) -> Optional[Dict]:
    """
    Classify the emotion of a text using j-hartmann's 7-class model.

    Returns None if the model isn't loaded yet (non-blocking) or if input is empty.

    Returns a dict with:
      - primary_emotion: top emotion label (e.g. "joy")
      - emotion_confidence: top score (0-1)
      - emotion_scores: dict of all 7 emotions to scores
      - sentiment_score: -1 / 0 / 1 (legacy)
      - confidence: top score (legacy alias of emotion_confidence)
      - label: POSITIVE / NEGATIVE / NEUTRAL (legacy, derived from primary_emotion)
    """
    if not text or not text.strip():
        return None

    if _model_disabled or not _model_ready.is_set() or not _sentiment_analyzer:
        return None

    try:
        raw = _sentiment_analyzer(text[:512])
        scores = _normalize_scores(raw)
        if not scores:
            logger.warning("Emotion model returned empty result")
            return None

        # Sort by score desc and pick the dominant emotion
        scores.sort(key=lambda s: s["score"], reverse=True)
        top = scores[0]
        primary_emotion = top["label"].lower()
        confidence = float(top["score"])

        # Build full {emotion: score} map
        emotion_scores = {s["label"].lower(): round(float(s["score"]), 4) for s in scores}

        # Legacy polarity for mismatch detection
        polarity = _polarity_for(primary_emotion)
        if polarity == "POSITIVE":
            sentiment_score = 1 if confidence > CONFIDENCE_THRESHOLD else 0
        elif polarity == "NEGATIVE":
            sentiment_score = -1 if confidence > CONFIDENCE_THRESHOLD else 0
        else:
            sentiment_score = 0

        return {
            "primary_emotion": primary_emotion,
            "emotion_confidence": round(confidence, 3),
            "emotion_scores": emotion_scores,
            "sentiment_score": sentiment_score,
            "confidence": round(confidence, 3),
            "label": polarity,
        }

    except Exception as e:
        logger.error(f"Error analyzing emotion: {e}")
        return None


def get_sentiment_description(sentiment_score: int) -> str:
    """Get human-readable description of sentiment score"""
    descriptions = {
        -1: "Negative sentiment detected",
        0: "Neutral sentiment",
        1: "Positive sentiment detected"
    }
    return descriptions.get(sentiment_score, "Unknown sentiment")


def batch_analyze_sentiments(texts: list[str]) -> list[Optional[Dict]]:
    """Analyze emotion for multiple texts"""
    return [analyze_sentiment(text) for text in texts]
