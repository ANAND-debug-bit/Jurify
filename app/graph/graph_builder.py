"""build_graph() skeleton (Module 9).

No nodes or edges are added yet. Each pipeline module (10: Supervisor,
11: Intake, 12: Research, ... 22: Judge) adds its own node(s) —
via graph.add_node(...) — and wires the edges documented in
docs/architecture/03-langgraph-workflow.md §3.3 as it lands, per
docs/architecture/14-testing-and-implementation-plan.md §14.3. This file
exists now so CaseState (Module 9) and the checkpointer (Module 9) are
both established before any node depends on them, and so later modules
extend one shared StateGraph builder rather than each inventing their
own.

The opt-in stress-test subgraph (stress_test_graph_builder.py,
docs/architecture/03-langgraph-workflow.md §3.4) is a separate, later
addition — Module 21's job, once Opposition/Counter/Judge exist.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import StateGraph

from app.graph.state import CaseState


def build_graph() -> StateGraph[CaseState, Any, Any, Any]:
    """Returns the graph builder with its state schema set. Deliberately
    NOT compiled here — an uncompiled StateGraph with zero nodes has no
    valid entry point, and compilation (graph.compile(checkpointer=...))
    is the last step, done once the full node/edge set exists."""
    return StateGraph(CaseState)
