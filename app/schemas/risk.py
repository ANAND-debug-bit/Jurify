"""Risk Assessment Agent output contract.
docs/architecture/08-pydantic-schemas.md §8.5."""

from __future__ import annotations

from pydantic import Field

from app.schemas._common import NyayaBaseModel, UrgencyLevel


class RiskAssessment(NyayaBaseModel):
    financial_risk: float = Field(ge=0.0, le=100.0)
    criminal_risk: float = Field(ge=0.0, le=100.0)
    urgency: UrgencyLevel
    needs_police: bool
    needs_lawyer: bool
    needs_medical: bool
    settlement_probability: float = Field(ge=0.0, le=100.0)
    case_strength: float = Field(ge=0.0, le=100.0)
    rationale: str
