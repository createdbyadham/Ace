from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DeckCreate(BaseModel):
    title: str


class DeckOut(BaseModel):
    deck_id: UUID
    owner_id: UUID
    title: str
    created_at: datetime


__all__ = ["DeckCreate", "DeckOut"]

