"""
Refresh Token Utilities — Create, validate, and revoke refresh tokens.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session


REFRESH_TOKEN_EXPIRE_DAYS = 30


def create_refresh_token(db: Session, user_id, user_agent: str = None) -> str:
    """Create a new refresh token for a user. Returns the raw token string."""
    from app.models.refresh_token import RefreshToken

    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    ua_hash = None
    if user_agent:
        ua_hash = hashlib.sha256(user_agent.encode()).hexdigest()[:16]

    refresh = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        user_agent_hash=ua_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh)
    db.commit()
    return raw_token


def validate_refresh_token(db: Session, raw_token: str, user_agent: str = None):
    """
    Validate a refresh token. Returns the RefreshToken row if valid, None otherwise.
    Also updates last_used_at on successful validation.
    """
    from app.models.refresh_token import RefreshToken

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    refresh = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked == False,
        RefreshToken.expires_at > datetime.now(timezone.utc),
    ).first()

    if not refresh:
        return None

    # Optionally validate user agent
    if refresh.user_agent_hash and user_agent:
        ua_hash = hashlib.sha256(user_agent.encode()).hexdigest()[:16]
        if ua_hash != refresh.user_agent_hash:
            return None

    refresh.last_used_at = datetime.now(timezone.utc)
    db.commit()
    return refresh


def revoke_refresh_token(db: Session, raw_token: str) -> bool:
    """Revoke a specific refresh token. Returns True if found and revoked."""
    from app.models.refresh_token import RefreshToken

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    refresh = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
    ).first()

    if not refresh:
        return False

    refresh.revoked = True
    db.commit()
    return True


def revoke_all_user_tokens(db: Session, user_id) -> int:
    """Revoke all refresh tokens for a user. Returns count of tokens revoked."""
    from app.models.refresh_token import RefreshToken

    count = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked == False,
    ).update({"revoked": True})
    db.commit()
    return count
