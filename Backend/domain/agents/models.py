"""
Models for AI agents.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class GeneratedCard(BaseModel):
    """A single generated flashcard."""
    front: str
    back: str
    source_file: str = Field(description="Which PDF this card was generated from")


class FlashcardGenerationRequest(BaseModel):
    """Request body for flashcard generation."""
    num_cards: int = Field(..., ge=1, le=100, description="Number of flashcards to generate")
    deck_title: str = Field(..., min_length=1, max_length=200, description="Title for the new deck")
    deck_description: Optional[str] = Field(default=None, max_length=1000)


class FlashcardGenerationResponse(BaseModel):
    """Response from flashcard generation."""
    deck_id: UUID
    deck_title: str
    cards_created: int
    cards: List[GeneratedCard]
    source_files: List[str]
    model_used: str = Field(default="openai", description="Model used for generation: 'openai' or 'ace'")


class DeckWithCardsOut(BaseModel):
    """Full deck output with cards."""
    deck_id: UUID
    owner_id: UUID
    title: str
    description: Optional[str]
    created_at: datetime
    cards_count: int


# ============================================
# Summary Generation Models
# ============================================

class SummaryGenerationResponseOut(BaseModel):
    """Response from summary generation."""
    summary_id: str
    title: str
    content: str
    key_points: List[str]
    source_files: List[str]
    word_count: int


class SummaryOut(BaseModel):
    """Summary output model."""
    summary_id: str
    owner_id: str
    title: str
    content: str
    key_points: List[str]
    source_files: List[str]
    word_count: int
    created_at: datetime
    updated_at: Optional[datetime]


class SummaryListResponse(BaseModel):
    """List of summaries response."""
    summaries: List[SummaryOut]
    total: int


__all__ = [
    "GeneratedCard",
    "FlashcardGenerationRequest",
    "FlashcardGenerationResponse",
    "DeckWithCardsOut",
    "SummaryGenerationResponseOut",
    "SummaryOut",
    "SummaryListResponse",
]

