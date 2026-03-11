"""
Course Routes - Course Management and Enrollment
"""
import os
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from uuid import UUID

from app.database import get_db

logger = logging.getLogger(__name__)
from app.models.course import Course, UserCourse, Semester
from app.models.user import User
from app.schemas.course import (
    CourseCreate,
    CourseResponse,
    UserCourseCreate,
    UserCourseUpdate,
    UserCourseResponse
)
from sqlalchemy.exc import IntegrityError
from app.utils.auth import get_current_user
from app.utils.pau_grading import PAUGradingSystem
from app.services.cache_service import cache_get, cache_set, cache_delete, cache_delete_pattern
from app.utils.input_sanitizer import sanitize_text

router = APIRouter()


@router.get(
    "/",
    response_model=List[CourseResponse],
    operation_id="list_courses",
    summary="List all available courses with optional filters",
)
async def get_all_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    level: str = None,
    status_filter: str = None,
    department: str = None
):
    """
    Get all available courses with optional filters

    Args:
        db: Database session
        level: Filter by level (e.g., '400')
        status_filter: Filter by status ('C', 'E', 'R')
        department: Filter by department

    Returns:
        List of courses
    """
    query = db.query(Course).filter(Course.is_approved == True)

    # Apply filters
    if level:
        query = query.filter(Course.level == level)
    if status_filter:
        query = query.filter(Course.status == status_filter)
    if department:
        query = query.filter(Course.department == department)

    courses = query.order_by(Course.code).all()
    return [CourseResponse(**course.to_dict()) for course in courses]


@router.get(
    "/{course_id}",
    response_model=CourseResponse,
    operation_id="get_course",
    summary="Get course details by ID",
)
async def get_course(course_id: str, db: Session = Depends(get_db)):
    """
    Get a specific course by ID

    Args:
        course_id: Course UUID
        db: Database session

    Returns:
        Course details
    """
    try:
        course_uuid = UUID(course_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid course ID format"
        )

    course = db.query(Course).filter(Course.id == course_uuid).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    return CourseResponse(**course.to_dict())


@router.post(
    "/",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="create_course",
    summary="Create a new course",
)
async def create_course(
    course_data: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new course (Admin or User)

    Args:
        course_data: Course creation data
        db: Database session

    Returns:
        Created course

    Raises:
        HTTPException: If course code already exists
    """
    # Only admins can create courses in the catalog
    admin_emails = set(
        e.strip().lower()
        for e in os.getenv("ADMIN_EMAILS", "").split(",")
        if e.strip()
    )
    if current_user.email.lower() not in admin_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create courses"
        )

    # Check if course code already exists
    existing_course = db.query(Course).filter(Course.code == course_data.code).first()
    if existing_course:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Course with code '{course_data.code}' already exists"
        )

    # Sanitize text fields to prevent XSS
    sanitized_title = sanitize_text(course_data.title)
    sanitized_description = sanitize_text(course_data.description) if course_data.description else None

    # Sanitize course code
    sanitized_code = sanitize_text(course_data.code)

    # Create new course
    new_course = Course(
        code=sanitized_code,
        title=sanitized_title,
        credits=course_data.credits,
        level=course_data.level,
        status=course_data.status,
        department=course_data.department,
        description=sanitized_description,
        created_by=str(current_user.id),
        is_approved=True  # Auto-approve for now
    )

    db.add(new_course)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Resource already exists")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save changes")
    db.refresh(new_course)

    return CourseResponse(**new_course.to_dict())


@router.post(
    "/enroll",
    response_model=UserCourseResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="enroll_in_course",
    summary="Enroll in a course",
)
async def enroll_in_course(
    enrollment_data: UserCourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enroll a user in a course

    Args:
        enrollment_data: Enrollment data
        current_user: Authenticated user (from JWT token)
        db: Database session

    Returns:
        User course enrollment details

    Raises:
        HTTPException: If course not found or already enrolled
    """
    try:
        course_uuid = UUID(enrollment_data.course_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid course ID format"
        )

    # Check if course exists
    course = db.query(Course).filter(Course.id == course_uuid).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Check if already enrolled in same semester (allows retakes in different semesters)
    # Resolve semester first so we can check against it
    semester_id = None
    if enrollment_data.semester_id:
        semester_id = UUID(enrollment_data.semester_id)
    else:
        active_sem = db.query(Semester).filter(
            Semester.user_id == current_user.id,
            Semester.is_active == True
        ).first()
        if active_sem:
            semester_id = active_sem.id

    dup_query = db.query(UserCourse).filter(
        UserCourse.user_id == current_user.id,
        UserCourse.course_id == course_uuid,
    )
    if semester_id is None:
        dup_query = dup_query.filter(UserCourse.semester_id.is_(None))
    else:
        dup_query = dup_query.filter(UserCourse.semester_id == semester_id)

    if dup_query.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already enrolled in this course for this semester"
        )

    # Create enrollment (semester_id already resolved above)
    new_enrollment = UserCourse(
        user_id=current_user.id,
        course_id=course_uuid,
        semester_id=semester_id,
        is_carryover=enrollment_data.is_carryover,
        is_priority=enrollment_data.is_priority,
        ca_score=0,
        completion_rate=0
    )

    db.add(new_enrollment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Resource already exists")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save changes")
    db.refresh(new_enrollment)

    cache_delete_pattern(f"courses:enrolled:{current_user.id}:*")

    return UserCourseResponse(**new_enrollment.to_dict())


