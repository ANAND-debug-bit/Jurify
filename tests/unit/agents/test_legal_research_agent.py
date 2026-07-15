from __future__ import annotations

from uuid import uuid4

import pytest
from langchain_core.documents import Document

from app.agents.legal_research_agent import LegalResearchAgent
from app.core.config import Settings
from app.graph.state import create_initial_state
from app.llm.gemma_client import get_chat_model
from app.rag.retriever import RetrievedChunk, StatuteRetriever
from app.rag.vectorstore import get_vector_store
from app.schemas.case import CaseProfile
from app.schemas.legal_research import LegalCitation, LegalProvision, LegalResearchResult
from tests.conftest import ollama_is_reachable
from tests.unit.agents.fakes import FakeStructuredChatModel


class _FakeVectorStore:
    def __init__(self, results: list[tuple[Document, float]]) -> None:
        self._results = results

    async def aadd_documents(self, documents: list[Document]) -> list[str]:
        raise NotImplementedError

    async def asimilarity_search_with_score(
        self, query: str, k: int = 8
    ) -> list[tuple[Document, float]]:
        return self._results[:k]


_CONSUMER_DOCUMENT = Document(
    page_content=(
        "A consumer who has a grievance over a defective good may file a complaint "
        "before the appropriate Consumer Disputes Redressal Commission."
    ),
    metadata={
        "act_name": "Consumer Protection Act, 2019",
        "section": "Section 35",
        "source_url": "https://www.indiacode.nic.in",
    },
)


def _agent_with_fake_llm_and_retriever(
    responses: list[object], results: list[tuple[Document, float]]
) -> LegalResearchAgent:
    llm = FakeStructuredChatModel(responses=responses)
    retriever = StatuteRetriever(_FakeVectorStore(results))
    return LegalResearchAgent(llm, model_name="fake-model", retriever=retriever)


async def test_returns_legal_research_result_from_fake() -> None:
    result_output = LegalResearchResult(
        applicable_laws=[
            LegalProvision(
                title="Consumer complaint",
                plain_explanation="You may file a complaint about the defective product.",
                citations=[
                    LegalCitation(act_name="Consumer Protection Act, 2019", section="Section 35")
                ],
            )
        ],
        overall_summary="You have a consumer protection claim.",
    )
    agent = _agent_with_fake_llm_and_retriever(
        responses=[result_output], results=[(_CONSUMER_DOCUMENT, 0.95)]
    )

    state = create_initial_state(uuid4(), uuid4())
    state["case_profile"] = CaseProfile(
        incident_category="consumer_dispute",
        summary="Bought a washing machine that broke; seller refuses a refund.",
        confidence=0.8,
    )

    result = await agent.run(state)

    assert result.output.overall_summary == "You have a consumer protection claim."
    assert result.output.applicable_laws[0].citations[0].section == "Section 35"


async def test_gather_context_returns_empty_when_no_case_profile() -> None:
    agent = _agent_with_fake_llm_and_retriever(responses=[], results=[(_CONSUMER_DOCUMENT, 0.9)])

    context = await agent._gather_context(create_initial_state(uuid4(), uuid4()))

    assert context == []


async def test_gather_context_retrieves_chunks_when_profile_present() -> None:
    agent = _agent_with_fake_llm_and_retriever(responses=[], results=[(_CONSUMER_DOCUMENT, 0.9)])
    state = create_initial_state(uuid4(), uuid4())
    state["case_profile"] = CaseProfile(
        incident_category="consumer_dispute", summary="Defective washing machine.", confidence=0.8
    )

    context = await agent._gather_context(state)

    assert len(context) == 1
    assert context[0].document is _CONSUMER_DOCUMENT


def test_build_user_content_handles_missing_profile() -> None:
    agent = _agent_with_fake_llm_and_retriever(responses=[], results=[])

    content = agent._build_user_content(create_initial_state(uuid4(), uuid4()), [])

    assert "No case profile available yet." in content


def test_build_user_content_includes_retrieved_context_verbatim() -> None:
    agent = _agent_with_fake_llm_and_retriever(responses=[], results=[])
    state = create_initial_state(uuid4(), uuid4())
    state["case_profile"] = CaseProfile(
        incident_category="consumer_dispute", summary="Defective washing machine.", confidence=0.8
    )
    context = [RetrievedChunk(document=_CONSUMER_DOCUMENT, score=0.9)]
    content = agent._build_user_content(state, context)

    assert "Consumer Protection Act, 2019" in content
    assert "Section 35" in content


def test_build_user_content_handles_no_retrieved_context() -> None:
    agent = _agent_with_fake_llm_and_retriever(responses=[], results=[])
    state = create_initial_state(uuid4(), uuid4())
    state["case_profile"] = CaseProfile(
        incident_category="consumer_dispute", summary="Defective washing machine.", confidence=0.8
    )

    content = agent._build_user_content(state, [])

    assert "no statute excerpts were retrieved" in content


@pytest.mark.skipif(not ollama_is_reachable(), reason="no local Ollama server reachable")
async def test_live_grounds_answer_in_real_chroma_retrieval(monkeypatch) -> None:
    monkeypatch.setenv("GEMMA_MODEL_NAME", "gemma2:2b")
    monkeypatch.setenv("EMBEDDING_MODEL", "nomic-embed-text")
    settings = Settings()
    llm = get_chat_model(settings)

    vector_store = get_vector_store(settings, collection_name="legal_research_agent_test_live")
    await vector_store.aadd_documents(
        [
            _CONSUMER_DOCUMENT,
            Document(
                page_content=(
                    "An employee whose wages have been delayed may file a claim before the "
                    "designated authority under the Payment of Wages Act."
                ),
                metadata={
                    "act_name": "Payment of Wages Act, 1936",
                    "section": "Section 15",
                    "source_url": "https://www.indiacode.nic.in",
                },
            ),
        ]
    )
    retriever = StatuteRetriever(vector_store, top_k=2)
    agent = LegalResearchAgent(llm, model_name=settings.llm.gemma_model_name, retriever=retriever)

    state = create_initial_state(uuid4(), uuid4())
    state["case_profile"] = CaseProfile(
        incident_category="consumer_dispute",
        summary="I bought a washing machine, it broke after two days, and the seller refuses a refund.",
        confidence=0.8,
    )

    result = await agent.run(state)

    assert result.output.applicable_laws
    cited_act_names = {
        citation.act_name
        for law in result.output.applicable_laws
        for citation in law.citations
    }
    assert cited_act_names <= {"Consumer Protection Act, 2019", "Payment of Wages Act, 1936"}
