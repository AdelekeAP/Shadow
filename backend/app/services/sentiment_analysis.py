"""
Sentiment Analysis Service
Uses Hugging Face DistilBERT for analyzing mood notes
"""
from transformers import pipeline
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

# Initialize the sentiment analysis pipeline
# Using distilbert-base-uncased-finetuned-sst-2-english as specified
try:
    sentiment_analyzer = pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english"
    )
    logger.info("✅ Sentiment analysis model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load sentiment analysis model: {e}")
    sentiment_analyzer = None


def analyze_sentiment(text: str) -> Optional[Dict]:
    """
    Analyze sentiment of text using Hugging Face DistilBERT

    Args:
        text: The text to analyze (mood note)

    Returns:
        Dict with:
        - sentiment_score: -1 (negative), 0 (neutral), 1 (positive)
        - confidence: float between 0 and 1
        - label: "POSITIVE" or "NEGATIVE"

        Returns None if analysis fails
    """
    if not text or not text.strip():
        return None

    if not sentiment_analyzer:
        logger.warning("Sentiment analyzer not available")
        return None

    try:
        # Run sentiment analysis
        result = sentiment_analyzer(text[:512])[0]  # Limit to 512 chars for model

        label = result['label']
        confidence = result['score']

        # Convert to -1, 0, 1 scale
        if label == "POSITIVE":
            # High confidence positive = 1, low confidence = 0 (neutral)
            sentiment_score = 1 if confidence > 0.7 else 0
        else:  # NEGATIVE
            # High confidence negative = -1, low confidence = 0 (neutral)
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
    """
    Get human-readable description of sentiment score

    Args:
        sentiment_score: -1, 0, or 1

    Returns:
        String description
    """
    descriptions = {
        -1: "Negative sentiment detected",
        0: "Neutral sentiment",
        1: "Positive sentiment detected"
    }
    return descriptions.get(sentiment_score, "Unknown sentiment")


def batch_analyze_sentiments(texts: list[str]) -> list[Optional[Dict]]:
    """
    Analyze sentiment for multiple texts

    Args:
        texts: List of text strings to analyze

    Returns:
        List of sentiment analysis results (or None for each failed analysis)
    """
    if not sentiment_analyzer:
        return [None] * len(texts)

    results = []
    for text in texts:
        results.append(analyze_sentiment(text))

    return results
