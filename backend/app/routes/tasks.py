"""
Task Routes - Task Management and Tracking
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from app.database import get_db
from app.models.task import Task
from app.models.course import UserCourse, Course
from app.models.user import User
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskComplete,
    TaskResponse,
    TaskWithCourse,
    TaskStats,
    CourseTaskSummary
)
from app.utils.auth import get_current_user
from app.utils.grading import calculate_predicted_grade

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


def update_course_grades(user_course: UserCourse, db: Session):
    """
    Calculate and update predicted grades for a course enrollment
    Considers both completed and pending tasks for realistic predictions

    Args:
        user_course: UserCourse instance to update
        db: Database session
    """
    ca_score = float(user_course.ca_score) if user_course.ca_score else 0.0
    exam_score = float(user_course.exam_score) if user_course.exam_score else None

    # Get all tasks for this course to analyze completion
    all_tasks = db.query(Task).filter(Task.user_course_id == user_course.id).all()

    # Analyze pending CA tasks
    pending_ca_tasks = [t for t in all_tasks if not t.is_completed and t.category == "CA"]
    overdue_ca_tasks = [
        t for t in pending_ca_tasks
        if t.due_date and t.due_date.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)
    ]

    # Calculate potential CA loss from pending/overdue tasks
    pending_ca_weight = sum(float(t.weight) for t in pending_ca_tasks)
    overdue_ca_weight = sum(float(t.weight) for t in overdue_ca_tasks)

    # Adjust CA prediction based on task completion
    # Assume 70% performance on overdue tasks, 80% on pending tasks
    adjusted_ca_prediction = ca_score
    adjusted_ca_prediction += overdue_ca_weight * 0.70  # Likely to get partial marks if rushed
    adjusted_ca_prediction += (pending_ca_weight - overdue_ca_weight) * 0.80  # Regular pending tasks

    # For prediction: use adjusted CA if there are pending tasks, otherwise use actual CA
    # This ensures we always predict EXAM even after CA is complete
    prediction_ca = adjusted_ca_prediction if pending_ca_tasks else ca_score

    # Calculate predicted grades
    # IMPORTANT: Always predict, even if all CA tasks are done (we still need to predict EXAM)
    current_score, predicted_score, predicted_letter, predicted_gp = calculate_predicted_grade(
        ca_score=prediction_ca,
        exam_score=exam_score,
        course_difficulty=1.0  # Default difficulty, can be customized per course
    )

    # Update UserCourse with calculations
    user_course.current_score = current_score
    user_course.predicted_score = predicted_score
    user_course.predicted_letter_grade = predicted_letter
    user_course.predicted_grade_point = predicted_gp

    # If exam is taken, also update final grade
    if exam_score is not None:
        user_course.letter_grade = predicted_letter
        user_course.current_grade_point = predicted_gp

    db.commit()


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="create_task",
    summary="Create a new academic task",
)
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_token)
):
    """
    Create a new task for a course

    Args:
        task_data: Task creation data
        db: Database session
        current_user: Authenticated user

    Returns:
        Created task

    Raises:
        HTTPException: If user_course not found or CA limit exceeded
    """
    # Verify user owns the course enrollment
    try:
        user_course_uuid = UUID(task_data.user_course_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_course_id format"
        )

    user_course = db.query(UserCourse).filter(
        UserCourse.id == user_course_uuid,
        UserCourse.user_id == current_user.id
    ).first()

    if not user_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course enrollment not found"
        )

    # Check CA total doesn't exceed 30 (5 marks reserved for participation)
    if task_data.category == "CA":
        existing_ca_total = db.query(func.sum(Task.weight)).filter(
            Task.user_course_id == user_course_uuid,
            Task.category == "CA"
        ).scalar() or 0

        if float(existing_ca_total) + float(task_data.weight) > 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Total CA cannot exceed 30 marks (5 marks reserved for participation). Current: {existing_ca_total}, Adding: {task_data.weight}"
            )

    # Create new task
    new_task = Task(
        user_id=current_user.id,
        user_course_id=user_course_uuid,
        title=task_data.title,
        description=task_data.description,
        task_type=task_data.task_type,
        weight=task_data.weight,
        max_marks=task_data.max_marks if task_data.max_marks else task_data.weight,
        category=task_data.category,
        due_date=task_data.due_date,
        effort_estimate=task_data.effort_estimate,
        is_completed=task_data.is_completed,
        earned_marks=task_data.earned_marks,
        completed_at=datetime.now(timezone.utc) if task_data.is_completed else None
    )

    # Calculate initial priority
    new_task.calculate_priority(
        current_cgpa=float(current_user.current_cgpa) if current_user.current_cgpa else None,
        target_cgpa=float(current_user.target_cgpa) if current_user.target_cgpa else None
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # Update UserCourse scores if task is completed with marks
    if new_task.is_completed and new_task.earned_marks:
        if new_task.category == "CA":
            # Update CA score
            ca_tasks = db.query(Task).filter(
                Task.user_course_id == user_course_uuid,
                Task.category == "CA",
                Task.is_completed == True,
                Task.earned_marks.isnot(None)
            ).all()
            user_course.ca_score = sum(float(t.earned_marks) for t in ca_tasks)

        elif new_task.category == "EXAM":
            # Update EXAM score
            exam_tasks = db.query(Task).filter(
                Task.user_course_id == user_course_uuid,
                Task.category == "EXAM",
                Task.is_completed == True,
                Task.earned_marks.isnot(None)
            ).all()
            user_course.exam_score = sum(float(t.earned_marks) for t in exam_tasks)

        # Update completion rate
        all_tasks = db.query(Task).filter(Task.user_course_id == user_course_uuid).count()
        completed = db.query(Task).filter(
            Task.user_course_id == user_course_uuid,
            Task.is_completed == True
        ).count()
        user_course.completion_rate = (completed / all_tasks * 100) if all_tasks > 0 else 0

        # Calculate and update predicted grades
        update_course_grades(user_course, db)
    else:
        # Even for pending tasks, update predictions (accounts for new pending work)
        update_course_grades(user_course, db)

    return TaskResponse(**new_task.to_dict())


@router.get(
    "/",
    response_model=List[TaskWithCourse],
    operation_id="list_tasks",
    summary="List tasks with optional filters",
)
async def get_user_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_token),
    course_id: Optional[str] = None,
    is_completed: Optional[bool] = None,
    category: Optional[str] = None,
    is_urgent: Optional[bool] = None
):
    """
    Get all tasks for the current user with optional filters

    Args:
        db: Database session
        current_user: Authenticated user
        course_id: Filter by course
        is_completed: Filter by completion status
        category: Filter by category ('CA' or 'EXAM')
        is_urgent: Filter by urgency

    Returns:
        List of user tasks with course information
    """
    query = db.query(Task).filter(Task.user_id == current_user.id)

    # Apply filters
    if course_id:
        try:
            course_uuid = UUID(course_id)
            query = query.join(UserCourse).filter(UserCourse.course_id == course_uuid)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid course_id format"
            )

    if is_completed is not None:
        query = query.filter(Task.is_completed == is_completed)

    if category:
        query = query.filter(Task.category == category.upper())

    if is_urgent is not None:
        query = query.filter(Task.is_urgent == is_urgent)

    tasks = query.order_by(Task.priority_score.desc(), Task.due_date).all()

    # Add course information to each task
    tasks_with_course = []
    for task in tasks:
        task_dict = task.to_dict()
        # Get course info from user_course relationship
        user_course = db.query(UserCourse).filter(UserCourse.id == task.user_course_id).first()
        if user_course and user_course.course:
            task_dict['course_code'] = user_course.course.code
            task_dict['course_title'] = user_course.course.title
        tasks_with_course.append(TaskWithCourse(**task_dict))

    return tasks_with_course


@router.get(
    "/stats",
    response_model=TaskStats,
    operation_id="get_task_stats",
    summary="Get task completion statistics",
)
async def get_task_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_token)
):
    """
    Get task statistics for the current user

    Args:
        db: Database session
        current_user: Authenticated user

    Returns:
        Task statistics
    """
    all_tasks = db.query(Task).filter(Task.user_id == current_user.id).all()

    total_tasks = len(all_tasks)
    completed_tasks = len([t for t in all_tasks if t.is_completed])
    pending_tasks = total_tasks - completed_tasks

    # Count overdue tasks (make due_date timezone-aware for comparison)
    overdue_tasks = 0
    for t in all_tasks:
        if not t.is_completed and t.due_date:
            due_date_aware = t.due_date
            if due_date_aware.tzinfo is None:
                due_date_aware = due_date_aware.replace(tzinfo=timezone.utc)
            if due_date_aware < datetime.now(timezone.utc):
                overdue_tasks += 1

    ca_tasks = [t for t in all_tasks if t.category == "CA"]
    total_ca_available = sum(float(t.weight) for t in ca_tasks)
    total_ca_earned = sum(
        float(t.earned_marks) for t in ca_tasks
        if t.is_completed and t.earned_marks
    )

    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0

    completed_with_marks = [t for t in all_tasks if t.is_completed and t.earned_marks and t.max_marks]
    average_score = None
    if completed_with_marks:
        average_score = sum(
            (float(t.earned_marks) / float(t.max_marks) * 100)
            for t in completed_with_marks
        ) / len(completed_with_marks)

    return TaskStats(
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        overdue_tasks=overdue_tasks,
        total_ca_available=total_ca_available,
        total_ca_earned=total_ca_earned,
        completion_rate=round(completion_rate, 2),
        average_score=round(average_score, 2) if average_score else None
    )


@router.get(
    "/by-course",
    response_model=List[CourseTaskSummary],
    operation_id="get_tasks_by_course",
    summary="Get tasks grouped by course",
)
async def get_tasks_by_course(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_token)
):
    """
    Get tasks grouped by course with CA progress

    Args:
        db: Database session
        current_user: Authenticated user

    Returns:
        List of course summaries with tasks
    """
    # Get all user courses
    user_courses = db.query(UserCourse).filter(
        UserCourse.user_id == current_user.id
    ).all()

    summaries = []
    for uc in user_courses:
        # Get tasks for this course
        tasks = db.query(Task).filter(
            Task.user_course_id == uc.id,
            Task.category == "CA"
        ).all()

        total_ca = sum(float(t.weight) for t in tasks)
        earned_ca = sum(
            float(t.earned_marks) for t in tasks
            if t.is_completed and t.earned_marks
        )
        remaining_ca = 35 - total_ca  # PAU max CA is 35
        ca_percentage = (earned_ca / 35 * 100) if total_ca > 0 else 0.0

        task_responses = [TaskResponse(**t.to_dict()) for t in tasks]

        summaries.append(CourseTaskSummary(
            course_id=str(uc.course_id),
            course_code=uc.course.code if uc.course else "Unknown",
            course_title=uc.course.title if uc.course else "Unknown",
            total_ca_marks=round(total_ca, 2),
            earned_ca_marks=round(earned_ca, 2),
            remaining_ca_marks=round(remaining_ca, 2),
            ca_percentage=round(ca_percentage, 2),
            total_tasks=len(tasks),
            completed_tasks=len([t for t in tasks if t.is_completed]),
            pending_tasks=len([t for t in tasks if not t.is_completed]),
            tasks=task_responses
        ))

    return summaries


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    operation_id="get_task",
    summary="Get task details by ID",
)
async def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_token)
):
    """
    Get a specific task by ID

    Args:
        task_id: Task UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        Task details
    """
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID format"
        )

    task = db.query(Task).filter(
        Task.id == task_uuid,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return TaskResponse(**task.to_dict())


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    operation_id="update_task",
    summary="Update a task",
)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_token)
):
    """
    Update a task

    Args:
        task_id: Task UUID
        task_update: Fields to update
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated task
    """
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID format"
        )

    task = db.query(Task).filter(
        Task.id == task_uuid,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Update fields
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    # Recalculate priority
    task.calculate_priority(
        current_cgpa=float(current_user.current_cgpa) if current_user.current_cgpa else None,
        target_cgpa=float(current_user.target_cgpa) if current_user.target_cgpa else None
    )

    db.commit()
    db.refresh(task)

    # Update UserCourse scores if task is completed
    if task.is_completed and task.earned_marks:
        user_course = db.query(UserCourse).filter(
            UserCourse.id == task.user_course_id
        ).first()
        if user_course:
            if task.category == "CA":
                # Recalculate total CA score
                ca_tasks = db.query(Task).filter(
                    Task.user_course_id == user_course.id,
                    Task.category == "CA",
                    Task.is_completed == True,
                    Task.earned_marks.isnot(None)
                ).all()
                user_course.ca_score = sum(float(t.earned_marks) for t in ca_tasks)

            elif task.category == "EXAM":
                # Recalculate total EXAM score
                exam_tasks = db.query(Task).filter(
                    Task.user_course_id == user_course.id,
                    Task.category == "EXAM",
                    Task.is_completed == True,
                    Task.earned_marks.isnot(None)
                ).all()
                user_course.exam_score = sum(float(t.earned_marks) for t in exam_tasks)

            # Calculate and update predicted grades
            update_course_grades(user_course, db)

    return TaskResponse(**task.to_dict())


@router.patch(
    "/{task_id}/complete",
    response_model=dict,
    operation_id="complete_task",
    summary="Mark a task as complete",
)
async def mark_task_complete(
    task_id: str,
    completion_data: TaskComplete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_token)
):
    """
    Mark a task as complete. Returns the updated task and, if the score
    is below 60%, an `intervention` object suggesting a SmartStudy plan.

    Args:
        task_id: Task UUID
        completion_data: Earned marks and effort
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated task with optional intervention suggestion
    """
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID format"
        )

    task = db.query(Task).filter(
        Task.id == task_uuid,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Mark as complete
    task.is_completed = True
    task.completed_at = datetime.now(timezone.utc)

    if completion_data.earned_marks is not None:
        task.earned_marks = completion_data.earned_marks

    if completion_data.actual_effort is not None:
        task.actual_effort = completion_data.actual_effort

    # Check if late (make both datetimes timezone-aware for comparison)
    if task.due_date:
        due_date_aware = task.due_date
        if due_date_aware.tzinfo is None:
            due_date_aware = due_date_aware.replace(tzinfo=timezone.utc)

        completed_at_aware = task.completed_at
        if completed_at_aware.tzinfo is None:
            completed_at_aware = completed_at_aware.replace(tzinfo=timezone.utc)

        if completed_at_aware > due_date_aware:
            task.is_late = True

    db.commit()
    db.refresh(task)

    # Update UserCourse scores
    if task.earned_marks:
        user_course = db.query(UserCourse).filter(
            UserCourse.id == task.user_course_id
        ).first()
        if user_course:
            if task.category == "CA":
                # Update CA score
                ca_tasks = db.query(Task).filter(
                    Task.user_course_id == user_course.id,
                    Task.category == "CA",
                    Task.is_completed == True,
                    Task.earned_marks.isnot(None)
                ).all()
                user_course.ca_score = sum(float(t.earned_marks) for t in ca_tasks)

            elif task.category == "EXAM":
                # Update EXAM score
                exam_tasks = db.query(Task).filter(
                    Task.user_course_id == user_course.id,
                    Task.category == "EXAM",
                    Task.is_completed == True,
                    Task.earned_marks.isnot(None)
                ).all()
                user_course.exam_score = sum(float(t.earned_marks) for t in exam_tasks)

            # Update completion rate
            all_tasks = db.query(Task).filter(Task.user_course_id == user_course.id).count()
            completed = db.query(Task).filter(
                Task.user_course_id == user_course.id,
                Task.is_completed == True
            ).count()
            user_course.completion_rate = (completed / all_tasks * 100) if all_tasks > 0 else 0

            # Calculate and update predicted grades
            update_course_grades(user_course, db)

    # Build response
    task_data = task.to_dict()
    response = {**task_data}

    # Check if score is low enough to suggest SmartStudy intervention
    if task.earned_marks is not None and task.max_marks and float(task.max_marks) > 0:
        score_pct = (float(task.earned_marks) / float(task.max_marks)) * 100
        if score_pct < 60:
            # Get course info for the suggestion
            user_course = db.query(UserCourse).filter(
                UserCourse.id == task.user_course_id
            ).first()
            course_code = user_course.course.code if user_course and user_course.course else None
            course_title = user_course.course.title if user_course and user_course.course else None

            response["intervention"] = {
                "suggested": True,
                "reason": "low_score",
                "score_percentage": round(score_pct, 1),
                "task_title": task.title,
                "course_code": course_code,
                "course_title": course_title,
                "message": f"You scored {round(score_pct)}% on {task.title}. SmartStudy can create a personalized study plan to help you improve.",
            }

    return response


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_task",
    summary="Delete a task",
)
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user_from_token)
):
    """
    Delete a task

    Args:
        task_id: Task UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        No content
    """
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID format"
        )

    task = db.query(Task).filter(
        Task.id == task_uuid,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    db.delete(task)
    db.commit()

    return None
