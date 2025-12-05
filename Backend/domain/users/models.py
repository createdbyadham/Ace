from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ProfileUpdate(BaseModel):
    """
    Request body for updating a profile. All fields optional.
    Profile is auto-created on signup, so this is always an update.
    """
    username: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class ProfileUpdateInternal(BaseModel):
    """Internal model with user_id (set from JWT)."""
    user_id: UUID
    username: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class ProfileOut(BaseModel):
    user_id: UUID
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime


__all__ = ["ProfileUpdate", "ProfileUpdateInternal", "ProfileOut"]

