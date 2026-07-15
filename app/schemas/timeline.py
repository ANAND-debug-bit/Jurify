"""Case Reconstruction Agent output contract.
docs/architecture/08-pydantic-schemas.md §8.2."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas._common import NyayaBaseModel


class TimelineEvent(NyayaBaseModel):
    occurred_at: datetime | None = None
    description: str
    sequence_order: int
    is_inconsistent: bool = False
    inconsistency_note: str | None = None
    supporting_evidence_refs: list[str] = Field(default_factory=list)


class Timeline(NyayaBaseModel):
    events: list[TimelineEvent]
    inconsistencies: list[str] = Field(default_factory=list)
    reconstructed_summary: str
