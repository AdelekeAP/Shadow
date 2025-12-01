"""
Authentication Schemas - Pydantic Models for Request/Response
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=255)
    university_id: Optional[str] = Field(None, max_length=50)
    entry_level: Optional[str] = Field("400L", max_length=10)
    current_cgpa: Optional[float] = Field(None, ge=0.0, le=5.0)
    target_cgpa: Optional[float] = Field(None, ge=0.0, le=5.0)

    @validator('entry_level')
    def validate_entry_level(cls, v):
        valid_levels = ['100L', '200L', '200L-DE', '300L', '400L']
        if v and v not in valid_levels:
            raise ValueError(f'entry_level must be one of {valid_levels}')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response (exclude password)"""
    id: str
    email: str
    full_name: str
    university_id: Optional[str]
    entry_level: Optional[str]
    gpa_scale: float
    target_cgpa: Optional[float]
    current_cgpa: Optional[float]
    total_credits_completed: int
    created_at: Optional[datetime]
    last_login: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True  # For Pydantic v2 (was orm_mode in v1)


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Schema for token payload data"""
    email: Optional[str] = None
    user_id: Optional[str] = None
