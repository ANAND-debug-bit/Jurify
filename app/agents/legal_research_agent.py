"""Legal Research Agent (Module 12).

Consumes the CaseProfile (and Timeline, when Case Reconstruction has
already run) to build a retrieval query, fetches candidate statute
chunks via StatuteRetriever, and asks the LLM to ground its answer only
in what was retrieved (app.prompts.legal_research). This is the first
agent to use BaseAgent's `_gather_context` hook (app/agents/base.py) —
retrieval is I/O and must happen before the synchronous
`_build_user_content` builds the prompt.
"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from app.agents.base import BaseAgent
from app.graph.state import CaseState
from app.prompts.legal_research import build_legal_research_system_prompt
from app.rag.retriever import RetrievedChunk, StatuteRetriever
from app.schemas.legal_research import LegalResearchResult


def _build_retrieval_query(state: CaseState) -> str | None:
    profile = state.get("case_profile")
    if profile is None:
        return None
    parts = [profile.incident_category, profile.summary]
    timeline = state.get("timeline")
    if timeline is not None and timeline.reconstructed_summary:
        parts.append(timeline.reconstructed_summary)
    return "\n".join(part for part in parts if part)


def _format_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "(no statute excerpts were retrieved)"
    entries: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        metadata = chunk.document.metadata
        entries.append(
            f"[{index}] Act: {metadata.get('act_name', 'Unknown Act')} | "
            f"Section: {metadata.get('section', 'Unknown Section')}\n"
            f"Excerpt: {chunk.document.page_content}"
        )
    return "\n\n".join(entries)


class LegalResearchAgent(BaseAgent[LegalResearchResult]):
    name = "legal_research"
    output_schema = LegalResearchResult

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
        return build_legal_research_system_prompt()

    async def _gather_context(self, state: CaseState) -> list[RetrievedChunk]:
        query = _build_retrieval_query(state)
        if query is None:
            return []
        return await self._retriever.retrieve(query)

    def _build_user_content(self, state: CaseState, context: list[RetrievedChunk]) -> str:
        profile = state.get("case_profile")
        if profile is None:
            return (
                "No case profile available yet.\n\n"
                f"Retrieved statute context:\n{_format_context(context)}"
            )

        timeline = state.get("timeline")
        timeline_json = timeline.model_dump_json() if timeline is not None else "null"

        return (
            f"Case profile:\n{profile.model_dump_json()}\n\n"
            f"Case timeline (null if not yet reconstructed):\n{timeline_json}\n\n"
            f"Retrieved statute context:\n{_format_context(context)}"
        )
