from collections.abc import AsyncIterator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import StaticPool


@pytest.fixture
async def sqlite_engine() -> AsyncIterator[AsyncEngine]:
    """A fresh in-memory SQLite database per test, standing in for Postgres
    where these tests only need real async engine/session/transaction
    behavior — StaticPool keeps all connections in the engine's pool
    pointed at the same in-memory database (the default pool would give
    each connection its own separate :memory: database)."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.execute(text("CREATE TABLE widgets (id INTEGER PRIMARY KEY, name TEXT)"))
    yield engine
    await engine.dispose()
