"""Persisted strategy option — versioned by created_at (see RiskScore)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Strategy(BaseModel):
    model_config = ConfigDict(frozen=False, from_attributes=True)

    id: UUID
    case_id: UUID
    forum: str
    estimated_cost: float | None = None
    estimated_time: str | None = None
    difficulty: str | None = None
    success_probability: float | None = None
    is_recommended: bool = False
    created_at: datetime
