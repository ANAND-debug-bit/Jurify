"""Case Intake Agent (Module 11).

Reads the full conversation so far (state.messages) plus any partial
CaseProfile already accumulated, and produces an updated CaseProfile —
the one agent whose job is turning free-form narrative into structured
facts (docs/architecture/02-agent-architecture.md §2.2.2).
"""

from __future__ import annotations

from typing import Any

from app.agents._message_utils import render_conversation
from app.agents.base import BaseAgent
from app.graph.state import CaseState
from app.prompts.case_intake import build_case_intake_system_prompt
from app.schemas.case import CaseProfile


class CaseIntakeAgent(BaseAgent[CaseProfile]):
    name = "case_intake"
    output_schema = CaseProfile

    def _system_prompt(self) -> str:
        return build_case_intake_system_prompt()

    def _build_user_content(self, state: CaseState, context: Any) -> str:
        conversation = render_conversation(state.get("messages") or [])
        existing_profile = state.get("case_profile")
        profile_json = existing_profile.model_dump_json() if existing_profile else "null"
        return (
            f"Conversation so far:\n{conversation}\n\n"
            f"Existing case profile (null if this is the first turn):\n{profile_json}"
        )
