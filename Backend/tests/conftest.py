"""Shared test fixtures for the test suite."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(__file__).rsplit("tests", 1)[0])

from main import create_app
from db.pool import get_pool


# Sample UUIDs for testing
TEST_USER_ID = UUID("12345678-1234-5678-1234-567812345678")
TEST_USER_ID_2 = UUID("87654321-4321-8765-4321-876543218765")


@pytest.fixture
def sample_user_id() -> UUID:
    """Return a consistent test user UUID."""
    return TEST_USER_ID


@pytest.fixture
def random_user_id() -> UUID:
    """Return a random user UUID."""
    return uuid4()


@pytest.fixture
def sample_profile_row() -> dict:
    """Return a sample profile database row."""
    return {
        "user_id": TEST_USER_ID,
        "username": "testuser",
        "display_name": "Test User",
        "avatar_url": "https://example.com/avatar.png",
        "created_at": datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
    }


@pytest.fixture
def sample_profile_row_minimal() -> dict:
    """Return a sample profile row with only required fields."""
    return {
        "user_id": TEST_USER_ID,
        "username": "minimaluser",
        "display_name": None,
        "avatar_url": None,
        "created_at": datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
    }


@pytest.fixture
def mock_pool() -> MagicMock:
    """Create a mock asyncpg pool."""
    pool = MagicMock()
    return pool


@pytest.fixture
def mock_connection() -> AsyncMock:
    """Create a mock asyncpg connection."""
    conn = AsyncMock()
    return conn


@pytest.fixture
def mock_pool_with_connection(mock_pool: MagicMock, mock_connection: AsyncMock) -> MagicMock:
    """Create a mock pool that yields a mock connection via context manager."""
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    return mock_pool


@pytest.fixture
def test_client(mock_pool: MagicMock) -> Generator[TestClient, None, None]:
    """Create a test client with mocked database pool."""
    app = create_app()
    
    # Override the get_pool dependency
    app.dependency_overrides[get_pool] = lambda: mock_pool
    
    with TestClient(app) as client:
        yield client
    
    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
def test_client_with_mock_conn(
    mock_pool_with_connection: MagicMock,
) -> Generator[TestClient, None, None]:
    """Create a test client with mocked database pool and connection."""
    app = create_app()
    
    app.dependency_overrides[get_pool] = lambda: mock_pool_with_connection
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


__all__ = [
    "TEST_USER_ID",
    "TEST_USER_ID_2",
    "sample_user_id",
    "random_user_id",
    "sample_profile_row",
    "sample_profile_row_minimal",
    "mock_pool",
    "mock_connection",
    "mock_pool_with_connection",
    "test_client",
    "test_client_with_mock_conn",
]

