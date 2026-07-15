"""Postgres-backed LangGraph checkpointer (Module 9).

This is what makes the interactive intake loop and the adaptive
evidence-collection pause possible without a long-lived process
(docs/architecture/03-langgraph-workflow.md §3.8): CaseState is
persisted after every node under `thread_id = case_id`, so any API
replica can resume any case from its last checkpoint.

`AsyncPostgresSaver.from_conn_string(...)` is an async context manager
that does not connect until entered — get_checkpointer() is therefore
lazy in the same sense as app.database.session.get_engine(), safe to
call without a live database.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.config import Settings


def to_psycopg_dsn(sqlalchemy_async_dsn: str) -> str:
    """Convert our SQLAlchemy-style DSN (postgresql+asyncpg://...) to the
    plain postgresql://... form psycopg (used by AsyncPostgresSaver)
    expects — the two DB layers use different drivers for the same
    underlying Postgres instance, so this is a pure string transform,
    not a second source of connection truth."""
    if "+asyncpg" in sqlalchemy_async_dsn:
        return sqlalchemy_async_dsn.replace("postgresql+asyncpg://", "postgresql://", 1)
    return sqlalchemy_async_dsn


@asynccontextmanager
async def get_checkpointer(settings: Settings) -> AsyncIterator[AsyncPostgresSaver]:
    """`async with get_checkpointer(settings) as checkpointer:` — runs
    .setup() once per connection to ensure the checkpoint tables exist,
    then yields a saver ready to pass to `graph.compile(checkpointer=...)`.
    """
    conn_string = to_psycopg_dsn(settings.database.async_dsn)
    async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
        await checkpointer.setup()
        yield checkpointer
