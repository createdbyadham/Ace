from __future__ import annotations

from typing import List, Optional
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import CurrentUser, get_current_user
from db.pool import get_pool
from domain.flashcards.models import CardCreate, CardOut, DeckCreate, DeckOut
from domain.flashcards.service import CardService, DeckService
from domain.sr.models import (
    DueCardOut, 
    StudySessionOut,
    UpcomingOut,
    ReviewIn, 
    ReviewOut,
    SnoozeIn,
    SnoozeOut,
    DeckStatsOut,
)
from domain.sr.service import ReviewService
from domain.users.models import ProfileUpdate, ProfileUpdateInternal, ProfileOut, GamificationOut
from domain.users.service import ProfileService

router = APIRouter()

VALID_RESPONSES = {"forgot", "meh", "got_it"}


def get_review_service(pool: asyncpg.Pool = Depends(get_pool)) -> ReviewService:
    return ReviewService(pool)


def get_profile_service(pool: asyncpg.Pool = Depends(get_pool)) -> ProfileService:
    return ProfileService(pool)


def get_deck_service(pool: asyncpg.Pool = Depends(get_pool)) -> DeckService:
    return DeckService(pool)


def get_card_service(pool: asyncpg.Pool = Depends(get_pool)) -> CardService:
    return CardService(pool)


@router.get("/users/me", response_model=ProfileOut)
async def get_my_profile(
    user: CurrentUser = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    """
    Get the current user's profile.
    
    Profile is auto-created on signup with default username (email_prefix_xxxx).
    """
    profile = await service.get_profile(user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Profile not found. This shouldn't happen - contact support."
        )
    return profile


@router.patch("/users/me", response_model=ProfileOut)
async def update_my_profile(
    payload: ProfileUpdate,
    user: CurrentUser = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    """
    Update the current user's profile.
    
    Requires: Authorization: Bearer <jwt>
    Body: { "username": "...", "display_name": "...", "avatar_url": "..." }
    
    All fields are optional - only provided fields will be updated.
    Profile is auto-created on signup, so this is always an update.
    """
    internal = ProfileUpdateInternal(
        user_id=user.id,
        username=payload.username,
        display_name=payload.display_name,
        avatar_url=payload.avatar_url,
    )
    try:
        return await service.update_profile(internal)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/users/me/gamification", response_model=GamificationOut)
async def get_my_gamification(
    user: CurrentUser = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    """
    Get detailed gamification stats for the current user.
    
    Returns: streak, xp, level, xp_to_next_level, xp_in_current_level, streak_multiplier.
    """
    stats = await service.get_gamification(user.id)
    if stats is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. This shouldn't happen - contact support."
        )
    return stats


@router.get("/users/{user_id}", response_model=ProfileOut)
async def get_profile(
    user_id: UUID, service: ProfileService = Depends(get_profile_service)
):
    """Get any user's public profile by ID."""
    profile = await service.get_profile(user_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return profile


@router.post("/decks", response_model=DeckOut)
async def create_deck(
    payload: DeckCreate,
    user: CurrentUser = Depends(get_current_user),
    service: DeckService = Depends(get_deck_service),
):
    """Create a new deck for the current user."""
    return await service.create_deck(owner_id=user.id, payload=payload)


@router.get("/decks", response_model=List[DeckOut])
async def list_decks(
    user: CurrentUser = Depends(get_current_user),
    service: DeckService = Depends(get_deck_service),
):
    """List all decks owned by the current user."""
    return await service.list_decks(owner_id=user.id)


@router.get("/decks/{deck_id}", response_model=DeckOut)
async def get_deck(
    deck_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    service: DeckService = Depends(get_deck_service),
):
    """Get a specific deck by ID (must be owned by current user)."""
    deck = await service.get_deck(owner_id=user.id, deck_id=deck_id)
    if deck is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found"
        )
    return deck


@router.post("/cards", response_model=CardOut)
async def create_card(
    payload: CardCreate,
    user: CurrentUser = Depends(get_current_user),
    service: CardService = Depends(get_card_service),
):
    """
    Create a new card for the current user.
    
    Optionally assign to a deck (must be owned by current user).
    """
    try:
        return await service.create_card(owner_id=user.id, payload=payload)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/cards", response_model=List[CardOut])
async def list_cards(
    deck_id: Optional[UUID] = None,
    user: CurrentUser = Depends(get_current_user),
    service: CardService = Depends(get_card_service),
):
    """List all cards owned by current user. Optionally filter by deck_id."""
    return await service.list_cards(owner_id=user.id, deck_id=deck_id)


@router.get("/cards/{card_id}", response_model=CardOut)
async def get_card(
    card_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    service: CardService = Depends(get_card_service),
):
    """Get a specific card by ID (must be owned by current user)."""
    card = await service.get_card(owner_id=user.id, card_id=card_id)
    if card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Card not found"
        )
    return card


@router.get("/due", response_model=List[DueCardOut])
async def fetch_due_cards(
    limit: int = 50,
    deck_id: Optional[UUID] = None,
    user: CurrentUser = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service),
):
    """
    Get cards due for review for the current user.
    
    Optionally filter by deck_id.
    """
    if limit <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit must be a positive integer",
        )
    return await service.fetch_due_cards(user_id=user.id, limit=limit, deck_id=deck_id)


