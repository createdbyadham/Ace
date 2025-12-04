"""Initial schema - users, decks, cards, spaced repetition

Revision ID: 001
Revises: 
Create Date: 2024-12-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create schemas
    op.execute("CREATE SCHEMA IF NOT EXISTS app")
    op.execute("CREATE SCHEMA IF NOT EXISTS sr")

    # users
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id UUID PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            display_name TEXT,
            avatar_url TEXT,
            created_at TIMESTAMPTZ DEFAULT now()
        )
    """)

    # decks
    op.execute("""
        CREATE TABLE IF NOT EXISTS decks (
            deck_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now()
        )
    """)

    # cards
    op.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            card_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            deck_id UUID REFERENCES decks(deck_id) ON DELETE CASCADE,
            owner_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            content JSONB NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_cards_deck ON cards(deck_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_cards_owner ON cards(owner_id)")

    # sr.states
    op.execute("""
        CREATE TABLE IF NOT EXISTS sr.states (
            state_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            card_id UUID NOT NULL REFERENCES cards(card_id) ON DELETE CASCADE,
            repetition INT DEFAULT 0,
            interval_days INT DEFAULT 0,
            next_review_at TIMESTAMPTZ DEFAULT now(),
            last_reviewed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now(),
            UNIQUE (user_id, card_id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_sr_user_next ON sr.states(user_id, next_review_at)")

    # sr.reviews
    op.execute("""
        CREATE TABLE IF NOT EXISTS sr.reviews (
            review_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(user_id),
            card_id UUID NOT NULL REFERENCES cards(card_id),
            response TEXT NOT NULL,
            elapsed_ms INT,
            created_at TIMESTAMPTZ DEFAULT now(),
            metadata JSONB DEFAULT '{}'::jsonb
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_reviews_user ON sr.reviews(user_id, created_at)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS sr.reviews")
    op.execute("DROP TABLE IF EXISTS sr.states")
    op.execute("DROP TABLE IF EXISTS cards")
    op.execute("DROP TABLE IF EXISTS decks")
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP SCHEMA IF EXISTS sr")
    op.execute("DROP SCHEMA IF EXISTS app")

