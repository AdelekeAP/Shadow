"""
CGPA Routes - API endpoints for CGPA calculations and analytics
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List
from app.database import get_db
from app.utils.auth import get_current_user
from app.utils.cgpa_calculator import CGPACalculator
from app.models.user import User
from app.models.course import Course, UserCourse, Semester
from app.models.task import Task
from pydantic import BaseModel

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/cgpa", tags=["CGPA"])


class TargetCGPARequest(BaseModel):
    """Request model for target CGPA calculation"""
    target_cgpa: float
    semester_credits: int


class PredictionRequest(BaseModel):
    """Request model for CGPA prediction"""
    predicted_courses: List[Dict]


@router.get(
    "/dashboard",
    operation_id="get_cgpa_dashboard",
    summary="Get comprehensive CGPA dashboard data",
)
def get_cgpa_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get comprehensive CGPA dashboard data for current user

    Returns:
        - Current CGPA
        - Semester breakdown
        - Predictions
        - Target analysis
    """
    try:
        cgpa_data = CGPACalculator.get_user_cgpa_data(db, current_user.id)
        return {
            "success": True,
            "data": cgpa_data
        }
    except Exception as e:
        logger.error("CGPA Dashboard Error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error calculating CGPA: {str(e)}")


@router.get(
    "/current",
    operation_id="get_current_cgpa",
    summary="Get current CGPA only",
)
def get_current_cgpa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get current CGPA only (lightweight endpoint)

    Returns:
        Current CGPA and total credits
    """
    try:
        cgpa_data = CGPACalculator.get_user_cgpa_data(db, current_user.id)
        return {
            "success": True,
            "cgpa": cgpa_data['current']['cgpa'],
            "total_credits": cgpa_data['current']['total_credits'],
            "total_courses": cgpa_data['total_courses']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating CGPA: {str(e)}")


@router.get(
    "/semester/{semester}/{year}",
    operation_id="get_semester_gpa",
    summary="Get GPA for a specific semester",
)
def get_semester_gpa(
    semester: str,
    year: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get GPA for a specific semester

    Args:
        semester: Semester name (e.g., "Fall", "Spring")
        year: Year (e.g., 2024)

    Returns:
        Semester GPA and course breakdown
    """
    try:
        # Find matching semester for this user
        semester_obj = db.query(Semester).filter(
            Semester.user_id == current_user.id,
            Semester.name.ilike(f"%{semester}%{year}%")
        ).first()

        if not semester_obj:
            # Try academic_year match
            semester_obj = db.query(Semester).filter(
                Semester.user_id == current_user.id,
                Semester.academic_year.ilike(f"%{year}%"),
                Semester.name.ilike(f"%{semester}%")
            ).first()

        if not semester_obj:
            raise HTTPException(
                status_code=404,
                detail=f"No semester found for {semester} {year}"
            )

        # Get user courses for this semester
        user_courses = db.query(UserCourse).filter(
            UserCourse.user_id == current_user.id,
            UserCourse.semester_id == semester_obj.id
        ).all()

        if not user_courses:
            raise HTTPException(
                status_code=404,
                detail=f"No courses found for {semester} {year}"
            )

        # Calculate semester GPA
        course_data = []
        for uc in user_courses:
            tasks = db.query(Task).filter(
                Task.user_course_id == uc.id,
                Task.earned_marks.isnot(None)
            ).all()

            total_weight = sum(task.weight for task in tasks if task.weight)
            weighted_score = sum((task.earned_marks or 0) * (task.weight / 100) for task in tasks if task.weight)
            current_score = weighted_score if total_weight > 0 else 0

            course_data.append({
                'credits': uc.course.credits if uc.course else 0,
                'score': current_score,
                'course_code': uc.course.code if uc.course else 'Unknown',
                'title': uc.course.title if uc.course else 'Unknown'
            })

        semester_result = CGPACalculator.calculate_semester_gpa(course_data)

        return {
            "success": True,
            "semester": f"{semester} {year}",
            "gpa": semester_result['gpa'],
            "total_credits": semester_result['total_credits'],
            "courses": course_data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating semester GPA: {str(e)}")


@router.post(
    "/target",
    operation_id="calculate_target_requirements",
    summary="Calculate what GPA is needed to reach a target CGPA",
)
def calculate_target_requirements(
    request: TargetCGPARequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Calculate what GPA is needed to reach a target CGPA

    Args:
        target_cgpa: Desired cumulative GPA
        semester_credits: Credits for upcoming semester

    Returns:
        Required GPA and feasibility analysis
    """
    try:
        cgpa_data = CGPACalculator.get_user_cgpa_data(db, current_user.id)
        current_cgpa = cgpa_data['current']['cgpa']
        current_credits = cgpa_data['current']['total_credits']

        target_analysis = CGPACalculator.calculate_target_semester_gpa(
            current_cgpa=current_cgpa,
            current_credits=current_credits,
            target_cgpa=request.target_cgpa,
            semester_credits=request.semester_credits
        )

        return {
            "success": True,
            "data": target_analysis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating target: {str(e)}")


@router.post(
    "/predict",
    operation_id="predict_final_cgpa",
    summary="Predict final CGPA based on predicted course performance",
)
def predict_final_cgpa(
    request: PredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Predict final CGPA based on predicted course performance

    Args:
        predicted_courses: List of courses with predicted scores

    Returns:
        Predicted final CGPA
    """
    try:
        cgpa_data = CGPACalculator.get_user_cgpa_data(db, current_user.id)
        current_cgpa = cgpa_data['current']['cgpa']
        current_credits = cgpa_data['current']['total_credits']

        prediction = CGPACalculator.predict_final_cgpa(
            current_cgpa=current_cgpa,
            current_credits=current_credits,
            predicted_courses=request.predicted_courses
        )

        return {
            "success": True,
            "data": prediction
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error predicting CGPA: {str(e)}")


@router.get(
    "/breakdown",
    operation_id="get_semester_breakdown",
    summary="Get detailed semester-by-semester breakdown",
)
def get_semester_breakdown(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get detailed semester-by-semester breakdown

    Returns:
        List of all semesters with GPA and courses
    """
    try:
        cgpa_data = CGPACalculator.get_user_cgpa_data(db, current_user.id)

        return {
            "success": True,
            "semesters": cgpa_data['semesters'],
            "cumulative_cgpa": cgpa_data['current']['cgpa']
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting breakdown: {str(e)}")


@router.get(
    "/analytics",
    operation_id="get_cgpa_analytics",
    summary="Get advanced CGPA analytics and insights",
)
def get_cgpa_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get advanced CGPA analytics and insights

    Returns:
        - Performance trends
        - Best/worst semesters
        - Grade distribution
        - Improvement suggestions
    """
    try:
        cgpa_data = CGPACalculator.get_user_cgpa_data(db, current_user.id)
        semesters = cgpa_data['semesters']

        if not semesters:
            return {
                "success": True,
                "message": "No data available yet",
                "analytics": None
            }

        # Calculate trends with semester names
        gpa_values = []
        semester_names = []

        for s in semesters:
            if s['courses']:
                sem_result = CGPACalculator.calculate_semester_gpa(s['courses'])
                gpa_values.append(sem_result['gpa'])
                semester_names.append(s['name'])

        # Best and worst semesters
        best_gpa = max(gpa_values) if gpa_values else 0
        worst_gpa = min(gpa_values) if gpa_values else 0
        avg_gpa = sum(gpa_values) / len(gpa_values) if gpa_values else 0

        # Trend analysis
        if len(gpa_values) >= 2:
            trend = "Improving" if gpa_values[-1] > gpa_values[0] else "Declining" if gpa_values[-1] < gpa_values[0] else "Stable"
        else:
            trend = "Insufficient data"

        # Grade distribution
        all_courses = []
        for semester in semesters:
            all_courses.extend(semester['courses'])

        from app.utils.pau_grading import PAUGradingSystem
        grade_distribution = {}
        for course in all_courses:
            if course['score'] > 0:
                grade = PAUGradingSystem.get_letter_grade(course['score'])
                grade_distribution[grade] = grade_distribution.get(grade, 0) + 1

        return {
            "success": True,
            "analytics": {
                "best_semester_gpa": round(best_gpa, 2),
                "worst_semester_gpa": round(worst_gpa, 2),
                "average_semester_gpa": round(avg_gpa, 2),
                "trend": trend,
                "grade_distribution": grade_distribution,
                "total_semesters": len(gpa_values),
                "semester_gpa_history": gpa_values,
                "semester_names": semester_names
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating analytics: {str(e)}")