@router.post("/review", response_model=ReviewOut)
async def submit_review(
    payload: ReviewIn,
    user: CurrentUser = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service),
):
    """
    Submit a review response for a card.
    
    Uses SM-2 algorithm to calculate next review date.
    Quality mapping: got_it=5, meh=3, forgot=1
    
    Args (in body):
        mode: 'review' (default) updates SM-2 state, 'all' is practice only (no tracking)
    """
    if payload.response.lower() not in VALID_RESPONSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"response must be one of: {', '.join(sorted(VALID_RESPONSES))}",
        )
    if payload.mode not in ("review", "all"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="mode must be 'review' or 'all'",
        )
    try:
        return await service.process_review(payload=payload, user_id=user.id)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


# =============================================================================
# Deck Study Endpoints (Step 3 of plan.md)
# =============================================================================

@router.get("/decks/{deck_id}/study", response_model=StudySessionOut)
async def get_deck_study_session(
    deck_id: UUID,
    limit: int = 20,
    mode: str = "review",
    user: CurrentUser = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service),
):
    """
    Get study session for a specific deck.
    
    Args:
        mode: Session type
            - "review" (default): Cards due for review (SM-2 based, weak cards)
            - "all": All cards in deck (normal session)
    
    Returns: Cards plus counts (due_count, total_count, mode).
    
    Frontend flow:
        1. Call GET /decks/{deck_id}/stats to check if due_now > 0
        2. If due_now > 0, show "You have X cards to review" prompt
        3. User clicks "Review" → mode=review (due cards only)
        4. User clicks "Practice All" → mode=all (all cards)
    """
    if limit <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit must be a positive integer",
        )
    if mode not in ("review", "all"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="mode must be 'review' or 'all'",
        )
    return await service.get_study_session(
        user_id=user.id, deck_id=deck_id, limit=limit, mode=mode
    )


@router.get("/decks/{deck_id}/stats", response_model=DeckStatsOut)
async def get_deck_stats(
    deck_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service),
):
    """
    Get statistics for a specific deck.
    
    Returns counts: total, due_now, due_today, mastered, learning, new.
    """
    return await service.get_deck_stats(user_id=user.id, deck_id=deck_id)


@router.get("/decks/{deck_id}/upcoming", response_model=UpcomingOut)
async def get_deck_upcoming(
    deck_id: UUID,
    days: int = 7,
    user: CurrentUser = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service),
):
    """
    Get upcoming review schedule for a deck.
    
    Returns count of cards due per day for the next N days.
    """
    if days <= 0 or days > 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="days must be between 1 and 30",
        )
    return await service.get_upcoming(user_id=user.id, deck_id=deck_id, days=days)


@router.post("/decks/{deck_id}/snooze", response_model=SnoozeOut)
async def snooze_card(
    deck_id: UUID,
    payload: SnoozeIn,
    user: CurrentUser = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service),
):
    """
    Snooze a card - postpone its next review.
    
    Default: 24 hours. Range: 1-168 hours (1 week max).
    """
    try:
        return await service.snooze_card(user_id=user.id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/upcoming", response_model=UpcomingOut)
async def get_global_upcoming(
    days: int = 7,
    user: CurrentUser = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service),
):
    """
    Get upcoming review schedule across all decks.
    
    Returns count of cards due per day for the next N days.
    """
    if days <= 0 or days > 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="days must be between 1 and 30",
        )
    return await service.get_upcoming(user_id=user.id, days=days)


@router.get("/health")
async def health(pool: asyncpg.Pool = Depends(get_pool)):
    try:
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1")
    except Exception as exc:  # pragma: no cover - log in real app
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DB connection failed: {exc}",
        ) from exc
    return {"ok": True}


__all__ = ["router"]

