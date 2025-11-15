"""
User Model - SQLAlchemy ORM
"""
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    university_id = Column(String(50), nullable=True)
    entry_level = Column(String(10), nullable=True)  # '100L', '200L', '300L', '400L'
    gpa_scale = Column(Numeric(3, 1), default=5.0)  # PAU uses 5.0
    target_cgpa = Column(Numeric(3, 2), nullable=True)  # User's goal (e.g., 4.50)
    current_cgpa = Column(Numeric(3, 2), nullable=True)
    total_credits_completed = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, name={self.full_name})>"

    def to_dict(self):
        """Convert user to dictionary (exclude password)"""
        return {
            "id": str(self.id),
            "email": self.email,
            "full_name": self.full_name,
            "university_id": self.university_id,
            "entry_level": self.entry_level,
            "gpa_scale": float(self.gpa_scale) if self.gpa_scale else 5.0,
            "target_cgpa": float(self.target_cgpa) if self.target_cgpa else None,
            "current_cgpa": float(self.current_cgpa) if self.current_cgpa else None,
            "total_credits_completed": self.total_credits_completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "is_active": self.is_active
        }
