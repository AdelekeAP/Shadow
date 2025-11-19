"""
Recommendations Routes - API endpoints for smart task recommendations
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from app.database import get_db
from app.utils.auth import get_current_user
from app.utils.priority_calculator import PriorityCalculator
from app.models.user import User


router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/priority-tasks")
def get_priority_tasks(
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get top priority task recommendations for the current user

    Args:
        limit: Number of recommendations to return (default: 5, max: 20)

    Returns:
        List of recommended tasks with priority scores and types
    """
    try:
        # Validate limit
        limit = min(max(1, limit), 20)  # Between 1 and 20

        recommendations = PriorityCalculator.get_priority_recommendations(
            user=current_user,
            db=db,
            limit=limit
        )

        # Group by recommendation type for better UX
        grouped_recommendations = {
            'urgent': [],
            'goal_driven': [],
            'mood_based': [],
            'recovery': []
        }

        for rec in recommendations:
            rec_type = rec['recommendation_type']
            if rec_type in grouped_recommendations:
                grouped_recommendations[rec_type].append(rec)

        return {
            "success": True,
            "total_recommendations": len(recommendations),
            "recommendations": recommendations,
            "grouped_by_type": grouped_recommendations,
            "summary": {
                "urgent_count": len(grouped_recommendations['urgent']),
                "goal_driven_count": len(grouped_recommendations['goal_driven']),
                "mood_based_count": len(grouped_recommendations['mood_based']),
                "recovery_count": len(grouped_recommendations['recovery'])
            }
        }

    except Exception as e:
        import traceback
        print(f"Recommendations Error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error getting recommendations: {str(e)}"
        )


@router.get("/urgent")
def get_urgent_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get only urgent tasks (due within 48 hours)

    Returns:
        List of urgent tasks
    """
    try:
        all_recommendations = PriorityCalculator.get_priority_recommendations(
            user=current_user,
            db=db,
            limit=20  # Get more to filter
        )

        # Filter only urgent
        urgent_tasks = [
            rec for rec in all_recommendations
            if rec['recommendation_type'] == 'urgent'
        ]

        return {
            "success": True,
            "count": len(urgent_tasks),
            "urgent_tasks": urgent_tasks
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting urgent tasks: {str(e)}"
        )


@router.get("/goal-driven")
def get_goal_driven_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get tasks with high impact on CGPA target

    Returns:
        List of goal-driven tasks
    """
    try:
        all_recommendations = PriorityCalculator.get_priority_recommendations(
            user=current_user,
            db=db,
            limit=20
        )

        # Filter only goal-driven
        goal_tasks = [
            rec for rec in all_recommendations
            if rec['recommendation_type'] == 'goal_driven'
        ]

        return {
            "success": True,
            "count": len(goal_tasks),
            "goal_driven_tasks": goal_tasks,
            "target_cgpa": float(current_user.target_cgpa) if current_user.target_cgpa else None
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting goal-driven tasks: {str(e)}"
        )


@router.get("/recovery")
def get_recovery_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get recovery tasks (critical when falling behind)

    Returns:
        List of recovery tasks
    """
    try:
        all_recommendations = PriorityCalculator.get_priority_recommendations(
            user=current_user,
            db=db,
            limit=20
        )

        # Filter only recovery
        recovery_tasks = [
            rec for rec in all_recommendations
            if rec['recommendation_type'] == 'recovery'
        ]

        return {
            "success": True,
            "count": len(recovery_tasks),
            "recovery_tasks": recovery_tasks
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting recovery tasks: {str(e)}"
        )


@router.get("/summary")
def get_recommendations_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get a summary of recommendations without full task details

    Returns:
        Summary counts and top 3 priorities
    """
    try:
        recommendations = PriorityCalculator.get_priority_recommendations(
            user=current_user,
            db=db,
            limit=20
        )

        # Count by type
        counts = {
            'urgent': 0,
            'goal_driven': 0,
            'mood_based': 0,
            'recovery': 0
        }

        for rec in recommendations:
            rec_type = rec['recommendation_type']
            if rec_type in counts:
                counts[rec_type] += 1

        # Top 3 priorities
        top_3 = recommendations[:3] if len(recommendations) >= 3 else recommendations

        return {
            "success": True,
            "total_pending_tasks": len(recommendations),
            "counts_by_type": counts,
            "top_3_priorities": top_3,
            "has_urgent_tasks": counts['urgent'] > 0,
            "has_recovery_tasks": counts['recovery'] > 0
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting recommendations summary: {str(e)}"
        )
