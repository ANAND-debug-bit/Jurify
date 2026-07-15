"""Application services — one per bounded context (Module 8).

Each service depends only on domain repository interfaces (Module 7) —
no agent orchestrator exists yet (LangGraph lands in Module 9, agents in
Modules 10+), so every method here is exactly what's expressible in
terms of persistence and the documented business rules alone. Triggering
the agent that PRODUCES the data a service persists is added as a thin
addition when that agent's own module lands — see each service's
docstring for which module that is.

dashboard_service.py is intentionally not part of this module — it is
explicitly scheduled as Module 23 in docs/architecture/14-testing-and-
implementation-plan.md §14.3, since its read-model shape depends on
every content-producing agent existing first.
"""
