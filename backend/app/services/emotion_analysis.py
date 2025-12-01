"""
Emotion Analysis Service - SmartStudy v2.0
Uses j-hartmann/emotion-english-distilroberta-base for 7-emotion classification
Replaces binary sentiment with nuanced emotion detection for better study recommendations
"""
from transformers import pipeline
from typing import Optional, Dict
import logging
import torch

logger = logging.getLogger(__name__)

# Initialize the emotion analysis pipeline with 7-emotion model
# Model detects: joy, sadness, anxiety, fear, anger, disgust, surprise
try:
    # Check for available device (MPS for Mac, CUDA for others, CPU fallback)
    device = -1  # CPU default
    if torch.cuda.is_available():
        device = 0
        logger.info("🚀 Using CUDA GPU for emotion analysis")
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        device = "mps"
        logger.info("🚀 Using Apple MPS GPU for emotion analysis")
    else:
        logger.info("💻 Using CPU for emotion analysis")

    emotion_analyzer = pipeline(
        "text-classification",
        model="j-hartmann/emotion-english-distilroberta-base",
        device=device,
        top_k=None  # Return all emotion scores
    )
    logger.info("✅ 7-emotion analysis model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load emotion analysis model: {e}")
    emotion_analyzer = None


def analyze_emotion(text: str) -> Optional[Dict]:
    """
    Analyze emotion using 7-emotion model

    Detects: joy, sadness, anxiety, fear, anger, disgust, surprise

    Args:
        text: The text to analyze (mood note)

    Returns:
        Dict with:
        - primary_emotion: str (the dominant emotion)
        - confidence: float (0.0-1.0, confidence of primary emotion)
        - all_emotions: dict (all 7 emotions with scores)

        Returns None if analysis fails
    """
    if not text or not text.strip():
        return None

    if not emotion_analyzer:
        logger.warning("Emotion analyzer not available")
        return None

    try:
        # Run emotion analysis (limit to 512 tokens for model)
        results = emotion_analyzer(text[:512])

        # Parse results - it returns a list of dicts with label and score
        if not results or not isinstance(results, list) or len(results) == 0:
            return None

        emotions = {}
        for result in results[0]:  # First (and only) text result
            emotion_label = result['label'].lower()
            emotion_score = result['score']
            emotions[emotion_label] = round(emotion_score, 3)

        # Find primary emotion (highest score)
        primary = max(emotions.items(), key=lambda x: x[1])

        return {
            'primary_emotion': primary[0],
            'confidence': primary[1],
            'all_emotions': emotions
        }

    except Exception as e:
        logger.error(f"Error analyzing emotion: {e}")
        return None


def get_mood_based_recommendation(emotion_analysis: Optional[Dict]) -> Optional[Dict]:
    """
    Get SmartStudy recommendation based on detected emotion
    Adapts study plan intensity and duration to student's emotional state

    Args:
        emotion_analysis: Result from analyze_emotion()

    Returns:
        Dict with:
        - intensity: 'light', 'normal', 'supportive', 'productive', 'break'
        - session_length: int (minutes)
        - message: str (supportive message)
    """
    if not emotion_analysis:
        return None

    emotion = emotion_analysis['primary_emotion']
    confidence = emotion_analysis['confidence']

    # Emotion-based study recommendations
    recommendations = {
        'joy': {
            'intensity': 'normal',
            'session_length': 30,
            'message': "Great energy! Perfect time for focused study."
        },
        'sadness': {
            'intensity': 'light',
            'session_length': 10,
            'message': "Take it easy today. Small progress is still progress."
        },
        'anxiety': {
            'intensity': 'light',
            'session_length': 15,
            'message': "You seem anxious. Let's do a short, easy session to build confidence."
        },
        'fear': {
            'intensity': 'supportive',
            'session_length': 20,
            'message': "Let's tackle this together. Start with something familiar."
        },
        'anger': {
            'intensity': 'productive',
            'session_length': 25,
            'message': "Channel that energy into productive learning!"
        },
        'surprise': {
            'intensity': 'normal',
            'session_length': 30,
            'message': "Ready to learn something new?"
        },
        'disgust': {
            'intensity': 'break',
            'session_length': 0,
            'message': "Maybe take a break and come back later?"
        }
    }

    return recommendations.get(emotion, recommendations['joy'])


def convert_emotion_to_legacy_sentiment(emotion: str) -> int:
    """
    Convert 7-emotion to legacy sentiment score for backward compatibility

    Args:
        emotion: One of the 7 emotions

    Returns:
        -1 (negative), 0 (neutral), 1 (positive)
    """
    emotion_to_sentiment = {
        'joy': 1,
        'surprise': 0,  # Neutral - can be positive or negative
        'sadness': -1,
        'anxiety': -1,
        'fear': -1,
        'anger': -1,
        'disgust': -1
    }
    return emotion_to_sentiment.get(emotion, 0)


def batch_analyze_emotions(texts: list[str]) -> list[Optional[Dict]]:
    """
    Analyze emotions for multiple texts

    Args:
        texts: List of text strings to analyze

    Returns:
        List of emotion analysis results (or None for each failed analysis)
    """
    if not emotion_analyzer:
        return [None] * len(texts)

    results = []
    for text in texts:
        results.append(analyze_emotion(text))

    return results


def get_emotion_emoji(emotion: str) -> str:
    """
    Get emoji representation of emotion

    Args:
        emotion: Emotion name

    Returns:
        Emoji string
    """
    emojis = {
        'joy': '😊',
        'sadness': '😢',
        'anxiety': '😰',
        'fear': '😨',
        'anger': '😠',
        'disgust': '🤢',
        'surprise': '😲'
    }
    return emojis.get(emotion, '😐')


def get_emotion_color(emotion: str) -> str:
    """
    Get color code for emotion (for UI)

    Args:
        emotion: Emotion name

    Returns:
        Hex color code
    """
    colors = {
        'joy': '#10B981',      # Green
        'sadness': '#3B82F6',  # Blue
        'anxiety': '#F59E0B',  # Amber
        'fear': '#8B5CF6',     # Purple
        'anger': '#EF4444',    # Red
        'disgust': '#6B7280',  # Gray
        'surprise': '#06B6D4'  # Cyan
    }
    return colors.get(emotion, '#64748B')
