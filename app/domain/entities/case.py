"""Case aggregate root domain entity.

Distinct from app.schemas.case.CaseProfile (the Case Intake Agent's
output contract, embedded here as case_profile) and from
app.models.case.Case (the SQLAlchemy ORM row) — this is the framework-
free shape CaseRepository hands to services and agents.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas._common import CaseStatus
from app.schemas.case import CaseProfile
from app.schemas.language import SupportedLanguage


class Case(BaseModel):
    model_config = ConfigDict(frozen=False, from_attributes=True)

    id: UUID
    user_id: UUID
    status: CaseStatus
    title: str | None = None
    incident_category: str | None = None
    case_profile: CaseProfile | None = None
    preferred_language: SupportedLanguage = SupportedLanguage.EN
    stress_test_requested: bool = False
    awaiting_evidence_upload: bool = False
    evidence_pause_count: int = 0
    max_rounds: int = 3
    round_count: int = 0
    created_at: datetime
    updated_at: datetime