@router.get(
    "/my-courses/",
    response_model=List[UserCourseResponse],
    operation_id="list_my_courses",
    summary="List enrolled courses",
)
async def get_my_courses(
    db: Session = Depends(get_db),
    active_only: bool = True,
    current_user: User = Depends(get_current_user)
):
    """
    Get all courses the user is enrolled in

    Args:
        current_user: Authenticated user (from JWT token)
        db: Database session
        active_only: Only return active semester courses

    Returns:
        List of user's enrolled courses with details
    """
    cache_key = f"courses:enrolled:{current_user.id}:{active_only}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    # Query user courses with eager-loaded relationships to avoid N+1
    query = db.query(UserCourse).options(
        joinedload(UserCourse.course),
        joinedload(UserCourse.semester)
    ).filter(UserCourse.user_id == current_user.id)

    # Filter by active semester if requested
    if active_only:
        active_sem = db.query(Semester).filter(
            Semester.user_id == current_user.id,
            Semester.is_active == True
        ).first()
        if active_sem:
            query = query.filter(
                (UserCourse.semester_id == active_sem.id) | (UserCourse.semester_id.is_(None))
            )

    enrollments = query.all()
    result = [UserCourseResponse(**enrollment.to_dict()).model_dump() for enrollment in enrollments]
    cache_set(cache_key, result, ttl=300)
    return result


