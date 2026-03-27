"""
Sentiment Analysis Service
Uses Hugging Face DistilBERT for analyzing mood notes.
Model loads in a background thread so it never blocks app startup or requests.
"""
from typing import Optional, Dict
import logging
import os
import threading

logger = logging.getLogger(__name__)

# Model loads in background — requests served immediately, sentiment returns None until ready
_sentiment_analyzer = None
_model_ready = threading.Event()
_model_disabled = os.getenv("DISABLE_ML_MODELS", "").lower() == "true"


def _load_model():
    """Load the sentiment model in a background thread. Imports transformers lazily."""
    global _sentiment_analyzer
    try:
        import importlib
        transformers = importlib.import_module("transformers")
        _sentiment_analyzer = transformers.pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )
        logger.info("Sentiment analysis model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load sentiment analysis model: {e}")
        _sentiment_analyzer = None
    finally:
        _model_ready.set()


# Start loading AFTER the app is fully imported — use a short delay
# so gunicorn workers can start accepting requests immediately
if not _model_disabled:
    def _deferred_load():
        import time
        time.sleep(2)  # Let the worker finish startup first
        _load_model()

    _loader = threading.Thread(target=_deferred_load, daemon=True)
    _loader.start()
    logger.info("Sentiment analysis model will load in background")
else:
    _model_ready.set()
    logger.info("Sentiment analysis disabled via DISABLE_ML_MODELS")


def analyze_sentiment(text: str) -> Optional[Dict]:
    """
    Analyze sentiment of text using Hugging Face DistilBERT

    Returns None immediately if model isn't loaded yet (non-blocking).
    """
    if not text or not text.strip():
        return None

    if _model_disabled or not _model_ready.is_set() or not _sentiment_analyzer:
        return None

    try:
        result = _sentiment_analyzer(text[:512])[0]

        label = result['label']
        confidence = result['score']

        if label == "POSITIVE":
            sentiment_score = 1 if confidence > 0.7 else 0
        else:
            sentiment_score = -1 if confidence > 0.7 else 0

        return {
            "sentiment_score": sentiment_score,
            "confidence": round(confidence, 3),
            "label": label
        }

    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
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
    """Analyze sentiment for multiple texts"""
    return [analyze_sentiment(text) for text in texts]
