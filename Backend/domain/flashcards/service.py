from __future__ import annotations

import json
from typing import Any, List, Optional
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


def _parse_tags(tags: Any) -> List[str]:
    """Parse tags from database (could be string, list, or None)."""
    if tags is None:
        return []
    if isinstance(tags, list):
        return tags
    if isinstance(tags, str):
        return json.loads(tags)
    return []


class DeckService:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def create_deck(self, *, owner_id: UUID, payload: DeckCreate) -> DeckOut:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO public.decks (owner_id, title, description, tags, language)
                VALUES ($1, $2, $3, $4::jsonb, $5)
                RETURNING deck_id, owner_id, title, description, tags, language, created_at, updated_at
                """,
                owner_id,
                payload.title,
                payload.description,
                json.dumps(payload.tags),
                payload.language,
            )
        return DeckOut(
            deck_id=row["deck_id"],
            owner_id=row["owner_id"],
            title=row["title"],
            description=row["description"],
            tags=_parse_tags(row["tags"]),
            language=row["language"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def list_decks(self, *, owner_id: UUID) -> List[DeckOut]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT deck_id, owner_id, title, description, tags, language, created_at, updated_at
                FROM public.decks
                WHERE owner_id = $1 AND deleted_at IS NULL
                ORDER BY created_at DESC
                """,
                owner_id,
            )
        return [
            DeckOut(
                deck_id=row["deck_id"],
                owner_id=row["owner_id"],
                title=row["title"],
                description=row["description"],
                tags=_parse_tags(row["tags"]),
                language=row["language"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    async def get_deck(self, *, owner_id: UUID, deck_id: UUID) -> Optional[DeckOut]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT deck_id, owner_id, title, description, tags, language, created_at, updated_at
                FROM public.decks
                WHERE owner_id = $1 AND deck_id = $2 AND deleted_at IS NULL
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
            description=row["description"],
            tags=_parse_tags(row["tags"]),
            language=row["language"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def update_deck(
        self, *, owner_id: UUID, deck_id: UUID, payload: DeckUpdate
    ) -> Optional[DeckOut]:
        # Build dynamic update query
        # Use model_fields_set to check which fields were explicitly provided
        # This allows distinguishing between "not provided" and "set to null"
        provided_fields = payload.model_fields_set
        updates = []
        params = [owner_id, deck_id]
        param_idx = 3

        if "title" in provided_fields and payload.title is not None:
            updates.append(f"title = ${param_idx}")
            params.append(payload.title)
            param_idx += 1

        if "description" in provided_fields:
            updates.append(f"description = ${param_idx}")
            params.append(payload.description)  # Can be None to clear
            param_idx += 1

        if "tags" in provided_fields:
            updates.append(f"tags = ${param_idx}::jsonb")
            # Can be None to clear (consistent with description/language)
            params.append(json.dumps(payload.tags) if payload.tags is not None else None)
            param_idx += 1

        if "language" in provided_fields:
            updates.append(f"language = ${param_idx}")
            params.append(payload.language)  # Can be None to clear
            param_idx += 1

        if not updates:
            return await self.get_deck(owner_id=owner_id, deck_id=deck_id)

        query = f"""
            UPDATE public.decks
            SET {', '.join(updates)}
            WHERE owner_id = $1 AND deck_id = $2 AND deleted_at IS NULL
            RETURNING deck_id, owner_id, title, description, tags, language, created_at, updated_at
        """

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)

        if row is None:
            return None
        return DeckOut(
            deck_id=row["deck_id"],
            owner_id=row["owner_id"],
            title=row["title"],
            description=row["description"],
            tags=_parse_tags(row["tags"]),
            language=row["language"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def delete_deck(self, *, owner_id: UUID, deck_id: UUID) -> bool:
        """Soft delete a deck by setting deleted_at timestamp."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE public.decks
                SET deleted_at = now()
                WHERE owner_id = $1 AND deck_id = $2 AND deleted_at IS NULL
                """,
                owner_id,
                deck_id,
            )
        return result == "UPDATE 1"


class CardService:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def create_card(self, *, owner_id: UUID, payload: CardCreate) -> CardOut:
        # asyncpg auto-encodes dicts to JSON via pool's init codec
        content = payload.content.model_dump()
        async with self._pool.acquire() as conn:
            if payload.deck_id is not None:
                deck_owner = await conn.fetchval(
                    "SELECT owner_id FROM public.decks WHERE deck_id = $1 AND deleted_at IS NULL",
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
                    "SELECT owner_id FROM public.decks WHERE deck_id = $1 AND deleted_at IS NULL",
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
