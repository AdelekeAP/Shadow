"""
Tests for Authentication Utilities
backend/app/utils/auth.py

Tests password hashing, JWT token generation/validation, and edge cases.
"""
import pytest
import os
from datetime import timedelta
from unittest.mock import patch, MagicMock


# Patch environment before importing auth module
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")

from app.utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    verify_token,
)


# ===================================================================
# Password hashing
# ===================================================================

class TestPasswordHashing:

    def test_hash_and_verify_password(self):
        password = "SecurePass123!"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_wrong_password_fails(self):
        hashed = get_password_hash("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_hash_is_not_plaintext(self):
        password = "mypassword"
        hashed = get_password_hash(password)
        assert hashed != password
        assert len(hashed) > len(password)

    def test_different_passwords_give_different_hashes(self):
        hash1 = get_password_hash("password1")
        hash2 = get_password_hash("password2")
        assert hash1 != hash2

    def test_same_password_gives_different_hashes(self):
        """bcrypt uses random salt, so same password produces different hashes"""
        hash1 = get_password_hash("samepassword")
        hash2 = get_password_hash("samepassword")
        assert hash1 != hash2
        # Both should verify correctly
        assert verify_password("samepassword", hash1) is True
        assert verify_password("samepassword", hash2) is True

    def test_empty_password(self):
        hashed = get_password_hash("")
        assert verify_password("", hashed) is True

    def test_long_password_truncated_to_72_bytes(self):
        """bcrypt has a 72-byte limit; passwords should be truncated"""
        long_password = "a" * 100
        hashed = get_password_hash(long_password)
        # The first 72 characters should verify
        assert verify_password(long_password, hashed) is True

    def test_unicode_password(self):
        password = "pAssw0rd"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_special_characters_password(self):
        password = "p@$$w0rd!#%^&*()"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True


# ===================================================================
# JWT token creation
# ===================================================================

class TestCreateAccessToken:

    def test_creates_valid_token(self):
        data = {"sub": "test@pau.edu.ng", "user_id": "123e4567-e89b-12d3-a456-426614174000"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_contains_payload(self):
        data = {"sub": "student@pau.edu.ng", "user_id": "abc-123"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "student@pau.edu.ng"
        assert decoded["user_id"] == "abc-123"

    def test_token_has_expiry(self):
        data = {"sub": "test@pau.edu.ng"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        assert "exp" in decoded

    def test_custom_expiry(self):
        data = {"sub": "test@pau.edu.ng"}
        token = create_access_token(data, expires_delta=timedelta(hours=2))
        decoded = decode_access_token(token)
        assert decoded is not None

    def test_original_data_not_mutated(self):
        data = {"sub": "test@pau.edu.ng"}
        original_keys = set(data.keys())
        create_access_token(data)
        assert set(data.keys()) == original_keys  # "exp" should NOT be in original


# ===================================================================
# JWT token decoding
# ===================================================================

class TestDecodeAccessToken:

    def test_valid_token_decodes(self):
        data = {"sub": "test@pau.edu.ng", "user_id": "uuid-here"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "test@pau.edu.ng"

    def test_invalid_token_returns_none(self):
        assert decode_access_token("invalid.token.string") is None

    def test_empty_token_returns_none(self):
        assert decode_access_token("") is None

    def test_expired_token_returns_none(self):
        data = {"sub": "test@pau.edu.ng"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        assert decode_access_token(token) is None

    def test_tampered_token_returns_none(self):
        data = {"sub": "test@pau.edu.ng"}
        token = create_access_token(data)
        # Tamper with the token by changing a character
        tampered = token[:-1] + ("a" if token[-1] != "a" else "b")
        result = decode_access_token(tampered)
        # Should be None due to signature mismatch
        assert result is None


# ===================================================================
# verify_token
# ===================================================================

class TestVerifyToken:

    def test_valid_token_returns_email(self):
        data = {"sub": "student@pau.edu.ng", "user_id": "uuid-123"}
        token = create_access_token(data)
        email = verify_token(token)
        assert email == "student@pau.edu.ng"

    def test_invalid_token_returns_none(self):
        assert verify_token("garbage") is None

    def test_token_without_sub_returns_none(self):
        data = {"user_id": "uuid-123"}  # Missing "sub" key
        token = create_access_token(data)
        email = verify_token(token)
        assert email is None
