"""Tests for ReviewService (SR domain service layer)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

import sys
sys.path.insert(0, str(__file__).rsplit("tests", 1)[0])

from domain.sr.models import (
    DueCardOut,
    StudySessionOut,
    ReviewIn,
    ReviewOut,
    SnoozeIn,
    SnoozeOut,
    DeckStatsOut,
    UpcomingOut,
)
from domain.sr.service import ReviewService


# Sample test data
TEST_USER_ID = UUID("12345678-1234-5678-1234-567812345678")
TEST_DECK_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
TEST_CARD_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
TEST_NOW = datetime(2024, 6, 15, 10, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def mock_pool() -> MagicMock:
    """Create a mock asyncpg pool."""
    return MagicMock()


@pytest.fixture
def mock_connection() -> AsyncMock:
    """Create a mock asyncpg connection."""
    conn = AsyncMock()
    # transaction() is NOT async - it returns a context manager synchronously
    # So we need to make it a regular Mock, not AsyncMock
    mock_transaction = MagicMock()
    mock_transaction.__aenter__ = AsyncMock(return_value=None)
    mock_transaction.__aexit__ = AsyncMock(return_value=None)
    # Use a regular function, not async
    conn.transaction = MagicMock(return_value=mock_transaction)
    return conn


@pytest.fixture
def service_with_mock(mock_pool: MagicMock, mock_connection: AsyncMock) -> ReviewService:
    """Create ReviewService with mocked pool and connection."""
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_connection)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    return ReviewService(mock_pool)


class TestReviewServiceInit:
    """Tests for ReviewService initialization."""

    def test_init_stores_pool(self, mock_pool: MagicMock):
        """Test that ReviewService stores the pool reference."""
        service = ReviewService(mock_pool)
        assert service._pool is mock_pool


class TestFetchDueCards:
    """Tests for ReviewService.fetch_due_cards method."""

    @pytest.mark.asyncio
    async def test_fetch_due_cards_global(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test fetching due cards across all decks."""
        mock_connection.fetch.return_value = [
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
        
        result = await service_with_mock.fetch_due_cards(
            user_id=TEST_USER_ID,
            limit=10,
        )
        
        assert len(result) == 1
        assert isinstance(result[0], DueCardOut)
        assert result[0].card_id == str(TEST_CARD_ID)

    @pytest.mark.asyncio
    async def test_fetch_due_cards_by_deck(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test fetching due cards for a specific deck."""
        mock_connection.fetch.return_value = [
            {
                "card_id": TEST_CARD_ID,
                "deck_id": TEST_DECK_ID,
                "content": {"front": "Q", "back": "A"},
                "next_review_at": TEST_NOW,
                "repetition": 2,
                "interval_days": 6,
                "ef": 2.6,
            }
        ]
        
        result = await service_with_mock.fetch_due_cards(
            user_id=TEST_USER_ID,
            limit=10,
            deck_id=TEST_DECK_ID,
        )
        
        assert len(result) == 1
        assert result[0].deck_id == str(TEST_DECK_ID)

    @pytest.mark.asyncio
    async def test_fetch_due_cards_includes_new_cards(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test that new cards (no state) are included."""
        mock_connection.fetch.return_value = [
            {
                "card_id": TEST_CARD_ID,
                "deck_id": TEST_DECK_ID,
                "content": {"front": "New Q", "back": "New A"},
                "next_review_at": None,  # No state yet
                "repetition": None,
                "interval_days": None,
                "ef": None,
            }
        ]
        
        result = await service_with_mock.fetch_due_cards(
            user_id=TEST_USER_ID,
            limit=10,
        )
        
        assert len(result) == 1
        # Should have default values for new cards
        assert result[0].repetition == 0
        assert result[0].interval_days == 0
        assert result[0].ef == 2.5

    @pytest.mark.asyncio
    async def test_fetch_due_cards_empty_result(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test fetching when no cards are due."""
        mock_connection.fetch.return_value = []
        
        result = await service_with_mock.fetch_due_cards(
            user_id=TEST_USER_ID,
            limit=10,
        )
        
        assert result == []


class TestGetStudySession:
    """Tests for ReviewService.get_study_session method."""

    @pytest.mark.asyncio
    async def test_study_session_review_mode(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test study session in review mode (default)."""
        # Mock due cards query
        mock_connection.fetch.return_value = [
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
        # Mock counts query
        mock_connection.fetchrow.return_value = {
            "due_count": 5,
            "total_count": 20,
        }
        
        result = await service_with_mock.get_study_session(
            user_id=TEST_USER_ID,
            deck_id=TEST_DECK_ID,
            mode="review",
        )
        
        assert isinstance(result, StudySessionOut)
        assert len(result.cards) == 1
        assert result.due_count == 5
        assert result.total_count == 20
        assert result.mode == "review"

    @pytest.mark.asyncio
    async def test_study_session_all_mode(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test study session in all mode (practice)."""
        # Mock all cards query (different query path)
        mock_connection.fetch.return_value = [
            {
                "card_id": TEST_CARD_ID,
                "deck_id": TEST_DECK_ID,
                "content": {"front": "Q1", "back": "A1"},
                "next_review_at": TEST_NOW + timedelta(days=30),  # Not due
                "repetition": 5,
                "interval_days": 30,
                "ef": 2.8,
            },
            {
                "card_id": uuid4(),
                "deck_id": TEST_DECK_ID,
                "content": {"front": "Q2", "back": "A2"},
                "next_review_at": TEST_NOW,  # Due
                "repetition": 1,
                "interval_days": 1,
                "ef": 2.5,
            },
        ]
        mock_connection.fetchrow.return_value = {
            "due_count": 1,
            "total_count": 2,
        }
        
        result = await service_with_mock.get_study_session(
            user_id=TEST_USER_ID,
            deck_id=TEST_DECK_ID,
            mode="all",
        )
        
        assert result.mode == "all"
        assert len(result.cards) == 2  # All cards, not just due
        assert result.total_count == 2

    @pytest.mark.asyncio
    async def test_study_session_default_mode_is_review(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test that default mode is 'review'."""
        mock_connection.fetch.return_value = []
        mock_connection.fetchrow.return_value = {"due_count": 0, "total_count": 0}
        
        result = await service_with_mock.get_study_session(
            user_id=TEST_USER_ID,
            deck_id=TEST_DECK_ID,
        )
        
        assert result.mode == "review"


class TestProcessReview:
    """Tests for ReviewService.process_review method."""

    @pytest.mark.asyncio
    async def test_process_review_creates_state_if_missing(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test that state is created for new cards."""
        # No client_review_id means idempotency check returns early (no DB call)
        # Then: FOR UPDATE returns None, INSERT returns state, UPDATE confirms
        mock_connection.fetchrow.side_effect = [
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
        mock_connection.execute.return_value = None
        
        payload = ReviewIn(
            card_id=str(TEST_CARD_ID),
            response="got_it",
            mode="review",
        )
        
        result = await service_with_mock.process_review(
            payload=payload,
            user_id=TEST_USER_ID,
        )
        
        assert isinstance(result, ReviewOut)
        assert result.repetition == 1  # First successful review
        assert result.interval_days == 1

    @pytest.mark.asyncio
    async def test_process_review_updates_existing_state(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test updating existing state with review."""
        # No client_review_id means no idempotency DB call
        mock_connection.fetchrow.side_effect = [
            {  # Existing state (FOR UPDATE)
                "state_id": uuid4(),
                "repetition": 2,
                "interval_days": 6,
                "ef": 2.5,
                "version": 3,
            },
            {"version": 4},  # Update result
        ]
        mock_connection.execute.return_value = None
        
        payload = ReviewIn(
            card_id=str(TEST_CARD_ID),
            response="got_it",
            mode="review",
        )
        
        result = await service_with_mock.process_review(
            payload=payload,
            user_id=TEST_USER_ID,
        )
        
        assert result.repetition == 3
        assert result.interval_days > 6  # Should grow

    @pytest.mark.asyncio
    async def test_process_review_forgot_resets_state(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test that 'forgot' response resets state."""
        # No client_review_id means no idempotency DB call
        mock_connection.fetchrow.side_effect = [
            {  # Existing state with high values (FOR UPDATE)
                "state_id": uuid4(),
                "repetition": 10,
                "interval_days": 100,
                "ef": 2.8,
                "version": 5,
            },
            {"version": 6},  # Update result
        ]
        mock_connection.execute.return_value = None
        
        payload = ReviewIn(
            card_id=str(TEST_CARD_ID),
            response="forgot",
            mode="review",
        )
        
        result = await service_with_mock.process_review(
            payload=payload,
            user_id=TEST_USER_ID,
        )
        
        assert result.repetition == 0
        assert result.interval_days == 1
        assert result.quality == 1

    @pytest.mark.asyncio
    async def test_process_review_practice_mode_skips_db(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test that mode='all' (practice) doesn't update database."""
        payload = ReviewIn(
            card_id=str(TEST_CARD_ID),
            response="got_it",
            mode="all",  # Practice mode
        )
        
        result = await service_with_mock.process_review(
            payload=payload,
            user_id=TEST_USER_ID,
        )
        
        # Should return result without hitting database
        assert isinstance(result, ReviewOut)
        assert result.quality == 5
        # No database calls should be made
        mock_connection.fetchrow.assert_not_called()
        mock_connection.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_review_idempotency(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test idempotency with client_review_id."""
        mock_connection.fetchrow.return_value = {
            "quality": 5,
            "repetition": 3,
            "interval_days": 15,
            "ef": 2.6,
            "next_review_at": TEST_NOW + timedelta(days=15),
        }
        
        payload = ReviewIn(
            card_id=str(TEST_CARD_ID),
            response="got_it",
            client_review_id="unique-client-id-123",
            mode="review",
        )
        
        result = await service_with_mock.process_review(
            payload=payload,
            user_id=TEST_USER_ID,
        )
        
        # Should return cached result
        assert result.repetition == 3
        assert result.interval_days == 15

    @pytest.mark.asyncio
    async def test_process_review_concurrent_update_conflict(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test handling of concurrent update conflict."""
        # No client_review_id means no idempotency DB call
        mock_connection.fetchrow.side_effect = [
            {  # Existing state (FOR UPDATE)
                "state_id": uuid4(),
                "repetition": 2,
                "interval_days": 6,
                "ef": 2.5,
                "version": 3,
            },
            None,  # Update failed (version mismatch)
        ]
        mock_connection.execute.return_value = None
        
        payload = ReviewIn(
            card_id=str(TEST_CARD_ID),
            response="got_it",
            mode="review",
        )
        
        with pytest.raises(RuntimeError) as exc_info:
            await service_with_mock.process_review(
                payload=payload,
                user_id=TEST_USER_ID,
            )
        
        assert "Concurrent update conflict" in str(exc_info.value)


class TestSnoozeCard:
    """Tests for ReviewService.snooze_card method."""

    @pytest.mark.asyncio
    async def test_snooze_card_success(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test successfully snoozing a card."""
        future_time = TEST_NOW + timedelta(hours=24)
        mock_connection.fetchrow.return_value = {
            "card_id": TEST_CARD_ID,
            "next_review_at": future_time,
        }
        
        payload = SnoozeIn(card_id=str(TEST_CARD_ID), hours=24)
        
        result = await service_with_mock.snooze_card(
            user_id=TEST_USER_ID,
            payload=payload,
        )
        
        assert isinstance(result, SnoozeOut)
        assert result.card_id == str(TEST_CARD_ID)

    @pytest.mark.asyncio
    async def test_snooze_card_not_found(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test snoozing a card that doesn't exist."""
        mock_connection.fetchrow.return_value = None
        
        payload = SnoozeIn(card_id=str(TEST_CARD_ID), hours=24)
        
        with pytest.raises(ValueError) as exc_info:
            await service_with_mock.snooze_card(
                user_id=TEST_USER_ID,
                payload=payload,
            )
        
        assert "No state found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_snooze_card_custom_hours(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test snoozing with custom hours."""
        mock_connection.fetchrow.return_value = {
            "card_id": TEST_CARD_ID,
            "next_review_at": TEST_NOW + timedelta(hours=48),
        }
        
        payload = SnoozeIn(card_id=str(TEST_CARD_ID), hours=48)
        
        result = await service_with_mock.snooze_card(
            user_id=TEST_USER_ID,
            payload=payload,
        )
        
        assert result is not None


class TestGetDeckStats:
    """Tests for ReviewService.get_deck_stats method."""

    @pytest.mark.asyncio
    async def test_get_deck_stats(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test getting deck statistics."""
        mock_connection.fetchrow.return_value = {
            "total_cards": 100,
            "due_now": 15,
            "due_today": 20,
            "mastered": 50,
            "learning": 30,
            "new": 20,
        }
        
        result = await service_with_mock.get_deck_stats(
            user_id=TEST_USER_ID,
            deck_id=TEST_DECK_ID,
        )
        
        assert isinstance(result, DeckStatsOut)
        assert result.total_cards == 100
        assert result.due_now == 15
        assert result.due_today == 20
        assert result.mastered == 50
        assert result.learning == 30
        assert result.new == 20

    @pytest.mark.asyncio
    async def test_get_deck_stats_empty_deck(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test stats for an empty deck."""
        mock_connection.fetchrow.return_value = {
            "total_cards": 0,
            "due_now": 0,
            "due_today": 0,
            "mastered": 0,
            "learning": 0,
            "new": 0,
        }
        
        result = await service_with_mock.get_deck_stats(
            user_id=TEST_USER_ID,
            deck_id=TEST_DECK_ID,
        )
        
        assert result.total_cards == 0
        assert result.due_now == 0


class TestGetUpcoming:
    """Tests for ReviewService.get_upcoming method."""

    @pytest.mark.asyncio
    async def test_get_upcoming_global(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test getting upcoming reviews globally."""
        from datetime import date
        
        mock_connection.fetch.return_value = [
            {"review_date": date(2024, 6, 16), "count": 5},
            {"review_date": date(2024, 6, 17), "count": 3},
            {"review_date": date(2024, 6, 18), "count": 8},
        ]
        
        result = await service_with_mock.get_upcoming(
            user_id=TEST_USER_ID,
            days=7,
        )
        
        assert isinstance(result, UpcomingOut)
        assert len(result.days) == 3
        assert result.total_upcoming == 16

    @pytest.mark.asyncio
    async def test_get_upcoming_by_deck(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test getting upcoming reviews for a specific deck."""
        from datetime import date
        
        mock_connection.fetch.return_value = [
            {"review_date": date(2024, 6, 16), "count": 2},
        ]
        
        result = await service_with_mock.get_upcoming(
            user_id=TEST_USER_ID,
            deck_id=TEST_DECK_ID,
            days=7,
        )
        
        assert len(result.days) == 1
        assert result.total_upcoming == 2

    @pytest.mark.asyncio
    async def test_get_upcoming_empty(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test getting upcoming when no cards are scheduled."""
        mock_connection.fetch.return_value = []
        
        result = await service_with_mock.get_upcoming(
            user_id=TEST_USER_ID,
            days=7,
        )
        
        assert result.days == []
        assert result.total_upcoming == 0


class TestHandlePracticeReview:
    """Tests for practice-only review handling."""

    @pytest.mark.asyncio
    async def test_practice_review_returns_correct_quality(
        self, service_with_mock: ReviewService
    ):
        """Test practice review returns correct quality mapping."""
        for response, expected_quality in [("got_it", 5), ("meh", 3), ("forgot", 1)]:
            payload = ReviewIn(
                card_id=str(TEST_CARD_ID),
                response=response,
                mode="all",
            )
            
            result = await service_with_mock.process_review(
                payload=payload,
                user_id=TEST_USER_ID,
            )
            
            assert result.quality == expected_quality

    @pytest.mark.asyncio
    async def test_practice_review_returns_default_values(
        self, service_with_mock: ReviewService
    ):
        """Test practice review returns default values."""
        payload = ReviewIn(
            card_id=str(TEST_CARD_ID),
            response="got_it",
            mode="all",
        )
        
        result = await service_with_mock.process_review(
            payload=payload,
            user_id=TEST_USER_ID,
        )
        
        assert result.repetition == 0
        assert result.interval_days == 0
        assert result.ef == 2.5


class TestEdgeCases:
    """Edge case tests for ReviewService."""

    @pytest.mark.asyncio
    async def test_fetch_due_cards_with_null_values(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test handling of NULL values in database response."""
        mock_connection.fetch.return_value = [
            {
                "card_id": TEST_CARD_ID,
                "deck_id": None,  # Card not in a deck
                "content": {"front": "Q", "back": "A"},
                "next_review_at": None,
                "repetition": None,
                "interval_days": None,
                "ef": None,
            }
        ]
        
        result = await service_with_mock.fetch_due_cards(
            user_id=TEST_USER_ID,
            limit=10,
        )
        
        assert len(result) == 1
        assert result[0].deck_id is None
        assert result[0].repetition == 0
        assert result[0].interval_days == 0
        assert result[0].ef == 2.5

    @pytest.mark.asyncio
    async def test_process_review_with_elapsed_ms(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test review with elapsed time tracking."""
        # No client_review_id means no idempotency DB call
        mock_connection.fetchrow.side_effect = [
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
        mock_connection.execute.return_value = None
        
        payload = ReviewIn(
            card_id=str(TEST_CARD_ID),
            response="got_it",
            elapsed_ms=5000,
            device_id=str(uuid4()),
            mode="review",
        )
        
        result = await service_with_mock.process_review(
            payload=payload,
            user_id=TEST_USER_ID,
        )
        
        assert result is not None
        # Verify execute was called for review log
        mock_connection.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_deck_stats_handles_null_counts(
        self, service_with_mock: ReviewService, mock_connection: AsyncMock
    ):
        """Test deck stats handles NULL values gracefully."""
        mock_connection.fetchrow.return_value = {
            "total_cards": None,
            "due_now": None,
            "due_today": None,
            "mastered": None,
            "learning": None,
            "new": None,
        }
        
        result = await service_with_mock.get_deck_stats(
            user_id=TEST_USER_ID,
            deck_id=TEST_DECK_ID,
        )
        
        assert result.total_cards == 0
        assert result.due_now == 0

