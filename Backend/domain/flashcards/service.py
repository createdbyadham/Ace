from __future__ import annotations

from typing import List, Optional
from uuid import UUID

import asyncpg

from domain.flashcards.models import (
    CardCreate,
    CardUpdate,
    CardOut,
    DeckCreate,
    DeckUpdate,
    DeckOut,
)


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

    async def update_deck(
        self, *, owner_id: UUID, deck_id: UUID, payload: DeckUpdate
    ) -> Optional[DeckOut]:
        if payload.title is None:
            return await self.get_deck(owner_id=owner_id, deck_id=deck_id)

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE public.decks
                SET title = $3
                WHERE owner_id = $1 AND deck_id = $2
                RETURNING deck_id, owner_id, title, created_at
                """,
                owner_id,
                deck_id,
                payload.title,
            )
        if row is None:
            return None
        return DeckOut(
            deck_id=row["deck_id"],
            owner_id=row["owner_id"],
            title=row["title"],
            created_at=row["created_at"],
        )

    async def delete_deck(self, *, owner_id: UUID, deck_id: UUID) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM public.decks
                WHERE owner_id = $1 AND deck_id = $2
                """,
                owner_id,
                deck_id,
            )
        return result == "DELETE 1"


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

    async def update_card(
        self, *, owner_id: UUID, card_id: UUID, payload: CardUpdate
    ) -> Optional[CardOut]:
        async with self._pool.acquire() as conn:
            # Verify card exists and belongs to user
            existing = await conn.fetchrow(
                """
                SELECT card_id, deck_id, owner_id, content, created_at
                FROM public.cards
                WHERE owner_id = $1 AND card_id = $2
                """,
                owner_id,
                card_id,
            )
            if existing is None:
                return None

            # If moving to a different deck, verify ownership
            new_deck_id = payload.deck_id if payload.deck_id is not None else existing["deck_id"]
            if payload.deck_id is not None and payload.deck_id != existing["deck_id"]:
                deck_owner = await conn.fetchval(
                    "SELECT owner_id FROM public.decks WHERE deck_id = $1",
                    payload.deck_id,
                )
                if deck_owner is None:
                    raise ValueError("Deck does not exist.")
                if deck_owner != owner_id:
                    raise PermissionError("Deck does not belong to the current user.")

            new_content = (
                payload.content.model_dump()
                if payload.content is not None
                else existing["content"]
            )

            row = await conn.fetchrow(
                """
                UPDATE public.cards
                SET deck_id = $3, content = $4
                WHERE owner_id = $1 AND card_id = $2
                RETURNING card_id, deck_id, owner_id, content, created_at
                """,
                owner_id,
                card_id,
                new_deck_id,
                new_content,
            )

        return CardOut(
            card_id=row["card_id"],
            deck_id=row["deck_id"],
            owner_id=row["owner_id"],
            content=row["content"],
            created_at=row["created_at"],
        )

    async def delete_card(self, *, owner_id: UUID, card_id: UUID) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM public.cards
                WHERE owner_id = $1 AND card_id = $2
                """,
                owner_id,
                card_id,
            )
        return result == "DELETE 1"


__all__ = ["DeckService", "CardService"]

