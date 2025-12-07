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
    streak: int = 0
    xp: int = 0
    created_at: datetime


class GamificationOut(BaseModel):
    """Detailed gamification stats for /users/me/gamification."""
    streak: int
    xp: int
    level: int
    xp_to_next_level: int
    xp_in_current_level: int
    streak_multiplier: float  # Bonus multiplier based on streak


# XP Constants
XP_BASE = {
    "got_it": 10,
    "meh": 5,
    "forgot": 2,
}

# Level thresholds: level N requires LEVEL_XP_BASE * (N^LEVEL_XP_EXPONENT) total XP
LEVEL_XP_BASE = 100
LEVEL_XP_EXPONENT = 1.5

# Streak multiplier: 1 + (streak * STREAK_MULTIPLIER_INCREMENT), capped at STREAK_MULTIPLIER_CAP
STREAK_MULTIPLIER_INCREMENT = 0.05  # +5% per day
STREAK_MULTIPLIER_CAP = 2.0  # Max 2x multiplier at 20-day streak


def calculate_level(xp: int) -> tuple[int, int, int]:
    """
    Calculate level from XP.
    
    Returns: (level, xp_in_current_level, xp_to_next_level)
    """
    level = 1
    total_xp_for_level = LEVEL_XP_BASE
    
    while xp >= total_xp_for_level:
        level += 1
        total_xp_for_level = int(LEVEL_XP_BASE * (level ** LEVEL_XP_EXPONENT))
    
    # XP required for current level (previous threshold)
    prev_level_xp = int(LEVEL_XP_BASE * ((level - 1) ** LEVEL_XP_EXPONENT)) if level > 1 else 0
    xp_in_current = xp - prev_level_xp
    xp_to_next = total_xp_for_level - xp
    
    return level, xp_in_current, xp_to_next


def calculate_streak_multiplier(streak: int) -> float:
    """Calculate XP multiplier based on current streak."""
    multiplier = 1.0 + (streak * STREAK_MULTIPLIER_INCREMENT)
    return min(multiplier, STREAK_MULTIPLIER_CAP)


def calculate_xp_earned(response: str, streak: int) -> tuple[int, int]:
    """
    Calculate XP earned for a review response.
    
    Returns: (base_xp, total_xp_with_multiplier)
    """
    base_xp = XP_BASE.get(response.lower(), 0)
    multiplier = calculate_streak_multiplier(streak)
    total_xp = int(base_xp * multiplier)
    return base_xp, total_xp


__all__ = [
    "ProfileUpdate", 
    "ProfileUpdateInternal", 
    "ProfileOut",
    "GamificationOut",
    "XP_BASE",
    "calculate_level",
    "calculate_streak_multiplier",
    "calculate_xp_earned",
]

