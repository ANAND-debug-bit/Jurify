"""Verification Agent (Module 13, Change 2).

Re-retrieves the statute corpus independently for every citation the
Legal Research Agent claimed, and asks the LLM to judge each claim
against that fresh evidence rather than re-approve its own prior
reasoning (app.prompts.verification). This is deliberately the same
retrieve-then-ground shape as LegalResearchAgent (app/agents/
legal_research_agent.py) — the two agents share StatuteRetriever but
never share a prompt or an LLM call.
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.language_models.chat_models import BaseChatModel

from app.agents.base import BaseAgent
from app.graph.state import CaseState
from app.prompts.verification import build_verification_system_prompt
from app.rag.retriever import RetrievedChunk, StatuteRetriever
from app.schemas.legal_research import LegalCitation
from app.schemas.verification import VerifiedLegalResearchResult


@dataclass(frozen=True)
class CitationEvidence:
    citation: LegalCitation
    retrieved: list[RetrievedChunk]


def _citation_key(citation: LegalCitation) -> tuple[str, str | None]:
    return (citation.act_name, citation.section)


def _format_evidence(evidence: list[CitationEvidence]) -> str:
    if not evidence:
        return "(no citations to verify)"
    entries: list[str] = []
    for index, item in enumerate(evidence, start=1):
        header = (
            f"[{index}] Claimed citation: {item.citation.act_name} | "
            f"Section: {item.citation.section}"
        )
        if not item.retrieved:
            entries.append(
                f"{header}\nRetrieved evidence: (no matching statute excerpt was found "
                "in the corpus)"
            )
            continue
        retrieved_lines = "\n".join(
            f"  - Act: {chunk.document.metadata.get('act_name', 'Unknown Act')} | "
            f"Section: {chunk.document.metadata.get('section', 'Unknown Section')}\n"
            f"    Excerpt: {chunk.document.page_content}"
            for chunk in item.retrieved
        )
        entries.append(f"{header}\nRetrieved evidence:\n{retrieved_lines}")
    return "\n\n".join(entries)


class VerificationAgent(BaseAgent[VerifiedLegalResearchResult]):
    name = "verification"
    output_schema = VerifiedLegalResearchResult

    def __init__(
        self,
        llm: BaseChatModel,
        model_name: str,
        retriever: StatuteRetriever,
        max_retries: int = 2,
    ) -> None:
        super().__init__(llm, model_name, max_retries)
        self._retriever = retriever

    def _system_prompt(self) -> str:
        return build_verification_system_prompt()

    async def _gather_context(self, state: CaseState) -> list[CitationEvidence]:
        research = state.get("legal_research")
        if research is None:
            return []

        seen: set[tuple[str, str | None]] = set()
        evidence: list[CitationEvidence] = []
        for law in research.applicable_laws:
            for citation in law.citations:
                key = _citation_key(citation)
                if key in seen:
                    continue
                seen.add(key)
                query = f"{citation.act_name} {citation.section or ''}".strip()
                retrieved = await self._retriever.retrieve(query)
                evidence.append(CitationEvidence(citation=citation, retrieved=retrieved))
        return evidence

    def _build_user_content(self, state: CaseState, context: list[CitationEvidence]) -> str:
        research = state.get("legal_research")
        if research is None:
            return "No legal research result available to verify."

        return (
            f"Original legal research (unverified):\n{research.model_dump_json()}\n\n"
            f"Independent re-retrieval evidence per claimed citation:\n{_format_evidence(context)}"
        )
