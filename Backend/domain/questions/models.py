"""
Models for MCQ question sets.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MCQOption(str, Enum):
    """Valid MCQ answer options."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class QuestionCreate(BaseModel):
    """Create a single MCQ question."""
    question_text: str = Field(..., min_length=1)
    option_a: str = Field(..., min_length=1)
    option_b: str = Field(..., min_length=1)
    option_c: str = Field(..., min_length=1)
    option_d: str = Field(..., min_length=1)
    correct_answer: MCQOption
    explanation: Optional[str] = None
    source_file: Optional[str] = None


class QuestionOut(BaseModel):
    """Output model for a question."""
    question_id: UUID
    set_id: UUID
    owner_id: UUID
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str
    explanation: Optional[str] = None
    source_file: Optional[str] = None
    created_at: datetime


class QuestionSetCreate(BaseModel):
    """Create a question set."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    tags: List[str] = Field(default_factory=list)


class QuestionSetOut(BaseModel):
    """Output model for a question set."""
    set_id: UUID
    owner_id: UUID
    title: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    questions_count: int = 0


class QuestionSetWithQuestions(BaseModel):
    """Question set with all its questions."""
    set_id: UUID
    owner_id: UUID
    title: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    questions: List[QuestionOut] = Field(default_factory=list)


__all__ = [
    "MCQOption",
    "QuestionCreate",
    "QuestionOut",
    "QuestionSetCreate",
    "QuestionSetOut",
    "QuestionSetWithQuestions",
]

