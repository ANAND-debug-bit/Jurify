"""Persisted emergency assessment.

Not in docs/architecture/06-folder-structure.md's original 8-file
domain/entities/ list, but EmergencyRepository (added in this module to
match its SQLAlchemy implementation counterpart) needs a typed,
persisted-row return shape distinct from
app.schemas.emergency.EmergencyAssessment (which has no id/case_id/
created_at). Combines both the Emergency Detection Agent's assessment
(is_emergency..rationale) and the Emergency Agent's guidance
(immediate_steps..recommended_authorities) — see
app.models.emergency_assessment for why one table holds both."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas._common import UrgencyLevel
from app.schemas.emergency import EmergencyCategory


class EmergencyAssessment(BaseModel):
    model_config = ConfigDict(frozen=False, from_attributes=True)

    id: UUID
    case_id: UUID
    is_emergency: bool
    category: EmergencyCategory
    severity: UrgencyLevel
    rationale: str | None = None
    # None until the Emergency Agent's guidance is recorded on this same
    # row (only happens when is_emergency is true) — see
    # app.models.emergency_assessment for why guidance lives here.
    immediate_steps: list[str] | None = None
    evidence_preservation_checklist: list[str] | None = None
    helplines: list[dict[str, str]] | None = None
    recommended_authorities: list[str] | None = None
    created_at: datetime
