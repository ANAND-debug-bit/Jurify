"""Shared column type helpers for ORM models (Module 5).

Both variants follow the same pattern (docs/architecture/04-database-
design.md §4.2, §11.3): the *documented, intended* type is used on
Postgres (production); a portable fallback is used on any other dialect
(SQLite in this project's tests) via with_variant — so the same model
file is both correct for production and testable without a live
Postgres instance.
"""

from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON
from sqlalchemy.dialects import postgresql

JSONBType = JSON().with_variant(postgresql.JSONB(), "postgresql")

# Matches EMBEDDING_MODEL=nomic-embed-text's default output dimension
# (app.core.config.LLMSettings.embedding_model) — revisit via migration
# if the embedding model changes.
EMBEDDING_DIMENSIONS = 768

VectorType = Vector(EMBEDDING_DIMENSIONS).with_variant(JSON(), "sqlite")
