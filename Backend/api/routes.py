from __future__ import annotations

from typing import List, Optional
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, Header, HTTPException, status

from api.auth import CurrentUser, get_current_user
from db.pool import get_pool
from domain.cards.models import CardCreate, CardOut
from domain.cards.service import CardService
from domain.decks.models import DeckCreate, DeckOut
from domain.decks.service import DeckService
from domain.sr.models import DueCardOut, ReviewIn, ReviewOut
from domain.sr.service import ReviewService
from domain.users.models import ProfileCreate, ProfileCreateInternal, ProfileOut
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


@router.post("/users", response_model=ProfileOut)
async def upsert_profile(
    payload: ProfileCreate,
    user: CurrentUser = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    """
    Create or update the current user's profile.
    
    Requires: Authorization: Bearer <jwt>
    Body: { "username": "...", "display_name": "...", "avatar_url": "..." }
    
    The user_id is taken from the JWT - users can only create their own profile.
    """
    internal = ProfileCreateInternal(
        user_id=user.id,
        username=payload.username,
        display_name=payload.display_name,
        avatar_url=payload.avatar_url,
    )
    return await service.upsert_profile(internal)


@router.get("/users/{user_id}", response_model=ProfileOut)
async def get_profile(
    user_id: UUID, service: ProfileService = Depends(get_profile_service)
):
    profile = await service.get_profile(user_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return profile


@router.post("/decks", response_model=DeckOut)
async def create_deck(
    payload: DeckCreate,
    user_id: UUID = Header(..., alias="X-User-Id"),
    service: DeckService = Depends(get_deck_service),
):
    return await service.create_deck(owner_id=user_id, payload=payload)


@router.get("/decks", response_model=List[DeckOut])
async def list_decks(
    user_id: UUID = Header(..., alias="X-User-Id"),
    service: DeckService = Depends(get_deck_service),
):
    return await service.list_decks(owner_id=user_id)


@router.get("/decks/{deck_id}", response_model=DeckOut)
async def get_deck(
    deck_id: UUID,
    user_id: UUID = Header(..., alias="X-User-Id"),
    service: DeckService = Depends(get_deck_service),
):
    deck = await service.get_deck(owner_id=user_id, deck_id=deck_id)
    if deck is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found for user"
        )
    return deck


@router.post("/cards", response_model=CardOut)
async def create_card(
    payload: CardCreate,
    user_id: UUID = Header(..., alias="X-User-Id"),
    service: CardService = Depends(get_card_service),
):
    try:
        return await service.create_card(owner_id=user_id, payload=payload)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/cards", response_model=List[CardOut])
async def list_cards(
    deck_id: Optional[UUID] = None,
    user_id: UUID = Header(..., alias="X-User-Id"),
    service: CardService = Depends(get_card_service),
):
    return await service.list_cards(owner_id=user_id, deck_id=deck_id)


@router.get("/cards/{card_id}", response_model=CardOut)
async def get_card(
    card_id: UUID,
    user_id: UUID = Header(..., alias="X-User-Id"),
    service: CardService = Depends(get_card_service),
):
    card = await service.get_card(owner_id=user_id, card_id=card_id)
    if card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Card not found for user"
        )
    return card


@router.get("/due", response_model=List[DueCardOut])
async def fetch_due_cards(
    limit: int = 50,
    user_id: UUID = Header(..., alias="X-User-Id"),
    service: ReviewService = Depends(get_review_service),
):
    if limit <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit must be a positive integer",
        )
    return await service.fetch_due_cards(user_id=user_id, limit=limit)


@router.post("/review", response_model=ReviewOut)
async def submit_review(
    payload: ReviewIn,
    user_id: UUID = Header(..., alias="X-User-Id"),
    service: ReviewService = Depends(get_review_service),
):
    if payload.response.lower() not in VALID_RESPONSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"response must be one of: {', '.join(sorted(VALID_RESPONSES))}",
        )
    return await service.process_review(payload=payload, user_id=user_id)


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

