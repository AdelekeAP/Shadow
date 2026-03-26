"""
Semester Routes - Academic year and semester management
"""
import re
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Dict
from uuid import UUID

from app.database import get_db
from app.models.course import Semester, UserCourse
from app.models.user import User
from app.schemas.course import SemesterResponse, SemesterUpdate
from app.utils.auth import get_current_user
from pydantic import BaseModel, Field, validator


router = APIRouter(prefix="/semesters", tags=["Semesters"])


# ── Schemas ──────────────────────────────────────────

class AcademicYearCreate(BaseModel):
    academic_year: str = Field(..., min_length=9, max_length=9)

    @validator('academic_year')
    def validate_format(cls, v):
        if not re.match(r'^\d{4}/\d{4}$', v):
            raise ValueError('Must be in YYYY/YYYY format (e.g. 2025/2026)')
        first, second = v.split('/')
        if int(second) != int(first) + 1:
            raise ValueError('Second year must be first year + 1')
        return v


class AssignCoursesRequest(BaseModel):
    user_course_ids: List[str]


# ── Endpoints ────────────────────────────────────────

@router.post(
    "/academic-year",
    operation_id="create_academic_year",
    summary="Create an academic year with two semesters",
)
async def create_academic_year(
    request: AcademicYearCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Create an academic year which auto-generates First and Second Semester.
    First Semester: Sept 1 - Jan 31. Second Semester: Feb 1 - Jul 31.
    First Semester is set as active.
    """
    year_str = request.academic_year
    first_year = int(year_str.split('/')[0])
    second_year = int(year_str.split('/')[1])

    # Check if this academic year already exists for this user
    existing = db.query(Semester).filter(
        Semester.user_id == current_user.id,
        Semester.academic_year == year_str
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Academic year {year_str} already exists"
        )

    # Lock and deactivate all existing semesters to prevent concurrent activation race
    db.query(Semester).filter(
        Semester.user_id == current_user.id
    ).with_for_update().all()

    db.query(Semester).filter(
        Semester.user_id == current_user.id
    ).update({"is_active": False})

    # Determine which semester is current based on today's date
    # First Semester: Sept 1 - Feb 14, Second Semester: Mar 2 - Jul 31
    # Gap period: Feb 15 - Mar 1 (neither semester active)
    today = datetime.now(timezone.utc)
    month = today.month
    day = today.day

    # First Semester: Sept 1 - Feb 14
    if month >= 9 or month == 1 or (month == 2 and day <= 14):
        first_is_active = True
        second_is_active = False
    # Second Semester: Mar 2 - Jul 31
    elif (month == 3 and day >= 2) or (4 <= month <= 7):
        first_is_active = False
        second_is_active = True
    # Gap period: Feb 15 - Mar 1 (August also counts as gap before new academic year)
    else:
        first_is_active = False
        second_is_active = False

    # Create First Semester (Sept 1 - Feb 14)
    first_sem = Semester(
        user_id=current_user.id,
        name=f"First Semester {year_str}",
        academic_year=year_str,
        semester_number=1,
        start_date=datetime(first_year, 9, 1, tzinfo=timezone.utc),
        end_date=datetime(second_year, 2, 14, tzinfo=timezone.utc),
        is_active=first_is_active,
    )

    # Create Second Semester (Mar 2 - Jul 31)
    second_sem = Semester(
        user_id=current_user.id,
        name=f"Second Semester {year_str}",
        academic_year=year_str,
        semester_number=2,
        start_date=datetime(second_year, 3, 2, tzinfo=timezone.utc),
        end_date=datetime(second_year, 7, 31, tzinfo=timezone.utc),
        is_active=second_is_active,
    )

    db.add(first_sem)
    db.add(second_sem)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Resource already exists")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save changes")
    db.refresh(first_sem)
    db.refresh(second_sem)

    return {
        "success": True,
        "academic_year": year_str,
        "semesters": [first_sem.to_dict(), second_sem.to_dict()]
    }


@router.get(
    "/",
    operation_id="list_semesters",
    summary="List all semesters for current user",
)
async def list_semesters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict]:
    """Get all semesters ordered by start date (newest first)."""
    semesters = db.query(Semester).filter(
        Semester.user_id == current_user.id
    ).order_by(Semester.start_date.desc()).all()

    return [s.to_dict() for s in semesters]


@router.get(
    "/active",
    operation_id="get_active_semester",
    summary="Get the currently active semester",
)
async def get_active_semester(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Get the user's currently active semester, or null if none."""
    semester = db.query(Semester).filter(
        Semester.user_id == current_user.id,
        Semester.is_active == True
    ).first()

    return {"semester": semester.to_dict() if semester else None}


@router.patch(
    "/{semester_id}/activate",
    operation_id="activate_semester",
    summary="Set a semester as active",
)
async def activate_semester(
    semester_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Activate a semester (deactivates all others)."""
    try:
        sem_uuid = UUID(semester_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid semester ID format")
    semester = db.query(Semester).filter(
        Semester.id == sem_uuid,
        Semester.user_id == current_user.id
    ).first()

    if not semester:
        raise HTTPException(status_code=404, detail="Semester not found")

    # Lock all user semesters to prevent concurrent activation race
    db.query(Semester).filter(
        Semester.user_id == current_user.id
    ).with_for_update().all()

    # Deactivate all, then activate target
    db.query(Semester).filter(
        Semester.user_id == current_user.id
    ).update({"is_active": False})

    semester.is_active = True
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Resource already exists")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save changes")
    db.refresh(semester)

    return {"success": True, "semester": semester.to_dict()}


@router.patch(
    "/{semester_id}",
    operation_id="update_semester",
    summary="Update semester details",
)
async def update_semester(
    semester_id: str,
    request: SemesterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Update semester name, target GPA, or active status."""
    try:
        sem_uuid = UUID(semester_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid semester ID format")
    semester = db.query(Semester).filter(
        Semester.id == sem_uuid,
        Semester.user_id == current_user.id
    ).first()

    if not semester:
        raise HTTPException(status_code=404, detail="Semester not found")

    update_data = request.model_dump(exclude_unset=True)

    # If activating via update, lock and deactivate all other semesters first
    if update_data.get("is_active") is True:
        db.query(Semester).filter(
            Semester.user_id == current_user.id
        ).with_for_update().all()

        db.query(Semester).filter(
            Semester.user_id == current_user.id,
            Semester.id != sem_uuid
        ).update({"is_active": False})

    for field, value in update_data.items():
        setattr(semester, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Resource already exists")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save changes")
    db.refresh(semester)

    return {"success": True, "semester": semester.to_dict()}


@router.delete(
    "/{semester_id}",
    operation_id="delete_semester",
    summary="Delete a semester",
)
async def delete_semester(
    semester_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a semester. Courses in this semester become unassigned."""
    try:
        sem_uuid = UUID(semester_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid semester ID format")
    semester = db.query(Semester).filter(
        Semester.id == sem_uuid,
        Semester.user_id == current_user.id
    ).first()

    if not semester:
        raise HTTPException(status_code=404, detail="Semester not found")

    # Nullify semester_id on all courses in this semester
    db.query(UserCourse).filter(
        UserCourse.semester_id == sem_uuid
    ).update({"semester_id": None})

    db.delete(semester)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Resource already exists")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save changes")

    return {"success": True}


@router.post(
    "/{semester_id}/assign-courses",
    operation_id="assign_courses_to_semester",
    summary="Assign courses to a semester",
)
async def assign_courses_to_semester(
    semester_id: str,
    request: AssignCoursesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Bulk-assign user courses to a semester."""
    try:
        sem_uuid = UUID(semester_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid semester ID format")
    semester = db.query(Semester).filter(
        Semester.id == sem_uuid,
        Semester.user_id == current_user.id
    ).first()

    if not semester:
        raise HTTPException(status_code=404, detail="Semester not found")

    updated = 0
    for uc_id in request.user_course_ids:
        uc = db.query(UserCourse).filter(
            UserCourse.id == UUID(uc_id),
            UserCourse.user_id == current_user.id
        ).first()
        if uc:
            uc.semester_id = sem_uuid
            updated += 1

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Resource already exists")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save changes")

    return {"success": True, "updated": updated}
