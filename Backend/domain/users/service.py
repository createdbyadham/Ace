from __future__ import annotations

from typing import Optional
from uuid import UUID

import asyncpg

from domain.users.models import (
    ProfileUpdateInternal, 
    ProfileOut,
    GamificationOut,
    calculate_level,
    calculate_streak_multiplier,
)


class ProfileService:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def update_profile(self, payload: ProfileUpdateInternal) -> ProfileOut:
        """
        Update the user's profile. Only updates fields that are not None.
        Profile must already exist (created by signup trigger).
        """
        # Build dynamic UPDATE query for only provided fields
        updates = []
        values = []
        param_num = 1
        
        if payload.username is not None:
            updates.append(f"username = ${param_num}")
            values.append(payload.username)
            param_num += 1
        
        if payload.display_name is not None:
            updates.append(f"display_name = ${param_num}")
            values.append(payload.display_name)
            param_num += 1
        
        if payload.avatar_url is not None:
            updates.append(f"avatar_url = ${param_num}")
            values.append(payload.avatar_url)
            param_num += 1
        
        # If nothing to update, just fetch and return current profile
        if not updates:
            return await self.get_profile(payload.user_id)
        
        # Add user_id as last parameter for WHERE clause
        values.append(payload.user_id)
        
        query = f"""
            UPDATE public.users
            SET {', '.join(updates)}
            WHERE user_id = ${param_num}
            RETURNING user_id, username, display_name, avatar_url, streak, xp, created_at
        """
        
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, *values)
        
        if row is None:
            # Profile doesn't exist yet (edge case - trigger should have created it)
            raise ValueError("Profile not found. Please sign up first.")
        
        return ProfileOut(
            user_id=row["user_id"],
            username=row["username"],
            display_name=row["display_name"],
            avatar_url=row["avatar_url"],
            streak=row["streak"] or 0,
            xp=row["xp"] or 0,
            created_at=row["created_at"],
        )

    async def get_profile(self, user_id: UUID) -> Optional[ProfileOut]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT user_id, username, display_name, avatar_url, streak, xp, created_at
                FROM public.users
                WHERE user_id = $1
                """,
                user_id,
            )
        if row is None:
            return None
        return ProfileOut(
            user_id=row["user_id"],
            username=row["username"],
            display_name=row["display_name"],
            avatar_url=row["avatar_url"],
            streak=row["streak"] or 0,
            xp=row["xp"] or 0,
            created_at=row["created_at"],
        )

    async def get_gamification(self, user_id: UUID) -> Optional[GamificationOut]:
        """Get detailed gamification stats for user."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT streak, xp
                FROM public.users
                WHERE user_id = $1
                """,
                user_id,
            )
        if row is None:
            return None
        
        streak = row["streak"] or 0
        xp = row["xp"] or 0
        level, xp_in_current, xp_to_next = calculate_level(xp)
        
        return GamificationOut(
            streak=streak,
            xp=xp,
            level=level,
            xp_to_next_level=xp_to_next,
            xp_in_current_level=xp_in_current,
            streak_multiplier=calculate_streak_multiplier(streak),
        )


__all__ = ["ProfileService"]

