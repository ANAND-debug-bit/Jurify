from __future__ import annotations

from uuid import uuid4

import pytest
from langchain_core.documents import Document

from app.agents.verification_agent import VerificationAgent
from app.core.config import Settings
from app.graph.state import create_initial_state
from app.llm.gemma_client import get_chat_model
from app.rag.retriever import StatuteRetriever
from app.rag.vectorstore import get_vector_store
from app.schemas.legal_research import LegalCitation, LegalProvision, LegalResearchResult
from app.schemas.verification import VerifiedLegalResearchResult
from tests.conftest import ollama_is_reachable
from tests.unit.agents.fakes import FakeStructuredChatModel

_CONSUMER_DOCUMENT = Document(
    page_content="A consumer may file a complaint about a defective product.",
    metadata={"act_name": "Consumer Protection Act, 2019", "section": "Section 35"},
)


class _FakeVectorStore:
    def __init__(self, results: list[tuple[Document, float]]) -> None:
        self._results = results

    async def aadd_documents(self, documents: list[Document]) -> list[str]:
        raise NotImplementedError

    async def asimilarity_search_with_score(
        self, query: str, k: int = 8
    ) -> list[tuple[Document, float]]:
        return self._results[:k]


def _agent(responses: list[object], results: list[tuple[Document, float]]) -> VerificationAgent:
    llm = FakeStructuredChatModel(responses=responses)
    retriever = StatuteRetriever(_FakeVectorStore(results))
    return VerificationAgent(llm, model_name="fake-model", retriever=retriever)


def _research_with_one_citation() -> LegalResearchResult:
    return LegalResearchResult(
        applicable_laws=[
            LegalProvision(
                title="Consumer complaint",
                plain_explanation="You may file a complaint.",
                citations=[
                    LegalCitation(act_name="Consumer Protection Act, 2019", section="Section 35")
                ],
            )
        ],
        overall_summary="summary",
    )


async def test_returns_verified_result_from_fake() -> None:
    output = VerifiedLegalResearchResult(
        jurisdiction="India",
        verified_provisions=[
            LegalProvision(
                title="Consumer complaint",
                plain_explanation="You may file a complaint.",
                citations=[
                    LegalCitation(act_name="Consumer Protection Act, 2019", section="Section 35")
                ],
            )
        ],
        rejected_citations=[],
        verification_summary="1 of 1 citations verified.",
    )
    agent = _agent(responses=[output], results=[(_CONSUMER_DOCUMENT, 0.9)])

    state = create_initial_state(uuid4(), uuid4())
    state["legal_research"] = _research_with_one_citation()

    result = await agent.run(state)

    assert result.output.verification_summary == "1 of 1 citations verified."
    assert len(result.output.verified_provisions) == 1


async def test_gather_context_returns_empty_when_no_legal_research() -> None:
    agent = _agent(responses=[], results=[(_CONSUMER_DOCUMENT, 0.9)])

    context = await agent._gather_context(create_initial_state(uuid4(), uuid4()))

    assert context == []


async def test_gather_context_retrieves_evidence_per_unique_citation() -> None:
    agent = _agent(responses=[], results=[(_CONSUMER_DOCUMENT, 0.9)])
    state = create_initial_state(uuid4(), uuid4())
    state["legal_research"] = LegalResearchResult(
        applicable_laws=[
            LegalProvision(
                title="A",
                plain_explanation="x",
                citations=[
                    LegalCitation(act_name="Consumer Protection Act, 2019", section="Section 35")
                ],
            ),
            LegalProvision(
                title="B",
                plain_explanation="x",
                # Same citation cited again from a different provision —
                # must be deduplicated, not retrieved twice.
                citations=[
                    LegalCitation(act_name="Consumer Protection Act, 2019", section="Section 35")
                ],
            ),
        ],
        overall_summary="x",
    )

    context = await agent._gather_context(state)

    assert len(context) == 1
    assert context[0].citation.act_name == "Consumer Protection Act, 2019"
    assert context[0].retrieved[0].document is _CONSUMER_DOCUMENT


def test_build_user_content_handles_missing_legal_research() -> None:
    agent = _agent(responses=[], results=[])

    content = agent._build_user_content(create_initial_state(uuid4(), uuid4()), [])

    assert "No legal research result available to verify." in content


def test_build_user_content_flags_missing_evidence() -> None:
    from app.agents.verification_agent import CitationEvidence

    agent = _agent(responses=[], results=[])
    state = create_initial_state(uuid4(), uuid4())
    state["legal_research"] = _research_with_one_citation()

    context = [
        CitationEvidence(
            citation=LegalCitation(act_name="Invented Act, 1999", section="Section 1"),
            retrieved=[],
        )
    ]
    content = agent._build_user_content(state, context)

    assert "no matching statute excerpt was found in the corpus" in content


@pytest.mark.skipif(not ollama_is_reachable(), reason="no local Ollama server reachable")
async def test_live_rejects_citation_with_no_supporting_evidence(monkeypatch) -> None:
    monkeypatch.setenv("GEMMA_MODEL_NAME", "gemma2:2b")
    monkeypatch.setenv("EMBEDDING_MODEL", "nomic-embed-text")
    settings = Settings()
    llm = get_chat_model(settings)

    vector_store = get_vector_store(settings, collection_name="verification_agent_test_live")
    await vector_store.aadd_documents([_CONSUMER_DOCUMENT])
    retriever = StatuteRetriever(vector_store, top_k=2)
    agent = VerificationAgent(llm, model_name=settings.llm.gemma_model_name, retriever=retriever)

    state = create_initial_state(uuid4(), uuid4())
    state["legal_research"] = LegalResearchResult(
        applicable_laws=[
            LegalProvision(
                title="Consumer complaint",
                plain_explanation="You may file a complaint.",
                citations=[
                    LegalCitation(act_name="Consumer Protection Act, 2019", section="Section 35")
                ],
            ),
            LegalProvision(
                title="Fabricated law",
                plain_explanation="This citation does not exist in the corpus.",
                citations=[
                    LegalCitation(act_name="The Fictitious Statutes Act, 1850", section="Section 999")
                ],
            ),
        ],
        overall_summary="summary",
    )

    result = await agent.run(state)

    verified_act_names = {
        citation.act_name
        for provision in result.output.verified_provisions
        for citation in provision.citations
    }
    rejected_act_names = {c.citation.act_name for c in result.output.rejected_citations}

    assert "Consumer Protection Act, 2019" in verified_act_names
    assert "The Fictitious Statutes Act, 1850" not in verified_act_names
    assert "The Fictitious Statutes Act, 1850" in rejected_act_names
