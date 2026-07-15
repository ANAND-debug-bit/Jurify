"""Case Reconstruction Agent (Module 12, gap-fill).

Builds a chronological Timeline from the CaseProfile Case Intake
produced — a single-shot transformation, no conversation history needed
(docs/architecture/02-agent-architecture.md §2.2.2).
"""

from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.graph.state import CaseState
from app.prompts.case_reconstruction import build_case_reconstruction_system_prompt
from app.schemas.timeline import Timeline


class CaseReconstructionAgent(BaseAgent[Timeline]):
    name = "case_reconstruction"
    output_schema = Timeline

    def _system_prompt(self) -> str:
        return build_case_reconstruction_system_prompt()

    def _build_user_content(self, state: CaseState, context: Any) -> str:
        profile = state.get("case_profile")
        if profile is None:
            return "No case profile available yet."
        return f"Case profile:\n{profile.model_dump_json()}"
