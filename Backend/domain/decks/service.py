from __future__ import annotations

from typing import List, Optional
from uuid import UUID

import asyncpg

from domain.decks.models import DeckCreate, DeckOut


class DeckService:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def create_deck(self, *, owner_id: UUID, payload: DeckCreate) -> DeckOut:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO public.decks (owner_id, title)
                VALUES ($1, $2)
                RETURNING deck_id, owner_id, title, created_at
                """,
                owner_id,
                payload.title,
            )
        return DeckOut(
            deck_id=row["deck_id"],
            owner_id=row["owner_id"],
            title=row["title"],
            created_at=row["created_at"],
        )

    async def list_decks(self, *, owner_id: UUID) -> List[DeckOut]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT deck_id, owner_id, title, created_at
                FROM public.decks
                WHERE owner_id = $1
                ORDER BY created_at DESC
                """,
                owner_id,
            )
        return [
            DeckOut(
                deck_id=row["deck_id"],
                owner_id=row["owner_id"],
                title=row["title"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    async def get_deck(self, *, owner_id: UUID, deck_id: UUID) -> Optional[DeckOut]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT deck_id, owner_id, title, created_at
                FROM public.decks
                WHERE owner_id = $1 AND deck_id = $2
                """,
                owner_id,
                deck_id,
            )
        if row is None:
            return None
        return DeckOut(
            deck_id=row["deck_id"],
            owner_id=row["owner_id"],
            title=row["title"],
            created_at=row["created_at"],
        )


__all__ = ["DeckService"]

