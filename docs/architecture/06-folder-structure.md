# 6. Folder Structure

> **Revision note (v2)**: adds `agents/supervisor_agent.py` + 4 new agents, corresponding `graph/nodes/`, `prompts/`, and `schemas/` files, and a new `i18n/` package for multilingual support (Change 9). Marked **NEW** below.

```
nyayaos/
├── app/
│   ├── main.py                          # FastAPI app factory, middleware, router mounting
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── deps.py                  # shared FastAPI Depends: get_db, get_current_user, get_container
│   │       ├── routes/
│   │       │   ├── auth.py
│   │       │   ├── case.py              # /case, /case/intake, /case/research, ...
│   │       │   ├── dashboard.py
│   │       │   ├── lawyers.py
│   │       │   └── documents.py
│   │       └── router.py                # aggregates all routers under /api/v1
│   │
│   ├── agents/
│   │   ├── base.py                      # BaseAgent, AgentPort, AgentResult, retry/logging wrapper
│   │   ├── registry.py                  # AgentRegistry / factory
│   │   ├── supervisor_agent.py          # NEW — routing only, see 08-pydantic-schemas.md §8.11
│   │   ├── case_intake_agent.py
│   │   ├── emergency_detection_agent.py # NEW
│   │   ├── emergency_agent.py           # NEW
│   │   ├── case_reconstruction_agent.py
│   │   ├── legal_research_agent.py
│   │   ├── verification_agent.py        # NEW
│   │   ├── evidence_analysis_agent.py
│   │   ├── risk_assessment_agent.py
│   │   ├── legal_strategy_agent.py
│   │   ├── government_scheme_agent.py   # NEW
│   │   ├── complaint_generation_agent.py
│   │   ├── lawyer_recommendation_agent.py
│   │   ├── explainability_agent.py      # NEW
│   │   ├── opposition_lawyer_agent.py
│   │   ├── counter_strategy_agent.py
│   │   └── judge_agent.py
│   │
│   ├── graph/
│   │   ├── state.py                     # CaseState, CaseStatus (v2 fields — see 03-langgraph-workflow.md §3.2)
│   │   ├── graph_builder.py             # build_graph() -> main_graph
│   │   ├── stress_test_graph_builder.py # NEW — build_stress_test_graph() (Change 6, separate compiled graph)
│   │   ├── edges.py                     # route_intake, supervisor_route, route_adversarial_loop
│   │   ├── checkpointer.py              # Postgres-backed LangGraph checkpointer
│   │   └── nodes/
│   │       ├── case_intake_node.py
│   │       ├── emergency_detection_node.py   # NEW
│   │       ├── emergency_agent_node.py       # NEW
│   │       ├── supervisor_node.py            # NEW — thin wrapper, see agents/supervisor_agent.py
│   │       ├── case_reconstruction_node.py
│   │       ├── legal_research_node.py
│   │       ├── verification_node.py          # NEW
│   │       ├── evidence_analysis_node.py
│   │       ├── awaiting_evidence_upload_node.py  # NEW — checkpoint/pause node, Change 7
│   │       ├── risk_assessment_node.py
│   │       ├── strategy_planning_node.py
│   │       ├── government_scheme_node.py     # NEW
│   │       ├── lawyer_recommendation_node.py
│   │       ├── complaint_generation_node.py
│   │       ├── explainability_node.py        # NEW
│   │       ├── opposition_lawyer_node.py
│   │       ├── counter_strategy_node.py
│   │       ├── judge_agent_node.py
│   │       └── finalize_dashboard_node.py
│   │
│   ├── core/
│   │   ├── config.py                    # Pydantic Settings (env-driven)
│   │   ├── container.py                 # DI container wiring
│   │   ├── security.py                  # JWT issue/verify, password hashing
│   │   ├── logging.py                   # structlog config
│   │   ├── exceptions.py                # domain/app exception hierarchy + FastAPI handlers
│   │   ├── rate_limit.py                # Redis token-bucket middleware
│   │   ├── cache.py                     # Redis cache decorator/client
│   │   └── telemetry.py                 # OpenTelemetry + Prometheus setup
│   │
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── case.py
│   │   │   ├── evidence.py
│   │   │   ├── timeline.py
│   │   │   ├── risk.py
│   │   │   ├── strategy.py
│   │   │   ├── document.py
│   │   │   ├── lawyer.py
│   │   │   └── opposition.py
│   │   ├── repositories/                # abstract interfaces (ports)
│   │   │   ├── case_repository.py
│   │   │   ├── evidence_repository.py
│   │   │   ├── lawyer_repository.py
│   │   │   └── memory_repository.py
│   │   └── exceptions.py
│   │
│   ├── services/                        # application layer, one per bounded context
│   │   ├── case_service.py
│   │   ├── intake_service.py
│   │   ├── evidence_service.py          # now also handles resume-from-pause (Change 7)
│   │   ├── risk_service.py
│   │   ├── strategy_service.py
│   │   ├── government_scheme_service.py # NEW
│   │   ├── document_service.py
│   │   ├── lawyer_service.py
│   │   ├── explainability_service.py    # NEW
│   │   ├── adversarial_service.py       # now the entrypoint for POST /case/stress-test (Change 6)
│   │   ├── memory_service.py
│   │   └── dashboard_service.py         # read-model aggregation
│   │
│   ├── repositories/                    # SQLAlchemy implementations of domain ports
│   │   ├── sqlalchemy_case_repository.py
│   │   ├── sqlalchemy_evidence_repository.py
│   │   ├── sqlalchemy_lawyer_repository.py
│   │   ├── sqlalchemy_memory_repository.py
│   │   ├── sqlalchemy_emergency_repository.py       # NEW
│   │   └── sqlalchemy_government_scheme_repository.py  # NEW
│   │
│   ├── models/                          # SQLAlchemy ORM models (infra, mirrors 04-database-design.md)
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── case.py
│   │   ├── evidence.py
│   │   ├── timeline.py
│   │   ├── legal_research.py            # now includes verification columns (Change 2)
│   │   ├── emergency_assessment.py      # NEW
│   │   ├── risk.py
│   │   ├── strategy.py
│   │   ├── government_scheme_match.py   # NEW
│   │   ├── document.py
│   │   ├── lawyer.py
│   │   ├── opposition.py
│   │   ├── judge_opinion.py
│   │   ├── explainability_report.py     # NEW
│   │   ├── agent_log.py
│   │   └── memory.py
│   │
│   ├── schemas/                         # Pydantic v2 DTOs — API + agent contracts (see doc 08)
│   │   ├── case.py
│   │   ├── routing.py                   # NEW — RoutingDecision, NodeName
│   │   ├── emergency.py                 # NEW
│   │   ├── evidence.py
│   │   ├── timeline.py
│   │   ├── legal_research.py
│   │   ├── verification.py              # NEW
│   │   ├── risk.py
│   │   ├── strategy.py
│   │   ├── government_scheme.py         # NEW
│   │   ├── document.py
│   │   ├── lawyer.py
│   │   ├── explainability.py            # NEW
│   │   ├── opposition.py
│   │   ├── judge.py
│   │   ├── language.py                  # NEW — SupportedLanguage
│   │   └── dashboard.py
│   │
│   ├── prompts/
│   │   ├── _shared.py                   # shared preamble, injection-defense clause, JSON-only instruction,
│   │   │                                 # target-language instruction (Change 9)
│   │   ├── supervisor.py                # NEW — routing-only prompt, receives condensed state only
│   │   ├── case_intake.py
│   │   ├── emergency_detection.py       # NEW
│   │   ├── emergency_agent.py           # NEW
│   │   ├── case_reconstruction.py
│   │   ├── legal_research.py
│   │   ├── verification.py              # NEW
│   │   ├── evidence_analysis.py
│   │   ├── risk_assessment.py
│   │   ├── legal_strategy.py
│   │   ├── government_scheme.py         # NEW
│   │   ├── complaint_generation.py
│   │   ├── lawyer_recommendation.py
│   │   ├── explainability.py            # NEW
│   │   ├── opposition_lawyer.py
│   │   ├── counter_strategy.py
│   │   └── judge.py
│   │
│   ├── i18n/                            # NEW — multilingual support (Change 9)
│   │   ├── language_detector.py         # detect user input language
│   │   ├── translator.py                # TranslatorPort + Gemma-backed implementation
│   │   ├── supported_languages.py       # SupportedLanguage registry, extensibility hook
│   │   └── prompt_localizer.py          # injects target-language instruction into agent prompts
│   │
│   ├── memory/
│   │   ├── conversation_memory.py       # short-term, per-case turn buffer (now language-tagged)
│   │   ├── long_term_memory.py          # per-user cross-case embeddings
│   │   └── memory_manager.py            # facade used by services/agents
│   │
│   ├── database/
│   │   ├── session.py                   # async engine/session factory
│   │   ├── base.py                      # Declarative base, naming convention
│   │   └── unit_of_work.py
│   │
│   ├── rag/
│   │   ├── ingestion/
│   │   │   ├── loaders.py               # per-source loaders (Constitution, BNS, BNSS, BSA, ...)
│   │   │   ├── chunking.py
│   │   │   └── ingest_cli.py            # `python -m app.rag.ingestion.ingest_cli`
│   │   ├── embeddings.py                # embedding model wrapper
│   │   ├── vectorstore.py               # Chroma/FAISS adapter behind a VectorStorePort
│   │   ├── retriever.py                 # hybrid (keyword + vector) retriever
│   │   └── citation.py                  # citation formatting from retrieved chunks
│   │
│   ├── background/
│   │   ├── worker.py                    # Celery/Arq app
│   │   └── tasks.py                     # run_case_pipeline, ingest_corpus, etc.
│   │
│   └── llm/
│       └── gemma_client.py              # LangChain ChatModel wrapper around vLLM/Ollama endpoint
│
├── alembic/
│   ├── env.py
│   └── versions/
│
├── tests/
│   ├── unit/                            # domain + agent unit tests (no DB/network)
│   │   ├── agents/                      # includes supervisor_agent, emergency_*, verification_agent,
│   │   │                                # government_scheme_agent, explainability_agent
│   │   ├── domain/
│   │   ├── graph/                       # includes supervisor_route, stress_test_graph
│   │   └── i18n/                        # NEW — language_detector, translator, prompt_localizer
│   ├── integration/                     # DB + repository tests (testcontainers Postgres)
│   ├── e2e/                             # full API + graph run against a seeded DB
│   └── conftest.py
│
├── config/
│   ├── settings.dev.yaml
│   ├── settings.staging.yaml
│   └── settings.prod.yaml
│
├── docker/
│   ├── api.Dockerfile
│   ├── worker.Dockerfile
│   └── vllm.Dockerfile                  # OR ollama — see 13-configuration-and-devops.md
│
├── docs/
│   └── architecture/                    # this package
│
├── docker-compose.yml
├── pyproject.toml
├── alembic.ini
├── .gitignore
└── .env.example
```

## 6.1 Rules this structure enforces

- `agents/` never imports from `api/` or `models/` — only `schemas/`, `prompts/`, `llm/`.
- `domain/` imports nothing outside the standard library + Pydantic. No SQLAlchemy, no FastAPI, no LangChain.
- `graph/nodes/` is the *only* place agents, repositories, and state intersect — this is intentional so orchestration logic has one home.
- `services/` is the only layer routes are allowed to call.
- Every subpackage under `tests/unit/` mirrors its counterpart 1:1 (`agents/legal_research_agent.py` ↔ `tests/unit/agents/test_legal_research_agent.py`).
- `agents/supervisor_agent.py` may import `schemas/routing.py` and nothing else from `schemas/` — it structurally cannot depend on `CaseProfile`, `EvidenceReport`, etc., which is what keeps it from being tempted into legal reasoning (§2.2.4 of the agent architecture doc).
- `i18n/` is called from `graph/nodes/` (translate-in before an agent runs, translate-out after) and from `services/dashboard_service.py` (render-time translation) — it is never imported by `agents/`, so agent logic stays language-agnostic and only ever reasons in English (see [12-multilingual-architecture.md](12-multilingual-architecture.md)).

Continue to [07-class-diagram.md](07-class-diagram.md).
