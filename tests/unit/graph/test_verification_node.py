from __future__ import annotations

from uuid import uuid4

from app.agents.verification_agent import VerificationAgent
from app.graph.nodes.verification_node import make_verification_node
from app.graph.state import create_initial_state
from app.rag.retriever import StatuteRetriever
from app.schemas.language import SupportedLanguage
from app.schemas.legal_research import LegalCitation, LegalProvision, LegalResearchResult
from app.schemas.verification import (
    CitationVerification,
    VerificationStatus,
    VerifiedLegalResearchResult,
)
from app.services.case_service import CaseService
from tests.unit.agents.fakes import FakeStructuredChatModel
from tests.unit.services.fakes import FakeCaseRepository, FakeEvidenceRepository


class _EmptyVectorStore:
    async def aadd_documents(self, documents):
        raise NotImplementedError

    async def asimilarity_search_with_score(self, query: str, k: int = 8):
        return []


def _verified_output() -> VerifiedLegalResearchResult:
    return VerifiedLegalResearchResult(
        jurisdiction="India",
        verified_provisions=[
            LegalProvision(
                title="Consumer complaint",
                plain_explanation="x",
                citations=[
                    LegalCitation(act_name="Consumer Protection Act, 2019", section="Section 35")
                ],
            )
        ],
        rejected_citations=[
            CitationVerification(
                citation=LegalCitation(act_name="Invented Act, 1999", section="Section 1"),
                status=VerificationStatus.REJECTED,
                verification_notes="No matching statute found.",
            )
        ],
        verification_summary="1 verified, 1 rejected.",
    )


async def test_node_persists_verification_and_increments_retry_count() -> None:
    llm = FakeStructuredChatModel(responses=[_verified_output()])
    retriever = StatuteRetriever(_EmptyVectorStore())
    agent = VerificationAgent(llm, model_name="fake-model", retriever=retriever)
    case_repo = FakeCaseRepository()
    service = CaseService(case_repo, FakeEvidenceRepository())
    node = make_verification_node(agent, service)

    case = await case_repo.create(uuid4(), SupportedLanguage.EN)
    research = await service.save_legal_research(
        case.id,
        LegalResearchResult(
            applicable_laws=[
                LegalProvision(
                    title="Consumer complaint",
                    plain_explanation="x",
                    citations=[
                        LegalCitation(
                            act_name="Consumer Protection Act, 2019", section="Section 35"
                        )
                    ],
                ),
                LegalProvision(
                    title="Fraud",
                    plain_explanation="x",
                    citations=[
                        LegalCitation(act_name="Invented Act, 1999", section="Section 1")
                    ],
                ),
            ],
            overall_summary="x",
        ),
    )
    state = create_initial_state(case.id, uuid4())
    state["legal_research"] = LegalResearchResult(
        applicable_laws=[], overall_summary="x"
    )

    update = await node(state)

    assert update["verified_legal_research"].verification_summary == "1 verified, 1 rejected."
    assert update["verification_retry_count"] == 1

    citations = await service.list_legal_citations(research.id)
    by_act = {c.act_name: c for c in citations}
    assert by_act["Consumer Protection Act, 2019"].is_verified is True
    assert by_act["Invented Act, 1999"].is_verified is False
    assert by_act["Invented Act, 1999"].verification_status == "rejected"


async def test_node_skips_persistence_when_no_legal_research_saved() -> None:
    llm = FakeStructuredChatModel(
        responses=[
            VerifiedLegalResearchResult(
                jurisdiction="India",
                verified_provisions=[],
                rejected_citations=[],
                verification_summary="nothing to verify",
            )
        ]
    )
    retriever = StatuteRetriever(_EmptyVectorStore())
    agent = VerificationAgent(llm, model_name="fake-model", retriever=retriever)
    case_repo = FakeCaseRepository()
    service = CaseService(case_repo, FakeEvidenceRepository())
    node = make_verification_node(agent, service)

    case = await case_repo.create(uuid4(), SupportedLanguage.EN)
    state = create_initial_state(case.id, uuid4())

    update = await node(state)

    assert update["verified_legal_research"].verification_summary == "nothing to verify"
    assert update["verification_retry_count"] == 1
