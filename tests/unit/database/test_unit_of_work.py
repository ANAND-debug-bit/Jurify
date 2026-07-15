import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.database.unit_of_work import UnitOfWork


async def test_commit_on_clean_exit_persists_changes(sqlite_engine) -> None:
    session_factory = async_sessionmaker(sqlite_engine, expire_on_commit=False)

    async with UnitOfWork(session_factory) as uow:
        await uow.session.execute(text("INSERT INTO widgets (id, name) VALUES (1, 'gear')"))

    async with session_factory() as verify_session:
        result = await verify_session.execute(text("SELECT name FROM widgets WHERE id = 1"))
        assert result.scalar_one() == "gear"


async def test_exception_inside_block_rolls_back_changes(sqlite_engine) -> None:
    session_factory = async_sessionmaker(sqlite_engine, expire_on_commit=False)

    with pytest.raises(ValueError, match="boom"):
        async with UnitOfWork(session_factory) as uow:
            await uow.session.execute(
                text("INSERT INTO widgets (id, name) VALUES (2, 'sprocket')")
            )
            raise ValueError("boom")

    async with session_factory() as verify_session:
        result = await verify_session.execute(
            text("SELECT COUNT(*) FROM widgets WHERE id = 2")
        )
        assert result.scalar_one() == 0


async def test_explicit_commit_method_persists_changes(sqlite_engine) -> None:
    session_factory = async_sessionmaker(sqlite_engine, expire_on_commit=False)

    async with UnitOfWork(session_factory) as uow:
        await uow.session.execute(text("INSERT INTO widgets (id, name) VALUES (3, 'cog')"))
        await uow.commit()

    async with session_factory() as verify_session:
        result = await verify_session.execute(
            text("SELECT COUNT(*) FROM widgets WHERE id = 3")
        )
        assert result.scalar_one() == 1


async def test_explicit_rollback_method_discards_pending_changes(sqlite_engine) -> None:
    session_factory = async_sessionmaker(sqlite_engine, expire_on_commit=False)

    async with UnitOfWork(session_factory) as uow:
        await uow.session.execute(text("INSERT INTO widgets (id, name) VALUES (4, 'bolt')"))
        await uow.rollback()

    async with session_factory() as verify_session:
        result = await verify_session.execute(
            text("SELECT COUNT(*) FROM widgets WHERE id = 4")
        )
        assert result.scalar_one() == 0


def test_session_property_raises_before_context_entered(sqlite_engine) -> None:
    session_factory = async_sessionmaker(sqlite_engine, expire_on_commit=False)
    uow = UnitOfWork(session_factory)

    with pytest.raises(RuntimeError, match="outside of an 'async with' block"):
        _ = uow.session


async def test_session_property_raises_again_after_context_exits(sqlite_engine) -> None:
    session_factory = async_sessionmaker(sqlite_engine, expire_on_commit=False)
    uow = UnitOfWork(session_factory)

    async with uow:
        pass

    with pytest.raises(RuntimeError, match="outside of an 'async with' block"):
        _ = uow.session


def test_default_construction_does_not_connect() -> None:
    # No session_factory passed -> lazily built from process settings; this
    # must not raise or attempt a connection merely by constructing it.
    uow = UnitOfWork()
    assert uow._session_factory is not None
