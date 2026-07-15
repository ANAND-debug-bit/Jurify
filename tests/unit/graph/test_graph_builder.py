from __future__ import annotations

from uuid import uuid4

from langgraph.graph import END

from app.graph.graph_builder import build_graph
from app.graph.state import CaseState, create_initial_state


def test_build_graph_returns_state_graph_with_case_state_schema() -> None:
    builder = build_graph()

    assert CaseState in builder.schemas


def test_build_graph_starts_with_no_nodes() -> None:
    # Module 9's scope is explicitly an empty skeleton — nodes arrive
    # incrementally starting with Module 10 (Supervisor).
    builder = build_graph()

    assert builder.nodes == {}


async def test_skeleton_can_be_extended_and_compiled_by_a_later_module() -> None:
    """Smoke test proving the skeleton is soundly wired for later modules
    to build on — adds a throwaway node purely for this test; production
    graph_builder.py adds none yet."""
    builder = build_graph()
    builder.add_node("noop", lambda state: {})
    builder.set_entry_point("noop")
    builder.add_edge("noop", END)

    graph = builder.compile()

    case_id = uuid4()
    initial = create_initial_state(case_id, uuid4())
    result = await graph.ainvoke(initial)

    assert result["case_id"] == case_id
