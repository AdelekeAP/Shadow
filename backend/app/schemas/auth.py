"""
Authentication Schemas - Pydantic Models for Request/Response
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime


def validate_password_strength(v: str) -> str:
    """
    Shared password strength validation.

    Ensures the password contains at least one uppercase letter,
    one lowercase letter, and one digit. The minimum length of 8
    characters is enforced by the Field constraint.

    Args:
        v: Password string to validate

    Returns:
        The password string if valid

    Raises:
        ValueError: If password fails strength requirements
    """
    if len(v) < 8:
        raise ValueError('Password must be at least 8 characters long')
    if not any(c.isupper() for c in v):
        raise ValueError('Password must contain at least one uppercase letter')
    if not any(c.islower() for c in v):
        raise ValueError('Password must contain at least one lowercase letter')
    if not any(c.isdigit() for c in v):
        raise ValueError('Password must contain at least one number')
    return v


class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
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
        return validate_password_strength(v)


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
    email_verified: Optional[bool] = False

    class Config:
        from_attributes = True  # For Pydantic v2 (was orm_mode in v1)


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Schema for token payload data"""
    email: Optional[str] = None
    user_id: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    """Schema for requesting a password reset."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for resetting password via token."""
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=72)

    @validator('new_password')
    def validate_password(cls, v):
        return validate_password_strength(v)


class ChangePasswordRequest(BaseModel):
    """Schema for changing password (authenticated)."""
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=72)

    @validator('new_password')
    def validate_password(cls, v):
        return validate_password_strength(v)


class LogoutRequest(BaseModel):
    """Schema for logout — optional refresh token to revoke."""
    refresh_token: Optional[str] = None


class RefreshRequest(BaseModel):
    """Schema for refreshing an access token.

    refresh_token is optional here because the token can also be supplied
    via the HttpOnly cookie. Callers that do not use cookies should still
    include it in the request body for backwards compatibility.
    """
    refresh_token: Optional[str] = Field(None, min_length=1)


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences with explicit validation."""
    learning_style: Optional[str] = None
    preferred_learning_style: Optional[str] = None
    target_cgpa: Optional[float] = Field(None, ge=0.0, le=5.0)

    @validator('learning_style', 'preferred_learning_style')
    def validate_learning_style(cls, v):
        if v is not None:
            valid = {'visual', 'auditory', 'reading', 'kinesthetic'}
            if v not in valid:
                raise ValueError(f'learning_style must be one of {valid}')
        return v
