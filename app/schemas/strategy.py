"""Legal Strategy Agent output contract.
docs/architecture/08-pydantic-schemas.md §8.6."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from app.schemas._common import NyayaBaseModel


class ForumType(StrEnum):
    POLICE_COMPLAINT = "police_complaint"
    CONSUMER_COURT = "consumer_court"
    CIVIL_COURT = "civil_court"
    CRIMINAL_COMPLAINT = "criminal_complaint"
    RTI = "rti"
    CYBER_CELL = "cyber_cell"
    WOMEN_CELL = "women_cell"
    LOK_ADALAT = "lok_adalat"


class StrategyOption(NyayaBaseModel):
    forum: ForumType
    description: str
    estimated_cost_inr: float
    estimated_time: str  # "2-4 weeks"
    difficulty: str  # "low" | "medium" | "high"
    success_probability: float = Field(ge=0.0, le=100.0)
    required_specialization: str | None = None  # feeds Lawyer Recommendation Agent


class StrategyPlan(NyayaBaseModel):
    options: list[StrategyOption]
    recommended_option_index: int
    reasoning: str
