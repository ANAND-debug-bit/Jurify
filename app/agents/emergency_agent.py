"""Emergency Agent (Module 11, Change 4).

Runs only when EmergencyDetectionAgent flagged is_emergency=true;
produces the actual guidance shown to the user immediately
(docs/architecture/03-langgraph-workflow.md §3.7).
"""

from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.graph.state import CaseState
from app.prompts.emergency_agent import build_emergency_agent_system_prompt
from app.schemas.emergency import EmergencyGuidance


class EmergencyAgent(BaseAgent[EmergencyGuidance]):
    name = "emergency_agent"
    output_schema = EmergencyGuidance

    def _system_prompt(self) -> str:
        return build_emergency_agent_system_prompt()

    def _build_user_content(self, state: CaseState, context: Any) -> str:
        assessment = state.get("emergency_assessment")
        if assessment is None:
            return "No emergency assessment available."
        return (
            f"category: {assessment.category.value}\n"
            f"severity: {assessment.severity.value}\n"
            f"rationale: {assessment.rationale}"
        )
