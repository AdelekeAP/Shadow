"""
Authentication Routes - Register, Login, Logout, Get Current User
"""
import asyncio
import logging
import os
from time import perf_counter
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models.user import User
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
import hashlib
import secrets
from app.schemas.auth import (
    UserCreate, UserLogin, UserResponse, Token, UserPreferencesUpdate,
    ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest,
    RefreshRequest, LogoutRequest,
)
from app.services.email_service import send_password_reset_email, send_verification_email
from app.utils.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
    get_current_user,
    oauth2_scheme,
)
from app.utils.token_blacklist import blacklist_token
from app.middleware.rate_limiter import limiter
from app.utils.input_sanitizer import sanitize_text
from app.services.cache_service import cache_get, cache_set, cache_delete
from app.utils.refresh_token import (
    create_refresh_token,
    validate_refresh_token,
    revoke_refresh_token,
    revoke_all_user_tokens,
)

router = APIRouter()
logger = logging.getLogger(__name__)


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
    # Check if user already exists (case-insensitive)
    existing_user = db.query(User).filter(func.lower(User.email) == user_data.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password
    hashed_password = get_password_hash(user_data.password)

    # Sanitize text fields to prevent XSS
    sanitized_name = sanitize_text(user_data.full_name)
    sanitized_university_id = sanitize_text(user_data.university_id) if user_data.university_id else None

    # Create new user (store email in lowercase for consistency)
    new_user = User(
        email=user_data.email.lower(),
        password_hash=hashed_password,
        full_name=sanitized_name,
        university_id=sanitized_university_id,
        entry_level=user_data.entry_level,
        target_cgpa=user_data.target_cgpa,
        gpa_scale=5.0,  # PAU uses 5.0 scale
        current_cgpa=user_data.current_cgpa,
        total_credits_completed=0,
        is_active=True
    )

    # Generate email verification token
    raw_verification_token = secrets.token_urlsafe(32)
    new_user.email_verified = False
    new_user.email_verification_token = hashlib.sha256(raw_verification_token.encode()).hexdigest()
    new_user.email_verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)

    # Save to database
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Resource already exists")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save changes")
    db.refresh(new_user)

    # Send verification email (best-effort, don't block registration)
    try:
        send_verification_email(
            to=new_user.email,
            token=raw_verification_token,
            name=sanitized_name,
        )
    except Exception as email_err:
        logger.warning(f"Failed to send verification email to {new_user.email}: {email_err}")

    # Create access token with token version and user agent binding
    user_agent = request.headers.get("user-agent", "")
    access_token = create_access_token(
        data={
            "sub": new_user.email,
            "user_id": str(new_user.id),
            "token_version": new_user.token_version or 0,
        },
        user_agent=user_agent,
    )

    # Create refresh token
    refresh_token = create_refresh_token(db, new_user.id, user_agent=user_agent)

    # Convert user to response format
    user_response = UserResponse(**new_user.to_dict())

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
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
        423: {
            "description": "Account locked due to too many failed login attempts.",
            "content": {
                "application/json": {
                    "example": {"detail": "Account locked. Try again in 15 minute(s)."}
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

    **Account lockout:** After 5 consecutive failed login attempts the account is
    locked for 15 minutes.

    Include the returned token in subsequent requests:
    ```
    Authorization: Bearer <access_token>
    ```
    """
    start = perf_counter()
    try:
        return await _do_login(credentials, db, request)
    finally:
        # Normalize response time to at least 200ms to prevent timing-based
        # account enumeration (user-not-found vs wrong-password).
        elapsed = perf_counter() - start
        if elapsed < 0.2:
            await asyncio.sleep(0.2 - elapsed)


async def _do_login(credentials: UserLogin, db: Session, request: Request) -> Token:
    """Internal login logic, separated for constant-time wrapper."""
    # Find user by email (case-insensitive)
    user = db.query(User).filter(func.lower(User.email) == credentials.email.lower()).first()

    if not user:
        # Run a dummy hash to keep timing consistent
        verify_password("dummy", get_password_hash("dummy"))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check account lockout (reset counter if lockout has expired)
    if user.locked_until:
        if user.locked_until > datetime.now(timezone.utc):
            remaining = int((user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60) + 1
            raise HTTPException(
                status_code=423,
                detail=f"Account locked. Try again in {remaining} minute(s)."
            )
        else:
            # Lockout expired — reset counter
            user.failed_login_attempts = 0
            user.locked_until = None
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise HTTPException(status_code=500, detail="Failed to save changes")

    # Check if user is active (before password verification to avoid unnecessary work)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        try:
            db.commit()
        except Exception:
            db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Successful login — reset lockout counters
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.now(timezone.utc)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save changes")

    # Create access token with token version and user agent binding
    user_agent = request.headers.get("user-agent", "")
    access_token = create_access_token(
        data={
            "sub": user.email,
            "user_id": str(user.id),
            "token_version": user.token_version or 0,
        },
        user_agent=user_agent,
    )

    # Create refresh token
    refresh_token = create_refresh_token(db, user.id, user_agent=user_agent)

    # Convert user to response format
    user_response = UserResponse(**user.to_dict())

    response = JSONResponse(content={
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response.model_dump(mode="json"),
        # Still include refresh_token in body for backwards compatibility
        "refresh_token": refresh_token,
    })
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=os.getenv("ENVIRONMENT") == "production",
        samesite="lax",
        max_age=30 * 24 * 60 * 60,  # 30 days
        path="/api/v1/auth",
    )
    return response


@router.post(
    "/logout",
    operation_id="logout_user",
    summary="Invalidate current JWT token",
    response_description="Confirmation that the token has been revoked.",
    responses={
        200: {
            "description": "Logged out successfully.",
            "content": {
                "application/json": {
                    "example": {"message": "Logged out successfully"}
                }
            },
        },
    },
)
async def logout(
    body: LogoutRequest = None,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    Invalidate the current JWT token and revoke the refresh token.

    The access token is added to a blacklist and the refresh token (if provided)
    is revoked in the database.
    """
    # Blacklist the access token
    payload = decode_access_token(token)
    if payload and "exp" in payload:
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        blacklist_token(token, exp)

    # Revoke the refresh token — prefer cookie, fall back to request body
    if body and body.refresh_token:
        revoke_refresh_token(db, body.refresh_token)

    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth",
    )
    return response


@router.post(
    "/refresh",
    response_model=Token,
    operation_id="refresh_token",
    summary="Exchange a refresh token for a new access token",
)
@limiter.limit("10/minute")
async def refresh(
    request: Request,
    body: RefreshRequest = None,
    refresh_token_cookie: str = Cookie(None, alias="refresh_token"),
    db: Session = Depends(get_db),
):
    """Exchange a valid refresh token for a new access token.

    The refresh token is read from the HttpOnly cookie (preferred) or from the
    request body for backwards compatibility.
    """
    # Prefer cookie; fall back to request body for backwards compat
    raw_token = refresh_token_cookie or (body.refresh_token if body else None)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
        )

    user_agent = request.headers.get("user-agent", "")
    refresh_row = validate_refresh_token(db, raw_token, user_agent=user_agent)

    if not refresh_row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Load user
    user = db.query(User).filter(User.id == refresh_row.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Create new access token
    access_token = create_access_token(
        data={
            "sub": user.email,
            "user_id": str(user.id),
            "token_version": user.token_version or 0,
        },
        user_agent=user_agent,
    )

    # Rotate refresh token: revoke old, issue new
    revoke_refresh_token(db, raw_token)
    new_refresh_token = create_refresh_token(db, user.id, user_agent=user_agent)

    user_response = UserResponse(**user.to_dict())

    response = JSONResponse(content={
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response.model_dump(mode="json"),
        # Include rotated refresh token in body for backwards compatibility
        "refresh_token": new_refresh_token,
    })
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=os.getenv("ENVIRONMENT") == "production",
        samesite="lax",
        max_age=30 * 24 * 60 * 60,  # 30 days
        path="/api/v1/auth",
    )
    return response


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
@limiter.limit("30/minute")
async def get_me(request: Request, current_user: User = Depends(get_current_user)):
    """
    Retrieve the full profile of the currently authenticated user.

    Requires a valid JWT Bearer token in the `Authorization` header. Returns
    all profile fields including academic information (CGPA, credits, entry level)
    and account metadata.
    """
    cache_key = f"user:profile:{current_user.id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    result = UserResponse(**current_user.to_dict()).model_dump()
    cache_set(cache_key, result, ttl=300)
    return result


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
@limiter.limit("30/minute")
async def update_preferences(
    request: Request,
    preferences: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the authenticated user's learning preferences and academic targets.

    Accepts a JSON object with any of the following keys:

    - `preferred_learning_style` or `learning_style`: One of `visual`, `auditory`,
      `reading`, `kinesthetic`
    - `target_cgpa`: Desired cumulative GPA on the 5.0 scale
    """
    style = preferences.learning_style or preferences.preferred_learning_style
    if style is not None:
        current_user.learning_style = style
    if preferences.target_cgpa is not None:
        current_user.target_cgpa = preferences.target_cgpa

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Resource already exists")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save changes")
    db.refresh(current_user)

    # Invalidate profile cache
    cache_delete(f"user:profile:{current_user.id}")

    return {
        "message": "Preferences updated successfully",
        "learning_style": current_user.learning_style,
        "target_cgpa": float(current_user.target_cgpa) if current_user.target_cgpa else None
    }


# ============================================
# Password Reset Endpoints
# ============================================

@router.post(
    "/forgot-password",
    operation_id="forgot_password",
    summary="Request a password reset email",
)
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Request a password reset email. Always returns 200 to avoid leaking
    whether the email exists in the system.
    """
    user = db.query(User).filter(func.lower(User.email) == body.email.lower()).first()
    if user:
        # Generate token, store hash + 1hr expiry
        raw_token = secrets.token_urlsafe(32)
        user.password_reset_token = hashlib.sha256(raw_token.encode()).hexdigest()
        user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to save changes")
        try:
            send_password_reset_email(to=user.email, token=raw_token, name=user.full_name)
        except Exception as email_err:
            logger.warning(f"Failed to send password reset email to {user.email}: {email_err}")

    return {"message": "If that email is registered, a reset link has been sent."}


@router.post(
    "/reset-password",
    operation_id="reset_password",
    summary="Reset password using token from email",
)
@limiter.limit("5/minute")
async def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """Reset the user's password given a valid reset token."""
    token_hash = hashlib.sha256(body.token.encode()).hexdigest()
    user = db.query(User).filter(
        User.password_reset_token == token_hash,
        User.password_reset_expires > datetime.now(timezone.utc),
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user.password_hash = get_password_hash(body.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    user.token_version = (user.token_version or 0) + 1  # Invalidate all sessions
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save changes")

    # Revoke all refresh tokens for security
    revoke_all_user_tokens(db, user.id)

    return {"message": "Password reset successfully. Please log in with your new password."}


@router.post(
    "/change-password",
    operation_id="change_password",
    summary="Change password (authenticated)",
)
@limiter.limit("5/minute")
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the authenticated user's password."""
    if not verify_password(body.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.password_hash = get_password_hash(body.new_password)
    current_user.token_version = (current_user.token_version or 0) + 1
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save changes")

    # Revoke all refresh tokens for security
    revoke_all_user_tokens(db, current_user.id)

    return {"message": "Password changed successfully. Please log in again."}


# ============================================
# Email Verification Endpoints
# ============================================

@router.get(
    "/verify-email/{token}",
    operation_id="verify_email",
    summary="Verify email address via link",
)
@limiter.limit("10/minute")
async def verify_email(
    request: Request,
    token: str,
    db: Session = Depends(get_db),
):
    """Verify a user's email using the token from the verification email."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    user = db.query(User).filter(
        User.email_verification_token == token_hash,
        User.email_verification_expires > datetime.now(timezone.utc),
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    user.email_verified = True
    user.email_verification_token = None
    user.email_verification_expires = None
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save changes")

    return {"message": "Email verified successfully."}


@router.post(
    "/resend-verification",
    operation_id="resend_verification",
    summary="Resend email verification link",
)
@limiter.limit("3/hour")
async def resend_verification(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Resend the email verification link for the authenticated user."""
    if current_user.email_verified:
        return {"message": "Email is already verified."}

    raw_token = secrets.token_urlsafe(32)
    current_user.email_verification_token = hashlib.sha256(raw_token.encode()).hexdigest()
    current_user.email_verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save changes")

    try:
        send_verification_email(
            to=current_user.email,
            token=raw_token,
            name=current_user.full_name,
        )
    except Exception as email_err:
        logger.warning(f"Failed to send verification email to {current_user.email}: {email_err}")

    return {"message": "Verification email sent."}
