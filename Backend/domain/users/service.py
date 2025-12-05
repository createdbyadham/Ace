from __future__ import annotations

from typing import Optional
from uuid import UUID

import asyncpg

from domain.users.models import ProfileCreateInternal, ProfileOut


class ProfileService:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def upsert_profile(self, payload: ProfileCreateInternal) -> ProfileOut:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO public.users (user_id, username, display_name, avatar_url)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id) DO UPDATE
                   SET username = EXCLUDED.username,
                       display_name = EXCLUDED.display_name,
                       avatar_url = EXCLUDED.avatar_url
                RETURNING user_id, username, display_name, avatar_url, created_at
                """,
                payload.user_id,
                payload.username,
                payload.display_name,
                payload.avatar_url,
            )

        return ProfileOut(
            user_id=row["user_id"],
            username=row["username"],
            display_name=row["display_name"],
            avatar_url=row["avatar_url"],
            created_at=row["created_at"],
        )

    async def get_profile(self, user_id: UUID) -> Optional[ProfileOut]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT user_id, username, display_name, avatar_url, created_at
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
            created_at=row["created_at"],
        )


__all__ = ["ProfileService"]

