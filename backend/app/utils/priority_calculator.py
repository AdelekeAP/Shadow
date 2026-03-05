"""
Priority Calculator - Smart task prioritization based on multiple factors
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.task import Task
from app.models.user import User
from app.models.course import UserCourse

logger = logging.getLogger(__name__)


class PriorityCalculator:
    """Calculate priority scores for tasks based on urgency, weight, mood, and goal impact"""

    # Weight constants for priority calculation
    URGENCY_WEIGHT = 0.4
    WEIGHT_IMPACT_WEIGHT = 0.3
    MOOD_WEIGHT = 0.15
    GOAL_IMPACT_WEIGHT = 0.15

    @staticmethod
    def calculate_urgency_score(task: Task) -> float:
        """
        Calculate urgency score (0-10) based on days until due

        Args:
            task: Task object

        Returns:
            Urgency score (0-10)
        """
        if not task.due_date:
            return 5.0  # Neutral score if no due date

        # Ensure timezone-aware comparison
        due_date = task.due_date
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)
        days_until_due = (due_date - datetime.now(timezone.utc)).days

        # Scoring:
        # Overdue: 10
        # Due today: 10
        # Due tomorrow: 9
        # Due in 2 days: 8
        # ... decreasing to 0 after 10+ days
        if days_until_due < 0:
            return 10.0  # Overdue - maximum urgency
        elif days_until_due == 0:
            return 10.0  # Due today
        elif days_until_due <= 10:
            return max(0, 10 - days_until_due)
        else:
            return 0.0  # More than 10 days away

    @staticmethod
    def calculate_weight_impact_score(task: Task) -> float:
        """
        Calculate weight impact score (0-10) based on task weight

        Args:
            task: Task object

        Returns:
            Weight impact score (0-10)
        """
        if not task.weight:
            return 0.0

        # Convert Decimal to float
        weight = float(task.weight) if task.weight else 0.0

        # Normalize: 30 marks (max CA) = 10 points
        # 65 marks (exam) = 10 points (exam is always critical)
        max_weight = 65 if task.category == 'EXAM' else 30

        return min(10.0, (weight / max_weight) * 10)

    @staticmethod
    def get_recent_mood(user: User, db: Session) -> "Optional[MoodLog]":
        """Get the most recent mood within last 24 hours (cacheable per-request)."""
        from app.models.mood import MoodLog
        return db.query(MoodLog).filter(
            MoodLog.user_id == user.id,
            MoodLog.logged_at >= datetime.now(timezone.utc) - timedelta(hours=24)
        ).order_by(MoodLog.logged_at.desc()).first()

    @staticmethod
    def calculate_mood_score(task: Task, user: User, db: Session, recent_mood=None) -> float:
        """
        Calculate mood alignment score (0-10)

        Matches task difficulty with current energy level:
        - High energy (4-5) → Recommend harder tasks (high weight)
        - Low energy (1-2) → Recommend easier tasks (low weight)
        - Stressed/Overwhelmed → Recommend quick wins (low effort)

        Args:
            task: Task object
            user: User object
            db: Database session
            recent_mood: Pre-fetched mood (avoids repeated DB queries)

        Returns:
            Mood alignment score (0-10)
        """
        # Use pre-fetched mood or query DB
        if recent_mood is None:
            recent_mood = PriorityCalculator.get_recent_mood(user, db)

        # If no recent mood, return neutral score
        if not recent_mood:
            return 5.0

        energy = recent_mood.energy_level  # 1-5
        mood_type = recent_mood.mood_type
        task_weight = task.weight or 10  # Default weight if not set

        # High energy (4-5) → Prefer harder/heavier tasks
        if energy >= 4:
            if task_weight >= 30:  # Heavy task
                return 9.0  # Great match!
            elif task_weight >= 20:
                return 7.0
            else:
                return 5.0  # Light task when energized is okay

        # Low energy (1-2) → Prefer lighter/easier tasks
        elif energy <= 2:
            if task_weight <= 10:  # Light task
                return 9.0  # Perfect match!
            elif task_weight <= 20:
                return 6.0
            else:
                return 3.0  # Heavy task when tired is bad

        # Stressed/Overwhelmed → Prefer quick wins
        elif mood_type in ['stressed', 'overwhelmed', 'anxious']:
            # Estimate effort by weight (lower weight = quicker)
            if task_weight <= 15:
                return 8.5  # Quick win - perfect!
            elif task_weight <= 25:
                return 5.5
            else:
                return 3.0  # Avoid heavy tasks when stressed

        # Focused/Motivated → Can handle anything
        elif mood_type in ['focused', 'motivated', 'confident']:
            if task_weight >= 25:
                return 8.0  # Leverage the focus!
            else:
                return 7.0

        # Medium energy or neutral mood → Balanced
        else:
            return 6.0

    @staticmethod
    def calculate_goal_impact_score(task: Task, user: User, db: Session) -> float:
        """
        Calculate goal impact score (0-10) based on CGPA gap

        Args:
            task: Task object
            user: User object
            db: Database session

        Returns:
            Goal impact score (0-10)
        """
        if not user.target_cgpa:
            return 5.0  # Neutral if no target set

        # Get user course to calculate predicted CGPA
        from app.utils.cgpa_calculator import CGPACalculator
        try:
            cgpa_data = CGPACalculator.get_user_cgpa_data(db, user.id)
            current_cgpa = cgpa_data['current']['cgpa']
            target_cgpa = float(user.target_cgpa) if user.target_cgpa else 4.5

            cgpa_gap = abs(target_cgpa - current_cgpa)

            # If current > target, neutral (don't penalize high performers)
            if current_cgpa >= target_cgpa:
                return 5.0

            # Calculate impact: larger gap = higher impact
            # Max gap of 2.0 points = score of 10
            gap_score = min(10.0, (cgpa_gap / 2.0) * 10)

            # Factor in task weight (higher weight = higher impact)
            # Convert Decimal to float
            weight = float(task.weight) if task.weight else 0.0
            weight_multiplier = weight / 100

            return min(10.0, gap_score * (1 + weight_multiplier))

        except Exception as e:
            logger.error("Error calculating goal impact: %s", e)
            return 5.0  # Neutral on error

    @staticmethod
    def calculate_priority_score(
        task: Task,
        user: User,
        db: Session,
        recent_mood=None
    ) -> Dict:
        """
        Calculate overall priority score for a task

        Formula: Priority = W1×Urgency + W2×Weight + W3×Mood + W4×Goal

        Args:
            task: Task object
            user: User object
            db: Database session
            recent_mood: Pre-fetched mood (avoids repeated DB queries)

        Returns:
            Dict with priority score and breakdown
        """
        urgency_score = PriorityCalculator.calculate_urgency_score(task)
        weight_score = PriorityCalculator.calculate_weight_impact_score(task)
        mood_score = PriorityCalculator.calculate_mood_score(task, user, db, recent_mood=recent_mood)
        goal_score = PriorityCalculator.calculate_goal_impact_score(task, user, db)

        # Weighted sum
        priority_score = (
            PriorityCalculator.URGENCY_WEIGHT * urgency_score +
            PriorityCalculator.WEIGHT_IMPACT_WEIGHT * weight_score +
            PriorityCalculator.MOOD_WEIGHT * mood_score +
            PriorityCalculator.GOAL_IMPACT_WEIGHT * goal_score
        )

        return {
            'priority_score': round(priority_score, 2),
            'urgency_score': round(urgency_score, 2),
            'weight_score': round(weight_score, 2),
            'mood_score': round(mood_score, 2),
            'goal_score': round(goal_score, 2)
        }

    @staticmethod
    def get_recommendation_type(task: Task, priority_breakdown: Dict) -> str:
        """
        Determine the recommendation type based on priority breakdown

        Args:
            task: Task object
            priority_breakdown: Priority score breakdown

        Returns:
            Recommendation type: 'urgent', 'goal_driven', 'mood_based', or 'recovery'
        """
        urgency = priority_breakdown['urgency_score']
        goal = priority_breakdown['goal_score']
        mood = priority_breakdown['mood_score']

        # Urgent: Due within 48 hours (urgency > 8)
        if urgency >= 8:
            return 'urgent'

        # Goal-Driven: High impact on CGPA target (goal > 7)
        elif goal >= 7:
            return 'goal_driven'

        # Mood-Based: Well-aligned with current energy (mood > 8)
        elif mood >= 8:
            return 'mood_based'

        # Recovery: Combination of factors indicating falling behind
        elif urgency >= 6 and goal >= 6:
            return 'recovery'

        else:
            return 'goal_driven'  # Default

    @staticmethod
    def get_priority_recommendations(
        user: User,
        db: Session,
        limit: int = 5
    ) -> List[Dict]:
        """
        Get top priority task recommendations for a user

        Args:
            user: User object
            db: Database session
            limit: Number of recommendations to return

        Returns:
            List of recommended tasks with priority scores
        """
        from sqlalchemy.orm import joinedload

        # Get pending tasks (capped at 200 to prevent resource exhaustion)
        pending_tasks = db.query(Task).filter(
            Task.user_id == user.id,
            Task.is_completed == False
        ).limit(200).all()

        if not pending_tasks:
            return []

        # Cache mood lookup (single query for all tasks)
        recent_mood = PriorityCalculator.get_recent_mood(user, db)

        # Batch-load course info (fixes N+1 query)
        uc_ids = list({t.user_course_id for t in pending_tasks if t.user_course_id})
        uc_map = {}
        if uc_ids:
            user_courses = db.query(UserCourse).options(
                joinedload(UserCourse.course)
            ).filter(UserCourse.id.in_(uc_ids)).all()
            uc_map = {uc.id: uc for uc in user_courses}

        now = datetime.now(timezone.utc)

        # Calculate priority for each task
        recommendations = []
        for task in pending_tasks:
            priority_breakdown = PriorityCalculator.calculate_priority_score(
                task, user, db, recent_mood=recent_mood
            )

            recommendation_type = PriorityCalculator.get_recommendation_type(
                task, priority_breakdown
            )

            # Look up course from batch-loaded map
            user_course = uc_map.get(task.user_course_id)
            course_code = user_course.course.code if user_course and user_course.course else 'Unknown'
            course_title = user_course.course.title if user_course and user_course.course else 'Unknown Course'

            # Timezone-safe overdue check
            is_overdue = False
            if task.due_date:
                due = task.due_date
                if due.tzinfo is None:
                    due = due.replace(tzinfo=timezone.utc)
                is_overdue = due < now

            recommendations.append({
                'task_id': str(task.id),
                'title': task.title,
                'course_code': course_code,
                'course_title': course_title,
                'task_type': task.task_type,
                'weight': task.weight,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'category': task.category,
                'priority_score': priority_breakdown['priority_score'],
                'urgency_score': priority_breakdown['urgency_score'],
                'weight_score': priority_breakdown['weight_score'],
                'mood_score': priority_breakdown['mood_score'],
                'goal_score': priority_breakdown['goal_score'],
                'recommendation_type': recommendation_type,
                'is_overdue': is_overdue,
            })

        # Sort by priority score (descending)
        recommendations.sort(key=lambda x: x['priority_score'], reverse=True)

        # Return top N
        return recommendations[:limit]
