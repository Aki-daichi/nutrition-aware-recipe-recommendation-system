import asyncpg


async def get_pool(app) -> asyncpg.pool.Pool:
    if not hasattr(app.state, "pool") or app.state.pool is None:
        raise RuntimeError("Database pool not initialized")
    return app.state.pool


async def create_pool(database_url: str) -> asyncpg.pool.Pool:
    return await asyncpg.create_pool(dsn=database_url, min_size=1, max_size=10)


async def close_pool(app) -> None:
    pool = getattr(app.state, "pool", None)
    if pool is not None:
        await pool.close()

