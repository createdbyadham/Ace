"""Database Update - Add missing fields to users, decks, cards

Revision ID: 170c2c4e039f
Revises: 58878e87d96a
Create Date: 2025-12-05 19:48:35.482589

Adds:
- Users: last_seen_at, streak, xp, bio, location, deleted_at, updated_at
- Decks: visibility enum, description, tags, language, updated_at, deleted_at
- Cards: card_type enum, difficulty, updated_at, deleted_at
- Auto-update triggers for updated_at columns
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '170c2c4e039f'
down_revision: Union[str, None] = '58878e87d96a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # 1. Create ENUM types
    # =========================================================================
    op.execute("""
        CREATE TYPE deck_visibility AS ENUM ('private', 'unlisted', 'public');
        CREATE TYPE card_type AS ENUM ('basic', 'cloze');
    """)

    # =========================================================================
    # 2. Update public.users table
    # =========================================================================
    op.execute("""
        ALTER TABLE public.users
            ADD COLUMN last_seen_at TIMESTAMPTZ,
            ADD COLUMN streak INTEGER NOT NULL DEFAULT 0,
            ADD COLUMN xp BIGINT NOT NULL DEFAULT 0,
            ADD COLUMN bio TEXT,
            ADD COLUMN location TEXT,
            ADD COLUMN deleted_at TIMESTAMPTZ,
            ADD COLUMN updated_at TIMESTAMPTZ DEFAULT now();
    """)

    # =========================================================================
    # 3. Update public.decks table
    # =========================================================================
    op.execute("""
        ALTER TABLE public.decks
            ADD COLUMN visibility deck_visibility NOT NULL DEFAULT 'private',
            ADD COLUMN description TEXT,
            ADD COLUMN tags JSONB DEFAULT '[]'::jsonb,
            ADD COLUMN language TEXT,
            ADD COLUMN updated_at TIMESTAMPTZ DEFAULT now(),
            ADD COLUMN deleted_at TIMESTAMPTZ;
    """)

    # =========================================================================
    # 4. Update public.cards table
    # =========================================================================
    op.execute("""
        ALTER TABLE public.cards
            ADD COLUMN card_type card_type NOT NULL DEFAULT 'basic',
            ADD COLUMN difficulty SMALLINT CHECK (difficulty >= 0 AND difficulty <= 5),
            ADD COLUMN updated_at TIMESTAMPTZ DEFAULT now(),
            ADD COLUMN deleted_at TIMESTAMPTZ;
    """)

    # =========================================================================
    # 5. Create updated_at trigger function (reusable)
    # =========================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION public.update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # =========================================================================
    # 6. Create triggers for auto-updating updated_at
    # =========================================================================
    op.execute("""
        CREATE TRIGGER update_users_updated_at
            BEFORE UPDATE ON public.users
            FOR EACH ROW
            EXECUTE FUNCTION public.update_updated_at_column();

        CREATE TRIGGER update_decks_updated_at
            BEFORE UPDATE ON public.decks
            FOR EACH ROW
            EXECUTE FUNCTION public.update_updated_at_column();

        CREATE TRIGGER update_cards_updated_at
            BEFORE UPDATE ON public.cards
            FOR EACH ROW
            EXECUTE FUNCTION public.update_updated_at_column();

        CREATE TRIGGER update_states_updated_at
            BEFORE UPDATE ON public.states
            FOR EACH ROW
            EXECUTE FUNCTION public.update_updated_at_column();
    """)

    # =========================================================================
    # 7. Add useful indexes
    # =========================================================================
    op.execute("""
        -- Index for filtering by visibility (public decks discovery)
        CREATE INDEX idx_decks_visibility ON public.decks(visibility) WHERE deleted_at IS NULL;
        
        -- Index for soft-deleted records
        CREATE INDEX idx_users_deleted_at ON public.users(deleted_at) WHERE deleted_at IS NOT NULL;
        CREATE INDEX idx_decks_deleted_at ON public.decks(deleted_at) WHERE deleted_at IS NOT NULL;
        CREATE INDEX idx_cards_deleted_at ON public.cards(deleted_at) WHERE deleted_at IS NOT NULL;
        
        -- Index for card_type filtering
        CREATE INDEX idx_cards_card_type ON public.cards(card_type) WHERE deleted_at IS NULL;
        
        -- GIN index for deck tags (for searching by tags)
        CREATE INDEX idx_decks_tags ON public.decks USING GIN (tags) WHERE deleted_at IS NULL;
    """)


def downgrade() -> None:
    # Drop indexes
    op.execute("""
        DROP INDEX IF EXISTS idx_decks_visibility;
        DROP INDEX IF EXISTS idx_users_deleted_at;
        DROP INDEX IF EXISTS idx_decks_deleted_at;
        DROP INDEX IF EXISTS idx_cards_deleted_at;
        DROP INDEX IF EXISTS idx_cards_card_type;
        DROP INDEX IF EXISTS idx_decks_tags;
    """)

    # Drop triggers
    op.execute("""
        DROP TRIGGER IF EXISTS update_users_updated_at ON public.users;
        DROP TRIGGER IF EXISTS update_decks_updated_at ON public.decks;
        DROP TRIGGER IF EXISTS update_cards_updated_at ON public.cards;
        DROP TRIGGER IF EXISTS update_states_updated_at ON public.states;
    """)

    # Drop trigger function
    op.execute("""
        DROP FUNCTION IF EXISTS public.update_updated_at_column();
    """)

    # Remove columns from cards
    op.execute("""
        ALTER TABLE public.cards
            DROP COLUMN IF EXISTS card_type,
            DROP COLUMN IF EXISTS difficulty,
            DROP COLUMN IF EXISTS updated_at,
            DROP COLUMN IF EXISTS deleted_at;
    """)

    # Remove columns from decks
    op.execute("""
        ALTER TABLE public.decks
            DROP COLUMN IF EXISTS visibility,
            DROP COLUMN IF EXISTS description,
            DROP COLUMN IF EXISTS tags,
            DROP COLUMN IF EXISTS language,
            DROP COLUMN IF EXISTS updated_at,
            DROP COLUMN IF EXISTS deleted_at;
    """)

    # Remove columns from users
    op.execute("""
        ALTER TABLE public.users
            DROP COLUMN IF EXISTS last_seen_at,
            DROP COLUMN IF EXISTS streak,
            DROP COLUMN IF EXISTS xp,
            DROP COLUMN IF EXISTS bio,
            DROP COLUMN IF EXISTS location,
            DROP COLUMN IF EXISTS deleted_at,
            DROP COLUMN IF EXISTS updated_at;
    """)

    # Drop enum types
    op.execute("""
        DROP TYPE IF EXISTS card_type;
        DROP TYPE IF EXISTS deck_visibility;
    """)
