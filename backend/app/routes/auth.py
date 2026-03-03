"""
Authentication Routes - Register, Login, Get Current User
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, UserResponse, Token
from app.utils.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token
)
from app.middleware.rate_limiter import limiter

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    operation_id="register_user",
    summary="Register a new student account",
    response_description="JWT access token and the newly created user profile.",
    responses={
        201: {
            "description": "Account created successfully. Returns a JWT token and user profile.",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "user": {
                            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                            "email": "student@pau.edu.ng",
                            "full_name": "Jane Doe",
                            "university_id": "PAU/2022/001",
                            "entry_level": "400L",
                            "gpa_scale": 5.0,
                            "target_cgpa": 4.5,
                            "current_cgpa": 3.8,
                            "total_credits_completed": 0,
                            "created_at": "2026-02-21T10:30:00",
                            "last_login": None,
                            "is_active": True
                        }
                    }
                }
            },
        },
        400: {
            "description": "Email already registered.",
            "content": {
                "application/json": {
                    "example": {"detail": "Email already registered"}
                }
            },
        },
        422: {
            "description": "Validation error (e.g., password too short, invalid email format, invalid entry level).",
        },
    },
)
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new PAU student account.

    Creates a new user with the provided profile information and returns a JWT
    access token that can be used immediately for authenticated requests.

    **Rate limit:** 5 requests per minute per client IP.

    **PAU-specific fields:**
    - `entry_level`: One of `100L`, `200L`, `200L-DE`, `300L`, `400L`
    - `gpa_scale`: Automatically set to 5.0 (PAU standard)
    - `target_cgpa` / `current_cgpa`: Must be between 0.0 and 5.0
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password
    hashed_password = get_password_hash(user_data.password)

    # Create new user
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        university_id=user_data.university_id,
        entry_level=user_data.entry_level,
        target_cgpa=user_data.target_cgpa,
        gpa_scale=5.0,  # PAU uses 5.0 scale
        current_cgpa=user_data.current_cgpa,
        total_credits_completed=0,
        is_active=True
    )

    # Save to database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create access token
    access_token = create_access_token(
        data={"sub": new_user.email, "user_id": str(new_user.id)}
    )

    # Convert user to response format
    user_response = UserResponse(**new_user.to_dict())

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )


@router.post(
    "/login",
    response_model=Token,
    operation_id="login_user",
    summary="Authenticate and obtain a JWT token",
    response_description="JWT access token and the authenticated user profile.",
    responses={
        200: {
            "description": "Login successful. Returns a JWT token and user profile.",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "user": {
                            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                            "email": "student@pau.edu.ng",
                            "full_name": "Jane Doe",
                            "university_id": "PAU/2022/001",
                            "entry_level": "400L",
                            "gpa_scale": 5.0,
                            "target_cgpa": 4.5,
                            "current_cgpa": 3.8,
                            "total_credits_completed": 45,
                            "created_at": "2026-01-15T08:00:00",
                            "last_login": "2026-02-21T10:30:00",
                            "is_active": True
                        }
                    }
                }
            },
        },
        401: {
            "description": "Invalid email or password.",
            "content": {
                "application/json": {
                    "example": {"detail": "Incorrect email or password"}
                }
            },
        },
        403: {
            "description": "User account is inactive.",
            "content": {
                "application/json": {
                    "example": {"detail": "User account is inactive"}
                }
            },
        },
    },
)
@limiter.limit("5/minute")
async def login(request: Request, credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate a student with email and password.

    On success, returns a JWT access token (valid for 24 hours) and the full
    user profile. The `last_login` timestamp is updated on every successful login.

    **Rate limit:** 5 requests per minute per client IP.

    Include the returned token in subsequent requests:
    ```
    Authorization: Bearer <access_token>
    ```
    """
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Create access token
    access_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.id)}
    )

    # Convert user to response format
    user_response = UserResponse(**user.to_dict())

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Get current authenticated user from JWT token

    Args:
        token: JWT access token from Authorization header
        db: Database session

    Returns:
        Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    # Get user from database by email
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    return user


@router.get(
    "/me",
    response_model=UserResponse,
    operation_id="get_current_user_profile",
    summary="Get the authenticated user's profile",
    response_description="Full profile of the currently authenticated user.",
    responses={
        200: {
            "description": "User profile retrieved successfully.",
        },
        401: {
            "description": "Missing or invalid JWT token.",
            "content": {
                "application/json": {
                    "example": {"detail": "Could not validate credentials"}
                }
            },
        },
    },
)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Retrieve the full profile of the currently authenticated user.

    Requires a valid JWT Bearer token in the `Authorization` header. Returns
    all profile fields including academic information (CGPA, credits, entry level)
    and account metadata.
    """
    return UserResponse(**current_user.to_dict())


@router.patch(
    "/me/preferences",
    operation_id="update_user_preferences",
    summary="Update learning preferences and academic targets",
    response_description="Confirmation message with updated preference values.",
    responses={
        200: {
            "description": "Preferences updated successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Preferences updated successfully",
                        "learning_style": "visual",
                        "target_cgpa": 4.5
                    }
                }
            },
        },
        401: {
            "description": "Missing or invalid JWT token.",
        },
    },
)
async def update_preferences(
    preferences: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the authenticated user's learning preferences and academic targets.

    Accepts a JSON object with any of the following keys:

    - `preferred_learning_style` or `learning_style`: One of `visual`, `auditory`,
      `reading`, `kinesthetic`
    - `target_cgpa`: Desired cumulative GPA on the 5.0 scale

    Only recognized fields are persisted; unknown keys are silently ignored.
    """
    # Map frontend field names to model field names
    field_mapping = {
        'preferred_learning_style': 'learning_style',
        'learning_style': 'learning_style',
        'target_cgpa': 'target_cgpa'
    }

    # Update allowed fields
    for field, value in preferences.items():
        model_field = field_mapping.get(field)
        if model_field:
            setattr(current_user, model_field, value)

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Preferences updated successfully",
        "learning_style": current_user.learning_style,
        "target_cgpa": float(current_user.target_cgpa) if current_user.target_cgpa else None
    }
