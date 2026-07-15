from __future__ import annotations

from uuid import uuid4

from app.agents.legal_research_agent import LegalResearchAgent
from app.graph.nodes.legal_research_node import make_legal_research_node
from app.graph.state import create_initial_state
from app.rag.retriever import StatuteRetriever
from app.schemas._common import CaseStatus
from app.schemas.language import SupportedLanguage
from app.schemas.legal_research import LegalResearchResult
from app.services.case_service import CaseService
from tests.unit.agents.fakes import FakeStructuredChatModel
from tests.unit.services.fakes import FakeCaseRepository, FakeEvidenceRepository


class _EmptyVectorStore:
    async def aadd_documents(self, documents):
        raise NotImplementedError

    async def asimilarity_search_with_score(self, query: str, k: int = 8):
        return []


async def test_node_saves_legal_research_and_advances_status() -> None:
    research = LegalResearchResult(applicable_laws=[], overall_summary="summary")
    llm = FakeStructuredChatModel(responses=[research])
    retriever = StatuteRetriever(_EmptyVectorStore())
    agent = LegalResearchAgent(llm, model_name="fake-model", retriever=retriever)
    case_repo = FakeCaseRepository()
    service = CaseService(case_repo, FakeEvidenceRepository())
    node = make_legal_research_node(agent, service)

    case = await case_repo.create(uuid4(), SupportedLanguage.EN)
    state = create_initial_state(case.id, uuid4())

    update = await node(state)

    assert update["status"] == CaseStatus.VERIFYING_CITATIONS
    assert update["legal_research"] == research
    saved = await service.get_latest_legal_research(case.id)
    assert saved is not None
    assert saved.plain_explanation == "summary"
