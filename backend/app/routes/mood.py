"""
Mood Logging API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.models.mood import MoodLog
from app.routes.auth import get_current_user
from app.services.sentiment_analysis import analyze_sentiment

router = APIRouter()


# Pydantic Schemas
class MoodLogCreate(BaseModel):
    """Schema for creating a mood log"""
    mood_type: str = Field(..., description="Mood type: focused, tired, stressed, motivated, anxious, confident")
    energy_level: int = Field(..., ge=1, le=5, description="Energy level (1-5)")
    note: Optional[str] = Field(None, max_length=500, description="Optional text note")
    course_id: Optional[UUID] = Field(None, description="Optional course linkage")
    task_id: Optional[UUID] = Field(None, description="Optional task linkage")


class MoodLogResponse(BaseModel):
    """Schema for mood log response"""
    id: UUID
    mood_type: str
    energy_level: int
    note: Optional[str]
    course_id: Optional[UUID]
    task_id: Optional[UUID]
    sentiment_score: Optional[int]
    logged_at: datetime


@router.post("/log-mood")
def log_mood(
    mood_data: MoodLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Log current mood and energy level
    """
    try:
        # Validate mood_type
        valid_moods = ['focused', 'tired', 'stressed', 'motivated', 'anxious', 'confident', 'overwhelmed', 'calm']
        if mood_data.mood_type.lower() not in valid_moods:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid mood type. Must be one of: {', '.join(valid_moods)}"
            )

        # Analyze sentiment if note is provided
        sentiment_score = None
        sentiment_data = None
        if mood_data.note and mood_data.note.strip():
            sentiment_data = analyze_sentiment(mood_data.note)
            if sentiment_data:
                sentiment_score = sentiment_data['sentiment_score']
                print(f"📊 Sentiment analysis: {sentiment_data}")

        # Create mood log
        mood_log = MoodLog(
            user_id=current_user.id,
            mood_type=mood_data.mood_type.lower(),
            energy_level=mood_data.energy_level,
            note=mood_data.note,
            course_id=mood_data.course_id,
            task_id=mood_data.task_id,
            sentiment_score=sentiment_score
        )

        db.add(mood_log)
        db.commit()
        db.refresh(mood_log)

        response = {
            "success": True,
            "message": "Mood logged successfully",
            "mood_log": mood_log.to_dict()
        }

        # Include sentiment analysis details if available
        if sentiment_data:
            response["sentiment_analysis"] = {
                "score": sentiment_data['sentiment_score'],
                "confidence": sentiment_data['confidence'],
                "label": sentiment_data['label']
            }

        return response

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error logging mood: {e}")
        raise HTTPException(status_code=500, detail=f"Error logging mood: {str(e)}")


@router.get("/moods")
def get_mood_history(
    limit: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get mood history for current user
    """
    try:
        # Get recent mood logs
        moods = db.query(MoodLog).filter(
            MoodLog.user_id == current_user.id
        ).order_by(desc(MoodLog.logged_at)).limit(limit).all()

        return {
            "success": True,
            "total": len(moods),
            "moods": [mood.to_dict() for mood in moods]
        }

    except Exception as e:
        print(f"Error fetching mood history: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching mood history: {str(e)}")


@router.get("/mood-trends")
def get_mood_trends(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get mood trends and analytics
    """
    try:
        # Get moods from last N days
        start_date = datetime.utcnow() - timedelta(days=days)

        moods = db.query(MoodLog).filter(
            MoodLog.user_id == current_user.id,
            MoodLog.logged_at >= start_date
        ).all()

        if not moods:
            return {
                "success": True,
                "message": "No mood data available",
                "trends": {
                    "avg_energy": 0,
                    "most_common_mood": None,
                    "total_logs": 0,
                    "mood_distribution": {},
                    "daily_avg_energy": []
                }
            }

        # Calculate metrics
        energy_levels = [m.energy_level for m in moods]
        avg_energy = sum(energy_levels) / len(energy_levels)

        # Mood distribution
        mood_counts = {}
        for mood in moods:
            mood_counts[mood.mood_type] = mood_counts.get(mood.mood_type, 0) + 1

        most_common_mood = max(mood_counts, key=mood_counts.get)

        # Daily average energy
        daily_energy = {}
        for mood in moods:
            day = mood.logged_at.date().isoformat()
            if day not in daily_energy:
                daily_energy[day] = []
            daily_energy[day].append(mood.energy_level)

        daily_avg = [
            {"date": day, "avg_energy": sum(energies) / len(energies)}
            for day, energies in sorted(daily_energy.items())
        ]

        # Sentiment analysis trends
        sentiment_stats = {
            "total_with_notes": 0,
            "positive": 0,
            "neutral": 0,
            "negative": 0,
            "avg_sentiment": None
        }

        sentiments_with_scores = [m.sentiment_score for m in moods if m.sentiment_score is not None]
        if sentiments_with_scores:
            sentiment_stats["total_with_notes"] = len(sentiments_with_scores)
            sentiment_stats["positive"] = sum(1 for s in sentiments_with_scores if s == 1)
            sentiment_stats["neutral"] = sum(1 for s in sentiments_with_scores if s == 0)
            sentiment_stats["negative"] = sum(1 for s in sentiments_with_scores if s == -1)
            sentiment_stats["avg_sentiment"] = round(sum(sentiments_with_scores) / len(sentiments_with_scores), 2)

        return {
            "success": True,
            "trends": {
                "avg_energy": round(avg_energy, 2),
                "most_common_mood": most_common_mood,
                "total_logs": len(moods),
                "mood_distribution": mood_counts,
                "daily_avg_energy": daily_avg,
                "sentiment_stats": sentiment_stats
            }
        }

    except Exception as e:
        print(f"Error calculating mood trends: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating mood trends: {str(e)}")


@router.get("/recent-energy")
def get_recent_energy(
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get recent energy levels (used by priority calculator)
    """
    try:
        moods = db.query(MoodLog).filter(
            MoodLog.user_id == current_user.id
        ).order_by(desc(MoodLog.logged_at)).limit(limit).all()

        if not moods:
            return {
                "success": True,
                "avg_energy": 3.0,  # Neutral default
                "recent_moods": []
            }

        energy_levels = [m.energy_level for m in moods]
        avg_energy = sum(energy_levels) / len(energy_levels)

        return {
            "success": True,
            "avg_energy": round(avg_energy, 2),
            "recent_moods": [mood.to_dict() for mood in moods]
        }

    except Exception as e:
        print(f"Error fetching recent energy: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching recent energy: {str(e)}")
