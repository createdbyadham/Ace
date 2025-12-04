from __future__ import annotations

from typing import Optional
import ssl

import asyncpg

from core.config import settings


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
                ssl=ssl_context
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

