"""Sample statute corpus (Module 12).

*** NOT AUTHORITATIVE — READ BEFORE USING ***

This is a small, hand-written SAMPLE corpus built to exercise the RAG
pipeline's mechanics (chunking, embedding, retrieval, citation
formatting) end-to-end. Every entry is a general, paraphrased summary of
a well-known provision, not verbatim statutory text, and section numbers
should be independently verified before being shown to a real user as
legal fact.

Real ingestion — sourcing exact, verified text from an authoritative
source such as https://www.indiacode.nic.in, covering the full corpus
named in docs/architecture/01-architecture-overview.md (Constitution,
BNS, BNSS, BSA, Consumer Protection Act, Motor Vehicles Act, Labour
Laws, Cyber Laws, state-specific Acts) — is future work
(docs/architecture/11-scalability-roadmap.md); this module's job is only
to prove the pipeline works, not to be the pipeline's final data source.
"""

from __future__ import annotations

from langchain_core.documents import Document

SAMPLE_STATUTE_CORPUS: list[Document] = [
    Document(
        page_content=(
            "Consumer Protection Act, 2019 — a consumer who has a grievance against a "
            "seller or service provider over a defective good, a deficient service, or "
            "an unfair trade practice may file a complaint before the appropriate "
            "Consumer Disputes Redressal Commission (District, State, or National, "
            "depending on the value of the goods/services and compensation claimed). "
            "Remedies can include replacement, refund, compensation for loss or injury, "
            "and removal of the defect."
        ),
        metadata={
            "act_name": "Consumer Protection Act, 2019",
            "section": "Section 35",
            "category": "consumer_dispute",
            "source_url": "https://www.indiacode.nic.in",
            "verified": False,
        },
    ),
    Document(
        page_content=(
            "Motor Vehicles Act, 1988 — a person injured, or the legal representatives "
            "of a person killed, in a motor vehicle accident may apply to the Motor "
            "Accidents Claims Tribunal for compensation. The application can be made by "
            "the victim, their representative, or their legal heirs, and covers medical "
            "expenses, loss of income, and other accident-related losses."
        ),
        metadata={
            "act_name": "Motor Vehicles Act, 1988",
            "section": "Section 166",
            "category": "motor_vehicle_accident",
            "source_url": "https://www.indiacode.nic.in",
            "verified": False,
        },
    ),
    Document(
        page_content=(
            "Bharatiya Nyaya Sanhita, 2023 — cheating is defined as fraudulently or "
            "dishonestly inducing a person to deliver property, or to do or omit to do "
            "something they would not otherwise do or omit, causing or likely to cause "
            "harm. Cheating is a criminal offence and can be reported to the police."
        ),
        metadata={
            "act_name": "Bharatiya Nyaya Sanhita, 2023",
            "section": "Section 318",
            "category": "fraud",
            "source_url": "https://www.indiacode.nic.in",
            "verified": False,
        },
    ),
    Document(
        page_content=(
            "Bharatiya Nagarik Suraksha Sanhita, 2023 — information about the "
            "commission of a cognizable offence given to an officer in charge of a "
            "police station must be reduced to writing and forms the First Information "
            "Report (FIR). A copy of the FIR must be given free of cost to the "
            "informant. Refusal to register an FIR for a cognizable offence can itself "
            "be challenged."
        ),
        metadata={
            "act_name": "Bharatiya Nagarik Suraksha Sanhita, 2023",
            "section": "Section 173",
            "category": "criminal_complaint",
            "source_url": "https://www.indiacode.nic.in",
            "verified": False,
        },
    ),
    Document(
        page_content=(
            "Information Technology Act, 2000 — fraudulently or dishonestly using "
            "another person's electronic signature, password, or other unique "
            "identification feature is identity theft and is a punishable offence, "
            "covering many common online/cyber fraud scenarios such as unauthorized use "
            "of someone's bank login or digital identity."
        ),
        metadata={
            "act_name": "Information Technology Act, 2000",
            "section": "Section 66C",
            "category": "cyber_fraud",
            "source_url": "https://www.indiacode.nic.in",
            "verified": False,
        },
    ),
    Document(
        page_content=(
            "Protection of Women from Domestic Violence Act, 2005 — an aggrieved woman "
            "may apply to a Magistrate for one or more reliefs, including a protection "
            "order, a residence order, monetary relief, custody orders, and compensation, "
            "against a person with whom she is or has been in a domestic relationship."
        ),
        metadata={
            "act_name": "Protection of Women from Domestic Violence Act, 2005",
            "section": "Section 12",
            "category": "domestic_violence",
            "source_url": "https://www.indiacode.nic.in",
            "verified": False,
        },
    ),
    Document(
        page_content=(
            "Right to Information Act, 2005 — a citizen may request information from a "
            "public authority by submitting a written or electronic request along with "
            "the prescribed fee. The public authority must generally dispose of the "
            "request and provide the information within thirty days of receipt."
        ),
        metadata={
            "act_name": "Right to Information Act, 2005",
            "section": "Section 6",
            "category": "rti",
            "source_url": "https://www.indiacode.nic.in",
            "verified": False,
        },
    ),
    Document(
        page_content=(
            "Payment of Wages Act, 1936 — an employee whose wages have been delayed or "
            "unlawfully deducted may file a claim before the designated authority under "
            "the Act, which can direct payment of the wages due along with compensation."
        ),
        metadata={
            "act_name": "Payment of Wages Act, 1936",
            "section": "Section 15",
            "category": "labour_dispute",
            "source_url": "https://www.indiacode.nic.in",
            "verified": False,
        },
    ),
]
