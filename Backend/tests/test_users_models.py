"""Tests for user domain models (Pydantic schemas)."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

import sys
sys.path.insert(0, str(__file__).rsplit("tests", 1)[0])

from domain.users.models import ProfileCreate, ProfileOut


class TestProfileCreate:
    """Tests for ProfileCreate model."""

    def test_create_with_all_fields(self):
        """Test creating ProfileCreate with all fields populated."""
        user_id = uuid4()
        profile = ProfileCreate(
            user_id=user_id,
            username="johndoe",
            display_name="John Doe",
            avatar_url="https://example.com/avatar.jpg",
        )
        
        assert profile.user_id == user_id
        assert profile.username == "johndoe"
        assert profile.display_name == "John Doe"
        assert profile.avatar_url == "https://example.com/avatar.jpg"

    def test_create_with_required_fields_only(self):
        """Test creating ProfileCreate with only required fields."""
        user_id = uuid4()
        profile = ProfileCreate(user_id=user_id, username="minimaluser")
        
        assert profile.user_id == user_id
        assert profile.username == "minimaluser"
        assert profile.display_name is None
        assert profile.avatar_url is None

    def test_create_with_none_optional_fields(self):
        """Test explicitly setting optional fields to None."""
        user_id = uuid4()
        profile = ProfileCreate(
            user_id=user_id,
            username="testuser",
            display_name=None,
            avatar_url=None,
        )
        
        assert profile.display_name is None
        assert profile.avatar_url is None

    def test_create_missing_user_id_raises(self):
        """Test that missing user_id raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ProfileCreate(username="testuser")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("user_id",)
        assert errors[0]["type"] == "missing"

    def test_create_missing_username_raises(self):
        """Test that missing username raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ProfileCreate(user_id=uuid4())
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("username",)
        assert errors[0]["type"] == "missing"

    def test_create_invalid_user_id_raises(self):
        """Test that invalid UUID format raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ProfileCreate(user_id="not-a-uuid", username="testuser")
        
        errors = exc_info.value.errors()
        assert errors[0]["loc"] == ("user_id",)

    def test_create_from_string_uuid(self):
        """Test creating ProfileCreate with string UUID."""
        uuid_str = "12345678-1234-5678-1234-567812345678"
        profile = ProfileCreate(user_id=uuid_str, username="testuser")
        
        assert profile.user_id == UUID(uuid_str)

    def test_create_empty_username(self):
        """Test that empty username is accepted (no min length constraint)."""
        profile = ProfileCreate(user_id=uuid4(), username="")
        assert profile.username == ""

    def test_model_dump(self):
        """Test serializing ProfileCreate to dict."""
        user_id = uuid4()
        profile = ProfileCreate(
            user_id=user_id,
            username="testuser",
            display_name="Test",
            avatar_url="https://example.com/pic.png",
        )
        
        data = profile.model_dump()
        assert data == {
            "user_id": user_id,
            "username": "testuser",
            "display_name": "Test",
            "avatar_url": "https://example.com/pic.png",
        }

    def test_model_dump_json(self):
        """Test serializing ProfileCreate to JSON string."""
        user_id = UUID("12345678-1234-5678-1234-567812345678")
        profile = ProfileCreate(user_id=user_id, username="testuser")
        
        json_str = profile.model_dump_json()
        assert '"user_id":"12345678-1234-5678-1234-567812345678"' in json_str
        assert '"username":"testuser"' in json_str


