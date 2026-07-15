"""Persisted case timeline event.

Distinct from app.schemas.timeline.TimelineEvent (the Case
Reconstruction Agent's output, no id/case_id) — this is the persisted row.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CaseTimelineEvent(BaseModel):
    model_config = ConfigDict(frozen=False, from_attributes=True)

    id: UUID
    case_id: UUID
    occurred_at: datetime | None = None
    description: str
    is_inconsistent: bool = False
    inconsistency_note: str | None = None
    sequence_order: int
