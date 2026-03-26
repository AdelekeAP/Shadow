"""
Analytics Routes - Effectiveness Analytics Dashboard API
Provides aggregated analytics on SmartStudy intervention effectiveness
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case, and_
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone
from uuid import UUID
import math
import statistics as pystats

from fastapi import Request as FastAPIRequest
from app.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User
from app.services.cache_service import cache_get, cache_set, TTL_ANALYTICS
from app.middleware.rate_limiter import limiter
from app.models.smartstudy import (
    StudyPlan,
    StudyPlanResource,
    InterventionOutcome,
    ChatConversation,
    ChatMessage
)
from app.models.mood import MoodLog
from app.models.usage_log import UsageLog

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/effectiveness/summary",
    operation_id="get_effectiveness_summary",
    summary="Overall SmartStudy effectiveness summary",
    response_description="Aggregated metrics covering study plans, engagement, and conversation activity.",
    responses={
        200: {
            "description": "Summary retrieved successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "summary": {
                            "total_study_plans": 12,
                            "active_study_plans": 3,
                            "completed_study_plans": 9,
                            "plans_with_improvement_data": 7,
                            "average_improvement": 8.45,
                            "positive_improvements": 6,
                            "total_conversations": 24,
                            "total_messages": 156
                        },
                        "engagement": {
                            "total_resources": 48,
                            "resources_clicked": 35,
                            "resources_completed": 22,
                            "engagement_rate": 72.9,
                            "completion_rate": 45.8,
                            "average_helpful_rating": 4.2,
                            "rated_resources_count": 18
                        }
                    }
                }
            },
        },
        401: {"description": "Missing or invalid JWT token."},
    },
)
@limiter.limit("30/minute")
async def get_effectiveness_summary(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a high-level effectiveness dashboard for the authenticated user's SmartStudy usage.

    Returns two sections:

    - **summary** -- Study plan counts (total, active, completed), average score
      improvement across plans with before/after data, and total AI chat activity.
    - **engagement** -- Resource interaction metrics including click-through rate,
      completion rate, and average helpfulness rating.

    This endpoint powers the main "Effectiveness Analytics" card on the student dashboard.
    """
    user_id = current_user.id

    # Check cache first
    cache_key = f"analytics:effectiveness_summary:{user_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    # Aggregate study plan stats in SQL
    plan_stats = db.query(
        func.count(StudyPlan.id).label('total'),
        func.sum(case((StudyPlan.is_active == True, 1), else_=0)).label('active'),
        func.sum(case((StudyPlan.is_active == False, 1), else_=0)).label('completed'),
        func.sum(case(
            (and_(StudyPlan.before_score.isnot(None), StudyPlan.after_score.isnot(None)), 1),
            else_=0
        )).label('with_scores'),
        func.avg(case(
            (and_(StudyPlan.before_score.isnot(None), StudyPlan.after_score.isnot(None)),
             StudyPlan.after_score - StudyPlan.before_score),
            else_=None
        )).label('avg_improvement'),
        func.sum(case(
            (and_(StudyPlan.before_score.isnot(None), StudyPlan.after_score.isnot(None),
                  StudyPlan.after_score > StudyPlan.before_score), 1),
            else_=0
        )).label('positive_improvements'),
    ).filter(StudyPlan.user_id == user_id).first()

    # Aggregate resource engagement stats in SQL
    resource_stats = db.query(
        func.count(StudyPlanResource.id).label('total'),
        func.sum(case((StudyPlanResource.clicked == True, 1), else_=0)).label('clicked'),
        func.sum(case((StudyPlanResource.completed == True, 1), else_=0)).label('completed'),
        func.count(StudyPlanResource.helpful_rating).label('rated_count'),
        func.avg(StudyPlanResource.helpful_rating).label('avg_rating'),
    ).join(StudyPlan).filter(StudyPlan.user_id == user_id).first()

    total_resources = int(resource_stats.total or 0)
    clicked_resources = int(resource_stats.clicked or 0)
    completed_resources = int(resource_stats.completed or 0)
    avg_rating = float(resource_stats.avg_rating or 0)

    engagement_rate = (clicked_resources / total_resources * 100) if total_resources > 0 else 0
    completion_rate = (completed_resources / total_resources * 100) if total_resources > 0 else 0

    # Get chat conversation count
    conversations = db.query(func.count(ChatConversation.id)).filter(
        ChatConversation.user_id == user_id
    ).scalar()

    # Get messages count
    messages = db.query(func.count(ChatMessage.id)).join(ChatConversation).filter(
        ChatConversation.user_id == user_id
    ).scalar()

    result = {
        "summary": {
            "total_study_plans": int(plan_stats.total or 0),
            "active_study_plans": int(plan_stats.active or 0),
            "completed_study_plans": int(plan_stats.completed or 0),
            "plans_with_improvement_data": int(plan_stats.with_scores or 0),
            "average_improvement": round(float(plan_stats.avg_improvement or 0), 2),
            "positive_improvements": int(plan_stats.positive_improvements or 0),
            "total_conversations": conversations,
            "total_messages": messages
        },
        "engagement": {
            "total_resources": total_resources,
            "resources_clicked": clicked_resources,
            "resources_completed": completed_resources,
            "engagement_rate": round(engagement_rate, 1),
            "completion_rate": round(completion_rate, 1),
            "average_helpful_rating": round(avg_rating, 1),
            "rated_resources_count": int(resource_stats.rated_count or 0)
        }
    }

    cache_set(cache_key, result, TTL_ANALYTICS)
    return result


