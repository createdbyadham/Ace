"""Tests for SR (spaced repetition) API routes."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, str(__file__).rsplit("tests", 1)[0])

from main import create_app
from db.pool import get_pool
from api.auth import get_current_user, CurrentUser


# Sample test data
TEST_USER_ID = UUID("12345678-1234-5678-1234-567812345678")
TEST_DECK_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
TEST_CARD_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
TEST_NOW = datetime(2024, 6, 15, 10, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def mock_user() -> CurrentUser:
    """Create a mock current user."""
    return CurrentUser(id=TEST_USER_ID, email="test@example.com")


@pytest.fixture
def mock_pool() -> MagicMock:
    """Create a mock asyncpg pool."""
    pool = MagicMock()
    conn = AsyncMock()
    
    # Set up connection context manager
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    
    # transaction() is NOT async - it returns a context manager synchronously
    mock_transaction = MagicMock()
    mock_transaction.__aenter__ = AsyncMock(return_value=None)
    mock_transaction.__aexit__ = AsyncMock(return_value=None)
    conn.transaction = MagicMock(return_value=mock_transaction)
    
    pool._connection = conn
    return pool


@pytest.fixture
def test_client(mock_pool: MagicMock, mock_user: CurrentUser) -> TestClient:
    """Create a test client with mocked dependencies."""
    app = create_app()
    
    app.dependency_overrides[get_pool] = lambda: mock_pool
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


class TestDueCardsEndpoint:
    """Tests for GET /due endpoint."""

    def test_get_due_cards_success(self, test_client: TestClient, mock_pool: MagicMock):
        """Test successful fetch of due cards."""
        mock_pool._connection.fetch.return_value = [
            {
                "card_id": TEST_CARD_ID,
                "deck_id": TEST_DECK_ID,
                "content": {"front": "Question", "back": "Answer"},
                "next_review_at": TEST_NOW,
                "repetition": 1,
                "interval_days": 1,
                "ef": 2.5,
            }
        ]
        
        response = test_client.get("/due?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["card_id"] == str(TEST_CARD_ID)

    def test_get_due_cards_with_deck_filter(
        self, test_client: TestClient, mock_pool: MagicMock
    ):
        """Test fetching due cards filtered by deck."""
        mock_pool._connection.fetch.return_value = []
        
        response = test_client.get(f"/due?limit=10&deck_id={TEST_DECK_ID}")
        
        assert response.status_code == 200
        assert response.json() == []

    def test_get_due_cards_invalid_limit(self, test_client: TestClient):
        """Test that invalid limit returns 400."""
        response = test_client.get("/due?limit=0")
        
        assert response.status_code == 400
        assert "positive integer" in response.json()["detail"]

    def test_get_due_cards_negative_limit(self, test_client: TestClient):
        """Test that negative limit returns 400."""
        response = test_client.get("/due?limit=-5")
        
        assert response.status_code == 400


class TestReviewEndpoint:
    """Tests for POST /review endpoint."""

    def test_submit_review_success(self, test_client: TestClient, mock_pool: MagicMock):
        """Test successful review submission."""
        # No client_review_id means no idempotency DB call
        mock_pool._connection.fetchrow.side_effect = [
            None,  # No existing state (FOR UPDATE)
            {  # Created state via INSERT
                "state_id": uuid4(),
                "repetition": 0,
                "interval_days": 0,
                "ef": 2.5,
                "version": 1,
            },
            {"version": 2},  # Update result
        ]
        mock_pool._connection.execute.return_value = None
        
        response = test_client.post(
            "/review",
            json={
                "card_id": str(TEST_CARD_ID),
                "response": "got_it",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["card_id"] == str(TEST_CARD_ID)
        assert data["quality"] == 5
        assert data["repetition"] == 1

    def test_submit_review_with_mode_all(
        self, test_client: TestClient, mock_pool: MagicMock
    ):
        """Test review in practice mode (mode=all)."""
        response = test_client.post(
            "/review",
            json={
                "card_id": str(TEST_CARD_ID),
                "response": "got_it",
                "mode": "all",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["quality"] == 5
        # Should return default values, not DB values
        assert data["repetition"] == 0
        assert data["interval_days"] == 0

    def test_submit_review_invalid_response(self, test_client: TestClient):
        """Test that invalid response type returns 400."""
        response = test_client.post(
            "/review",
            json={
                "card_id": str(TEST_CARD_ID),
                "response": "invalid_response",
            },
        )
        
        assert response.status_code == 400
        assert "forgot" in response.json()["detail"]

    def test_submit_review_invalid_mode(self, test_client: TestClient):
        """Test that invalid mode returns 400."""
        response = test_client.post(
            "/review",
            json={
                "card_id": str(TEST_CARD_ID),
                "response": "got_it",
                "mode": "invalid_mode",
            },
        )
        
        assert response.status_code == 400
        assert "mode" in response.json()["detail"]

    def test_submit_review_forgot(self, test_client: TestClient, mock_pool: MagicMock):
        """Test review with 'forgot' response."""
        # No client_review_id means no idempotency DB call
        mock_pool._connection.fetchrow.side_effect = [
            {  # Existing state (FOR UPDATE)
                "state_id": uuid4(),
                "repetition": 5,
                "interval_days": 30,
                "ef": 2.6,
                "version": 3,
            },
            {"version": 4},
        ]
        mock_pool._connection.execute.return_value = None
        
        response = test_client.post(
            "/review",
            json={
                "card_id": str(TEST_CARD_ID),
                "response": "forgot",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["quality"] == 1
        assert data["repetition"] == 0  # Reset
        assert data["interval_days"] == 1

    def test_submit_review_meh(self, test_client: TestClient, mock_pool: MagicMock):
        """Test review with 'meh' response."""
        # No client_review_id means no idempotency DB call
        mock_pool._connection.fetchrow.side_effect = [
            {  # Existing state (FOR UPDATE)
                "state_id": uuid4(),
                "repetition": 1,
                "interval_days": 1,
                "ef": 2.5,
                "version": 2,
            },
            {"version": 3},
        ]
        mock_pool._connection.execute.return_value = None
        
        response = test_client.post(
            "/review",
            json={
                "card_id": str(TEST_CARD_ID),
                "response": "meh",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["quality"] == 3
        assert data["repetition"] == 2

    def test_submit_review_with_optional_fields(
        self, test_client: TestClient, mock_pool: MagicMock
    ):
        """Test review with optional elapsed_ms and device_id."""
        # No client_review_id means no idempotency DB call
        mock_pool._connection.fetchrow.side_effect = [
            None,  # No existing state (FOR UPDATE)
            {  # Created state via INSERT
                "state_id": uuid4(),
                "repetition": 0,
                "interval_days": 0,
                "ef": 2.5,
                "version": 1,
            },
            {"version": 2},
        ]
        mock_pool._connection.execute.return_value = None
        
        device_id = str(uuid4())
        response = test_client.post(
            "/review",
            json={
                "card_id": str(TEST_CARD_ID),
                "response": "got_it",
                "elapsed_ms": 3500,
                "device_id": device_id,
            },
        )
        
        assert response.status_code == 200


class TestStudySessionEndpoint:
    """Tests for GET /decks/{deck_id}/study endpoint."""

    def test_get_study_session_review_mode(
        self, test_client: TestClient, mock_pool: MagicMock
    ):
        """Test study session in review mode."""
        mock_pool._connection.fetch.return_value = [
            {
                "card_id": TEST_CARD_ID,
                "deck_id": TEST_DECK_ID,
                "content": {"front": "Q", "back": "A"},
                "next_review_at": TEST_NOW,
                "repetition": 1,
                "interval_days": 1,
                "ef": 2.5,
            }
        ]
        mock_pool._connection.fetchrow.return_value = {
            "due_count": 5,
            "total_count": 20,
        }
        
        response = test_client.get(f"/decks/{TEST_DECK_ID}/study?mode=review")
        
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "review"
        assert data["due_count"] == 5
        assert data["total_count"] == 20
        assert len(data["cards"]) == 1

    def test_get_study_session_all_mode(
        self, test_client: TestClient, mock_pool: MagicMock
    ):
        """Test study session in all mode."""
        mock_pool._connection.fetch.return_value = [
            {
                "card_id": TEST_CARD_ID,
                "deck_id": TEST_DECK_ID,
                "content": {"front": "Q1", "back": "A1"},
                "next_review_at": TEST_NOW + timedelta(days=30),
                "repetition": 5,
                "interval_days": 30,
                "ef": 2.8,
            },
            {
                "card_id": uuid4(),
                "deck_id": TEST_DECK_ID,
                "content": {"front": "Q2", "back": "A2"},
                "next_review_at": TEST_NOW,
                "repetition": 1,
                "interval_days": 1,
                "ef": 2.5,
            },
        ]
        mock_pool._connection.fetchrow.return_value = {
            "due_count": 1,
            "total_count": 2,
        }
        
        response = test_client.get(f"/decks/{TEST_DECK_ID}/study?mode=all")
        
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "all"
        assert len(data["cards"]) == 2

    def test_get_study_session_default_mode(
        self, test_client: TestClient, mock_pool: MagicMock
    ):
        """Test that default mode is 'review'."""
        mock_pool._connection.fetch.return_value = []
        mock_pool._connection.fetchrow.return_value = {
            "due_count": 0,
            "total_count": 0,
        }
        
        response = test_client.get(f"/decks/{TEST_DECK_ID}/study")
        
        assert response.status_code == 200
        assert response.json()["mode"] == "review"

    def test_get_study_session_invalid_mode(self, test_client: TestClient):
        """Test that invalid mode returns 400."""
        response = test_client.get(f"/decks/{TEST_DECK_ID}/study?mode=invalid")
        
        assert response.status_code == 400
        assert "mode" in response.json()["detail"]

    def test_get_study_session_invalid_limit(self, test_client: TestClient):
        """Test that invalid limit returns 400."""
        response = test_client.get(f"/decks/{TEST_DECK_ID}/study?limit=0")
        
        assert response.status_code == 400

    def test_get_study_session_with_custom_limit(
        self, test_client: TestClient, mock_pool: MagicMock
    ):
        """Test study session with custom limit."""
        mock_pool._connection.fetch.return_value = []
        mock_pool._connection.fetchrow.return_value = {
            "due_count": 0,
            "total_count": 0,
        }
        
        response = test_client.get(f"/decks/{TEST_DECK_ID}/study?limit=50")
        
        assert response.status_code == 200


class TestDeckStatsEndpoint:
    """Tests for GET /decks/{deck_id}/stats endpoint."""

    def test_get_deck_stats_success(
        self, test_client: TestClient, mock_pool: MagicMock
    ):
        """Test successful stats retrieval."""
        mock_pool._connection.fetchrow.return_value = {
            "total_cards": 100,
            "due_now": 15,
            "due_today": 20,
            "mastered": 50,
            "learning": 30,
            "new": 20,
        }
        
        response = test_client.get(f"/decks/{TEST_DECK_ID}/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["deck_id"] == str(TEST_DECK_ID)
        assert data["total_cards"] == 100
        assert data["due_now"] == 15
        assert data["mastered"] == 50
        assert data["learning"] == 30
        assert data["new"] == 20


class TestSnoozeEndpoint:
    """Tests for POST /decks/{deck_id}/snooze endpoint."""

    def test_snooze_card_success(self, test_client: TestClient, mock_pool: MagicMock):
        """Test successful card snooze."""
        future_time = TEST_NOW + timedelta(hours=24)
        mock_pool._connection.fetchrow.return_value = {
            "card_id": TEST_CARD_ID,
            "next_review_at": future_time,
        }
        
        response = test_client.post(
            f"/decks/{TEST_DECK_ID}/snooze",
            json={
                "card_id": str(TEST_CARD_ID),
                "hours": 24,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["card_id"] == str(TEST_CARD_ID)

    def test_snooze_card_not_found(self, test_client: TestClient, mock_pool: MagicMock):
        """Test snoozing non-existent card."""
        mock_pool._connection.fetchrow.return_value = None
        
        response = test_client.post(
            f"/decks/{TEST_DECK_ID}/snooze",
            json={
                "card_id": str(TEST_CARD_ID),
                "hours": 24,
            },
        )
        
        assert response.status_code == 404
        assert "No state found" in response.json()["detail"]

    def test_snooze_card_custom_hours(
        self, test_client: TestClient, mock_pool: MagicMock
    ):
        """Test snoozing with custom hours."""
        mock_pool._connection.fetchrow.return_value = {
            "card_id": TEST_CARD_ID,
            "next_review_at": TEST_NOW + timedelta(hours=48),
        }
        
        response = test_client.post(
            f"/decks/{TEST_DECK_ID}/snooze",
            json={
                "card_id": str(TEST_CARD_ID),
                "hours": 48,
            },
        )
        
        assert response.status_code == 200


class TestUpcomingEndpoints:
    """Tests for upcoming review endpoints."""

    def test_get_deck_upcoming(self, test_client: TestClient, mock_pool: MagicMock):
        """Test deck-specific upcoming schedule."""
        from datetime import date
        
        mock_pool._connection.fetch.return_value = [
            {"review_date": date(2024, 6, 16), "count": 5},
            {"review_date": date(2024, 6, 17), "count": 3},
        ]
        
        response = test_client.get(f"/decks/{TEST_DECK_ID}/upcoming?days=7")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["days"]) == 2
        assert data["total_upcoming"] == 8

    def test_get_global_upcoming(self, test_client: TestClient, mock_pool: MagicMock):
        """Test global upcoming schedule."""
        from datetime import date
        
        mock_pool._connection.fetch.return_value = [
            {"review_date": date(2024, 6, 16), "count": 10},
        ]
        
        response = test_client.get("/upcoming?days=7")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_upcoming"] == 10

    def test_upcoming_invalid_days(self, test_client: TestClient):
        """Test that invalid days parameter returns 400."""
        response = test_client.get("/upcoming?days=0")
        assert response.status_code == 400
        
        response = test_client.get("/upcoming?days=31")
        assert response.status_code == 400


class TestResponseValidation:
    """Tests for request/response validation."""

    def test_review_missing_card_id(self, test_client: TestClient):
        """Test that missing card_id returns 422."""
        response = test_client.post(
            "/review",
            json={"response": "got_it"},
        )
        
        assert response.status_code == 422

    def test_review_missing_response(self, test_client: TestClient):
        """Test that missing response returns 422."""
        response = test_client.post(
            "/review",
            json={"card_id": str(TEST_CARD_ID)},
        )
        
        assert response.status_code == 422

    def test_snooze_invalid_hours_range(self, test_client: TestClient):
        """Test snooze hours validation (1-168)."""
        # Too low
        response = test_client.post(
            f"/decks/{TEST_DECK_ID}/snooze",
            json={"card_id": str(TEST_CARD_ID), "hours": 0},
        )
        assert response.status_code == 422
        
        # Too high
        response = test_client.post(
            f"/decks/{TEST_DECK_ID}/snooze",
            json={"card_id": str(TEST_CARD_ID), "hours": 200},
        )
        assert response.status_code == 422

    def test_review_case_insensitive_response(
        self, test_client: TestClient, mock_pool: MagicMock
    ):
        """Test that response values are case-insensitive."""
        # No client_review_id means no idempotency DB call
        mock_pool._connection.fetchrow.side_effect = [
            None,  # No existing state (FOR UPDATE)
            {"state_id": uuid4(), "repetition": 0, "interval_days": 0, "ef": 2.5, "version": 1},  # Created
            {"version": 2},
        ]
        mock_pool._connection.execute.return_value = None
        
        response = test_client.post(
            "/review",
            json={"card_id": str(TEST_CARD_ID), "response": "GOT_IT"},
        )
        
        assert response.status_code == 200
        assert response.json()["quality"] == 5

