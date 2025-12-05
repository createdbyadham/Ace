from __future__ import annotations

from typing import List, Optional
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import CurrentUser, get_current_user
from db.pool import get_pool
from domain.cards.models import CardCreate, CardOut
from domain.cards.service import CardService
from domain.decks.models import DeckCreate, DeckOut
from domain.decks.service import DeckService
from domain.sr.models import DueCardOut, ReviewIn, ReviewOut
from domain.sr.service import ReviewService
from domain.users.models import ProfileUpdate, ProfileUpdateInternal, ProfileOut
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
    user: CurrentUser = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service),
):
    """Get cards due for review for the current user."""
    if limit <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit must be a positive integer",
        )
    return await service.fetch_due_cards(user_id=user.id, limit=limit)


@router.post("/review", response_model=ReviewOut)
async def submit_review(
    payload: ReviewIn,
    user: CurrentUser = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service),
):
    """Submit a review response for a card."""
    if payload.response.lower() not in VALID_RESPONSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"response must be one of: {', '.join(sorted(VALID_RESPONSES))}",
        )
    return await service.process_review(payload=payload, user_id=user.id)


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

