"""Database Update for SR

Revision ID: 44c0ba00cbba
Revises: 2a1b3c4d5e6f
Create Date: 2025-12-05 22:30:40.341267

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '44c0ba00cbba'
down_revision: Union[str, None] = '170c2c4e039f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # 1A: Add indexes for optimized SR queries
    # =========================================================================
    op.execute("""
        -- Primary index for fetching due cards per user, ordered by next_review_at
        CREATE INDEX IF NOT EXISTS idx_states_user_next 
            ON public.states (user_id, next_review_at)
            WHERE next_review_at IS NOT NULL;

        -- Index for card->deck joins in due card queries
        CREATE INDEX IF NOT EXISTS idx_cards_deck_id 
            ON public.cards (deck_id)
            WHERE deleted_at IS NULL;
            
        -- Index for deck-specific card listing
        CREATE INDEX IF NOT EXISTS idx_cards_owner_deck 
            ON public.cards (owner_id, deck_id)
            WHERE deleted_at IS NULL;
    """)

    # =========================================================================
    # 1C: Add columns to reviews table
    # =========================================================================
    op.execute("""
        ALTER TABLE public.reviews
            ADD COLUMN IF NOT EXISTS quality SMALLINT,
            ADD COLUMN IF NOT EXISTS device_id UUID,
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();
            
        -- Index for querying reviews by user/card/date (audit trail)
        CREATE INDEX IF NOT EXISTS idx_reviews_user_card_date 
            ON public.reviews (user_id, card_id, created_at DESC);
    """)

    # =========================================================================
    # Add EF (easiness factor) and version to states for proper SM-2
    # =========================================================================
    op.execute("""
        ALTER TABLE public.states
            ADD COLUMN IF NOT EXISTS ef NUMERIC(4,2) DEFAULT 2.5,
            ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;
            
        -- Ensure EF stays within valid range (1.3 to 5.0)
        ALTER TABLE public.states
            ADD CONSTRAINT states_ef_range CHECK (ef >= 1.3 AND ef <= 5.0);
    """)

    # =========================================================================
    # Add unique constraint on (user_id, card_id) for states
    # This enables proper UPSERT and prevents duplicate state rows
    # =========================================================================
    op.execute("""
        -- First, remove any duplicates (keep the most recent one)
        DELETE FROM public.states s1
        USING public.states s2
        WHERE s1.user_id = s2.user_id 
          AND s1.card_id = s2.card_id 
          AND s1.updated_at < s2.updated_at;

        -- Now add the unique constraint
        ALTER TABLE public.states
            DROP CONSTRAINT IF EXISTS states_user_card_unique;
        ALTER TABLE public.states
            ADD CONSTRAINT states_user_card_unique UNIQUE (user_id, card_id);
    """)

    # =========================================================================
    # Create response_type enum for type safety
    # =========================================================================
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE response_type AS ENUM ('forgot', 'meh', 'got_it');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # =========================================================================
    # Add updated_at trigger to reviews
    # =========================================================================
    op.execute("""
        DROP TRIGGER IF EXISTS update_reviews_updated_at ON public.reviews;
        CREATE TRIGGER update_reviews_updated_at
            BEFORE UPDATE ON public.reviews
            FOR EACH ROW
            EXECUTE FUNCTION public.update_updated_at_column();
    """)


def downgrade() -> None:
    # Drop trigger
    op.execute("""
        DROP TRIGGER IF EXISTS update_reviews_updated_at ON public.reviews;
    """)

    # Drop enum
    op.execute("""
        DROP TYPE IF EXISTS response_type;
    """)

    # Remove unique constraint from states
    op.execute("""
        ALTER TABLE public.states DROP CONSTRAINT IF EXISTS states_user_card_unique;
    """)

    # Remove columns from states
    op.execute("""
        ALTER TABLE public.states DROP CONSTRAINT IF EXISTS states_ef_range;
        ALTER TABLE public.states DROP COLUMN IF EXISTS ef;
        ALTER TABLE public.states DROP COLUMN IF EXISTS version;
    """)

    # Remove columns and index from reviews
    op.execute("""
        DROP INDEX IF EXISTS idx_reviews_user_card_date;
        ALTER TABLE public.reviews DROP COLUMN IF EXISTS quality;
        ALTER TABLE public.reviews DROP COLUMN IF EXISTS device_id;
        ALTER TABLE public.reviews DROP COLUMN IF EXISTS updated_at;
    """)

    # Drop indexes
    op.execute("""
        DROP INDEX IF EXISTS idx_states_user_next;
        DROP INDEX IF EXISTS idx_cards_deck_id;
        DROP INDEX IF EXISTS idx_cards_owner_deck;
    """)



