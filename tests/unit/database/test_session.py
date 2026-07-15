import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.database import session as session_module
from app.database.session import (
    get_db_session,
    get_engine,
    get_sessionmaker,
    reset_engine,
)


@pytest.fixture(autouse=True)
def _reset_engine_around_test():
    reset_engine()
    yield
    reset_engine()
    get_settings.cache_clear()


def test_get_engine_returns_process_wide_singleton() -> None:
    first = get_engine()
    second = get_engine()

    assert first is second


def test_reset_engine_forces_rebuild_on_next_call() -> None:
    first = get_engine()

    reset_engine()
    second = get_engine()

    assert first is not second


def test_get_engine_builds_dsn_from_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./should_never_be_created.db")
    get_settings.cache_clear()

    engine = get_engine()

    assert str(engine.url).startswith("sqlite+aiosqlite")


async def test_get_sessionmaker_with_explicit_engine_executes_query(sqlite_engine) -> None:
    session_factory = get_sessionmaker(engine=sqlite_engine)

    async with session_factory() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar_one() == 1


async def test_get_db_session_yields_one_working_session_then_stops(
    sqlite_engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(session_module, "_engine", sqlite_engine)

    generator = get_db_session()
    session = await anext(generator)

    result = await session.execute(text("SELECT 1"))
    assert result.scalar_one() == 1

    with pytest.raises(StopAsyncIteration):
        await anext(generator)
