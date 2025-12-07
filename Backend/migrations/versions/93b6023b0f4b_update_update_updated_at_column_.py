"""update update_updated_at_column function with search_path and security definer

Revision ID: 93b6023b0f4b
Revises: 3b2c4d5e6f7a
Create Date: 2025-12-06 15:27:53.543344

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '93b6023b0f4b'
down_revision: Union[str, None] = '3b2c4d5e6f7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Replace the function with secure version
    op.execute("""
    CREATE OR REPLACE FUNCTION public.update_updated_at_column()
    RETURNS trigger
    LANGUAGE plpgsql
    SECURITY DEFINER
    SET search_path = public
    AS $$
    BEGIN
        NEW.updated_at := NOW();
        RETURN NEW;
    END;
    $$;
    """)


def downgrade() -> None:
    # Optional: replace with previous version (without search_path / security definer)
    op.execute("""
    CREATE OR REPLACE FUNCTION public.update_updated_at_column()
    RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    BEGIN
        NEW.updated_at := NOW();
        RETURN NEW;
    END;
    $$;
    """)

