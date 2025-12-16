from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in the conversation."""
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation memory. If not provided, a new session is created."
    )


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    response: str
    session_id: str
    sources: List[str] = Field(default_factory=list, description="Source documents used for context")


