"""Pydantic v2 DTOs — the canonical contracts every agent output, the
LangGraph state, and the API layer are built from
(docs/architecture/08-pydantic-schemas.md). Each module here is
independently importable; there is no import-everything side effect to
rely on (unlike app.models, schemas don't need shared metadata
registration).
"""
