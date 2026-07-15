"""Judge Agent output contract.
docs/architecture/08-pydantic-schemas.md §8.10."""

from __future__ import annotations

from pydantic import Field

from app.schemas._common import NyayaBaseModel


class JudgeOpinion(NyayaBaseModel):
    strengths: list[str]
    weaknesses: list[str]
    likely_outcome: str
    settlement_recommendation: str
    recommended_improvements: list[str]
    overall_case_rating: float = Field(ge=0.0, le=100.0)
