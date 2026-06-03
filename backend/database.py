import asyncpg
from typing import Optional


async def get_pool(app) -> asyncpg.pool.Pool:
    pool = getattr(app.state, "db_pool", None)
    if pool is None:
        raise RuntimeError("Database pool not initialized")
    return pool


async def create_pool(database_url: str) -> asyncpg.pool.Pool:
    return await asyncpg.create_pool(dsn=database_url, min_size=1, max_size=10)


async def close_pool(app) -> None:
    pool: Optional[asyncpg.pool.Pool] = getattr(app.state, "db_pool", None)
    if pool is not None:
        await pool.close()

