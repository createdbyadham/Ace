from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List
from uuid import UUID

import asyncpg

from domain.sr.logic import compute_new_interval_and_repetition
from domain.sr.models import DueCardOut, ReviewIn, ReviewOut


class ReviewService:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def fetch_due_cards(self, *, user_id: UUID, limit: int) -> List[DueCardOut]:
        user_key = str(user_id)
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT s.card_id,
                       s.next_review_at,
                       s.repetition,
                       s.interval_days,
                       c.deck_id,
                       c.content
                FROM sr.states s
                JOIN app.cards c ON c.card_id = s.card_id
                WHERE s.user_id = $1
                  AND s.next_review_at <= now()
                ORDER BY s.next_review_at
                LIMIT $2
                """,
                user_key,
                limit,
            )

        return [
            DueCardOut(
                card_id=str(row["card_id"]),
                deck_id=str(row["deck_id"]) if row["deck_id"] else None,
                content=row["content"],
                next_review_at=row["next_review_at"],
                repetition=row["repetition"] or 0,
                interval_days=row["interval_days"] or 0,
            )
            for row in rows
        ]

    async def process_review(self, *, payload: ReviewIn, user_id: UUID) -> ReviewOut:
        user_key = str(user_id)
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                state = await self._handle_idempotent_review(conn, payload, user_key)
                if state is not None:
                    return state

                await self._insert_review_log(conn, payload, user_key)

                state_row = await conn.fetchrow(
                    """
                    SELECT state_id, repetition, interval_days
                    FROM sr.states
                    WHERE user_id = $1 AND card_id = $2
                    FOR UPDATE
                    """,
                    user_key,
                    payload.card_id,
                )

                if state_row is None:
                    await conn.execute(
                        """
                        INSERT INTO sr.states (
                            user_id,
                            card_id,
                            repetition,
                            interval_days,
                            next_review_at,
                            last_reviewed_at,
                            created_at,
                            updated_at
                        )
                        VALUES ($1, $2, 0, 0, now(), NULL, now(), now())
                        """,
                        user_key,
                        payload.card_id,
                    )
                    state_row = await conn.fetchrow(
                        """
                        SELECT state_id, repetition, interval_days
                        FROM sr.states
                        WHERE user_id = $1 AND card_id = $2
                        FOR UPDATE
                        """,
                        user_key,
                        payload.card_id,
                    )

                prev_repetition = state_row["repetition"] or 0
                prev_interval = state_row["interval_days"] or 0

                new_repetition, new_interval = compute_new_interval_and_repetition(
                    prev_repetition, prev_interval, payload.response
                )
                next_review_at = datetime.now(timezone.utc) + timedelta(days=new_interval)

                await conn.execute(
                    """
                    INSERT INTO sr.states (
                        state_id,
                        user_id,
                        card_id,
                        repetition,
                        interval_days,
                        next_review_at,
                        last_reviewed_at,
                        updated_at,
                        created_at
                    )
                    VALUES (
                        $1, $2, $3, $4, $5, $6, now(), now(),
                        coalesce((SELECT created_at FROM sr.states WHERE user_id = $2 AND card_id = $3), now())
                    )
                    ON CONFLICT (user_id, card_id) DO UPDATE
                    SET repetition = EXCLUDED.repetition,
                        interval_days = EXCLUDED.interval_days,
                        next_review_at = EXCLUDED.next_review_at,
                        last_reviewed_at = EXCLUDED.last_reviewed_at,
                        updated_at = EXCLUDED.updated_at
                    """,
                    state_row["state_id"],
                    user_key,
                    payload.card_id,
                    new_repetition,
                    new_interval,
                    next_review_at,
                )

                return ReviewOut(
                    card_id=payload.card_id,
                    repetition=new_repetition,
                    interval_days=new_interval,
                    next_review_at=next_review_at,
                )

    async def _handle_idempotent_review(
        self, conn: asyncpg.Connection, payload: ReviewIn, user_key: str
    ) -> ReviewOut | None:
        if not payload.client_review_id:
            return None

        existing = await conn.fetchrow(
            """
            SELECT 1
            FROM sr.reviews
            WHERE metadata->>'client_review_id' = $1 AND user_id = $2
            """,
            payload.client_review_id,
            user_key,
        )
        if not existing:
            return None

        state = await conn.fetchrow(
            """
            SELECT repetition, interval_days, next_review_at
            FROM sr.states
            WHERE user_id = $1 AND card_id = $2
            """,
            user_key,
            payload.card_id,
        )
        if state is None:
            raise RuntimeError("State missing after idempotent review.")

        return ReviewOut(
            card_id=payload.card_id,
            repetition=state["repetition"] or 0,
            interval_days=state["interval_days"] or 0,
            next_review_at=state["next_review_at"],
        )

    async def _insert_review_log(
        self, conn: asyncpg.Connection, payload: ReviewIn, user_key: str
    ) -> None:
        metadata = {"source": "fastapi-service"}
        if payload.client_review_id:
            metadata["client_review_id"] = payload.client_review_id

        await conn.execute(
            """
            INSERT INTO sr.reviews (user_id, card_id, response, elapsed_ms, created_at, metadata)
            VALUES ($1, $2, $3, $4, now(), $5::jsonb)
            """,
            user_key,
            payload.card_id,
            payload.response.lower(),
            payload.elapsed_ms,
            metadata,
        )


__all__ = ["ReviewService"]

