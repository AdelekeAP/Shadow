"""
Tests for Pydantic schema validation
backend/app/schemas/

Tests that request/response schemas enforce correct validation rules.
"""
import pytest
from pydantic import ValidationError
from app.schemas.auth import UserCreate, UserLogin, UserResponse, Token


# ===================================================================
# UserCreate schema validation
# ===================================================================

class TestUserCreateSchema:

    def test_valid_user(self):
        user = UserCreate(
            email="student@pau.edu.ng",
            password="SecurePass123",
            full_name="John Doe",
            university_id="PAU/2022/001",
            entry_level="400L",
            target_cgpa=4.5,
        )
        assert user.email == "student@pau.edu.ng"
        assert user.full_name == "John Doe"

    def test_minimum_required_fields(self):
        user = UserCreate(
            email="minimal@pau.edu.ng",
            password="12345678",
            full_name="Jo",
        )
        assert user.email == "minimal@pau.edu.ng"

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="not-an-email",
                password="12345678",
                full_name="Test",
            )

    def test_password_too_short_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@pau.edu.ng",
                password="short",
                full_name="Test",
            )

    def test_password_exactly_8_chars(self):
        user = UserCreate(
            email="test@pau.edu.ng",
            password="exactly8",
            full_name="Test",
        )
        assert len(user.password) == 8

    def test_password_100_chars_max(self):
        user = UserCreate(
            email="test@pau.edu.ng",
            password="a" * 100,
            full_name="Test",
        )
        assert len(user.password) == 100

    def test_password_over_100_chars_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@pau.edu.ng",
                password="a" * 101,
                full_name="Test",
            )

    def test_full_name_too_short_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@pau.edu.ng",
                password="12345678",
                full_name="A",  # min_length=2
            )

    def test_valid_entry_levels(self):
        valid = ["100L", "200L", "200L-DE", "300L", "400L"]
        for level in valid:
            user = UserCreate(
                email="test@pau.edu.ng",
                password="12345678",
                full_name="Test",
                entry_level=level,
            )
            assert user.entry_level == level

    def test_invalid_entry_level_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@pau.edu.ng",
                password="12345678",
                full_name="Test",
                entry_level="500L",
            )

    def test_target_cgpa_range(self):
        user = UserCreate(
            email="test@pau.edu.ng",
            password="12345678",
            full_name="Test",
            target_cgpa=5.0,
        )
        assert user.target_cgpa == 5.0

    def test_target_cgpa_above_5_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@pau.edu.ng",
                password="12345678",
                full_name="Test",
                target_cgpa=5.1,
            )

    def test_target_cgpa_negative_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@pau.edu.ng",
                password="12345678",
                full_name="Test",
                target_cgpa=-0.1,
            )

    def test_optional_fields_default_to_none(self):
        user = UserCreate(
            email="test@pau.edu.ng",
            password="12345678",
            full_name="Test",
        )
        assert user.university_id is None
        assert user.current_cgpa is None
        assert user.target_cgpa is None

    def test_entry_level_defaults_to_400L(self):
        user = UserCreate(
            email="test@pau.edu.ng",
            password="12345678",
            full_name="Test",
        )
        assert user.entry_level == "400L"


# ===================================================================
# UserLogin schema
# ===================================================================

class TestUserLoginSchema:

    def test_valid_login(self):
        login = UserLogin(
            email="test@pau.edu.ng",
            password="mypassword",
        )
        assert login.email == "test@pau.edu.ng"

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            UserLogin(email="bad-email", password="password")

    def test_missing_password_raises(self):
        with pytest.raises(ValidationError):
            UserLogin(email="test@pau.edu.ng")


# ===================================================================
# UserResponse schema
# ===================================================================

class TestUserResponseSchema:

    def test_excludes_password(self):
        data = {
            "id": "uuid-123",
            "email": "test@pau.edu.ng",
            "full_name": "Test Student",
            "university_id": None,
            "entry_level": "400L",
            "gpa_scale": 5.0,
            "target_cgpa": 4.5,
            "current_cgpa": None,
            "total_credits_completed": 60,
            "created_at": None,
            "last_login": None,
            "is_active": True,
        }
        response = UserResponse(**data)
        response_dict = response.model_dump()
        assert "password" not in response_dict
        assert "password_hash" not in response_dict
