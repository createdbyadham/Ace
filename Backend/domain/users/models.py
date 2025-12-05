from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ProfileCreate(BaseModel):
    """Request body for creating/updating a profile. user_id comes from JWT."""
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class ProfileCreateInternal(BaseModel):
    """Internal model with user_id (set by the service from JWT)."""
    user_id: UUID
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class ProfileOut(BaseModel):
    user_id: UUID
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime


__all__ = ["ProfileCreate", "ProfileCreateInternal", "ProfileOut"]

