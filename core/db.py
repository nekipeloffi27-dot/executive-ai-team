"""asyncpg pool management."""
from __future__ import annotations
import asyncpg
from loguru import logger
from core.config import settings


_pool: asyncpg.Pool | None = None


def _to_asyncpg_dsn(url: str) -> str:
    """asyncpg doesn't accept the postgresql+asyncpg:// prefix."""
    return url.replace("postgresql+asyncpg://", "postgresql://")


async def init_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        dsn = _to_asyncpg_dsn(settings.database_url)
        _pool = await asyncpg.create_pool(
            dsn,
            min_size=2,
            max_size=10,
            command_timeout=60,
        )
        logger.info("DB pool created: {}", dsn.split("@")[-1])
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("DB pool closed")


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialized; call init_pool() first")
    return _pool
