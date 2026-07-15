"""Case Intake Agent output contract.
docs/architecture/08-pydantic-schemas.md §8.1."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas._common import NyayaBaseModel


class PartyInfo(NyayaBaseModel):
    role: str  # "complainant" | "respondent" | "witness"
    name: str | None = None
    relationship_to_user: str | None = None


class CaseProfile(NyayaBaseModel):
    incident_category: str  # e.g. "consumer_dispute", "motor_vehicle_accident"
    summary: str
    incident_date: datetime | None = None
    location: str | None = None
    parties: list[PartyInfo] = Field(default_factory=list)
    facts_collected: dict[str, str] = Field(default_factory=dict)
    evidence_mentioned: list[str] = Field(default_factory=list)
    user_goal: str | None = None  # what the user wants: compensation, criminal action, etc.
    missing_fields: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
