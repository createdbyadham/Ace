# setup_db.py
import os
import asyncio
from pathlib import Path

import asyncpg

DEFAULT_DATABASE_URL = "postgresql://postgres:1357997531@localhost:5432/flash"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
SCHEMA_SQL = Path(__file__).with_name("schema.sql").read_text()


async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(SCHEMA_SQL)
        print("Schema applied successfully.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())