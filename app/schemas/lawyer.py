"""Lawyer Recommendation Agent output contract.
docs/architecture/08-pydantic-schemas.md §8.8."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from app.schemas._common import NyayaBaseModel


class LawyerProfile(NyayaBaseModel):
    id: UUID
    full_name: str
    specialization: str
    city: str
    languages: list[str]
    fee_range_inr: tuple[float, float]
    rating: float = Field(ge=0.0, le=5.0)
    years_experience: int


class LawyerMatch(NyayaBaseModel):
    lawyer: LawyerProfile
    match_score: float = Field(ge=0.0, le=100.0)
    match_reason: str
