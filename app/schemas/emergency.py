"""Emergency Detection / Emergency Agent output contracts (NEW, Change 4).
docs/architecture/08-pydantic-schemas.md §8.12."""

from __future__ import annotations

from enum import StrEnum

from app.schemas._common import NyayaBaseModel, UrgencyLevel


class EmergencyCategory(StrEnum):
    DOMESTIC_VIOLENCE = "domestic_violence"
    CHILD_ABUSE = "child_abuse"
    ILLEGAL_DETENTION = "illegal_detention"
    HUMAN_TRAFFICKING = "human_trafficking"
    KIDNAPPING = "kidnapping"
    MEDICAL_EMERGENCY = "medical_emergency"
    IMMEDIATE_PHYSICAL_DANGER = "immediate_physical_danger"
    NONE = "none"


class EmergencyAssessment(NyayaBaseModel):
    is_emergency: bool
    category: EmergencyCategory
    severity: UrgencyLevel
    rationale: str


class HelplineInfo(NyayaBaseModel):
    name: str
    phone: str
    available: str  # e.g. "24x7"


class EmergencyGuidance(NyayaBaseModel):
    immediate_steps: list[str]
    evidence_preservation_checklist: list[str]
    helplines: list[HelplineInfo]
    recommended_authorities: list[str]
