"""
Authentication Utilities
JWT token generation/validation and password hashing
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from jwt.exceptions import PyJWTError
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db

load_dotenv()

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    import warnings
    warnings.warn("SECRET_KEY not set — using random key (sessions won't persist across restarts)")
    import secrets
    SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Uses bcrypt's timing-safe comparison to prevent timing attacks.
    The comparison time is constant regardless of where the password
    differs from the hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    The schema layer enforces max 72 characters (bcrypt's limit),
    so no truncation is needed here.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None, user_agent: Optional[str] = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Dictionary containing user data to encode
        expires_delta: Optional custom expiration time
        user_agent: Optional User-Agent string to bind token to

    Returns:
        Encoded JWT token
    """
    import hashlib

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    # Bind token to user agent if provided
    if user_agent:
        to_encode["ua"] = hashlib.sha256(user_agent.encode()).hexdigest()[:16]

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except PyJWTError:
        return None


def verify_token(token: str) -> Optional[str]:
    """
    Verify JWT token and extract user email

    Args:
        token: JWT token string

    Returns:
        User email if valid, None otherwise
    """
    payload = decode_access_token(token)
    if payload:
        email: str = payload.get("sub")
        return email
    return None


# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    request = None,
):
    """
    Dependency to get current authenticated user

    Args:
        token: JWT token from Authorization header (extracted via oauth2_scheme)
        db: Database session (injected via Depends)

    Returns:
        User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    from app.models.user import User

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    from app.utils.token_blacklist import is_blacklisted

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    if is_blacklisted(token):
        raise credentials_exception

    # Validate user-agent claim if present and request is available
    if request is not None:
        request_ua = getattr(request, 'headers', {}).get("user-agent", "") if hasattr(request, 'headers') else ""
        if request_ua and not validate_user_agent_claim(payload, request_ua):
            raise credentials_exception

    email: str = payload.get("sub")
    user_id: str = payload.get("user_id")

    if email is None or user_id is None:
        raise credentials_exception

    # Get user from database
    from uuid import UUID
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None:
        raise credentials_exception

    # Validate token version (allows forced session invalidation)
    token_version = payload.get("token_version", 0)
    if hasattr(user, 'token_version') and user.token_version is not None:
        if user.token_version != token_version:
            raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


def validate_user_agent_claim(payload: dict, request_user_agent: str) -> bool:
    """Validate the user-agent claim in a JWT token, if present."""
    import hashlib
    ua_claim = payload.get("ua")
    if not ua_claim or not request_user_agent:
        return True  # No UA binding or no request UA — skip validation
    expected = hashlib.sha256(request_user_agent.encode()).hexdigest()[:16]
    return ua_claim == expected
