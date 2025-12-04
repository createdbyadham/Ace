from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from domain.cards.models import CardContent


class DueCardOut(BaseModel):
    card_id: str
    deck_id: Optional[str] = None
    content: CardContent
    next_review_at: datetime
    repetition: int
    interval_days: int


class ReviewIn(BaseModel):
    card_id: str = Field(..., description="UUID of the card")
    response: str = Field(..., description="'forgot' | 'meh' | 'got_it'")
    elapsed_ms: Optional[int] = None
    client_review_id: Optional[str] = Field(
        None, description="Optional idempotency key from client"
    )


class ReviewOut(BaseModel):
    card_id: str
    repetition: int
    interval_days: int
    next_review_at: datetime


__all__ = ["CardContent", "DueCardOut", "ReviewIn", "ReviewOut"]

