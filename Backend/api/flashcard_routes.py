"""
API routes for flashcards (decks and cards CRUD).

Endpoints:
- POST /decks - Create a deck
- GET /decks - List all decks
- GET /decks/{deck_id} - Get a deck
- PATCH /decks/{deck_id} - Update a deck
- DELETE /decks/{deck_id} - Delete a deck
- POST /cards - Create a card
- GET /cards - List all cards (optionally filter by deck)
- GET /cards/{card_id} - Get a card
- PATCH /cards/{card_id} - Update a card
- DELETE /cards/{card_id} - Delete a card
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import CurrentUser, get_current_user
from db.pool import get_pool
from domain.flashcards.models import (
    CardCreate,
    CardUpdate,
    CardOut,
    DeckCreate,
    DeckUpdate,
    DeckOut,
)
from domain.flashcards.service import CardService, DeckService

router = APIRouter (prefix="/flashcards", tags=["flashcards"])


def get_deck_service(pool: asyncpg.Pool = Depends(get_pool)) -> DeckService:
    return DeckService(pool)


def get_card_service(pool: asyncpg.Pool = Depends(get_pool)) -> CardService:
    return CardService(pool)


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


@router.patch("/decks/{deck_id}", response_model=DeckOut)
async def update_deck(
    deck_id: UUID,
    payload: DeckUpdate,
    user: CurrentUser = Depends(get_current_user),
    service: DeckService = Depends(get_deck_service),
):
    """Update a deck. Only provided fields will be updated."""
    deck = await service.update_deck(owner_id=user.id, deck_id=deck_id, payload=payload)
    if deck is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found"
        )
    return deck


@router.delete("/decks/{deck_id}")
async def delete_deck(
    deck_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    service: DeckService = Depends(get_deck_service),
):
    """Delete a deck and all its cards."""
    deleted = await service.delete_deck(owner_id=user.id, deck_id=deck_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found"
        )
    return {"message": "Deck deleted", "deck_id": str(deck_id)}


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


@router.patch("/cards/{card_id}", response_model=CardOut)
async def update_card(
    card_id: UUID,
    payload: CardUpdate,
    user: CurrentUser = Depends(get_current_user),
    service: CardService = Depends(get_card_service),
):
    """
    Update a card. Only provided fields will be updated.
    
    Can move card to a different deck (must own the target deck).
    """
    try:
        card = await service.update_card(owner_id=user.id, card_id=card_id, payload=payload)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Card not found"
        )
    return card


@router.delete("/cards/{card_id}")
async def delete_card(
    card_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    service: CardService = Depends(get_card_service),
):
    """Delete a card permanently."""
    deleted = await service.delete_card(owner_id=user.id, card_id=card_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Card not found"
        )
    return {"message": "Card deleted", "card_id": str(card_id)}


__all__ = ["router"]
