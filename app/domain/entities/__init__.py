"""Framework-free domain entities (Module 7).

Distinct from app.schemas (agent input/output contracts, no identity) and
app.models (SQLAlchemy ORM rows) — these are the persisted-entity shapes
repositories hand to services and agents. Per docs/architecture/01-
architecture-overview.md §1.2, this package may depend on Pydantic and
the standard library only — never SQLAlchemy, FastAPI, or LangChain.
"""
