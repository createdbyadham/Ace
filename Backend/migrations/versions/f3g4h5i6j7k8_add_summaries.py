"""Add summaries table

Revision ID: f3g4h5i6j7k8
Revises: d2e3f4g5h6i7
Create Date: 2025-12-17

Adds:
- summaries table for AI-generated summaries from lecture PDFs
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3g4h5i6j7k8'
down_revision: Union[str, None] = 'd2e3f4g5h6i7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create summaries table
    op.execute("""
        CREATE TABLE IF NOT EXISTS public.summaries (
            summary_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            key_points TEXT[] NOT NULL DEFAULT '{}',
            source_files TEXT[] NOT NULL DEFAULT '{}',
            word_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now(),
            deleted_at TIMESTAMPTZ
        );
        
        -- Index for user's summaries
        CREATE INDEX IF NOT EXISTS idx_summaries_owner 
            ON public.summaries (owner_id, created_at DESC)
            WHERE deleted_at IS NULL;
            
        -- Index for full-text search on title and content
        CREATE INDEX IF NOT EXISTS idx_summaries_search 
            ON public.summaries 
            USING gin(to_tsvector('english', title || ' ' || content))
            WHERE deleted_at IS NULL;
    """)
    
    # Add updated_at trigger
    op.execute("""
        CREATE OR REPLACE TRIGGER update_summaries_updated_at
            BEFORE UPDATE ON public.summaries
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS update_summaries_updated_at ON public.summaries")
    op.execute("DROP TABLE IF EXISTS public.summaries")

