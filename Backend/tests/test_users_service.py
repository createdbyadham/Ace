"""Tests for ProfileService (users domain service layer)."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

import sys
sys.path.insert(0, str(__file__).rsplit("tests", 1)[0])

from domain.users.models import ProfileCreate, ProfileOut
from domain.users.service import ProfileService


# Sample test data
TEST_USER_ID = UUID("12345678-1234-5678-1234-567812345678")
TEST_CREATED_AT = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)


@pytest.fixture
def mock_pool() -> MagicMock:
    """Create a mock asyncpg pool."""
    return MagicMock()


@pytest.fixture
def mock_connection() -> AsyncMock:
    """Create a mock asyncpg connection."""
    return AsyncMock()


@pytest.fixture
def service_with_mock_pool(mock_pool: MagicMock, mock_connection: AsyncMock) -> ProfileService:
    """Create ProfileService with mocked pool and connection."""
    # Set up the context manager for pool.acquire()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    return ProfileService(mock_pool)


class TestProfileServiceInit:
    """Tests for ProfileService initialization."""

    def test_init_stores_pool(self, mock_pool: MagicMock):
        """Test that ProfileService stores the pool reference."""
        service = ProfileService(mock_pool)
        assert service._pool is mock_pool


class TestUpsertProfile:
    """Tests for ProfileService.upsert_profile method."""

    @pytest.mark.asyncio
    async def test_upsert_profile_creates_new_profile(
        self, service_with_mock_pool: ProfileService, mock_connection: AsyncMock
    ):
        """Test creating a new profile via upsert."""
        payload = ProfileCreate(
            user_id=TEST_USER_ID,
            username="newuser",
            display_name="New User",
            avatar_url="https://example.com/avatar.png",
        )
        
        mock_connection.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "newuser",
            "display_name": "New User",
            "avatar_url": "https://example.com/avatar.png",
            "created_at": TEST_CREATED_AT,
        }
        
        result = await service_with_mock_pool.upsert_profile(payload)
        
        assert isinstance(result, ProfileOut)
        assert result.user_id == TEST_USER_ID
        assert result.username == "newuser"
        assert result.display_name == "New User"
        assert result.avatar_url == "https://example.com/avatar.png"
        assert result.created_at == TEST_CREATED_AT

    @pytest.mark.asyncio
    async def test_upsert_profile_updates_existing(
        self, service_with_mock_pool: ProfileService, mock_connection: AsyncMock
    ):
        """Test updating an existing profile via upsert."""
        payload = ProfileCreate(
            user_id=TEST_USER_ID,
            username="updateduser",
            display_name="Updated Name",
            avatar_url="https://example.com/new-avatar.png",
        )
        
        mock_connection.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "updateduser",
            "display_name": "Updated Name",
            "avatar_url": "https://example.com/new-avatar.png",
            "created_at": TEST_CREATED_AT,
        }
        
        result = await service_with_mock_pool.upsert_profile(payload)
        
        assert result.username == "updateduser"
        assert result.display_name == "Updated Name"
        assert result.avatar_url == "https://example.com/new-avatar.png"

    @pytest.mark.asyncio
    async def test_upsert_profile_with_minimal_data(
        self, service_with_mock_pool: ProfileService, mock_connection: AsyncMock
    ):
        """Test upserting with only required fields."""
        payload = ProfileCreate(user_id=TEST_USER_ID, username="minimaluser")
        
        mock_connection.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "minimaluser",
            "display_name": None,
            "avatar_url": None,
            "created_at": TEST_CREATED_AT,
        }
        
        result = await service_with_mock_pool.upsert_profile(payload)
        
        assert result.user_id == TEST_USER_ID
        assert result.username == "minimaluser"
        assert result.display_name is None
        assert result.avatar_url is None

    @pytest.mark.asyncio
    async def test_upsert_profile_calls_correct_sql(
        self, service_with_mock_pool: ProfileService, mock_connection: AsyncMock
    ):
        """Test that upsert_profile executes the correct SQL query."""
        payload = ProfileCreate(
            user_id=TEST_USER_ID,
            username="sqltest",
            display_name="SQL Test",
            avatar_url="https://example.com/sql.png",
        )
        
        mock_connection.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "sqltest",
            "display_name": "SQL Test",
            "avatar_url": "https://example.com/sql.png",
            "created_at": TEST_CREATED_AT,
        }
        
        await service_with_mock_pool.upsert_profile(payload)
        
        # Verify fetchrow was called
        mock_connection.fetchrow.assert_called_once()
        
        # Get the SQL query from the call
        call_args = mock_connection.fetchrow.call_args
        sql_query = call_args[0][0]
        
        # Verify key parts of the SQL
        assert "INSERT INTO app.profiles" in sql_query
        assert "ON CONFLICT (user_id) DO UPDATE" in sql_query
        assert "RETURNING" in sql_query
        
        # Verify parameters
        assert call_args[0][1] == TEST_USER_ID
        assert call_args[0][2] == "sqltest"
        assert call_args[0][3] == "SQL Test"
        assert call_args[0][4] == "https://example.com/sql.png"

    @pytest.mark.asyncio
    async def test_upsert_profile_acquires_connection(
        self, mock_pool: MagicMock, mock_connection: AsyncMock
    ):
        """Test that upsert_profile acquires a connection from the pool."""
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        service = ProfileService(mock_pool)
        
        mock_connection.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "test",
            "display_name": None,
            "avatar_url": None,
            "created_at": TEST_CREATED_AT,
        }
        
        await service.upsert_profile(ProfileCreate(user_id=TEST_USER_ID, username="test"))
        
        mock_pool.acquire.assert_called_once()


class TestGetProfile:
    """Tests for ProfileService.get_profile method."""

    @pytest.mark.asyncio
    async def test_get_profile_returns_profile_when_found(
        self, service_with_mock_pool: ProfileService, mock_connection: AsyncMock
    ):
        """Test getting an existing profile."""
        mock_connection.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "existinguser",
            "display_name": "Existing User",
            "avatar_url": "https://example.com/existing.png",
            "created_at": TEST_CREATED_AT,
        }
        
        result = await service_with_mock_pool.get_profile(TEST_USER_ID)
        
        assert result is not None
        assert isinstance(result, ProfileOut)
        assert result.user_id == TEST_USER_ID
        assert result.username == "existinguser"
        assert result.display_name == "Existing User"
        assert result.avatar_url == "https://example.com/existing.png"
        assert result.created_at == TEST_CREATED_AT

    @pytest.mark.asyncio
    async def test_get_profile_returns_none_when_not_found(
        self, service_with_mock_pool: ProfileService, mock_connection: AsyncMock
    ):
        """Test getting a non-existent profile returns None."""
        mock_connection.fetchrow.return_value = None
        
        result = await service_with_mock_pool.get_profile(TEST_USER_ID)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_profile_with_minimal_data(
        self, service_with_mock_pool: ProfileService, mock_connection: AsyncMock
    ):
        """Test getting a profile with only required fields populated."""
        mock_connection.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "minimaluser",
            "display_name": None,
            "avatar_url": None,
            "created_at": TEST_CREATED_AT,
        }
        
        result = await service_with_mock_pool.get_profile(TEST_USER_ID)
        
        assert result is not None
        assert result.display_name is None
        assert result.avatar_url is None

    @pytest.mark.asyncio
    async def test_get_profile_calls_correct_sql(
        self, service_with_mock_pool: ProfileService, mock_connection: AsyncMock
    ):
        """Test that get_profile executes the correct SQL query."""
        mock_connection.fetchrow.return_value = None
        
        await service_with_mock_pool.get_profile(TEST_USER_ID)
        
        mock_connection.fetchrow.assert_called_once()
        
        call_args = mock_connection.fetchrow.call_args
        sql_query = call_args[0][0]
        
        assert "SELECT" in sql_query
        assert "FROM app.profiles" in sql_query
        assert "WHERE user_id = $1" in sql_query
        assert call_args[0][1] == TEST_USER_ID

    @pytest.mark.asyncio
    async def test_get_profile_acquires_connection(
        self, mock_pool: MagicMock, mock_connection: AsyncMock
    ):
        """Test that get_profile acquires a connection from the pool."""
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        service = ProfileService(mock_pool)
        
        mock_connection.fetchrow.return_value = None
        
        await service.get_profile(TEST_USER_ID)
        
        mock_pool.acquire.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_profile_with_different_user_ids(
        self, service_with_mock_pool: ProfileService, mock_connection: AsyncMock
    ):
        """Test get_profile with various user IDs."""
        test_ids = [
            uuid4(),
            UUID("00000000-0000-0000-0000-000000000000"),
            UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
        ]
        
        for user_id in test_ids:
            mock_connection.fetchrow.return_value = None
            mock_connection.fetchrow.reset_mock()
            
            await service_with_mock_pool.get_profile(user_id)
            
            call_args = mock_connection.fetchrow.call_args
            assert call_args[0][1] == user_id


class TestProfileServiceEdgeCases:
    """Edge case tests for ProfileService."""

    @pytest.mark.asyncio
    async def test_upsert_with_empty_username(
        self, service_with_mock_pool: ProfileService, mock_connection: AsyncMock
    ):
        """Test upserting with empty username string."""
        payload = ProfileCreate(user_id=TEST_USER_ID, username="")
        
        mock_connection.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "",
            "display_name": None,
            "avatar_url": None,
            "created_at": TEST_CREATED_AT,
        }
        
        result = await service_with_mock_pool.upsert_profile(payload)
        
        assert result.username == ""

    @pytest.mark.asyncio
    async def test_upsert_with_unicode_characters(
        self, service_with_mock_pool: ProfileService, mock_connection: AsyncMock
    ):
        """Test upserting with unicode characters."""
        payload = ProfileCreate(
            user_id=TEST_USER_ID,
            username="用户名",
            display_name="日本語名前 🎉",
            avatar_url="https://example.com/émoji.png",
        )
        
        mock_connection.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "用户名",
            "display_name": "日本語名前 🎉",
            "avatar_url": "https://example.com/émoji.png",
            "created_at": TEST_CREATED_AT,
        }
        
        result = await service_with_mock_pool.upsert_profile(payload)
        
        assert result.username == "用户名"
        assert result.display_name == "日本語名前 🎉"

    @pytest.mark.asyncio
    async def test_upsert_with_very_long_strings(
        self, service_with_mock_pool: ProfileService, mock_connection: AsyncMock
    ):
        """Test upserting with very long string values."""
        long_username = "a" * 1000
        long_display_name = "b" * 1000
        long_url = "https://example.com/" + "c" * 1000
        
        payload = ProfileCreate(
            user_id=TEST_USER_ID,
            username=long_username,
            display_name=long_display_name,
            avatar_url=long_url,
        )
        
        mock_connection.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": long_username,
            "display_name": long_display_name,
            "avatar_url": long_url,
            "created_at": TEST_CREATED_AT,
        }
        
        result = await service_with_mock_pool.upsert_profile(payload)
        
        assert result.username == long_username
        assert result.display_name == long_display_name
        assert result.avatar_url == long_url

    @pytest.mark.asyncio
    async def test_service_handles_special_characters_in_strings(
        self, service_with_mock_pool: ProfileService, mock_connection: AsyncMock
    ):
        """Test handling of SQL-sensitive special characters."""
        payload = ProfileCreate(
            user_id=TEST_USER_ID,
            username="user'; DROP TABLE profiles; --",
            display_name="Robert'); DROP TABLE Students;--",
            avatar_url="https://example.com/test?q=1&x=2",
        )
        
        mock_connection.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "user'; DROP TABLE profiles; --",
            "display_name": "Robert'); DROP TABLE Students;--",
            "avatar_url": "https://example.com/test?q=1&x=2",
            "created_at": TEST_CREATED_AT,
        }
        
        result = await service_with_mock_pool.upsert_profile(payload)
        
        # Values should be stored as-is (parameterized queries prevent SQL injection)
        assert result.username == "user'; DROP TABLE profiles; --"


class TestProfileServiceDatabaseExceptions:
    """Tests for database exception handling in ProfileService."""

    @pytest.mark.asyncio
    async def test_upsert_profile_propagates_db_exceptions(
        self, service_with_mock_pool: ProfileService, mock_connection: AsyncMock
    ):
        """Test that database exceptions propagate from upsert_profile."""
        import asyncpg
        
        payload = ProfileCreate(user_id=TEST_USER_ID, username="test")
        
        mock_connection.fetchrow.side_effect = asyncpg.PostgresError("Connection lost")
        
        with pytest.raises(asyncpg.PostgresError):
            await service_with_mock_pool.upsert_profile(payload)

    @pytest.mark.asyncio
    async def test_get_profile_propagates_db_exceptions(
        self, service_with_mock_pool: ProfileService, mock_connection: AsyncMock
    ):
        """Test that database exceptions propagate from get_profile."""
        import asyncpg
        
        mock_connection.fetchrow.side_effect = asyncpg.PostgresError("Connection lost")
        
        with pytest.raises(asyncpg.PostgresError):
            await service_with_mock_pool.get_profile(TEST_USER_ID)

    @pytest.mark.asyncio
    async def test_upsert_profile_unique_violation(
        self, service_with_mock_pool: ProfileService, mock_connection: AsyncMock
    ):
        """Test handling of unique constraint violations."""
        import asyncpg
        
        payload = ProfileCreate(user_id=TEST_USER_ID, username="duplicate")
        
        mock_connection.fetchrow.side_effect = asyncpg.UniqueViolationError(
            "duplicate key value"
        )
        
        with pytest.raises(asyncpg.UniqueViolationError):
            await service_with_mock_pool.upsert_profile(payload)

    @pytest.mark.asyncio
    async def test_upsert_profile_connection_timeout(
        self, service_with_mock_pool: ProfileService, mock_connection: AsyncMock
    ):
        """Test handling of connection timeouts."""
        import asyncio
        
        payload = ProfileCreate(user_id=TEST_USER_ID, username="test")
        
        mock_connection.fetchrow.side_effect = asyncio.TimeoutError("Query timed out")
        
        with pytest.raises(asyncio.TimeoutError):
            await service_with_mock_pool.upsert_profile(payload)


class TestProfileServiceConcurrency:
    """Tests for concurrent access patterns."""

    @pytest.mark.asyncio
    async def test_multiple_get_profile_calls(
        self, service_with_mock_pool: ProfileService, mock_connection: AsyncMock
    ):
        """Test multiple sequential get_profile calls."""
        user_ids = [uuid4() for _ in range(5)]
        
        for user_id in user_ids:
            mock_connection.fetchrow.return_value = {
                "user_id": user_id,
                "username": f"user_{user_id}",
                "display_name": None,
                "avatar_url": None,
                "created_at": TEST_CREATED_AT,
            }
            
            result = await service_with_mock_pool.get_profile(user_id)
            assert result.user_id == user_id

    @pytest.mark.asyncio
    async def test_concurrent_upsert_calls(
        self, mock_pool: MagicMock
    ):
        """Test concurrent upsert_profile calls."""
        import asyncio
        
        mock_conn = AsyncMock()
        
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_conn.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "test",
            "display_name": None,
            "avatar_url": None,
            "created_at": TEST_CREATED_AT,
        }
        
        service = ProfileService(mock_pool)
        
        # Make two concurrent calls
        payload = ProfileCreate(user_id=TEST_USER_ID, username="test")
        
        results = await asyncio.gather(
            service.upsert_profile(payload),
            service.upsert_profile(payload),
        )
        
        assert len(results) == 2
        assert all(isinstance(r, ProfileOut) for r in results)
        # Verify fetchrow was called twice (once per concurrent call)
        assert mock_conn.fetchrow.call_count == 2
