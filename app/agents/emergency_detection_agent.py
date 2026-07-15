"""Emergency Detection Agent (Module 11, Change 4).

Runs on every intake turn, screening only the latest user message
against a fixed category list — narrow scope by design so it stays cheap
enough to run unconditionally (docs/architecture/02-agent-architecture.md
§2.5).
"""

from __future__ import annotations

from typing import Any

from app.agents._message_utils import latest_human_message
from app.agents.base import BaseAgent
from app.graph.state import CaseState
from app.prompts.emergency_detection import build_emergency_detection_system_prompt
from app.schemas.emergency import EmergencyAssessment


class EmergencyDetectionAgent(BaseAgent[EmergencyAssessment]):
    name = "emergency_detection"
    output_schema = EmergencyAssessment

    def _system_prompt(self) -> str:
        return build_emergency_detection_system_prompt()

    def _build_user_content(self, state: CaseState, context: Any) -> str:
        message = latest_human_message(state.get("messages") or [])
        return f"Latest user message:\n{message or '(empty)'}"