@router.get(
    "/effectiveness/by-learning-style",
    operation_id="get_effectiveness_by_learning_style",
    summary="Effectiveness breakdown by learning style and resource type",
    response_description="Metrics grouped by learning style (visual, auditory, reading, kinesthetic) and resource type (video, article, document).",
    responses={
        200: {
            "description": "Breakdown retrieved successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "by_learning_style": {
                            "visual": {
                                "plan_count": 5,
                                "avg_completion": 78.4,
                                "avg_effectiveness": 82.1
                            },
                            "reading": {
                                "plan_count": 3,
                                "avg_completion": 65.0,
                                "avg_effectiveness": 70.5
                            }
                        },
                        "by_resource_type": {
                            "video": {
                                "total": 20,
                                "clicked": 18,
                                "completed": 12,
                                "engagement_rate": 90.0,
                                "completion_rate": 60.0,
                                "avg_rating": 4.3
                            },
                            "article": {
                                "total": 15,
                                "clicked": 10,
                                "completed": 6,
                                "engagement_rate": 66.7,
                                "completion_rate": 40.0,
                                "avg_rating": 3.8
                            }
                        }
                    }
                }
            },
        },
        401: {"description": "Missing or invalid JWT token."},
    },
)
@limiter.limit("30/minute")
async def get_effectiveness_by_learning_style(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze SmartStudy effectiveness segmented by learning style and resource type.

    Returns two breakdowns:

    - **by_learning_style** -- For each learning style the student has used (visual,
      auditory, reading, kinesthetic), shows the number of study plans, average
      completion percentage, and average effectiveness score.
    - **by_resource_type** -- For each resource type (video, article, document),
      shows engagement and completion rates plus average helpfulness rating.

    Useful for identifying which learning modality is most effective for the student
    and for recommending optimal resource types in future study plans.
    """
    user_id = current_user.id

    cache_key = f"analytics:by_learning_style:{user_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    # Get study plans grouped by learning style
    plans_by_style = db.query(
        StudyPlan.learning_style_used,
        func.count(StudyPlan.id).label('plan_count'),
        func.avg(StudyPlan.completion_percentage).label('avg_completion'),
        func.avg(StudyPlan.effectiveness_score).label('avg_effectiveness')
    ).filter(
        StudyPlan.user_id == user_id,
        StudyPlan.learning_style_used != None
    ).group_by(StudyPlan.learning_style_used).all()

    # Get resource engagement by type (which correlates with learning style)
    resource_stats = db.query(
        StudyPlanResource.resource_type,
        func.count(StudyPlanResource.id).label('total'),
        func.sum(case((StudyPlanResource.clicked == True, 1), else_=0)).label('clicked'),
        func.sum(case((StudyPlanResource.completed == True, 1), else_=0)).label('completed'),
        func.avg(StudyPlanResource.helpful_rating).label('avg_rating')
    ).join(StudyPlan).filter(
        StudyPlan.user_id == user_id
    ).group_by(StudyPlanResource.resource_type).all()

    learning_styles = {}
    for style_data in plans_by_style:
        style = style_data[0] or 'unknown'
        learning_styles[style] = {
            "plan_count": style_data[1],
            "avg_completion": round(float(style_data[2] or 0), 1),
            "avg_effectiveness": round(float(style_data[3] or 0), 1)
        }

    resource_types = {}
    for res_data in resource_stats:
        res_type = res_data[0] or 'unknown'
        total = res_data[1] or 0
        resource_types[res_type] = {
            "total": total,
            "clicked": int(res_data[2] or 0),
            "completed": int(res_data[3] or 0),
            "engagement_rate": round((int(res_data[2] or 0) / total * 100) if total > 0 else 0, 1),
            "completion_rate": round((int(res_data[3] or 0) / total * 100) if total > 0 else 0, 1),
            "avg_rating": round(float(res_data[4] or 0), 1)
        }

    result = {
        "by_learning_style": learning_styles,
        "by_resource_type": resource_types
    }
    cache_set(cache_key, result, TTL_ANALYTICS)
    return result


@router.get(
    "/effectiveness/over-time",
    operation_id="get_effectiveness_over_time",
    summary="Effectiveness trend data over a configurable time window",
    response_description="Daily time-series data for study plan creation and resource engagement.",
    responses={
        200: {
            "description": "Time-series data retrieved successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "period_days": 30,
                        "study_plans_over_time": [
                            {"date": "2026-02-01", "plans_created": 2, "avg_completion": 45.0},
                            {"date": "2026-02-05", "plans_created": 1, "avg_completion": 80.0}
                        ],
                        "engagement_over_time": [
                            {"date": "2026-02-01", "resources_engaged": 5},
                            {"date": "2026-02-03", "resources_engaged": 8}
                        ]
                    }
                }
            },
        },
        401: {"description": "Missing or invalid JWT token."},
    },
)
@limiter.limit("30/minute")
async def get_effectiveness_over_time(
    request: FastAPIRequest,
    days: int = 30,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve daily time-series data on study plan activity and resource engagement.

    **Query parameter:**
    - `days` (default: 30) -- Number of days to look back from today.

    Returns two arrays suitable for charting:

    - **study_plans_over_time** -- One entry per day with the count of plans
      created and the average completion percentage for those plans.
    - **engagement_over_time** -- One entry per day with the count of resources
      that were clicked/engaged on that day.

    This data powers the trend line charts on the Effectiveness Analytics dashboard.
    """
    user_id = current_user.id

    cache_key = f"analytics:over_time:{user_id}:{days}:{limit}:{offset}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Get study plans created over time
    plans_over_time = db.query(
        func.date_trunc('day', StudyPlan.created_at).label('date'),
        func.count(StudyPlan.id).label('plans_created'),
        func.avg(StudyPlan.completion_percentage).label('avg_completion')
    ).filter(
        StudyPlan.user_id == user_id,
        StudyPlan.created_at >= cutoff_date
    ).group_by(func.date_trunc('day', StudyPlan.created_at)).order_by('date').all()

    # Get resource engagement over time
    engagement_over_time = db.query(
        func.date_trunc('day', StudyPlanResource.clicked_at).label('date'),
        func.count(StudyPlanResource.id).label('resources_engaged')
    ).join(StudyPlan).filter(
        StudyPlan.user_id == user_id,
        StudyPlanResource.clicked_at >= cutoff_date,
        StudyPlanResource.clicked_at != None
    ).group_by(func.date_trunc('day', StudyPlanResource.clicked_at)).order_by('date').all()

    # Format for charts
    plans_data = [
        {
            "date": str(row[0].date()) if row[0] else None,
            "plans_created": row[1],
            "avg_completion": round(float(row[2] or 0), 1)
        }
        for row in plans_over_time if row[0]
    ]

    engagement_data = [
        {
            "date": str(row[0].date()) if row[0] else None,
            "resources_engaged": row[1]
        }
        for row in engagement_over_time if row[0]
    ]

    total_plans = len(plans_data)
    total_engagement = len(engagement_data)

    result = {
        "period_days": days,
        "study_plans_over_time": plans_data[offset:offset + limit],
        "engagement_over_time": engagement_data[offset:offset + limit],
        "total": max(total_plans, total_engagement),
        "limit": limit,
        "offset": offset
    }
    cache_set(cache_key, result, TTL_ANALYTICS)
    return result


@router.get(
    "/effectiveness/mood-correlation",
    operation_id="get_mood_effectiveness_correlation",
    summary="Mood-to-effectiveness correlation analysis",
    response_description="Mood distribution with average energy levels and per-mood grade improvement data.",
    responses={
        200: {
            "description": "Correlation data retrieved successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "mood_distribution": {
                            "focused": {"count": 25, "total_energy": 100, "study_sessions": 0, "avg_energy": 4.0},
                            "stressed": {"count": 10, "total_energy": 22, "study_sessions": 0, "avg_energy": 2.2}
                        },
                        "effectiveness_by_mood": {
                            "focused": {"count": 8, "total_improvement": 12.5, "avg_improvement": 1.56},
                            "stressed": {"count": 4, "total_improvement": 2.0, "avg_improvement": 0.5}
                        }
                    }
                }
            },
        },
        401: {"description": "Missing or invalid JWT token."},
    },
)
@limiter.limit("30/minute")
async def get_mood_effectiveness_correlation(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze the relationship between a student's mood states and their study effectiveness.

    Uses the most recent 100 mood logs and all intervention outcomes that have mood context.

    Returns two sections:

    - **mood_distribution** -- Frequency of each mood type (e.g., focused, tired, stressed,
      motivated, anxious, confident) with average energy level per mood.
    - **effectiveness_by_mood** -- For each mood type recorded during study interventions,
      shows the average grade improvement, helping students understand when they study best.

    This data supports the insight: *"You improve most when studying in a focused mood."*
    """
    user_id = current_user.id

    cache_key = f"analytics:mood_correlation:{user_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    # Get mood logs with nearby study plan completions
    mood_logs = db.query(MoodLog).filter(
        MoodLog.user_id == user_id
    ).order_by(MoodLog.logged_at.desc()).limit(100).all()

    # Aggregate by mood type
    mood_stats = {}
    for mood in mood_logs:
        mood_type = mood.mood_type
        if mood_type not in mood_stats:
            mood_stats[mood_type] = {
                "count": 0,
                "total_energy": 0,
                "study_sessions": 0
            }
        mood_stats[mood_type]["count"] += 1
        mood_stats[mood_type]["total_energy"] += mood.energy_level or 0

    # Calculate averages
    for mood_type in mood_stats:
        count = mood_stats[mood_type]["count"]
        mood_stats[mood_type]["avg_energy"] = round(
            mood_stats[mood_type]["total_energy"] / count if count > 0 else 0, 1
        )

    # Get intervention outcomes with mood context
    outcomes = db.query(InterventionOutcome).filter(
        InterventionOutcome.user_id == user_id,
        InterventionOutcome.student_mood_during != None
    ).all()

    mood_effectiveness = {}
    for outcome in outcomes:
        mood = outcome.student_mood_during
        if mood not in mood_effectiveness:
            mood_effectiveness[mood] = {
                "count": 0,
                "total_improvement": 0
            }
        mood_effectiveness[mood]["count"] += 1
        if outcome.grade_improvement:
            mood_effectiveness[mood]["total_improvement"] += float(outcome.grade_improvement)

    # Calculate average improvement by mood
    for mood in mood_effectiveness:
        count = mood_effectiveness[mood]["count"]
        mood_effectiveness[mood]["avg_improvement"] = round(
            mood_effectiveness[mood]["total_improvement"] / count if count > 0 else 0, 2
        )

    result = {
        "mood_distribution": mood_stats,
        "effectiveness_by_mood": mood_effectiveness
    }
    cache_set(cache_key, result, TTL_ANALYTICS)
    return result


@router.get(
    "/effectiveness/intervention-outcomes",
    operation_id="get_intervention_outcomes",
    summary="Detailed intervention outcome history",
    response_description="List of individual intervention outcomes with summary statistics.",
    responses={
        200: {
            "description": "Outcomes retrieved successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "outcomes": [
                            {
                                "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                                "grade_improvement": 5.0,
                                "study_plan_topic": "Data Structures - Binary Trees",
                                "learning_style_used": "visual"
                            }
                        ],
                        "summary": {
                            "total_outcomes": 15,
                            "positive_outcomes": 12,
                            "success_rate": 80.0,
                            "average_improvement": 4.25
                        }
                    }
                }
            },
        },
        401: {"description": "Missing or invalid JWT token."},
    },
)
@limiter.limit("30/minute")
async def get_intervention_outcomes(
    request: FastAPIRequest,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve a paginated list of intervention outcomes with aggregated statistics.

    Each outcome records the measured grade improvement after a SmartStudy intervention,
    enriched with the associated study plan topic and learning style for context.

    **Query parameter:**
    - `limit` (default: 20) -- Maximum number of outcomes to return, ordered most recent first.

    The **summary** object provides:
    - `total_outcomes` -- Total number of measured interventions
    - `positive_outcomes` -- Count where grade improvement > 0
    - `success_rate` -- Percentage of positive outcomes
    - `average_improvement` -- Mean grade improvement across all outcomes
    """
    user_id = current_user.id

    cache_key = f"analytics:intervention_outcomes:{user_id}:{limit}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    outcomes = db.query(InterventionOutcome).options(
        joinedload(InterventionOutcome.study_plan)
    ).filter(
        InterventionOutcome.user_id == user_id
    ).order_by(InterventionOutcome.measured_at.desc()).limit(limit).all()

    # Build result with eager-loaded study plan context
    result = []
    for outcome in outcomes:
        outcome_data = outcome.to_dict()

        # Add study plan topic if available (eager-loaded, no extra query)
        if outcome.study_plan:
            outcome_data["study_plan_topic"] = outcome.study_plan.topic
            outcome_data["learning_style_used"] = outcome.study_plan.learning_style_used

        result.append(outcome_data)

    # Calculate summary statistics
    total_outcomes = len(outcomes)
    positive_outcomes = len([o for o in outcomes if o.grade_improvement and float(o.grade_improvement) > 0])
    avg_improvement = sum(
        float(o.grade_improvement) for o in outcomes if o.grade_improvement
    ) / total_outcomes if total_outcomes > 0 else 0

    response = {
        "outcomes": result,
        "summary": {
            "total_outcomes": total_outcomes,
            "positive_outcomes": positive_outcomes,
            "success_rate": round(positive_outcomes / total_outcomes * 100 if total_outcomes > 0 else 0, 1),
            "average_improvement": round(avg_improvement, 2)
        }
    }
    cache_set(cache_key, response, TTL_ANALYTICS)
    return response


