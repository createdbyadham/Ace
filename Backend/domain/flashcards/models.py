from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


# Card models
class CardContent(BaseModel):
    front: str
    back: Optional[str] = None
    cloze: Optional[List[str]] = None
    hints: Optional[List[str]] = None


class CardCreate(BaseModel):
    deck_id: Optional[UUID] = None
    content: CardContent


class CardOut(BaseModel):
    card_id: UUID
    deck_id: Optional[UUID] = None
    owner_id: UUID
    content: CardContent
    created_at: datetime


# Deck models
class DeckCreate(BaseModel):
    title: str


class DeckOut(BaseModel):
    deck_id: UUID
    owner_id: UUID
    title: str
    created_at: datetime


__all__ = ["CardContent", "CardCreate", "CardOut", "DeckCreate", "DeckOut"]

