"""
Course and UserCourse Models - SQLAlchemy ORM
"""
from sqlalchemy import Column, Index, String, Integer, Numeric, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class Course(Base):
    """
    Course Model - Represents a university course
    Pre-loaded with CS400 courses, users can also create custom courses
    """
    __tablename__ = "courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), unique=True, nullable=False, index=True)  # 'CSC401', 'PAU-CSC411'
    title = Column(String(255), nullable=False)
    credits = Column(Integer, nullable=False)
    level = Column(String(10), nullable=True)  # '400'
    status = Column(String(20), default='C')  # 'C' (Compulsory), 'E' (Elective), 'R' (Required)
    # How the course is graded:
    #   'standard_35_65' — 35% CA + 65% Exam (PAU default)
    #   'single_grade'   — one final score out of 100 (e.g. Final Year Project): no CA/Exam
    #                      split, no exam prediction; grade-point uses the 5.0 scale directly.
    grading_type = Column(String(20), nullable=False, server_default='standard_35_65', default='standard_35_65')
    department = Column(String(100), default='Computer Science')
    description = Column(Text, nullable=True)
    created_by = Column(String(10), default='admin')  # 'admin' or 'user'
    is_approved = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user_courses = relationship("UserCourse", back_populates="course", cascade="all, delete-orphan")
    library_documents = relationship("LibraryDocument", back_populates="course", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Course(code={self.code}, title={self.title}, credits={self.credits})>"

    def to_dict(self):
        """Convert course to dictionary"""
        return {
            "id": str(self.id),
            "code": self.code,
            "title": self.title,
            "credits": self.credits,
            "level": self.level,
            "status": self.status,
            "grading_type": self.grading_type,
            "department": self.department,
            "description": self.description,
            "created_by": self.created_by,
            "is_approved": self.is_approved,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class UserCourse(Base):
    """
    UserCourse Model - Represents a user's enrollment in a course
    Tracks grades, predictions, and completion
    """
    __tablename__ = "user_courses"
    __table_args__ = (
        Index('ix_user_courses_user_course', 'user_id', 'course_id'),
        Index('ix_user_courses_user_semester', 'user_id', 'semester_id'),
        Index('ix_user_courses_course_id', 'course_id'),
        Index('ix_user_courses_semester_id', 'semester_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    semester_id = Column(UUID(as_uuid=True), ForeignKey('semesters.id', ondelete='CASCADE'), nullable=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)

    is_carryover = Column(Boolean, default=False)
    is_priority = Column(Boolean, default=False)  # Flag for critical courses

    # PAU-specific fields (35/65 split)
    ca_score = Column(Numeric(5, 2), default=0)  # Current CA out of 35
    participation_score = Column(Numeric(5, 2), nullable=True)  # Out of 5
    exam_score = Column(Numeric(5, 2), nullable=True)  # Out of 65 (if taken)
    predicted_exam_score = Column(Numeric(5, 2), nullable=True)  # Predicted exam score

    # Overall grades
    current_score = Column(Numeric(5, 2), nullable=True)  # CA + Exam (if taken)
    predicted_score = Column(Numeric(5, 2), nullable=True)  # CA + Predicted Exam
    current_grade_point = Column(Numeric(3, 2), nullable=True)  # 0.0-5.0 (if final)
    predicted_grade_point = Column(Numeric(3, 2), nullable=True)  # Predicted GP
    letter_grade = Column(String(2), nullable=True)  # 'A', 'B', 'C', etc.
    predicted_letter_grade = Column(String(2), nullable=True)

    completion_rate = Column(Numeric(5, 2), default=0)  # Percentage of tasks completed
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    course = relationship("Course", back_populates="user_courses")
    semester = relationship("Semester", foreign_keys=[semester_id])

    def __repr__(self):
        return f"<UserCourse(user_id={self.user_id}, course_id={self.course_id}, predicted_gp={self.predicted_grade_point})>"

    def to_dict(self):
        """Convert user course to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "semester_id": str(self.semester_id) if self.semester_id else None,
            "course_id": str(self.course_id),
            "is_carryover": self.is_carryover,
            "is_priority": self.is_priority,
            "ca_score": float(self.ca_score) if self.ca_score is not None else 0.0,
            "participation_score": float(self.participation_score) if self.participation_score is not None else None,
            "exam_score": float(self.exam_score) if self.exam_score is not None else None,
            "predicted_exam_score": float(self.predicted_exam_score) if self.predicted_exam_score is not None else None,
            "current_score": float(self.current_score) if self.current_score is not None else None,
            "predicted_score": float(self.predicted_score) if self.predicted_score is not None else None,
            "current_grade_point": float(self.current_grade_point) if self.current_grade_point is not None else None,
            "predicted_grade_point": float(self.predicted_grade_point) if self.predicted_grade_point is not None else None,
            "letter_grade": self.letter_grade,
            "predicted_letter_grade": self.predicted_letter_grade,
            "completion_rate": float(self.completion_rate) if self.completion_rate is not None else 0.0,
            "enrolled_at": self.enrolled_at.isoformat() if self.enrolled_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "course": self.course.to_dict() if self.course else None
        }


class Semester(Base):
    """
    Semester Model - Represents an academic semester
    """
    __tablename__ = "semesters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(50), nullable=False)  # 'Fall 2024', 'Spring 2025'
    academic_year = Column(String(20), nullable=True)  # '2024/2025'
    semester_number = Column(Integer, nullable=True)  # 1 for First Semester, 2 for Second
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    target_gpa = Column(Numeric(3, 2), nullable=True)  # Semester-specific goal
    actual_gpa = Column(Numeric(3, 2), nullable=True)  # Final semester GPA
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Semester(name={self.name}, year={self.academic_year})>"

    def to_dict(self):
        """Convert semester to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "name": self.name,
            "academic_year": self.academic_year,
            "semester_number": self.semester_number,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "target_gpa": float(self.target_gpa) if self.target_gpa else None,
            "actual_gpa": float(self.actual_gpa) if self.actual_gpa else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
