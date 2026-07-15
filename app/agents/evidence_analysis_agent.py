"""Evidence Analysis Agent (Module 14).

No RAG or repository access needed here — unlike LegalResearchAgent/
VerificationAgent, this agent only reasons over what evidence_analysis_node
already loaded into CaseState (`evidence_items`, via EvidenceService), so
it uses BaseAgent's default no-op `_gather_context`.
"""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.graph.state import CaseState
from app.prompts.evidence_analysis import build_evidence_analysis_system_prompt
from app.schemas.evidence import EvidenceReport


def _format_evidence_items(state: CaseState) -> str:
    items = state.get("evidence_items") or []
    if not items:
        return "(no evidence submitted yet)"
    lines = [
        f"- type: {item.evidence_type} | description: {item.description or '(none given)'}"
        for item in items
    ]
    return "\n".join(lines)


class EvidenceAnalysisAgent(BaseAgent[EvidenceReport]):
    name = "evidence_analysis"
    output_schema = EvidenceReport

    def _system_prompt(self) -> str:
        return build_evidence_analysis_system_prompt()

    def _build_user_content(self, state: CaseState, context: object) -> str:
        profile = state.get("case_profile")
        if profile is None:
            return (
                "No case profile available yet.\n\n"
                f"Submitted evidence:\n{_format_evidence_items(state)}"
            )

        timeline = state.get("timeline")
        timeline_json = timeline.model_dump_json() if timeline is not None else "null"

        return (
            f"Case profile:\n{profile.model_dump_json()}\n\n"
            f"Case timeline (null if not yet reconstructed):\n{timeline_json}\n\n"
            f"Submitted evidence:\n{_format_evidence_items(state)}"
        )
