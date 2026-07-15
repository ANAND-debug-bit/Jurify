"""Agent-layer exceptions (Module 10)."""

from __future__ import annotations


class AgentExecutionError(Exception):
    """Raised when an agent fails to produce valid structured output
    after exhausting retries (docs/architecture/03-langgraph-workflow.md
    §3.6) — the graph's error boundary catches this, logs it, and routes
    to the terminal Failed node rather than crashing the process."""