class TestProfileOut:
    """Tests for ProfileOut model."""

    def test_create_with_all_fields(self):
        """Test creating ProfileOut with all fields populated."""
        user_id = uuid4()
        created_at = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        
        profile = ProfileOut(
            user_id=user_id,
            username="johndoe",
            display_name="John Doe",
            avatar_url="https://example.com/avatar.jpg",
            created_at=created_at,
        )
        
        assert profile.user_id == user_id
        assert profile.username == "johndoe"
        assert profile.display_name == "John Doe"
        assert profile.avatar_url == "https://example.com/avatar.jpg"
        assert profile.created_at == created_at

    def test_create_with_required_fields_only(self):
        """Test creating ProfileOut with required fields and optional as None."""
        user_id = uuid4()
        created_at = datetime.now(timezone.utc)
        
        profile = ProfileOut(
            user_id=user_id,
            username="minimaluser",
            created_at=created_at,
        )
        
        assert profile.user_id == user_id
        assert profile.username == "minimaluser"
        assert profile.display_name is None
        assert profile.avatar_url is None
        assert profile.created_at == created_at

    def test_create_missing_created_at_raises(self):
        """Test that missing created_at raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ProfileOut(user_id=uuid4(), username="testuser")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("created_at",)
        assert errors[0]["type"] == "missing"

    def test_create_missing_user_id_raises(self):
        """Test that missing user_id raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ProfileOut(username="testuser", created_at=datetime.now(timezone.utc))
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("user_id",)

    def test_create_missing_username_raises(self):
        """Test that missing username raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ProfileOut(user_id=uuid4(), created_at=datetime.now(timezone.utc))
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("username",)

    def test_create_from_string_uuid(self):
        """Test creating ProfileOut with string UUID."""
        uuid_str = "12345678-1234-5678-1234-567812345678"
        profile = ProfileOut(
            user_id=uuid_str,
            username="testuser",
            created_at=datetime.now(timezone.utc),
        )
        
        assert profile.user_id == UUID(uuid_str)

    def test_create_from_iso_datetime_string(self):
        """Test creating ProfileOut with ISO datetime string."""
        profile = ProfileOut(
            user_id=uuid4(),
            username="testuser",
            created_at="2024-01-15T10:30:00Z",
        )
        
        assert profile.created_at == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    def test_model_dump(self):
        """Test serializing ProfileOut to dict."""
        user_id = uuid4()
        created_at = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        
        profile = ProfileOut(
            user_id=user_id,
            username="testuser",
            display_name="Test",
            avatar_url="https://example.com/pic.png",
            created_at=created_at,
        )
        
        data = profile.model_dump()
        assert data == {
            "user_id": user_id,
            "username": "testuser",
            "display_name": "Test",
            "avatar_url": "https://example.com/pic.png",
            "created_at": created_at,
        }

    def test_model_dump_json(self):
        """Test serializing ProfileOut to JSON string."""
        user_id = UUID("12345678-1234-5678-1234-567812345678")
        created_at = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        
        profile = ProfileOut(
            user_id=user_id,
            username="testuser",
            created_at=created_at,
        )
        
        json_str = profile.model_dump_json()
        assert '"user_id":"12345678-1234-5678-1234-567812345678"' in json_str
        assert '"username":"testuser"' in json_str

    def test_created_at_naive_datetime_accepted(self):
        """Test that naive datetime (without timezone) is accepted."""
        naive_dt = datetime(2024, 1, 15, 10, 30, 0)
        profile = ProfileOut(
            user_id=uuid4(),
            username="testuser",
            created_at=naive_dt,
        )
        
        assert profile.created_at == naive_dt


class TestProfileModelsEquality:
    """Tests for model equality and comparison."""

    def test_profile_create_equality(self):
        """Test that two ProfileCreate instances with same values are equal."""
        user_id = uuid4()
        profile1 = ProfileCreate(user_id=user_id, username="test")
        profile2 = ProfileCreate(user_id=user_id, username="test")
        
        assert profile1 == profile2

    def test_profile_create_inequality(self):
        """Test that ProfileCreate instances with different values are not equal."""
        user_id = uuid4()
        profile1 = ProfileCreate(user_id=user_id, username="test1")
        profile2 = ProfileCreate(user_id=user_id, username="test2")
        
        assert profile1 != profile2

    def test_profile_out_equality(self):
        """Test that two ProfileOut instances with same values are equal."""
        user_id = uuid4()
        created_at = datetime.now(timezone.utc)
        
        profile1 = ProfileOut(user_id=user_id, username="test", created_at=created_at)
        profile2 = ProfileOut(user_id=user_id, username="test", created_at=created_at)
        
        assert profile1 == profile2

    def test_profile_out_inequality(self):
        """Test that ProfileOut instances with different values are not equal."""
        user_id = uuid4()
        created_at = datetime.now(timezone.utc)
        
        profile1 = ProfileOut(user_id=user_id, username="test1", created_at=created_at)
        profile2 = ProfileOut(user_id=user_id, username="test2", created_at=created_at)
        
        assert profile1 != profile2

