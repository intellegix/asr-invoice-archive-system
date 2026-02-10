"""
ASR Production Server - Async Database Configuration
SQLAlchemy async engine and session management for audit trail persistence.
"""

import logging
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# Module-level state
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def _convert_database_url(url: str) -> str:
    """Convert sync database URLs to async driver equivalents."""
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


async def init_database(
    database_url: str,
    pool_size: int = 20,
    max_overflow: int = 30,
    pool_recycle: int = 3600,
) -> None:
    """Create async engine, session factory, and run table creation."""
    global _engine, _session_factory

    # Dispose previous engine if re-initializing (e.g. tests calling init_database multiple times)
    if _engine is not None:
        await _engine.dispose()

    async_url = _convert_database_url(database_url)
    is_sqlite = async_url.startswith("sqlite")

    # Ensure parent directory exists for SQLite file paths
    if is_sqlite and ":///" in async_url and ":memory:" not in async_url:
        db_path = async_url.split(":///", 1)[1]
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    engine_kwargs: dict = {"echo": False}
    if not is_sqlite:
        engine_kwargs.update(
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=pool_recycle,
        )

    _engine = create_async_engine(async_url, **engine_kwargs)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database engine initialized (%s)", "SQLite" if is_sqlite else "PostgreSQL")


async def close_database() -> None:
    """Dispose the async engine."""
    global _engine, _session_factory
    if _engine:
        await _engine.dispose()
        logger.info("Database engine disposed")
    _engine = None
    _session_factory = None


def get_async_session() -> AsyncSession:
    """Return a new AsyncSession. Raises RuntimeError if DB not initialized."""
    if _session_factory is None:
        raise RuntimeError("Database not initialized — call init_database() first")
    return _session_factory()
