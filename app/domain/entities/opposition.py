"""Persisted opposition/counter round.

Distinct from app.schemas.opposition.OppositionRound (whose `content`
field is the discriminated OppositionReport | CounterReport union) —
here `content` is the raw persisted JSON shape; callers are responsible
for parsing it back into the typed union when needed.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OppositionRound(BaseModel):
    model_config = ConfigDict(frozen=False, from_attributes=True)

    id: UUID
    case_id: UUID
    round_number: int
    role: str  # "opposition" | "counter"
    content: dict[str, Any]
    created_at: datetime
