from __future__ import annotations

from uuid import uuid4

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, StateGraph

from app.core.config import Settings
from app.graph.checkpointer import get_checkpointer, to_psycopg_dsn
from app.graph.state import CaseState, create_initial_state


def test_to_psycopg_dsn_strips_asyncpg_suffix() -> None:
    result = to_psycopg_dsn("postgresql+asyncpg://nyaya:secret@localhost:5432/nyayaos")

    assert result == "postgresql://nyaya:secret@localhost:5432/nyayaos"


def test_to_psycopg_dsn_passthrough_for_plain_postgres_urls() -> None:
    dsn = "postgresql://nyaya:secret@localhost:5432/nyayaos"

    assert to_psycopg_dsn(dsn) == dsn


def test_get_checkpointer_does_not_connect_until_entered() -> None:
    # AsyncPostgresSaver.from_conn_string is an @asynccontextmanager —
    # calling get_checkpointer() must not attempt a connection (there is
    # no live Postgres in this environment); only `async with` would.
    settings = Settings()

    context_manager = get_checkpointer(settings)

    assert hasattr(context_manager, "__aenter__")
    assert hasattr(context_manager, "__aexit__")


async def test_compiled_graph_with_checkpointer_persists_state_by_thread_id() -> None:
    """Proves the general LangGraph checkpointing pattern this module
    wires up actually works: CaseState as the schema, a compiled graph,
    and state retrievable via thread_id after a run — the exact mechanism
    docs/architecture/03-langgraph-workflow.md §3.5/§3.8 describe. Uses
    AsyncSqliteSaver as a stand-in for AsyncPostgresSaver (no live
    Postgres in this environment) — both implement the same
    BaseCheckpointSaver interface that graph.compile(checkpointer=...)
    depends on, so this validates the pattern get_checkpointer() plugs
    into, not a claim that SQLite is used in production.
    """
    async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
        builder = StateGraph(CaseState)
        builder.add_node(
            "bump_round", lambda state: {"round_count": state["round_count"] + 1}
        )
        builder.set_entry_point("bump_round")
        builder.add_edge("bump_round", END)
        graph = builder.compile(checkpointer=checkpointer)

        case_id = uuid4()
        user_id = uuid4()
        config: RunnableConfig = {"configurable": {"thread_id": str(case_id)}}
        initial = create_initial_state(case_id, user_id)

        result = await graph.ainvoke(initial, config=config)
        assert result["round_count"] == 1

        snapshot = await graph.aget_state(config)
        assert snapshot.values["round_count"] == 1
        assert snapshot.values["case_id"] == case_id
        assert snapshot.values["user_id"] == user_id
