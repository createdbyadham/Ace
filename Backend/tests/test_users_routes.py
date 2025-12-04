"""Tests for users API endpoints (routes)."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, str(__file__).rsplit("tests", 1)[0])

from main import create_app
from db.pool import get_pool
from domain.users.models import ProfileOut
from domain.users.service import ProfileService


# Test constants
TEST_USER_ID = UUID("12345678-1234-5678-1234-567812345678")
TEST_USER_ID_STR = "12345678-1234-5678-1234-567812345678"
TEST_CREATED_AT = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)


@pytest.fixture
def mock_pool() -> MagicMock:
    """Create a mock asyncpg pool."""
    return MagicMock()


@pytest.fixture
def app_with_mock_pool(mock_pool: MagicMock):
    """Create FastAPI app with mocked database pool."""
    app = create_app()
    app.dependency_overrides[get_pool] = lambda: mock_pool
    return app


@pytest.fixture
def client(app_with_mock_pool) -> TestClient:
    """Create test client."""
    with TestClient(app_with_mock_pool) as c:
        yield c


class TestCreateUserEndpoint:
    """Tests for POST /users endpoint."""

    def test_create_user_success(self, client: TestClient, mock_pool: MagicMock):
        """Test successful user creation."""
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_conn.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "newuser",
            "display_name": "New User",
            "avatar_url": "https://example.com/avatar.png",
            "created_at": TEST_CREATED_AT,
        }
        
        response = client.post(
            "/users",
            json={
                "user_id": TEST_USER_ID_STR,
                "username": "newuser",
                "display_name": "New User",
                "avatar_url": "https://example.com/avatar.png",
            },
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == TEST_USER_ID_STR
        assert data["username"] == "newuser"
        assert data["display_name"] == "New User"
        assert data["avatar_url"] == "https://example.com/avatar.png"
        assert "created_at" in data

    def test_create_user_minimal_payload(self, client: TestClient, mock_pool: MagicMock):
        """Test user creation with only required fields."""
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_conn.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "minimaluser",
            "display_name": None,
            "avatar_url": None,
            "created_at": TEST_CREATED_AT,
        }
        
        response = client.post(
            "/users",
            json={
                "user_id": TEST_USER_ID_STR,
                "username": "minimaluser",
            },
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == TEST_USER_ID_STR
        assert data["username"] == "minimaluser"
        assert data["display_name"] is None
        assert data["avatar_url"] is None

    def test_create_user_missing_user_id(self, client: TestClient):
        """Test that missing user_id returns 422."""
        response = client.post(
            "/users",
            json={"username": "testuser"},
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data
        errors = data["detail"]
        assert any(err["loc"][-1] == "user_id" for err in errors)

    def test_create_user_missing_username(self, client: TestClient):
        """Test that missing username returns 422."""
        response = client.post(
            "/users",
            json={"user_id": TEST_USER_ID_STR},
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data
        errors = data["detail"]
        assert any(err["loc"][-1] == "username" for err in errors)

    def test_create_user_invalid_user_id_format(self, client: TestClient):
        """Test that invalid UUID format returns 422."""
        response = client.post(
            "/users",
            json={
                "user_id": "not-a-valid-uuid",
                "username": "testuser",
            },
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_user_empty_body(self, client: TestClient):
        """Test that empty request body returns 422."""
        response = client.post("/users", json={})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_user_null_optional_fields(self, client: TestClient, mock_pool: MagicMock):
        """Test user creation with explicit null values for optional fields."""
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_conn.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "testuser",
            "display_name": None,
            "avatar_url": None,
            "created_at": TEST_CREATED_AT,
        }
        
        response = client.post(
            "/users",
            json={
                "user_id": TEST_USER_ID_STR,
                "username": "testuser",
                "display_name": None,
                "avatar_url": None,
            },
        )
        
        assert response.status_code == status.HTTP_200_OK

    def test_create_user_updates_existing(self, client: TestClient, mock_pool: MagicMock):
        """Test that creating a user with existing ID updates the user (upsert)."""
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # First creation
        mock_conn.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "originaluser",
            "display_name": "Original",
            "avatar_url": None,
            "created_at": TEST_CREATED_AT,
        }
        
        response1 = client.post(
            "/users",
            json={
                "user_id": TEST_USER_ID_STR,
                "username": "originaluser",
                "display_name": "Original",
            },
        )
        assert response1.status_code == status.HTTP_200_OK
        
        # Update (upsert)
        mock_conn.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "updateduser",
            "display_name": "Updated",
            "avatar_url": "https://new-avatar.png",
            "created_at": TEST_CREATED_AT,
        }
        
        response2 = client.post(
            "/users",
            json={
                "user_id": TEST_USER_ID_STR,
                "username": "updateduser",
                "display_name": "Updated",
                "avatar_url": "https://new-avatar.png",
            },
        )
        
        assert response2.status_code == status.HTTP_200_OK
        data = response2.json()
        assert data["username"] == "updateduser"
        assert data["display_name"] == "Updated"

    def test_create_user_with_unicode(self, client: TestClient, mock_pool: MagicMock):
        """Test user creation with unicode characters."""
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_conn.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "用户",
            "display_name": "テストユーザー 🎉",
            "avatar_url": None,
            "created_at": TEST_CREATED_AT,
        }
        
        response = client.post(
            "/users",
            json={
                "user_id": TEST_USER_ID_STR,
                "username": "用户",
                "display_name": "テストユーザー 🎉",
            },
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "用户"
        assert data["display_name"] == "テストユーザー 🎉"


class TestGetUserEndpoint:
    """Tests for GET /users/{user_id} endpoint."""

    def test_get_user_success(self, client: TestClient, mock_pool: MagicMock):
        """Test successful user retrieval."""
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_conn.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "existinguser",
            "display_name": "Existing User",
            "avatar_url": "https://example.com/avatar.png",
            "created_at": TEST_CREATED_AT,
        }
        
        response = client.get(f"/users/{TEST_USER_ID_STR}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == TEST_USER_ID_STR
        assert data["username"] == "existinguser"
        assert data["display_name"] == "Existing User"
        assert data["avatar_url"] == "https://example.com/avatar.png"
        assert "created_at" in data

    def test_get_user_not_found(self, client: TestClient, mock_pool: MagicMock):
        """Test getting a non-existent user returns 404."""
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_conn.fetchrow.return_value = None
        
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/users/{non_existent_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["detail"] == "User not found"

    def test_get_user_invalid_uuid_format(self, client: TestClient):
        """Test getting user with invalid UUID format returns 422."""
        response = client.get("/users/not-a-valid-uuid")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_user_with_minimal_profile(self, client: TestClient, mock_pool: MagicMock):
        """Test getting a user with only required fields populated."""
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_conn.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "minimaluser",
            "display_name": None,
            "avatar_url": None,
            "created_at": TEST_CREATED_AT,
        }
        
        response = client.get(f"/users/{TEST_USER_ID_STR}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["display_name"] is None
        assert data["avatar_url"] is None

    def test_get_user_various_uuid_formats(self, client: TestClient, mock_pool: MagicMock):
        """Test that various valid UUID formats are accepted."""
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Standard lowercase
        mock_conn.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "test",
            "display_name": None,
            "avatar_url": None,
            "created_at": TEST_CREATED_AT,
        }
        
        response = client.get(f"/users/{TEST_USER_ID_STR.lower()}")
        assert response.status_code == status.HTTP_200_OK
        
        # Uppercase
        response = client.get(f"/users/{TEST_USER_ID_STR.upper()}")
        assert response.status_code == status.HTTP_200_OK


class TestUserEndpointsResponseFormat:
    """Tests for response format and content-type."""

    def test_create_user_returns_json(self, client: TestClient, mock_pool: MagicMock):
        """Test that POST /users returns JSON content-type."""
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
        
        response = client.post(
            "/users",
            json={"user_id": TEST_USER_ID_STR, "username": "test"},
        )
        
        assert "application/json" in response.headers.get("content-type", "")

    def test_get_user_returns_json(self, client: TestClient, mock_pool: MagicMock):
        """Test that GET /users/{user_id} returns JSON content-type."""
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
        
        response = client.get(f"/users/{TEST_USER_ID_STR}")
        
        assert "application/json" in response.headers.get("content-type", "")

    def test_error_response_format(self, client: TestClient, mock_pool: MagicMock):
        """Test that error responses have correct format."""
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_conn.fetchrow.return_value = None
        
        response = client.get(f"/users/{TEST_USER_ID_STR}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)


class TestUserEndpointsWithServiceMock:
    """Tests using service-level mocking for more isolated testing."""

    def test_create_user_calls_service(self, mock_pool: MagicMock):
        """Test that POST /users calls ProfileService.upsert_profile."""
        app = create_app()
        
        mock_profile_out = ProfileOut(
            user_id=TEST_USER_ID,
            username="testuser",
            display_name="Test",
            avatar_url=None,
            created_at=TEST_CREATED_AT,
        )
        
        with patch.object(ProfileService, "upsert_profile", new_callable=AsyncMock) as mock_upsert:
            mock_upsert.return_value = mock_profile_out
            app.dependency_overrides[get_pool] = lambda: mock_pool
            
            with TestClient(app) as client:
                response = client.post(
                    "/users",
                    json={"user_id": TEST_USER_ID_STR, "username": "testuser", "display_name": "Test"},
                )
            
            assert response.status_code == status.HTTP_200_OK
            mock_upsert.assert_called_once()

    def test_get_user_calls_service(self, mock_pool: MagicMock):
        """Test that GET /users/{user_id} calls ProfileService.get_profile."""
        app = create_app()
        
        mock_profile_out = ProfileOut(
            user_id=TEST_USER_ID,
            username="testuser",
            display_name=None,
            avatar_url=None,
            created_at=TEST_CREATED_AT,
        )
        
        with patch.object(ProfileService, "get_profile", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_profile_out
            app.dependency_overrides[get_pool] = lambda: mock_pool
            
            with TestClient(app) as client:
                response = client.get(f"/users/{TEST_USER_ID_STR}")
            
            assert response.status_code == status.HTTP_200_OK
            mock_get.assert_called_once_with(TEST_USER_ID)

    def test_get_user_service_returns_none(self, mock_pool: MagicMock):
        """Test 404 when service returns None."""
        app = create_app()
        
        with patch.object(ProfileService, "get_profile", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            app.dependency_overrides[get_pool] = lambda: mock_pool
            
            with TestClient(app) as client:
                response = client.get(f"/users/{TEST_USER_ID_STR}")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUserEndpointsEdgeCases:
    """Edge case tests for user endpoints."""

    def test_create_user_with_extra_fields_ignored(self, client: TestClient, mock_pool: MagicMock):
        """Test that extra fields in request are ignored."""
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
        
        response = client.post(
            "/users",
            json={
                "user_id": TEST_USER_ID_STR,
                "username": "test",
                "extra_field": "should_be_ignored",
                "another_extra": 12345,
            },
        )
        
        assert response.status_code == status.HTTP_200_OK

    def test_create_user_wrong_content_type(self, client: TestClient):
        """Test that non-JSON content type is rejected."""
        response = client.post(
            "/users",
            content="user_id=123&username=test",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_user_with_trailing_slash(self, client: TestClient, mock_pool: MagicMock):
        """Test GET /users/{user_id}/ with trailing slash."""
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
        
        # FastAPI may redirect or handle trailing slash differently
        response = client.get(f"/users/{TEST_USER_ID_STR}/", follow_redirects=True)
        
        # Either 200 (if redirected) or 307 (temporary redirect) or 404 is acceptable
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_307_TEMPORARY_REDIRECT,
            status.HTTP_404_NOT_FOUND,
        ]

    def test_create_user_empty_string_username(self, client: TestClient, mock_pool: MagicMock):
        """Test creating user with empty string username."""
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_conn.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "",
            "display_name": None,
            "avatar_url": None,
            "created_at": TEST_CREATED_AT,
        }
        
        response = client.post(
            "/users",
            json={"user_id": TEST_USER_ID_STR, "username": ""},
        )
        
        # Empty username should be accepted (no validation constraint)
        assert response.status_code == status.HTTP_200_OK

    def test_create_user_whitespace_only_username(self, client: TestClient, mock_pool: MagicMock):
        """Test creating user with whitespace-only username."""
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_conn.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "   ",
            "display_name": None,
            "avatar_url": None,
            "created_at": TEST_CREATED_AT,
        }
        
        response = client.post(
            "/users",
            json={"user_id": TEST_USER_ID_STR, "username": "   "},
        )
        
        assert response.status_code == status.HTTP_200_OK


class TestUserEndpointsHTTPMethods:
    """Tests for HTTP method handling."""

    def test_users_endpoint_allows_post(self, client: TestClient, mock_pool: MagicMock):
        """Test that POST is allowed on /users."""
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
        
        response = client.post(
            "/users",
            json={"user_id": TEST_USER_ID_STR, "username": "test"},
        )
        
        assert response.status_code == status.HTTP_200_OK

    def test_users_endpoint_rejects_get(self, client: TestClient):
        """Test that GET on /users (without ID) returns 405."""
        response = client.get("/users")
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_users_endpoint_rejects_put(self, client: TestClient):
        """Test that PUT on /users returns 405."""
        response = client.put(
            "/users",
            json={"user_id": TEST_USER_ID_STR, "username": "test"},
        )
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_users_endpoint_rejects_delete(self, client: TestClient):
        """Test that DELETE on /users returns 405."""
        response = client.delete("/users")
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_user_id_endpoint_allows_get(self, client: TestClient, mock_pool: MagicMock):
        """Test that GET is allowed on /users/{user_id}."""
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
        
        response = client.get(f"/users/{TEST_USER_ID_STR}")
        
        assert response.status_code == status.HTTP_200_OK

    def test_user_id_endpoint_rejects_post(self, client: TestClient):
        """Test that POST on /users/{user_id} returns 405."""
        response = client.post(
            f"/users/{TEST_USER_ID_STR}",
            json={"username": "test"},
        )
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_user_id_endpoint_rejects_put(self, client: TestClient):
        """Test that PUT on /users/{user_id} returns 405."""
        response = client.put(
            f"/users/{TEST_USER_ID_STR}",
            json={"username": "test"},
        )
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_user_id_endpoint_rejects_delete(self, client: TestClient):
        """Test that DELETE on /users/{user_id} returns 405."""
        response = client.delete(f"/users/{TEST_USER_ID_STR}")
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestUserEndpointsDatabaseErrors:
    """Tests for database error handling."""

    def test_create_user_db_connection_error(self, mock_pool: MagicMock):
        """Test that database connection errors are handled."""
        app = create_app()
        
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Simulate database error
        mock_conn.fetchrow.side_effect = Exception("Connection refused")
        
        app.dependency_overrides[get_pool] = lambda: mock_pool
        
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(
                "/users",
                json={"user_id": TEST_USER_ID_STR, "username": "test"},
            )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_user_db_connection_error(self, mock_pool: MagicMock):
        """Test that database connection errors are handled on GET."""
        app = create_app()
        
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_conn.fetchrow.side_effect = Exception("Database unavailable")
        
        app.dependency_overrides[get_pool] = lambda: mock_pool
        
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get(f"/users/{TEST_USER_ID_STR}")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_create_user_unique_constraint_violation(self, mock_pool: MagicMock):
        """Test handling of unique constraint violations (e.g., duplicate username)."""
        import asyncpg
        
        app = create_app()
        
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Simulate unique constraint violation
        mock_conn.fetchrow.side_effect = asyncpg.UniqueViolationError(
            "duplicate key value violates unique constraint"
        )
        
        app.dependency_overrides[get_pool] = lambda: mock_pool
        
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(
                "/users",
                json={"user_id": TEST_USER_ID_STR, "username": "duplicate"},
            )
        
        # Should return 500 or could be customized to 409
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestUserEndpointsInputSanitization:
    """Tests for input validation and sanitization."""

    def test_create_user_strips_leading_trailing_whitespace_in_json(
        self, client: TestClient, mock_pool: MagicMock
    ):
        """Test that JSON parsing handles whitespace in string values."""
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_conn.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "  spaceduser  ",  # DB stores as-is
            "display_name": None,
            "avatar_url": None,
            "created_at": TEST_CREATED_AT,
        }
        
        response = client.post(
            "/users",
            json={
                "user_id": TEST_USER_ID_STR,
                "username": "  spaceduser  ",
            },
        )
        
        assert response.status_code == status.HTTP_200_OK
        # Model doesn't strip whitespace (by design)
        assert response.json()["username"] == "  spaceduser  "

    def test_create_user_with_very_long_avatar_url(
        self, client: TestClient, mock_pool: MagicMock
    ):
        """Test handling very long avatar URL."""
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        long_url = "https://example.com/" + "a" * 5000
        
        mock_conn.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "test",
            "display_name": None,
            "avatar_url": long_url,
            "created_at": TEST_CREATED_AT,
        }
        
        response = client.post(
            "/users",
            json={
                "user_id": TEST_USER_ID_STR,
                "username": "test",
                "avatar_url": long_url,
            },
        )
        
        assert response.status_code == status.HTTP_200_OK

    def test_create_user_with_special_json_characters(
        self, client: TestClient, mock_pool: MagicMock
    ):
        """Test handling special JSON characters in strings."""
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        special_name = 'user"with\\quotes\nand\tnewlines'
        
        mock_conn.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": special_name,
            "display_name": None,
            "avatar_url": None,
            "created_at": TEST_CREATED_AT,
        }
        
        response = client.post(
            "/users",
            json={
                "user_id": TEST_USER_ID_STR,
                "username": special_name,
            },
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["username"] == special_name

    def test_create_user_null_byte_in_username(
        self, client: TestClient, mock_pool: MagicMock
    ):
        """Test handling null bytes in username."""
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_conn.fetchrow.return_value = {
            "user_id": TEST_USER_ID,
            "username": "user\x00name",
            "display_name": None,
            "avatar_url": None,
            "created_at": TEST_CREATED_AT,
        }
        
        response = client.post(
            "/users",
            json={
                "user_id": TEST_USER_ID_STR,
                "username": "user\x00name",
            },
        )
        
        # Null bytes in JSON strings are technically valid but may cause issues
        # FastAPI/Pydantic should handle this
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    def test_get_user_with_url_encoded_uuid(
        self, client: TestClient, mock_pool: MagicMock
    ):
        """Test that URL-encoded UUID is handled."""
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
        
        # URL encode the dashes in the UUID
        encoded_uuid = TEST_USER_ID_STR.replace("-", "%2D")
        
        response = client.get(f"/users/{encoded_uuid}")
        
        # Should either work or return 422 for invalid format
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]


class TestUserEndpointsResponseHeaders:
    """Tests for response headers."""

    def test_create_user_response_headers(
        self, client: TestClient, mock_pool: MagicMock
    ):
        """Test response headers on successful user creation."""
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
        
        response = client.post(
            "/users",
            json={"user_id": TEST_USER_ID_STR, "username": "test"},
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "content-length" in response.headers
        assert response.headers.get("content-type") == "application/json"

    def test_get_user_not_found_response_headers(
        self, client: TestClient, mock_pool: MagicMock
    ):
        """Test response headers on 404."""
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        mock_conn.fetchrow.return_value = None
        
        response = client.get(f"/users/{TEST_USER_ID_STR}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.headers.get("content-type") == "application/json"
