from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from domain.flashcards.models import CardContent


# =============================================================================
# Due Cards
# =============================================================================

class DueCardOut(BaseModel):
    """A card that is due for review."""
    card_id: str
    deck_id: Optional[str] = None
    content: CardContent
    next_review_at: datetime
    repetition: int
    interval_days: int
    ef: float = 2.5  # Easiness factor


class StudySessionOut(BaseModel):
    """Response for deck study endpoint with counts."""
    cards: List[DueCardOut]
    due_count: int      # Total due cards in this deck (needing review)
    total_count: int    # Total cards in this deck
    mode: str = "review"  # "review" (due cards only) or "all" (normal session)


class UpcomingDay(BaseModel):
    """Cards due on a specific day."""
    date: str           # ISO date string (YYYY-MM-DD)
    count: int


class UpcomingOut(BaseModel):
    """Upcoming review schedule."""
    days: List[UpcomingDay]
    total_upcoming: int


# =============================================================================
# Reviews
# =============================================================================

class ReviewIn(BaseModel):
    """Input for submitting a review."""
    card_id: str = Field(..., description="UUID of the card")
    response: str = Field(..., description="'forgot' | 'meh' | 'got_it'")
    elapsed_ms: Optional[int] = Field(None, description="Time spent on card in ms")
    device_id: Optional[str] = Field(None, description="Device UUID for tracking")
    client_review_id: Optional[str] = Field(
        None, description="Optional idempotency key from client"
    )
    mode: str = Field(
        default="review",
        description="Session mode: 'review' (updates SM-2) or 'all' (practice only, no tracking)"
    )


class ReviewOut(BaseModel):
    """Output after submitting a review."""
    card_id: str
    repetition: int
    interval_days: int
    ef: float           # Updated easiness factor
    next_review_at: datetime
    quality: int        # Quality score used (1-5)
    # Gamification
    xp_earned: int = 0          # XP earned from this review
    streak: int = 0             # Current streak after this review
    streak_updated: bool = False  # True if streak was incremented this review


# =============================================================================
# Snooze
# =============================================================================

class SnoozeIn(BaseModel):
    """Input for snoozing a card."""
    card_id: str = Field(..., description="UUID of the card to snooze")
    hours: int = Field(default=24, ge=1, le=168, description="Hours to snooze (1-168)")


class SnoozeOut(BaseModel):
    """Output after snoozing a card."""
    card_id: str
    next_review_at: datetime


# =============================================================================
# Deck Stats
# =============================================================================

class DeckStatsOut(BaseModel):
    """Statistics for a deck."""
    deck_id: str
    total_cards: int
    due_now: int
    due_today: int
    mastered: int       # Cards with interval > 21 days
    learning: int       # Cards with 0 < interval <= 21 days
    new: int            # Cards never reviewed (repetition = 0)


__all__ = [
    "DueCardOut", 
    "StudySessionOut",
    "UpcomingDay",
    "UpcomingOut",
    "ReviewIn", 
    "ReviewOut",
    "SnoozeIn",
    "SnoozeOut",
    "DeckStatsOut",
]
