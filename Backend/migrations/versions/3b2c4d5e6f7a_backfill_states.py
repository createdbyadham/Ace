"""Step 2: Backfill states for existing cards

Revision ID: 3b2c4d5e6f7a
Revises: 44c0ba00cbba
Create Date: 2025-12-05

Purpose: Ensure every card has a states row for its owner.
This makes all existing cards appear in review queues immediately.

Default values:
- repetition = 0 (never reviewed)
- ef = 2.5 (SM-2 default easiness factor)
- interval_days = 0 (new card)
- next_review_at = now() (immediately due)
- version = 1
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '3b2c4d5e6f7a'
down_revision: Union[str, None] = '44c0ba00cbba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # Backfill: Create states rows for all cards that don't have one
    # 
    # For each card, create a state for its owner if one doesn't exist.
    # This ensures all cards appear in the user's review queue.
    # =========================================================================
    op.execute("""
        INSERT INTO public.states (
            user_id,
            card_id,
            repetition,
            ef,
            interval_days,
            next_review_at,
            last_reviewed_at,
            created_at,
            updated_at,
            version
        )
        SELECT 
            c.owner_id,           -- The card owner becomes the state owner
            c.card_id,
            0,                    -- repetition: never reviewed
            2.5,                  -- ef: SM-2 default easiness factor
            0,                    -- interval_days: new card
            now(),                -- next_review_at: immediately due
            NULL,                 -- last_reviewed_at: never reviewed
            now(),
            now(),
            1                     -- version: initial
        FROM public.cards c
        LEFT JOIN public.states s 
            ON s.card_id = c.card_id 
            AND s.user_id = c.owner_id
        WHERE s.card_id IS NULL           -- Only cards without a state
          AND c.deleted_at IS NULL;       -- Skip soft-deleted cards
    """)

    # Log how many states were created (for visibility in migration output)
    # This is informational only
    op.execute("""
        DO $$
        DECLARE
            state_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO state_count FROM public.states;
            RAISE NOTICE 'Total states after backfill: %', state_count;
        END $$;
    """)


def downgrade() -> None:
    # =========================================================================
    # Downgrade: Remove backfilled states
    # 
    # WARNING: This removes states that were created by the backfill.
    # It identifies them by: repetition=0, ef=2.5, last_reviewed_at IS NULL
    # Be careful - this could also remove legitimately new states!
    # =========================================================================
    op.execute("""
        DELETE FROM public.states
        WHERE repetition = 0
          AND ef = 2.5
          AND last_reviewed_at IS NULL
          AND interval_days = 0;
    """)

