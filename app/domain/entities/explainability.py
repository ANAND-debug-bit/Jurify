"""Persisted explainability item — one row per ExplainabilityItem in an
agent's ExplainabilityReport (docs/architecture/08-pydantic-schemas.md
§8.15); the report itself is just `items: list[ExplainabilityItem]`, so
the persisted shape is per-item, matching how Strategy rows relate to
StrategyOption.

Not in the original 8-file domain/entities/ list — added here (Module 8)
because ExplainabilityService needs a typed, persisted-row return shape,
and — like timeline/risk/strategy/document/opposition — explainability
reports have no dedicated repository of their own; CaseRepository owns
them as another Case-aggregate child collection.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ExplainabilityItem(BaseModel):
    model_config = ConfigDict(frozen=False, from_attributes=True)

    id: UUID
    case_id: UUID
    conclusion: str | None = None
    reasoning: str | None = None
    supporting_evidence_refs: list[str] | None = None
    supporting_legal_refs: list[str] | None = None
    confidence_score: float | None = None
    missing_information: list[str] | None = None
    created_at: datetime
