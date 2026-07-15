"""Async SQLAlchemy engine/session factory (Module 4).

One engine per process (built lazily, cached in a module global — not via
functools.lru_cache, since Settings instances aren't hashable). One
AsyncSession per request/task, never a module-level session shared across
requests — sharing a session across concurrent requests would violate
AsyncSession's single-task-at-a-time contract (ADR-7, async everywhere).

get_engine()/get_sessionmaker() accept an optional override so callers
(tests, or a future non-Postgres deployment) can point at a different
engine without touching the process-wide singleton.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Process-wide cached engine, built from the cached Settings' DSN."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(settings.database.async_dsn, pool_pre_ping=True)
    return _engine


def reset_engine() -> None:
    """Drop the cached engine so the next get_engine() call rebuilds it
    from current Settings. Intended for tests only."""
    global _engine
    _engine = None


def get_sessionmaker(
    engine: AsyncEngine | None = None,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine or get_engine(), expire_on_commit=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: `Depends(get_db_session)`. Yields one session
    per request; the session is closed automatically when the request
    ends, whether it succeeded or raised."""
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        yield session
