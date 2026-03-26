"""
Tests for Refresh Token Utilities
backend/app/utils/refresh_token.py

Tests creation, validation, revocation, expiry handling, and
user-agent binding for refresh tokens.
"""
import pytest
import os
import uuid
import hashlib
from datetime import datetime, timedelta, timezone

os.environ.setdefault("DISABLE_ML_MODELS", "true")
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-refresh-tests")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.ext.compiler import compiles

from app.database import Base

# ---------------------------------------------------------------------------
# SQLite compatibility patches
# ---------------------------------------------------------------------------

@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

_original_uuid_bind_processor = PG_UUID.bind_processor

def _patched_uuid_bind_processor(self, dialect):
    original = _original_uuid_bind_processor(self, dialect)
    if original is None:
        return None
    def process(value):
        if isinstance(value, str):
            value = uuid.UUID(value)
        return original(value)
    return process

PG_UUID.bind_processor = _patched_uuid_bind_processor

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db_session):
    """Create a test user in the database."""
    from app.models.user import User
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    user = User(
        id=uuid.uuid4(),
        email="refreshtest@pau.edu.ng",
        password_hash=pwd_context.hash("TestPass123!"),
        full_name="Refresh Token Tester",
        university_id="PAU/2022/050",
        entry_level="400L",
        target_cgpa=4.5,
        current_cgpa=3.5,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_user(db_session):
    """Create a second test user for multi-user tests."""
    from app.models.user import User
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    user = User(
        id=uuid.uuid4(),
        email="refreshtest2@pau.edu.ng",
        password_hash=pwd_context.hash("TestPass456!"),
        full_name="Second Refresh Tester",
        university_id="PAU/2022/051",
        entry_level="400L",
        target_cgpa=4.0,
        current_cgpa=3.0,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ===================================================================
# create_refresh_token
# ===================================================================

class TestCreateRefreshToken:

    def test_creates_token_string(self, db_session, test_user):
        """create_refresh_token should return a non-empty raw token string."""
        from app.utils.refresh_token import create_refresh_token

        raw_token = create_refresh_token(db_session, test_user.id)

        assert isinstance(raw_token, str)
        assert len(raw_token) > 0

    def test_token_stored_in_database(self, db_session, test_user):
        """The token hash should be persisted in the database."""
        from app.utils.refresh_token import create_refresh_token
        from app.models.refresh_token import RefreshToken

        raw_token = create_refresh_token(db_session, test_user.id)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        row = db_session.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()

        assert row is not None
        assert row.user_id == test_user.id
        assert row.revoked is False

    def test_token_with_user_agent(self, db_session, test_user):
        """Creating a token with a user agent should store the UA hash."""
        from app.utils.refresh_token import create_refresh_token
        from app.models.refresh_token import RefreshToken

        ua = "Mozilla/5.0 TestBrowser"
        raw_token = create_refresh_token(db_session, test_user.id, user_agent=ua)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        row = db_session.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()

        expected_ua_hash = hashlib.sha256(ua.encode()).hexdigest()[:16]
        assert row.user_agent_hash == expected_ua_hash

    def test_token_without_user_agent(self, db_session, test_user):
        """Creating a token without a user agent should leave ua_hash null."""
        from app.utils.refresh_token import create_refresh_token
        from app.models.refresh_token import RefreshToken

        raw_token = create_refresh_token(db_session, test_user.id, user_agent=None)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        row = db_session.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()

        assert row.user_agent_hash is None

    def test_each_call_produces_unique_token(self, db_session, test_user):
        """Successive calls should produce different tokens."""
        from app.utils.refresh_token import create_refresh_token

        t1 = create_refresh_token(db_session, test_user.id)
        t2 = create_refresh_token(db_session, test_user.id)

        assert t1 != t2

    def test_token_has_future_expiry(self, db_session, test_user):
        """The token should have an expiry date in the future."""
        from app.utils.refresh_token import create_refresh_token
        from app.models.refresh_token import RefreshToken

        raw_token = create_refresh_token(db_session, test_user.id)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        row = db_session.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()

        # SQLite returns naive datetimes, so compare with naive UTC
        assert row.expires_at > datetime.utcnow()


# ===================================================================
# validate_refresh_token
# ===================================================================

class TestValidateRefreshToken:

    def test_valid_token_returns_row(self, db_session, test_user):
        """A valid, non-revoked, non-expired token should return the row."""
        from app.utils.refresh_token import create_refresh_token, validate_refresh_token

        raw_token = create_refresh_token(db_session, test_user.id)
        result = validate_refresh_token(db_session, raw_token)

        assert result is not None
        assert result.user_id == test_user.id

    def test_invalid_token_returns_none(self, db_session, test_user):
        """A completely invalid token string should return None."""
        from app.utils.refresh_token import validate_refresh_token

        result = validate_refresh_token(db_session, "completely-invalid-token")

        assert result is None

    def test_revoked_token_returns_none(self, db_session, test_user):
        """A revoked token should not validate."""
        from app.utils.refresh_token import (
            create_refresh_token,
            validate_refresh_token,
            revoke_refresh_token,
        )

        raw_token = create_refresh_token(db_session, test_user.id)
        revoke_refresh_token(db_session, raw_token)

        result = validate_refresh_token(db_session, raw_token)
        assert result is None

    def test_expired_token_returns_none(self, db_session, test_user):
        """An expired token should not validate."""
        from app.utils.refresh_token import validate_refresh_token
        from app.models.refresh_token import RefreshToken

        # Manually create an already-expired token
        raw_token = "expired-test-token"
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        expired_row = RefreshToken(
            user_id=test_user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        db_session.add(expired_row)
        db_session.commit()

        result = validate_refresh_token(db_session, raw_token)
        assert result is None

    def test_validation_updates_last_used_at(self, db_session, test_user):
        """Successful validation should update last_used_at."""
        from app.utils.refresh_token import create_refresh_token, validate_refresh_token
        from app.models.refresh_token import RefreshToken

        raw_token = create_refresh_token(db_session, test_user.id)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        # Before validation, last_used_at should be None
        row = db_session.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()
        assert row.last_used_at is None

        # Validate
        validate_refresh_token(db_session, raw_token)

        # After validation, last_used_at should be set
        db_session.refresh(row)
        assert row.last_used_at is not None

    def test_user_agent_mismatch_returns_none(self, db_session, test_user):
        """Token created with one UA should not validate with a different UA."""
        from app.utils.refresh_token import create_refresh_token, validate_refresh_token

        raw_token = create_refresh_token(
            db_session, test_user.id, user_agent="Mozilla/5.0 Chrome"
        )

        result = validate_refresh_token(
            db_session, raw_token, user_agent="Mozilla/5.0 Firefox"
        )
        assert result is None

    def test_user_agent_match_validates(self, db_session, test_user):
        """Token created with a UA should validate with the same UA."""
        from app.utils.refresh_token import create_refresh_token, validate_refresh_token

        ua = "Mozilla/5.0 TestAgent"
        raw_token = create_refresh_token(db_session, test_user.id, user_agent=ua)

        result = validate_refresh_token(db_session, raw_token, user_agent=ua)
        assert result is not None


# ===================================================================
# revoke_refresh_token
# ===================================================================

class TestRevokeRefreshToken:

    def test_revoke_existing_token(self, db_session, test_user):
        """Revoking a valid token should return True."""
        from app.utils.refresh_token import create_refresh_token, revoke_refresh_token

        raw_token = create_refresh_token(db_session, test_user.id)
        result = revoke_refresh_token(db_session, raw_token)

        assert result is True

    def test_revoke_nonexistent_token(self, db_session, test_user):
        """Revoking a token that does not exist should return False."""
        from app.utils.refresh_token import revoke_refresh_token

        result = revoke_refresh_token(db_session, "nonexistent-token")

        assert result is False

    def test_revoked_token_has_flag_set(self, db_session, test_user):
        """After revocation, the token row should have revoked=True."""
        from app.utils.refresh_token import create_refresh_token, revoke_refresh_token
        from app.models.refresh_token import RefreshToken

        raw_token = create_refresh_token(db_session, test_user.id)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        revoke_refresh_token(db_session, raw_token)

        row = db_session.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()
        assert row.revoked is True

    def test_double_revoke_is_safe(self, db_session, test_user):
        """Revoking the same token twice should not raise an error."""
        from app.utils.refresh_token import create_refresh_token, revoke_refresh_token

        raw_token = create_refresh_token(db_session, test_user.id)

        assert revoke_refresh_token(db_session, raw_token) is True
        # Second revoke still finds the row (already revoked) and sets revoked=True again
        assert revoke_refresh_token(db_session, raw_token) is True


# ===================================================================
# revoke_all_user_tokens
# ===================================================================

class TestRevokeAllUserTokens:

    def test_revoke_all_returns_count(self, db_session, test_user):
        """Should return the number of tokens revoked."""
        from app.utils.refresh_token import create_refresh_token, revoke_all_user_tokens

        create_refresh_token(db_session, test_user.id)
        create_refresh_token(db_session, test_user.id)
        create_refresh_token(db_session, test_user.id)

        count = revoke_all_user_tokens(db_session, test_user.id)
        assert count == 3

    def test_revoke_all_with_no_tokens(self, db_session, test_user):
        """Should return 0 when user has no active tokens."""
        from app.utils.refresh_token import revoke_all_user_tokens

        count = revoke_all_user_tokens(db_session, test_user.id)
        assert count == 0

    def test_revoke_all_does_not_affect_other_users(self, db_session, test_user, second_user):
        """Revoking all tokens for User A should not revoke User B's tokens."""
        from app.utils.refresh_token import (
            create_refresh_token,
            revoke_all_user_tokens,
            validate_refresh_token,
        )

        # Create tokens for both users
        create_refresh_token(db_session, test_user.id)
        user_b_token = create_refresh_token(db_session, second_user.id)

        # Revoke all of test_user's tokens
        revoke_all_user_tokens(db_session, test_user.id)

        # User B's token should still be valid
        result = validate_refresh_token(db_session, user_b_token)
        assert result is not None

    def test_revoke_all_skips_already_revoked(self, db_session, test_user):
        """Already revoked tokens should not be counted in the revoke-all count."""
        from app.utils.refresh_token import (
            create_refresh_token,
            revoke_refresh_token,
            revoke_all_user_tokens,
        )

        t1 = create_refresh_token(db_session, test_user.id)
        create_refresh_token(db_session, test_user.id)

        # Revoke one individually
        revoke_refresh_token(db_session, t1)

        # revoke_all should only count the remaining active one
        count = revoke_all_user_tokens(db_session, test_user.id)
        assert count == 1
