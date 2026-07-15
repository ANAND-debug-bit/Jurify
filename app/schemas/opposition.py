"""Opposition Lawyer / Counter Strategy Agent output contracts.
docs/architecture/08-pydantic-schemas.md §8.9."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from app.schemas._common import NyayaBaseModel, UrgencyLevel


class ObjectionCategory(StrEnum):
    EVIDENCE = "evidence"
    TIMELINE = "timeline"
    WITNESS = "witness"
    CREDIBILITY = "credibility"
    JURISDICTION = "jurisdiction"
    LIMITATION = "limitation"


class Objection(NyayaBaseModel):
    category: ObjectionCategory
    argument: str
    severity: UrgencyLevel


class OppositionReport(NyayaBaseModel):
    round_number: int
    objections: list[Objection]


class Rebuttal(NyayaBaseModel):
    responds_to_category: ObjectionCategory
    argument: str
    additional_evidence_needed: str | None = None


class CounterReport(NyayaBaseModel):
    round_number: int
    rebuttals: list[Rebuttal]
    unresolved_objections: list[Objection] = Field(default_factory=list)


class OppositionRound(NyayaBaseModel):
    round_number: int
    role: str  # "opposition" | "counter"
    content: OppositionReport | CounterReport
