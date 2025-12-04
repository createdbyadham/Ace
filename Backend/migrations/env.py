import asyncio
import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv

load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_url() -> str:
    """Build database URL from env vars or use default."""
    user = os.getenv("user", "postgres")
    password = os.getenv("password", "1357997531")
    host = os.getenv("host", "localhost")
    port = os.getenv("port", "5432")
    dbname = os.getenv("dbname", "flash")
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generates SQL script)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=None,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (executes against database)."""
    from sqlalchemy import create_engine, pool

    url = get_url()
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=None)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

