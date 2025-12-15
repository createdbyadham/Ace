"""
Models for MCQ question sets.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class QuestionCreate(BaseModel):
    """Create a single MCQ question."""
    question_text: str = Field(..., min_length=1)
    options: List[str] = Field(..., min_length=4, max_length=4, description="Exactly 4 options")
    correct_answer: int = Field(..., ge=0, le=3, description="Index of correct option (0-3)")
    explanation: Optional[str] = None
    source_file: Optional[str] = None
    
    @field_validator("options")
    @classmethod
    def validate_options(cls, v: List[str]) -> List[str]:
        if len(v) != 4:
            raise ValueError("Must have exactly 4 options")
        if any(not opt.strip() for opt in v):
            raise ValueError("All options must be non-empty")
        return v


class QuestionUpdate(BaseModel):
    """Update a question. All fields optional."""
    question_text: Optional[str] = Field(default=None, min_length=1)
    options: Optional[List[str]] = Field(default=None, min_length=4, max_length=4)
    correct_answer: Optional[int] = Field(default=None, ge=0, le=3)
    explanation: Optional[str] = None
    
    @field_validator("options")
    @classmethod
    def validate_options(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        if len(v) != 4:
            raise ValueError("Must have exactly 4 options")
        if any(not opt.strip() for opt in v):
            raise ValueError("All options must be non-empty")
        return v


class QuestionOut(BaseModel):
    """Output model for a question."""
    question_id: UUID
    set_id: UUID
    owner_id: UUID
    question_text: str
    options: List[str]
    correct_answer: int
    explanation: Optional[str] = None
    source_file: Optional[str] = None
    created_at: datetime


class QuestionSetCreate(BaseModel):
    """Create a question set."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    tags: List[str] = Field(default_factory=list)


class QuestionSetUpdate(BaseModel):
    """Update a question set. All fields optional."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    tags: Optional[List[str]] = None


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
    "QuestionCreate",
    "QuestionUpdate",
    "QuestionOut",
    "QuestionSetCreate",
    "QuestionSetUpdate",
    "QuestionSetOut",
    "QuestionSetWithQuestions",
]
