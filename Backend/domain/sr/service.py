from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

import asyncpg

from domain.sr.logic import compute_sm2, map_response_to_quality
from domain.sr.models import (
    DueCardOut, 
    StudySessionOut,
    UpcomingDay,
    UpcomingOut,
    ReviewIn, 
    ReviewOut,
    SnoozeIn,
    SnoozeOut,
    DeckStatsOut,
)


class ReviewService:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    # =========================================================================
    # Due Cards - Global
    # =========================================================================
    
    async def fetch_due_cards(
        self, 
        *, 
        user_id: UUID, 
        limit: int,
        deck_id: Optional[UUID] = None,
    ) -> List[DueCardOut]:
        """
        Fetch cards ready to study for a user, optionally filtered by deck.
        
        Returns:
        - New cards (no state yet)
        - Due cards (state exists and next_review_at <= now)
        """
        async with self._pool.acquire() as conn:
            if deck_id is None:
                rows = await conn.fetch(
                    """
                    SELECT c.card_id, c.deck_id, c.content,
                           s.next_review_at, s.repetition, s.interval_days, s.ef
                    FROM public.cards c
                    LEFT JOIN public.states s ON s.card_id = c.card_id AND s.user_id = $1
                    WHERE c.owner_id = $1
                      AND c.deleted_at IS NULL
                      AND (s.next_review_at <= now() OR s.card_id IS NULL)
                    ORDER BY 
                        CASE WHEN s.card_id IS NULL THEN 0 ELSE 1 END,  -- New cards first
                        s.next_review_at NULLS FIRST
                    LIMIT $2
                    """,
                    user_id,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT c.card_id, c.deck_id, c.content,
                           s.next_review_at, s.repetition, s.interval_days, s.ef
                    FROM public.cards c
                    LEFT JOIN public.states s ON s.card_id = c.card_id AND s.user_id = $1
                    WHERE c.owner_id = $1
                      AND c.deck_id = $2
                      AND c.deleted_at IS NULL
                      AND (s.next_review_at <= now() OR s.card_id IS NULL)
                    ORDER BY 
                        CASE WHEN s.card_id IS NULL THEN 0 ELSE 1 END,  -- New cards first
                        s.next_review_at NULLS FIRST
                    LIMIT $3
                    """,
                    user_id,
                    deck_id,
                    limit,
                )

        return [
            DueCardOut(
                card_id=str(row["card_id"]),
                deck_id=str(row["deck_id"]) if row["deck_id"] else None,
                content=row["content"],
                next_review_at=row["next_review_at"] or datetime.now(timezone.utc),
                repetition=row["repetition"] or 0,
                interval_days=row["interval_days"] or 0,
                ef=float(row["ef"] or 2.5),
            )
            for row in rows
        ]

    # =========================================================================
    # Study Session - Deck-specific
    # =========================================================================
    
    async def get_study_session(
        self,
        *,
        user_id: UUID,
        deck_id: UUID,
        limit: int = 20,
        mode: str = "review",
    ) -> StudySessionOut:
        """
        Get study session for a specific deck.
        
        Args:
            mode: 
                - "review" (default): Only cards due for review (SM-2 based)
                - "all": All cards in the deck (normal session)
        """
        async with self._pool.acquire() as conn:
            if mode == "all":
                # Normal session: ALL cards in the deck
                cards = await self._fetch_all_cards(conn, user_id, deck_id, limit)
            else:
                # Review session: Only due cards (SM-2)
                cards = await self.fetch_due_cards(
                    user_id=user_id, 
                    deck_id=deck_id, 
                    limit=limit
                )
            
            # Get counts (due = new cards + cards with next_review_at <= now)
            counts = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) FILTER (
                        WHERE s.next_review_at <= now() OR s.card_id IS NULL
                    ) AS due_count,
                    COUNT(*) AS total_count
                FROM public.cards c
                LEFT JOIN public.states s ON s.card_id = c.card_id AND s.user_id = $1
                WHERE c.deck_id = $2 AND c.deleted_at IS NULL
                """,
                user_id,
                deck_id,
            )
            
        return StudySessionOut(
            cards=cards,
            due_count=counts["due_count"] or 0,
            total_count=counts["total_count"] or 0,
            mode=mode,
        )

    async def _fetch_all_cards(
        self,
        conn: asyncpg.Connection,
        user_id: UUID,
        deck_id: UUID,
        limit: int,
    ) -> List[DueCardOut]:
        """Fetch ALL cards in a deck (normal session, no due filtering)."""
        rows = await conn.fetch(
            """
            SELECT c.card_id, c.deck_id, c.content,
                   s.next_review_at, s.repetition, s.interval_days, s.ef
            FROM public.cards c
            LEFT JOIN public.states s ON s.card_id = c.card_id AND s.user_id = $1
            WHERE c.owner_id = $1
              AND c.deck_id = $2
              AND c.deleted_at IS NULL
            ORDER BY c.created_at
            LIMIT $3
            """,
            user_id,
            deck_id,
            limit,
        )

        return [
            DueCardOut(
                card_id=str(row["card_id"]),
                deck_id=str(row["deck_id"]) if row["deck_id"] else None,
                content=row["content"],
                next_review_at=row["next_review_at"] or datetime.now(timezone.utc),
                repetition=row["repetition"] or 0,
                interval_days=row["interval_days"] or 0,
                ef=float(row["ef"] or 2.5),
            )
            for row in rows
        ]

    # =========================================================================
    # Upcoming Schedule
    # =========================================================================
    
    async def get_upcoming(
        self,
        *,
        user_id: UUID,
        deck_id: Optional[UUID] = None,
        days: int = 7,
    ) -> UpcomingOut:
        """Get upcoming review counts per day."""
        async with self._pool.acquire() as conn:
            if deck_id is None:
                rows = await conn.fetch(
                    """
                    SELECT 
                        DATE(s.next_review_at) AS review_date,
                        COUNT(*) AS count
                    FROM public.states s
                    JOIN public.cards c ON c.card_id = s.card_id
                    WHERE s.user_id = $1
                      AND s.next_review_at > now()
                      AND s.next_review_at <= now() + ($2 || ' days')::interval
                      AND c.deleted_at IS NULL
                    GROUP BY DATE(s.next_review_at)
                    ORDER BY review_date
                    """,
                    user_id,
                    str(days),
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT 
                        DATE(s.next_review_at) AS review_date,
                        COUNT(*) AS count
                    FROM public.states s
                    JOIN public.cards c ON c.card_id = s.card_id
                    WHERE s.user_id = $1
                      AND c.deck_id = $2
                      AND s.next_review_at > now()
                      AND s.next_review_at <= now() + ($3 || ' days')::interval
                      AND c.deleted_at IS NULL
                    GROUP BY DATE(s.next_review_at)
                    ORDER BY review_date
                    """,
                    user_id,
                    deck_id,
                    str(days),
                )
        
        upcoming_days = [
            UpcomingDay(
                date=row["review_date"].isoformat(),
                count=row["count"],
            )
            for row in rows
        ]
        
        return UpcomingOut(
            days=upcoming_days,
            total_upcoming=sum(d.count for d in upcoming_days),
        )

    # =========================================================================
    # Deck Stats
    # =========================================================================
    
    async def get_deck_stats(
        self,
        *,
        user_id: UUID,
        deck_id: UUID,
    ) -> DeckStatsOut:
        """Get statistics for a deck."""
        async with self._pool.acquire() as conn:
            stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) AS total_cards,
                    COUNT(*) FILTER (
                        WHERE s.next_review_at <= now() OR s.card_id IS NULL
                    ) AS due_now,
                    COUNT(*) FILTER (
                        WHERE DATE(s.next_review_at) = CURRENT_DATE OR s.card_id IS NULL
                    ) AS due_today,
                    COUNT(*) FILTER (WHERE s.interval_days > 21) AS mastered,
                    COUNT(*) FILTER (WHERE s.interval_days > 0 AND s.interval_days <= 21) AS learning,
                    COUNT(*) FILTER (WHERE s.repetition = 0 OR s.card_id IS NULL) AS new
                FROM public.cards c
                LEFT JOIN public.states s ON s.card_id = c.card_id AND s.user_id = $1
                WHERE c.deck_id = $2 AND c.deleted_at IS NULL
                """,
                user_id,
                deck_id,
            )
            
        return DeckStatsOut(
            deck_id=str(deck_id),
            total_cards=stats["total_cards"] or 0,
            due_now=stats["due_now"] or 0,
            due_today=stats["due_today"] or 0,
            mastered=stats["mastered"] or 0,
            learning=stats["learning"] or 0,
            new=stats["new"] or 0,
        )

    # =========================================================================
    # Process Review - Core SM-2 Logic
    # =========================================================================
    
    async def process_review(
        self, 
        *, 
        payload: ReviewIn, 
        user_id: UUID,
    ) -> ReviewOut:
        """
        Process a review and update state using SM-2 algorithm.
        
        If payload.mode='all', skips SM-2 state updates (practice only).
        """
        # Practice mode (mode=all): no SM-2 tracking, just return dummy response
        if payload.mode == "all":
            return await self._handle_practice_review(payload)
        
        # Full review mode: update SM-2 state
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                # Handle idempotency
                existing = await self._handle_idempotent_review(conn, payload, user_id)
                if existing is not None:
                    return existing

                # Get or create state with lock
                state_row = await conn.fetchrow(
                    """
                    SELECT state_id, repetition, interval_days, ef, version
                    FROM public.states
                    WHERE user_id = $1 AND card_id = $2
                    FOR UPDATE
                    """,
                    user_id,
                    payload.card_id,
                )

                if state_row is None:
                    # Create initial state
                    state_row = await conn.fetchrow(
                        """
                        INSERT INTO public.states (
                            user_id, card_id, repetition, ef, interval_days,
                            next_review_at, last_reviewed_at, version, created_at, updated_at
                        )
                        VALUES ($1, $2, 0, 2.5, 0, now(), NULL, 1, now(), now())
                        RETURNING state_id, repetition, interval_days, ef, version
                        """,
                        user_id,
                        payload.card_id,
                    )

                # Compute new SM-2 values
                prev_repetition = state_row["repetition"] or 0
                prev_interval = state_row["interval_days"] or 0
                prev_ef = float(state_row["ef"] or 2.5)
                prev_version = state_row["version"] or 1

                result = compute_sm2(prev_repetition, prev_interval, prev_ef, payload.response)
                next_review_at = datetime.now(timezone.utc) + timedelta(days=result.interval_days)

                # Insert review log with quality
                await self._insert_review_log(conn, payload, user_id, result.quality)

                # Update state with optimistic locking
                updated = await conn.fetchrow(
                    """
                    UPDATE public.states
                    SET repetition = $1,
                        interval_days = $2,
                        ef = $3,
                        next_review_at = $4,
                        last_reviewed_at = now(),
                        version = version + 1,
                        updated_at = now()
                    WHERE user_id = $5 AND card_id = $6 AND version = $7
                    RETURNING version
                    """,
                    result.repetition,
                    result.interval_days,
                    result.ef,
                    next_review_at,
                    user_id,
                    payload.card_id,
                    prev_version,
                )

                if updated is None:
                    # Conflict - someone else updated. Retry logic could go here.
                    raise RuntimeError("Concurrent update conflict. Please retry.")

                return ReviewOut(
                    card_id=payload.card_id,
                    repetition=result.repetition,
                    interval_days=result.interval_days,
                    ef=result.ef,
                    next_review_at=next_review_at,
                    quality=result.quality,
                )

    async def _handle_practice_review(self, payload: ReviewIn) -> ReviewOut:
        """
        Handle practice-only review (no SM-2 tracking).
        
        Returns a response for UI feedback but doesn't persist anything.
        """
        from domain.sr.logic import map_response_to_quality
        
        quality = map_response_to_quality(payload.response)
        
        return ReviewOut(
            card_id=payload.card_id,
            repetition=0,  # Not tracked
            interval_days=0,  # Not tracked
            ef=2.5,  # Default
            next_review_at=datetime.now(timezone.utc),  # Placeholder
            quality=quality,
        )

    # =========================================================================
    # Snooze Card
    # =========================================================================
    
    async def snooze_card(
        self,
        *,
        user_id: UUID,
        payload: SnoozeIn,
    ) -> SnoozeOut:
        """Postpone a card's review by specified hours."""
        next_review_at = datetime.now(timezone.utc) + timedelta(hours=payload.hours)
        
        async with self._pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                UPDATE public.states
                SET next_review_at = $1, updated_at = now()
                WHERE user_id = $2 AND card_id = $3
                RETURNING card_id, next_review_at
                """,
                next_review_at,
                user_id,
                payload.card_id,
            )
            
            if result is None:
                raise ValueError(f"No state found for card {payload.card_id}")
            
        return SnoozeOut(
            card_id=str(result["card_id"]),
            next_review_at=result["next_review_at"],
        )

    # =========================================================================
    # Private Helpers
    # =========================================================================
    
    async def _handle_idempotent_review(
        self, 
        conn: asyncpg.Connection, 
        payload: ReviewIn, 
        user_id: UUID,
    ) -> ReviewOut | None:
        """Check if this review was already processed (idempotency)."""
        if not payload.client_review_id:
            return None

        existing = await conn.fetchrow(
            """
            SELECT r.quality, s.repetition, s.interval_days, s.ef, s.next_review_at
            FROM public.reviews r
            JOIN public.states s ON s.user_id = r.user_id AND s.card_id = r.card_id
            WHERE r.metadata->>'client_review_id' = $1 AND r.user_id = $2
            """,
            payload.client_review_id,
            user_id,
        )
        
        if not existing:
            return None

        return ReviewOut(
            card_id=payload.card_id,
            repetition=existing["repetition"] or 0,
            interval_days=existing["interval_days"] or 0,
            ef=float(existing["ef"] or 2.5),
            next_review_at=existing["next_review_at"],
            quality=existing["quality"] or 3,
        )

    async def _insert_review_log(
        self, 
        conn: asyncpg.Connection, 
        payload: ReviewIn, 
        user_id: UUID,
        quality: int,
    ) -> None:
        """Insert review into audit log."""
        metadata = {"source": "fastapi-service"}
        if payload.client_review_id:
            metadata["client_review_id"] = payload.client_review_id

        await conn.execute(
            """
            INSERT INTO public.reviews (
                user_id, card_id, response, quality, elapsed_ms, 
                device_id, metadata, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, now(), now())
            """,
            user_id,
            payload.card_id,
            payload.response.lower(),
            quality,
            payload.elapsed_ms,
            UUID(payload.device_id) if payload.device_id else None,
            metadata,
        )


__all__ = ["ReviewService"]
