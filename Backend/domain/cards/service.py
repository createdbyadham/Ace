from __future__ import annotations

from typing import List, Optional
from uuid import UUID

import asyncpg

from domain.cards.models import CardCreate, CardOut


class CardService:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def create_card(self, *, owner_id: UUID, payload: CardCreate) -> CardOut:
        # asyncpg auto-encodes dicts to JSON via pool's init codec
        content = payload.content.model_dump()
        async with self._pool.acquire() as conn:
            if payload.deck_id is not None:
                deck_owner = await conn.fetchval(
                    "SELECT owner_id FROM public.decks WHERE deck_id = $1",
                    payload.deck_id,
                )
                if deck_owner is None:
                    raise ValueError("Deck does not exist.")
                if deck_owner != owner_id:
                    raise PermissionError("Deck does not belong to the current user.")

            row = await conn.fetchrow(
                """
                INSERT INTO public.cards (deck_id, owner_id, content)
                VALUES ($1, $2, $3)
                RETURNING card_id, deck_id, owner_id, content, created_at
                """,
                payload.deck_id,
                owner_id,
                content,
            )

        return CardOut(
            card_id=row["card_id"],
            deck_id=row["deck_id"],
            owner_id=row["owner_id"],
            content=row["content"],
            created_at=row["created_at"],
        )

    async def list_cards(
        self, *, owner_id: UUID, deck_id: Optional[UUID] = None
    ) -> List[CardOut]:
        async with self._pool.acquire() as conn:
            if deck_id is None:
                rows = await conn.fetch(
                    """
                    SELECT card_id, deck_id, owner_id, content, created_at
                    FROM public.cards
                    WHERE owner_id = $1
                    ORDER BY created_at DESC
                    """,
                    owner_id,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT card_id, deck_id, owner_id, content, created_at
                    FROM public.cards
                    WHERE owner_id = $1 AND deck_id = $2
                    ORDER BY created_at DESC
                    """,
                    owner_id,
                    deck_id,
                )

        return [
            CardOut(
                card_id=row["card_id"],
                deck_id=row["deck_id"],
                owner_id=row["owner_id"],
                content=row["content"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    async def get_card(self, *, owner_id: UUID, card_id: UUID) -> Optional[CardOut]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT card_id, deck_id, owner_id, content, created_at
                FROM public.cards
                WHERE owner_id = $1 AND card_id = $2
                """,
                owner_id,
                card_id,
            )
        if row is None:
            return None
        return CardOut(
            card_id=row["card_id"],
            deck_id=row["deck_id"],
            owner_id=row["owner_id"],
            content=row["content"],
            created_at=row["created_at"],
        )


__all__ = ["CardService"]

