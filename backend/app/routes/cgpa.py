"""
CGPA Routes - API endpoints for CGPA calculations and analytics
"""
import logging
import re
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Dict, List
from app.database import get_db
from app.utils.auth import get_current_user
from app.utils.cgpa_calculator import CGPACalculator
from app.models.user import User
from app.models.course import Course, UserCourse, Semester
from app.models.task import Task
from app.services.cache_service import cache_get, cache_set, cache_delete_pattern
from app.services.cgpa_export_service import generate_csv, generate_pdf
from app.middleware.rate_limiter import limiter
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
@limiter.limit("20/minute")
def get_cgpa_dashboard(
    request: Request,
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
        cache_key = f"cgpa:dashboard:{current_user.id}"
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

        cgpa_data = CGPACalculator.get_user_cgpa_data(db, current_user.id)
        result = {
            "success": True,
            "data": cgpa_data
        }
        cache_set(cache_key, result, ttl=300)
        return result
    except Exception as e:
        logger.error("CGPA Dashboard Error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to calculate CGPA dashboard")


@router.get(
    "/current",
    operation_id="get_current_cgpa",
    summary="Get current CGPA only",
)
@limiter.limit("20/minute")
def get_current_cgpa(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get current CGPA only (lightweight endpoint)

    Returns:
        Current CGPA and total credits
    """
    try:
        cache_key = f"cgpa:current:{current_user.id}"
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

        cgpa_data = CGPACalculator.get_user_cgpa_data(db, current_user.id)
        result = {
            "success": True,
            "cgpa": cgpa_data['current']['cgpa'],
            "total_credits": cgpa_data['current']['total_credits'],
            "total_courses": cgpa_data['total_courses']
        }
        cache_set(cache_key, result, ttl=300)
        return result
    except Exception as e:
        logger.error("Current CGPA Error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to calculate current CGPA")


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

        # Batch-fetch all tasks for these courses (avoids N+1)
        uc_ids = [uc.id for uc in user_courses]
        all_tasks = db.query(Task).filter(
            Task.user_course_id.in_(uc_ids),
            Task.earned_marks.isnot(None)
        ).all() if uc_ids else []

        from collections import defaultdict
        tasks_by_uc = defaultdict(list)
        for t in all_tasks:
            tasks_by_uc[t.user_course_id].append(t)

        # Calculate semester GPA
        course_data = []
        for uc in user_courses:
            uc_tasks = tasks_by_uc.get(uc.id, [])

            # Only include tasks with valid weight and max_marks
            valid_tasks = [t for t in uc_tasks if t.weight and (t.max_marks or t.weight)]
            total_weight = sum(float(task.weight) for task in valid_tasks)
            weighted_score = sum(
                (float(task.earned_marks if task.earned_marks is not None else 0) / float(task.max_marks if task.max_marks else task.weight))
                * float(task.weight)
                for task in valid_tasks
            )
            current_score = (weighted_score / total_weight) * 100 if total_weight > 0 else 0

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

    except HTTPException as he:
        logger.warning("Semester GPA request rejected: %s %s", he.status_code, he.detail)
        raise
    except Exception as e:
        logger.error("Semester GPA Error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to calculate semester GPA")


@router.post(
    "/target",
    operation_id="calculate_target_requirements",
    summary="Calculate what GPA is needed to reach a target CGPA",
)
@limiter.limit("10/minute")
def calculate_target_requirements(
    request: Request,
    body: TargetCGPARequest,
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
            target_cgpa=body.target_cgpa,
            semester_credits=body.semester_credits
        )

        return {
            "success": True,
            "data": target_analysis
        }

    except Exception as e:
        logger.error("Target CGPA Error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to calculate target requirements")


@router.post(
    "/predict",
    operation_id="predict_final_cgpa",
    summary="Predict final CGPA based on predicted course performance",
)
@limiter.limit("10/minute")
def predict_final_cgpa(
    request: Request,
    body: PredictionRequest,
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
            predicted_courses=body.predicted_courses
        )

        return {
            "success": True,
            "data": prediction
        }

    except Exception as e:
        logger.error("Predict CGPA Error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to predict CGPA")


@router.get(
    "/breakdown",
    operation_id="get_semester_breakdown",
    summary="Get detailed semester-by-semester breakdown",
)
@limiter.limit("20/minute")
def get_semester_breakdown(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get detailed semester-by-semester breakdown

    Returns:
        List of all semesters with GPA and courses
    """
    try:
        cache_key = f"cgpa:breakdown:{current_user.id}"
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

        cgpa_data = CGPACalculator.get_user_cgpa_data(db, current_user.id)

        result = {
            "success": True,
            "semesters": cgpa_data['semesters'],
            "cumulative_cgpa": cgpa_data['current']['cgpa']
        }
        cache_set(cache_key, result, ttl=300)
        return result

    except Exception as e:
        logger.error("Semester Breakdown Error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get semester breakdown")


@router.get(
    "/analytics",
    operation_id="get_cgpa_analytics",
    summary="Get advanced CGPA analytics and insights",
)
@limiter.limit("20/minute")
def get_cgpa_analytics(
    request: Request,
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
        cache_key = f"cgpa:analytics:{current_user.id}"
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

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

        result = {
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
        cache_set(cache_key, result, ttl=300)
        return result

    except Exception as e:
        logger.error("CGPA Analytics Error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to calculate analytics")


@router.get(
    "/export/csv",
    operation_id="export_cgpa_csv",
    summary="Export CGPA data as CSV",
)
@limiter.limit("10/hour")
def export_cgpa_csv(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export CGPA data as a downloadable CSV file"""
    try:
        cgpa_data = CGPACalculator.get_user_cgpa_data(db, current_user.id)
        csv_bytes = generate_csv(cgpa_data)

        # Sanitize filename to prevent injection attacks
        safe_name = re.sub(r'[^\w\s-]', '', current_user.full_name or 'student')
        safe_name = safe_name.replace(' ', '_')[:50]
        filename = f"shadow-cgpa-{safe_name}.csv"

        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        logger.error("CSV export error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export CSV")


@router.get(
    "/export/pdf",
    operation_id="export_cgpa_pdf",
    summary="Export CGPA data as PDF",
)
@limiter.limit("10/hour")
def export_cgpa_pdf(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export CGPA data as a downloadable PDF transcript"""
    try:
        cgpa_data = CGPACalculator.get_user_cgpa_data(db, current_user.id)
        pdf_bytes = generate_pdf(cgpa_data, current_user.full_name or 'Student')

        # Sanitize filename to prevent injection attacks
        safe_name = re.sub(r'[^\w\s-]', '', current_user.full_name or 'student')
        safe_name = safe_name.replace(' ', '_')[:50]
        filename = f"shadow-cgpa-{safe_name}.pdf"

        return Response(
            content=bytes(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        logger.error("PDF export error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export PDF")
