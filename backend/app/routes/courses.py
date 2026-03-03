"""
Course Routes - Course Management and Enrollment
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.course import Course, UserCourse, Semester
from app.models.user import User
from app.schemas.course import (
    CourseCreate,
    CourseResponse,
    UserCourseCreate,
    UserCourseUpdate,
    UserCourseResponse
)
from app.utils.auth import get_current_user

router = APIRouter()


async def get_user_from_token(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
) -> User:
    """Extract and validate user from Authorization header"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme"
        )
    token = authorization.replace("Bearer ", "")
    return await get_current_user(token, db)


@router.get(
    "/",
    response_model=List[CourseResponse],
    operation_id="list_courses",
    summary="List all available courses with optional filters",
)
async def get_all_courses(
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db)
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
    # Check if course code already exists
    existing_course = db.query(Course).filter(Course.code == course_data.code).first()
    if existing_course:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Course with code '{course_data.code}' already exists"
        )

    # Create new course
    new_course = Course(
        code=course_data.code,
        title=course_data.title,
        credits=course_data.credits,
        level=course_data.level,
        status=course_data.status,
        department=course_data.department,
        description=course_data.description,
        created_by="user",  # TODO: Get from authenticated user
        is_approved=True  # Auto-approve for now
    )

    db.add(new_course)
    db.commit()
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
    current_user: User = Depends(get_user_from_token)
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

    # Check if already enrolled
    existing_enrollment = db.query(UserCourse).filter(
        UserCourse.user_id == current_user.id,
        UserCourse.course_id == course_uuid
    ).first()

    if existing_enrollment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already enrolled in this course"
        )

    # Resolve semester: explicit > active > none
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

    # Create enrollment
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
    db.commit()
    db.refresh(new_enrollment)

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
    current_user: User = Depends(get_user_from_token)
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
    # Query user courses
    query = db.query(UserCourse).filter(UserCourse.user_id == current_user.id)

    # TODO: Filter by active semester if active_only is True

    enrollments = query.all()
    return [UserCourseResponse(**enrollment.to_dict()) for enrollment in enrollments]


@router.get(
    "/my-courses/{user_course_id}",
    response_model=UserCourseResponse,
    operation_id="get_enrollment",
    summary="Get enrollment details",
)
async def get_user_course(
    user_course_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_token)
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
    current_user: User = Depends(get_user_from_token)
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

    # TODO: Recalculate predicted scores and grades

    db.commit()
    db.refresh(enrollment)

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
    current_user: User = Depends(get_user_from_token)
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
    db.commit()

    return None
