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
        new_username TEXT;
        new_display_name TEXT;
        fallback_suffix TEXT;
    BEGIN
        -- Get username from metadata (passed during signup)
        -- Fallback to email prefix + UUID suffix if not provided
        new_username := NEW.raw_user_meta_data->>'username';
        
        IF new_username IS NULL OR new_username = '' THEN
            -- Fallback: email prefix + short UUID for uniqueness
            fallback_suffix := SUBSTRING(REPLACE(NEW.id::text, '-', ''), 1, 8);
            new_username := COALESCE(SPLIT_PART(NEW.email, '@', 1), 'user') || '_' || fallback_suffix;
        END IF;
        
        -- Get display_name from metadata, fallback to username
        new_display_name := COALESCE(
            NULLIF(NEW.raw_user_meta_data->>'display_name', ''),
            new_username
        );
        
        INSERT INTO public.users (user_id, username, display_name)
        VALUES (
            NEW.id,
            new_username,
            new_display_name
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
