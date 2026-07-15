"""Risk Assessment Agent (Module 15).

Synthesizes across case_profile, timeline, verified_legal_research, and
evidence_report — all already in CaseState by the time this agent runs
(docs/architecture/03-langgraph-workflow.md §3.3: RiskAssessment is a
fixed, unconditional step after EvidenceAnalysis, no Supervisor call in
between). No repository or RAG access needed, so this uses BaseAgent's
default no-op `_gather_context`, same as EvidenceAnalysisAgent.
"""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.graph.state import CaseState
from app.prompts.risk_assessment import build_risk_assessment_system_prompt
from app.schemas.risk import RiskAssessment


class RiskAssessmentAgent(BaseAgent[RiskAssessment]):
    name = "risk_assessment"
    output_schema = RiskAssessment

    def _system_prompt(self) -> str:
        return build_risk_assessment_system_prompt()

    def _build_user_content(self, state: CaseState, context: object) -> str:
        profile = state.get("case_profile")
        if profile is None:
            return "No case profile available yet."

        timeline = state.get("timeline")
        timeline_json = timeline.model_dump_json() if timeline is not None else "null"

        verified_research = state.get("verified_legal_research")
        verified_research_json = (
            verified_research.model_dump_json() if verified_research is not None else "null"
        )

        evidence_report = state.get("evidence_report")
        evidence_report_json = (
            evidence_report.model_dump_json() if evidence_report is not None else "null"
        )

        return (
            f"Case profile:\n{profile.model_dump_json()}\n\n"
            f"Case timeline (null if not yet reconstructed):\n{timeline_json}\n\n"
            f"Verified legal research (null if not yet verified):\n{verified_research_json}\n\n"
            f"Evidence report (null if not yet analyzed):\n{evidence_report_json}"
        )