@router.get(
    "/my-courses/{user_course_id}",
    response_model=UserCourseResponse,
    operation_id="get_enrollment",
    summary="Get enrollment details",
)
async def get_user_course(
    user_course_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific enrollment details

    Args:
        user_course_id: User course enrollment ID
        current_user: Authenticated user (from JWT token)
        db: Database session

    Returns:
        Enrollment details
    """
    try:
        enrollment_uuid = UUID(user_course_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid enrollment ID format"
        )

    enrollment = db.query(UserCourse).filter(
        UserCourse.id == enrollment_uuid,
        UserCourse.user_id == current_user.id
    ).first()

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )

    return UserCourseResponse(**enrollment.to_dict())


@router.patch(
    "/my-courses/{user_course_id}",
    response_model=UserCourseResponse,
    operation_id="update_enrollment",
    summary="Update enrollment details",
)
async def update_user_course(
    user_course_id: str,
    update_data: UserCourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update enrollment details (marks, priority, etc.)

    Args:
        user_course_id: User course enrollment ID
        update_data: Update data
        current_user: Authenticated user (from JWT token)
        db: Database session

    Returns:
        Updated enrollment
    """
    try:
        enrollment_uuid = UUID(user_course_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid enrollment ID format"
        )

    enrollment = db.query(UserCourse).filter(
        UserCourse.id == enrollment_uuid,
        UserCourse.user_id == current_user.id
    ).first()

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )

    # Update fields if provided
    if update_data.is_carryover is not None:
        enrollment.is_carryover = update_data.is_carryover
    if update_data.is_priority is not None:
        enrollment.is_priority = update_data.is_priority
    if update_data.ca_score is not None:
        enrollment.ca_score = update_data.ca_score
    if update_data.participation_score is not None:
        enrollment.participation_score = update_data.participation_score
    if update_data.exam_score is not None:
        enrollment.exam_score = update_data.exam_score

    # Recalculate scores and grades from component scores
    ca = float(enrollment.ca_score) if enrollment.ca_score is not None else 0.0
    participation = float(enrollment.participation_score) if enrollment.participation_score is not None else 0.0

    if enrollment.exam_score is not None:
        total = ca + participation + float(enrollment.exam_score)
        enrollment.current_score = min(total, 100)
        enrollment.current_grade_point = PAUGradingSystem.get_grade_point(enrollment.current_score)
        enrollment.letter_grade = PAUGradingSystem.get_letter_grade(enrollment.current_score)
        enrollment.predicted_score = enrollment.current_score
        enrollment.predicted_grade_point = enrollment.current_grade_point
        enrollment.predicted_letter_grade = enrollment.letter_grade
    elif enrollment.predicted_exam_score is not None:
        predicted_total = ca + participation + float(enrollment.predicted_exam_score)
        enrollment.predicted_score = min(predicted_total, 100)
        enrollment.predicted_grade_point = PAUGradingSystem.get_grade_point(enrollment.predicted_score)
        enrollment.predicted_letter_grade = PAUGradingSystem.get_letter_grade(enrollment.predicted_score)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Resource already exists")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save changes")
    db.refresh(enrollment)

    # Invalidate CGPA and course caches when scores change
    if any(v is not None for v in [update_data.ca_score, update_data.participation_score, update_data.exam_score]):
        cache_delete_pattern(f"cgpa:*:{current_user.id}")
        cache_delete_pattern(f"courses:enrolled:{current_user.id}:*")

        # Send CGPA alert email when exam scores are entered (significant CGPA change)
        if update_data.exam_score is not None and current_user.target_cgpa:
            try:
                from app.utils.cgpa_calculator import CGPACalculator
                from app.services.email_service import send_cgpa_alert_email
                cgpa_data = CGPACalculator.get_user_cgpa_data(db, current_user.id)
                new_cgpa = cgpa_data['current']['cgpa']
                classification = cgpa_data['current'].get('classification', 'Unclassified')
                send_cgpa_alert_email(
                    to=current_user.email,
                    name=current_user.full_name or "Student",
                    current_cgpa=float(new_cgpa),
                    target_cgpa=float(current_user.target_cgpa),
                    classification=classification,
                )
            except Exception as email_err:
                import logging
                logging.getLogger(__name__).warning(f"Failed to send CGPA alert email: {email_err}")

    return UserCourseResponse(**enrollment.to_dict())


@router.delete(
    "/my-courses/{user_course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="unenroll_from_course",
    summary="Unenroll from a course",
)
async def unenroll_from_course(
    user_course_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Unenroll from a course (delete enrollment)

    Args:
        user_course_id: User course enrollment ID
        current_user: Authenticated user (from JWT token)
        db: Database session

    Returns:
        No content
    """
    try:
        enrollment_uuid = UUID(user_course_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid enrollment ID format"
        )

    enrollment = db.query(UserCourse).filter(
        UserCourse.id == enrollment_uuid,
        UserCourse.user_id == current_user.id
    ).first()

    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )

    db.delete(enrollment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Resource already exists")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save changes")

    cache_delete_pattern(f"cgpa:*:{current_user.id}")
    cache_delete_pattern(f"courses:enrolled:{current_user.id}:*")

    return None
