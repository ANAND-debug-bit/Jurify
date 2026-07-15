"""Persisted risk score — versioned by created_at, never overwritten
(docs/architecture/04-database-design.md §4.2)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RiskScore(BaseModel):
    model_config = ConfigDict(frozen=False, from_attributes=True)

    id: UUID
    case_id: UUID
    financial_risk: float | None = None
    criminal_risk: float | None = None
    urgency_level: str | None = None
    needs_police: bool = False
    needs_lawyer: bool = False
    needs_medical: bool = False
    settlement_probability: float | None = None
    case_strength: float | None = None
    rationale: str | None = None
    created_at: datetime