@router.get(
    "/effectiveness/topics",
    operation_id="get_topic_effectiveness",
    summary="Per-topic effectiveness leaderboard",
    response_description="Top 20 study topics ranked by plan count with completion and effectiveness scores.",
    responses={
        200: {
            "description": "Topic effectiveness data retrieved successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "topics": [
                            {
                                "topic": "Data Structures - Binary Trees",
                                "plan_count": 4,
                                "completed_count": 3,
                                "avg_completion": 85.0,
                                "avg_effectiveness": 78.5
                            },
                            {
                                "topic": "Operating Systems - Scheduling",
                                "plan_count": 2,
                                "completed_count": 2,
                                "avg_completion": 92.0,
                                "avg_effectiveness": 88.0
                            }
                        ]
                    }
                }
            },
        },
        401: {"description": "Missing or invalid JWT token."},
    },
)
@limiter.limit("30/minute")
async def get_topic_effectiveness(
    request: FastAPIRequest,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve effectiveness metrics grouped by study topic.

    Returns the **top 20 topics** (by plan count) with:
    - `plan_count` -- Number of study plans created for the topic
    - `completed_count` -- Number of those plans that are no longer active (completed)
    - `avg_completion` -- Average completion percentage across all plans for the topic
    - `avg_effectiveness` -- Average effectiveness score (based on before/after performance)

    Helps students identify which topics they have studied most and how effective
    their study interventions have been for each subject area.
    """
    user_id = current_user.id

    cache_key = f"analytics:topics:{user_id}:{limit}:{offset}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    # Aggregate by topic
    topic_stats = db.query(
        StudyPlan.topic,
        func.count(StudyPlan.id).label('plan_count'),
        func.avg(StudyPlan.completion_percentage).label('avg_completion'),
        func.avg(StudyPlan.effectiveness_score).label('avg_effectiveness'),
        func.sum(case((StudyPlan.is_active == False, 1), else_=0)).label('completed_count')
    ).filter(
        StudyPlan.user_id == user_id
    ).group_by(StudyPlan.topic).all()

    topics = []
    for row in topic_stats:
        topics.append({
            "topic": row[0],
            "plan_count": row[1],
            "completed_count": int(row[4] or 0),
            "avg_completion": round(float(row[2] or 0), 1),
            "avg_effectiveness": round(float(row[3] or 0), 1)
        })

    # Sort by plan count
    topics.sort(key=lambda x: x["plan_count"], reverse=True)

    total = len(topics)

    result = {
        "topics": topics[offset:offset + limit],
        "total": total,
        "limit": limit,
        "offset": offset
    }
    cache_set(cache_key, result, TTL_ANALYTICS)
    return result


# ---------------------------------------------------------------------------
# Helper: compute p-value from t-statistic and degrees of freedom
# Uses scipy.stats.t.sf when available; falls back to a manual
# approximation based on the regularised incomplete beta function.
# ---------------------------------------------------------------------------

def _t_survival(t_stat: float, df: int) -> float:
    """Return the two-tailed p-value for a t-statistic with *df* degrees of freedom."""
    try:
        from scipy.stats import t as t_dist
        return float(t_dist.sf(abs(t_stat), df) * 2)
    except ImportError:
        pass

    # Fallback: regularised incomplete beta function via the continued-fraction
    # expansion (Lentz's method).  Accurate to ~12 digits for typical df values.
    x = df / (df + t_stat ** 2)
    a, b = df / 2.0, 0.5

    def _betainc(x, a, b, max_iter=200, tol=1e-14):
        from math import lgamma, exp, log
        if x <= 0:
            return 0.0
        if x >= 1:
            return 1.0
        lbeta = lgamma(a + b) - lgamma(a) - lgamma(b)
        front = exp(log(x) * a + log(1 - x) * b + lbeta) / a
        f = 1.0
        c = 1.0
        d = 1.0 - (a + b) * x / (a + 1.0)
        if abs(d) < 1e-30:
            d = 1e-30
        d = 1.0 / d
        f = d
        for m in range(1, max_iter + 1):
            num = m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m))
            d = 1.0 + num * d
            if abs(d) < 1e-30:
                d = 1e-30
            c = 1.0 + num / c
            if abs(c) < 1e-30:
                c = 1e-30
            d = 1.0 / d
            f *= d * c
            num = -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1))
            d = 1.0 + num * d
            if abs(d) < 1e-30:
                d = 1e-30
            c = 1.0 + num / c
            if abs(c) < 1e-30:
                c = 1e-30
            d = 1.0 / d
            delta = d * c
            f *= delta
            if abs(delta - 1.0) < tol:
                break
        return front * f

    p = _betainc(x, a, b)
    return min(max(p, 0.0), 1.0)


def _t_critical_two_tail(alpha: float, df: int) -> float:
    """Return the two-tailed t critical value for *alpha* and *df*."""
    try:
        from scipy.stats import t as t_dist
        return float(t_dist.ppf(1 - alpha / 2, df))
    except ImportError:
        z = 1.959964
        g1 = (z ** 3 + z) / (4 * df)
        g2 = (5 * z ** 5 + 16 * z ** 3 + 3 * z) / (96 * df ** 2)
        return z + g1 + g2


@router.get(
    "/effectiveness/statistical-analysis",
    operation_id="get_statistical_analysis",
    summary="Research-grade statistical analysis of intervention effectiveness",
)
@limiter.limit("30/minute")
async def get_statistical_analysis(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Compute research-grade inferential statistics on SmartStudy intervention effectiveness.

    Performs a **paired-samples t-test** on before/after scores from the user's
    completed study plans and returns:

    - **paired_scores** -- Each study plan's before score, after score, improvement, and topic.
    - **descriptive_statistics** -- Mean, median, standard deviation, min, and max improvement.
    - **inferential_statistics** -- t-statistic, p-value, degrees of freedom, Cohen's d
      effect size with interpretation, 95 % confidence interval, and significance flag.
    - **sample_adequacy** -- Whether the sample meets the n >= 30 threshold for
      conventional statistical power, with a note when underpowered.
    - **interpretation** -- A plain-English summary suitable for a research defense slide.

    Edge cases handled:
    - *n = 0* -- returns a message indicating no data.
    - *n = 1* -- cannot compute variance; returns descriptive stats only.
    - *zero variance* -- all improvements identical; t-test is undefined.
    """
    user_id = current_user.id

    # Check cache first
    cache_key = f"analytics:statistical_analysis:{user_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    # 1. Query study plans with both before and after scores
    plans = (
        db.query(StudyPlan)
        .filter(
            StudyPlan.user_id == user_id,
            StudyPlan.before_score.isnot(None),
            StudyPlan.after_score.isnot(None),
        )
        .order_by(StudyPlan.created_at)
        .all()
    )

    n = len(plans)

    # --- Edge case: no data ---
    if n == 0:
        result = {
            "sample_size": 0,
            "paired_scores": [],
            "descriptive_statistics": None,
            "inferential_statistics": None,
            "sample_adequacy": {
                "is_adequate": False,
                "current_n": 0,
                "recommended_n": 30,
                "power_note": (
                    "No study plans with before/after scores found. "
                    "Complete study plans and record scores to enable statistical analysis."
                ),
            },
            "interpretation": (
                "Insufficient data to perform statistical analysis. "
                "No completed study plans with both before and after scores were found."
            ),
        }
        cache_set(cache_key, result, TTL_ANALYTICS)
        return result

    # Build paired-score list
    paired_scores = []
    improvements: List[float] = []
    for plan in plans:
        before = float(plan.before_score)
        after = float(plan.after_score)
        imp = round(after - before, 2)
        paired_scores.append(
            {
                "before": before,
                "after": after,
                "improvement": imp,
                "topic": plan.topic,
            }
        )
        improvements.append(imp)

    # 2. Descriptive statistics (always computable when n >= 1)
    mean_imp = round(pystats.mean(improvements), 2)
    median_imp = round(pystats.median(improvements), 2)
    min_imp = round(min(improvements), 2)
    max_imp = round(max(improvements), 2)
    std_imp = round(pystats.stdev(improvements), 4) if n >= 2 else 0.0

    descriptive = {
        "mean_improvement": mean_imp,
        "median_improvement": median_imp,
        "std_improvement": round(std_imp, 2),
        "min_improvement": min_imp,
        "max_improvement": max_imp,
    }

    # --- Edge case: n = 1 (cannot compute t-test) ---
    if n == 1:
        result = {
            "sample_size": 1,
            "paired_scores": paired_scores,
            "descriptive_statistics": descriptive,
            "inferential_statistics": None,
            "sample_adequacy": {
                "is_adequate": False,
                "current_n": 1,
                "recommended_n": 30,
                "power_note": (
                    "Only one observation. At least 2 are needed for inferential statistics, "
                    "and 30+ for adequate statistical power."
                ),
            },
            "interpretation": (
                "Only one study plan with before/after scores exists. "
                "Cannot perform inferential statistical analysis with a single observation."
            ),
        }
        cache_set(cache_key, result, TTL_ANALYTICS)
        return result

    # --- Edge case: zero variance (all improvements identical) ---
    if std_imp == 0.0:
        result = {
            "sample_size": n,
            "paired_scores": paired_scores,
            "descriptive_statistics": descriptive,
            "inferential_statistics": {
                "t_statistic": None,
                "p_value": None,
                "degrees_of_freedom": n - 1,
                "cohens_d": None,
                "effect_size_interpretation": "undefined",
                "confidence_interval_95": {
                    "lower": mean_imp,
                    "upper": mean_imp,
                },
                "is_statistically_significant": False,
                "significance_level": 0.05,
            },
            "sample_adequacy": {
                "is_adequate": n >= 30,
                "current_n": n,
                "recommended_n": 30,
                "power_note": (
                    "All improvements are identical (zero variance). "
                    "The t-test is undefined when the standard deviation is zero."
                ),
            },
            "interpretation": (
                f"All {n} study plan interventions produced the same improvement "
                f"of {mean_imp} percentage points. Because there is no variability, "
                "a t-test cannot be computed."
            ),
        }
        cache_set(cache_key, result, TTL_ANALYTICS)
        return result

    # 3. Paired t-test  t = mean_diff / (std_diff / sqrt(n))
    df = n - 1
    se = std_imp / math.sqrt(n)
    t_stat = round(mean_imp / se, 2)

    # p-value (two-tailed)
    p_value = round(_t_survival(t_stat, df), 4)

    # 4. Cohen's d  = mean_diff / std_diff
    cohens_d = round(mean_imp / std_imp, 2)

    if abs(cohens_d) < 0.2:
        effect_interp = "negligible"
    elif abs(cohens_d) < 0.5:
        effect_interp = "small"
    elif abs(cohens_d) < 0.8:
        effect_interp = "medium"
    else:
        effect_interp = "large"

    # 5. 95% confidence interval
    t_crit = _t_critical_two_tail(0.05, df)
    margin = round(t_crit * se, 2)
    ci_lower = round(mean_imp - margin, 2)
    ci_upper = round(mean_imp + margin, 2)

    is_significant = p_value < 0.05

    inferential = {
        "t_statistic": t_stat,
        "p_value": p_value,
        "degrees_of_freedom": df,
        "cohens_d": cohens_d,
        "effect_size_interpretation": effect_interp,
        "confidence_interval_95": {"lower": ci_lower, "upper": ci_upper},
        "is_statistically_significant": is_significant,
        "significance_level": 0.05,
    }

    # 6. Sample adequacy
    is_adequate = n >= 30
    if is_adequate:
        power_note = (
            f"Sample size of {n} meets the recommended minimum of 30 "
            "for adequate statistical power."
        )
    else:
        power_note = (
            f"Sample size is below 30. Results should be interpreted with caution. "
            f"Collect {30 - n} more observations for conventional adequacy."
        )

    sample_adequacy = {
        "is_adequate": is_adequate,
        "current_n": n,
        "recommended_n": 30,
        "power_note": power_note,
    }

    # 7. Plain-English interpretation
    direction = "positive" if mean_imp > 0 else ("negative" if mean_imp < 0 else "zero")
    sig_text = "statistically significant" if is_significant else "not statistically significant"
    interpretation = (
        f"SmartStudy interventions show a {sig_text} {direction} effect on student grades "
        f"(t({df})={t_stat}, p={p_value}, d={cohens_d}). "
        f"The average improvement of {mean_imp} percentage points represents "
        f"a {effect_interp} effect size."
    )

    result = {
        "sample_size": n,
        "paired_scores": paired_scores,
        "descriptive_statistics": descriptive,
        "inferential_statistics": inferential,
        "sample_adequacy": sample_adequacy,
        "interpretation": interpretation,
    }

    cache_set(cache_key, result, TTL_ANALYTICS)
    return result


@router.get(
    "/cost-analysis",
    operation_id="get_cost_analysis",
    summary="OpenAI API cost analysis and projections",
)
@limiter.limit("30/minute")
async def get_cost_analysis(
    request: FastAPIRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Compute OpenAI API cost analysis and usage projections for the authenticated user.

    Aggregates token usage across all chat messages, counts conversations and study
    plans, and estimates costs based on the GPT-4 input rate approximation
    ($0.00003 per token).

    Returns monthly and semester projections based on usage velocity.
    """
    user_id = current_user.id

    cache_key = f"analytics:cost_analysis:{user_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    # Total tokens used across all user messages
    total_tokens_row = (
        db.query(func.coalesce(func.sum(ChatMessage.tokens_used), 0))
        .join(ChatConversation)
        .filter(ChatConversation.user_id == user_id)
        .scalar()
    )
    total_tokens = int(total_tokens_row)

    # Total messages
    total_messages = (
        db.query(func.count(ChatMessage.id))
        .join(ChatConversation)
        .filter(ChatConversation.user_id == user_id)
        .scalar()
    )

    # Total conversations
    total_conversations = (
        db.query(func.count(ChatConversation.id))
        .filter(ChatConversation.user_id == user_id)
        .scalar()
    )

    # Total study plans
    total_study_plans = (
        db.query(func.count(StudyPlan.id))
        .filter(StudyPlan.user_id == user_id)
        .scalar()
    )

    # Estimated cost
    estimated_cost_usd = total_tokens * 0.00003

    # Per-unit costs
    cost_per_conversation = (
        estimated_cost_usd / total_conversations if total_conversations else 0
    )
    cost_per_study_plan = (
        estimated_cost_usd / total_study_plans if total_study_plans else 0
    )
    cost_per_message = (
        estimated_cost_usd / total_messages if total_messages else 0
    )

    # Monthly / semester projection based on days active
    first_message_date = (
        db.query(func.min(ChatMessage.created_at))
        .join(ChatConversation)
        .filter(ChatConversation.user_id == user_id)
        .scalar()
    )

    if first_message_date:
        # Ensure timezone-aware comparison (SQLite returns naive datetimes)
        if first_message_date.tzinfo is None:
            first_message_date = first_message_date.replace(tzinfo=timezone.utc)
        days_active = max((datetime.now(timezone.utc) - first_message_date).days, 1)
    else:
        days_active = 1

    monthly_projection = (estimated_cost_usd / days_active) * 30
    semester_projection = monthly_projection * 4

    result = {
        "total_tokens": total_tokens,
        "total_messages": total_messages,
        "total_conversations": total_conversations,
        "total_study_plans": total_study_plans,
        "estimated_cost_usd": estimated_cost_usd,
        "cost_per_conversation": cost_per_conversation,
        "cost_per_study_plan": cost_per_study_plan,
        "cost_per_message": cost_per_message,
        "monthly_projection": monthly_projection,
        "semester_projection": semester_projection,
    }
    cache_set(cache_key, result, TTL_ANALYTICS)
    return result


@router.get(
    "/usage-summary",
    operation_id="get_usage_summary",
    summary="API usage analytics summary",
    response_description="Aggregated API usage metrics for the authenticated user.",
    responses={
        200: {
            "description": "Usage summary retrieved successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "total_requests": 142,
                        "daily_active_days": 12,
                        "most_used_endpoints": [
                            {"endpoint_path": "/api/v1/smartstudy/chat", "count": 45},
                            {"endpoint_path": "/api/v1/courses", "count": 30},
                        ],
                        "average_response_time_ms": 128.5,
                    }
                }
            },
        },
        401: {"description": "Missing or invalid JWT token."},
    },
)
@limiter.limit("30/minute")
async def get_usage_summary(
    request: FastAPIRequest,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return an API usage analytics summary for the authenticated user.

    **Query parameter:**
    - `days` (default: 30) -- Number of days to look back from today.

    Returns:
    - **total_requests** -- Total number of API requests logged in the period.
    - **daily_active_days** -- Count of distinct calendar dates with at least one request.
    - **most_used_endpoints** -- Top 5 endpoints ranked by request count.
    - **average_response_time_ms** -- Mean response time across all requests in the period.
    """
    user_id = current_user.id

    cache_key = f"analytics:usage_summary:{user_id}:{days}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    base_query = db.query(UsageLog).filter(
        UsageLog.user_id == user_id,
        UsageLog.timestamp >= cutoff,
    )

    # Total requests
    total_requests = base_query.count()

    # Daily active days -- count of distinct dates
    daily_active_days = (
        db.query(func.count(func.distinct(func.date(UsageLog.timestamp))))
        .filter(UsageLog.user_id == user_id, UsageLog.timestamp >= cutoff)
        .scalar()
    ) or 0

    # Most used endpoints -- top 5
    top_endpoints = (
        db.query(UsageLog.endpoint_path, func.count(UsageLog.id).label("cnt"))
        .filter(UsageLog.user_id == user_id, UsageLog.timestamp >= cutoff)
        .group_by(UsageLog.endpoint_path)
        .order_by(func.count(UsageLog.id).desc())
        .limit(5)
        .all()
    )
    most_used_endpoints = [
        {"endpoint_path": row[0], "count": row[1]} for row in top_endpoints
    ]

    # Average response time
    avg_response_time = (
        db.query(func.avg(UsageLog.response_time_ms))
        .filter(UsageLog.user_id == user_id, UsageLog.timestamp >= cutoff)
        .scalar()
    )
    average_response_time_ms = round(float(avg_response_time), 2) if avg_response_time else 0.0

    result = {
        "total_requests": total_requests,
        "daily_active_days": daily_active_days,
        "most_used_endpoints": most_used_endpoints,
        "average_response_time_ms": average_response_time_ms,
    }
    cache_set(cache_key, result, TTL_ANALYTICS)
    return result
