"""auto profile-create through db trigger

Revision ID: 58878e87d96a
Revises: a40f8ffbfe39
Create Date: 2025-12-05 15:49:04.752550

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '58878e87d96a'
down_revision: Union[str, None] = 'a40f8ffbfe39'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create the trigger function
    op.execute("""
    CREATE OR REPLACE FUNCTION public.handle_new_user()
    RETURNS TRIGGER
    LANGUAGE plpgsql
    SECURITY DEFINER
    SET search_path = public
    AS $$
    DECLARE
        base_username TEXT;
        final_username TEXT;
        suffix TEXT;
    BEGIN
        -- Start with email prefix as base username
        base_username := COALESCE(
            SPLIT_PART(NEW.email, '@', 1),
            'user'
        );
        
        -- Add short UUID suffix to ensure uniqueness
        -- Format: emailprefix_a1b2c3d4
        suffix := SUBSTRING(REPLACE(NEW.id::text, '-', ''), 1, 8);
        final_username := base_username || '_' || suffix;
        
        INSERT INTO public.users (user_id, username, display_name)
        VALUES (
            NEW.id,
            final_username,
            base_username  -- Display name is just the email prefix (human readable)
        )
        ON CONFLICT (user_id) DO NOTHING;  -- Safety: don't fail if profile already exists
        
        RETURN NEW;
    END;
    $$;
    """)

    # Create the trigger on auth.users
    op.execute("""
    CREATE TRIGGER on_auth_user_created
        AFTER INSERT ON auth.users
        FOR EACH ROW
        EXECUTE FUNCTION public.handle_new_user();
    """)


def downgrade():
    # Drop trigger first
    op.execute("""
    DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
    """)
    
    # Drop function
    op.execute("""
    DROP FUNCTION IF EXISTS public.handle_new_user();
    """)
