"""Persisted government scheme match.

Not in the original 8-file domain/entities/ list — GovernmentSchemeRepository
(added in this module to match its SQLAlchemy implementation counterpart)
needs a typed, persisted-row return shape distinct from
app.schemas.government_scheme.GovernmentSchemeMatch (no id/case_id/
created_at)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.government_scheme import GovernmentScheme


class GovernmentSchemeMatch(BaseModel):
    model_config = ConfigDict(frozen=False, from_attributes=True)

    id: UUID
    case_id: UUID
    scheme: GovernmentScheme
    eligible: bool
    confidence: float | None = None
    documents_required: list[str] = Field(default_factory=list)
    how_to_apply: str | None = None
    relevant_authority: str | None = None
    created_at: datetime
