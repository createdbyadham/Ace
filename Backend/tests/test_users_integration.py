"""Integration tests for users endpoints.

These tests require a real database connection and should be run separately
from unit tests. Mark them with pytest.mark.integration.

To run: pytest tests/test_users_integration.py -v
Requires: DATABASE_URL environment variable set to a test database
"""
from __future__ import annotations

import os
from uuid import uuid4

import pytest

import sys
sys.path.insert(0, str(__file__).rsplit("tests", 1)[0])

# Skip all tests in this module if no database is configured
pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set - skipping integration tests",
)


@pytest.fixture
async def real_pool():
    """Create a real database pool for integration tests."""
    import asyncpg
    
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL not configured")
    
    pool = await asyncpg.create_pool(database_url, min_size=1, max_size=5)
    yield pool
    await pool.close()


@pytest.fixture
def integration_client(real_pool):
    """Create a test client with real database pool."""
    from fastapi.testclient import TestClient
    
    from main import create_app
    from db.pool import get_pool
    
    app = create_app()
    app.dependency_overrides[get_pool] = lambda: real_pool
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


class TestUsersIntegration:
    """Integration tests for user endpoints with real database."""

    @pytest.mark.asyncio
    async def test_create_and_get_user_roundtrip(self, integration_client):
        """Test creating a user and then retrieving it."""
        user_id = str(uuid4())
        
        # Create user
        create_response = integration_client.post(
            "/users",
            json={
                "user_id": user_id,
                "username": "integration_test_user",
                "display_name": "Integration Test",
                "avatar_url": "https://example.com/integration.png",
            },
        )
        
        assert create_response.status_code == 200
        created_data = create_response.json()
        assert created_data["user_id"] == user_id
        assert created_data["username"] == "integration_test_user"
        
        # Get user
        get_response = integration_client.get(f"/users/{user_id}")
        
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["user_id"] == user_id
        assert get_data["username"] == "integration_test_user"
        assert get_data["display_name"] == "Integration Test"

    @pytest.mark.asyncio
    async def test_upsert_updates_existing_user(self, integration_client):
        """Test that upserting an existing user updates their data."""
        user_id = str(uuid4())
        
        # Create initial user
        integration_client.post(
            "/users",
            json={
                "user_id": user_id,
                "username": "original_name",
                "display_name": "Original",
            },
        )
        
        # Update via upsert
        update_response = integration_client.post(
            "/users",
            json={
                "user_id": user_id,
                "username": "updated_name",
                "display_name": "Updated Display",
                "avatar_url": "https://new-avatar.png",
            },
        )
        
        assert update_response.status_code == 200
        updated_data = update_response.json()
        assert updated_data["username"] == "updated_name"
        assert updated_data["display_name"] == "Updated Display"
        assert updated_data["avatar_url"] == "https://new-avatar.png"

    @pytest.mark.asyncio
    async def test_get_nonexistent_user_returns_404(self, integration_client):
        """Test that getting a non-existent user returns 404."""
        nonexistent_id = str(uuid4())
        
        response = integration_client.get(f"/users/{nonexistent_id}")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    @pytest.mark.asyncio
    async def test_create_user_with_minimal_data(self, integration_client):
        """Test creating a user with only required fields."""
        user_id = str(uuid4())
        
        response = integration_client.post(
            "/users",
            json={
                "user_id": user_id,
                "username": "minimal_user",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_id
        assert data["username"] == "minimal_user"
        assert data["display_name"] is None
        assert data["avatar_url"] is None

    @pytest.mark.asyncio
    async def test_create_user_with_unicode(self, integration_client):
        """Test creating a user with unicode characters."""
        user_id = str(uuid4())
        
        response = integration_client.post(
            "/users",
            json={
                "user_id": user_id,
                "username": "ユーザー",
                "display_name": "日本語テスト 🎉",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "ユーザー"
        assert data["display_name"] == "日本語テスト 🎉"


class TestUsersConcurrency:
    """Tests for concurrent access patterns."""

    @pytest.mark.asyncio
    async def test_concurrent_upserts_same_user(self, integration_client):
        """Test that concurrent upserts for the same user don't cause issues."""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        user_id = str(uuid4())
        
        def make_upsert(i: int):
            return integration_client.post(
                "/users",
                json={
                    "user_id": user_id,
                    "username": f"concurrent_user_{i}",
                    "display_name": f"Concurrent Test {i}",
                },
            )
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_upsert, i) for i in range(5)]
            results = [f.result() for f in futures]
        
        # All requests should succeed
        for result in results:
            assert result.status_code == 200
        
        # Final state should be consistent
        get_response = integration_client.get(f"/users/{user_id}")
        assert get_response.status_code == 200

    @pytest.mark.asyncio
    async def test_concurrent_creates_different_users(self, integration_client):
        """Test concurrent creation of different users."""
        from concurrent.futures import ThreadPoolExecutor
        
        def create_user():
            user_id = str(uuid4())
            return integration_client.post(
                "/users",
                json={
                    "user_id": user_id,
                    "username": f"user_{user_id[:8]}",
                },
            )
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_user) for _ in range(10)]
            results = [f.result() for f in futures]
        
        # All creations should succeed
        for result in results:
            assert result.status_code == 200


class TestUsersCleanup:
    """Cleanup utilities for integration tests.
    
    Note: In a real scenario, you'd want to clean up test data.
    This could be done via database transactions that get rolled back,
    or explicit cleanup queries.
    """

    @pytest.fixture(autouse=True)
    async def cleanup_test_users(self, real_pool):
        """Clean up any test users after each test."""
        yield
        # In a real implementation, you might want to delete test users here
        # async with real_pool.acquire() as conn:
        #     await conn.execute(
        #         "DELETE FROM app.profiles WHERE username LIKE 'integration_test%'"
        #     )
        pass

