from __future__ import annotations

import json
from typing import Optional
import ssl

import asyncpg

from core.config import settings


async def _setup_json_codec(conn: asyncpg.Connection) -> None:
    """Configure asyncpg to auto-encode/decode JSON and JSONB."""
    await conn.set_type_codec(
        'jsonb',
        encoder=json.dumps,
        decoder=json.loads,
        schema='pg_catalog'
    )
    await conn.set_type_codec(
        'json',
        encoder=json.dumps,
        decoder=json.loads,
        schema='pg_catalog'
    )


class DatabasePool:
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> asyncpg.Pool:
        if self._pool is None:
            # Supabase requires SSL
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            self._pool = await asyncpg.create_pool(
                user=settings.db_user,
                password=settings.db_password,
                host=settings.db_host,
                port=settings.db_port,
                database=settings.db_name,
                min_size=1,
                max_size=10,
                ssl=ssl_context,
                # Supabase uses PgBouncer which doesn't support prepared statements
                statement_cache_size=0,
                # Auto-setup JSON codec for every connection
                init=_setup_json_codec,
            )
        return self._pool

    async def disconnect(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    def get(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("Database pool has not been initialised.")
        return self._pool


database_pool = DatabasePool()


async def init_pool() -> asyncpg.Pool:
    return await database_pool.connect()


async def close_pool() -> None:
    await database_pool.disconnect()


def get_pool() -> asyncpg.Pool:
    return database_pool.get()


__all__ = ["database_pool", "get_pool", "init_pool", "close_pool"]

