# 1. Complete Software Architecture

## 1.1 Framing

NyayaOS is not a chatbot with a system prompt. It is an **AI legal operations platform**: a durable, resumable, multi-agent pipeline that turns a raw incident description into a full case file — timeline, applicable law, evidence assessment, risk profile, strategy, drafted documents, lawyer matches, and an adversarially-tested opinion — with every step logged, typed, and independently testable.

Three architectural commitments drive every decision below:

1. **No agent is a monolithic prompt.** Each agent has one responsibility, one structured output contract, and can be tested/replaced in isolation.
2. **No business logic lives in FastAPI routes.** Routes translate HTTP ↔ application services. Services orchestrate repositories, agents, and the LangGraph runtime.
3. **Every agent output is a typed contract (Pydantic v2), never free text.** The graph state, the database, and the API all speak the same schemas.

## 1.2 Clean Architecture layers

```
┌─────────────────────────────────────────────────────────────────┐
│  INTERFACE LAYER                                                  │
│  FastAPI routers · request/response DTOs · WebSocket/SSE          │
│  streaming endpoints · dependency wiring (Depends)                │
├─────────────────────────────────────────────────────────────────┤
│  APPLICATION LAYER                                                 │
│  Use-case services (CaseService, RiskService, ...) · LangGraph     │
│  orchestration entrypoint · background task dispatch · DTO<->      │
│  domain mapping                                                    │
├─────────────────────────────────────────────────────────────────┤
│  DOMAIN LAYER                                                      │
│  Entities & value objects (Case, Evidence, Timeline, RiskProfile)  │
│  Domain services (pure logic, no I/O) · Repository INTERFACES      │
│  (ports) · Domain events                                           │
├─────────────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE LAYER                                              │
│  SQLAlchemy repository IMPLEMENTATIONS · Alembic migrations ·      │
│  Redis cache/rate-limit adapters · Vector store adapter (Chroma/   │
│  FAISS) · Gemma LLM client (LangChain ChatModel wrapper) ·         │
│  external APIs (lawyer directories, geocoding)                     │
└─────────────────────────────────────────────────────────────────┘
```

Dependency rule: **arrows point inward.** Infrastructure depends on domain interfaces, never the reverse. Application depends on domain. Interface depends on application. The domain layer imports nothing from FastAPI, SQLAlchemy, or LangChain — it is plain Python + Pydantic value objects, so it is trivially unit-testable without spinning up a DB or an LLM.

Agents themselves sit in their own vertical (`agents/`), consumed by the application layer through a thin `AgentPort` interface — this keeps LangGraph/LangChain specifics out of the domain and lets the graph layer (`graph/`) be swapped or versioned independently of agent logic.

## 1.3 Domain-Driven Design: bounded contexts

| Bounded Context | Owns | Key aggregates |
|---|---|---|
| **Identity & Access** | Users, auth, sessions | `User` |
| **Case Management** | Case lifecycle, intake, timeline | `Case` (aggregate root), `TimelineEvent` |
| **Evidence** | Evidence items, completeness scoring | `EvidenceItem`, `EvidenceReport` |
| **Legal Knowledge (RAG)** | Statute corpus, retrieval, citations | `LegalProvision`, `Citation` |
| **Risk & Strategy** | Risk scoring, strategy options | `RiskProfile`, `StrategyPlan` |
| **Document Generation** | Drafted legal documents | `Complaint`/`Document` |
| **Lawyer Directory** | Lawyer profiles, matching | `Lawyer`, `CaseLawyerMatch` |
| **Adversarial Simulation** | Opposition/counter/judge rounds | `OppositionRound`, `JudgeOpinion` |
| **Memory** | Conversation & long-term memory | `ConversationMemory`, `LongTermMemory` |
| **Observability** | Agent execution logs | `AgentLog` |

`Case` is the aggregate root that most other contexts hang off via `case_id` foreign keys — but each context owns its own repository and service, so (for example) the Lawyer Directory context could be split into its own microservice later without touching Case Management.

## 1.4 Cross-cutting patterns

- **Repository Pattern**: every persistence access goes through an abstract repository interface defined in `domain/repositories/`, implemented in `infrastructure/repositories/`. Services never import SQLAlchemy directly.
- **Service Layer**: one application service per bounded context (`CaseIntakeService`, `EvidenceService`, `RiskService`, `StrategyService`, `DocumentService`, `LawyerService`, `AdversarialService`, `MemoryService`). Routes call exactly one service method per endpoint.
- **Dependency Injection**: FastAPI `Depends()` graph rooted in `core/container.py`. Services receive repositories, the LLM client, and the vector store via constructor injection — nothing is globally imported, everything is mockable in tests.
- **Unit of Work**: an `AsyncSession`-scoped Unit of Work wraps each request/graph-node so multi-repository writes (e.g., Risk Assessment writing `risk_scores` + `agent_logs`) commit atomically.
- **CQRS-lite**: write paths go through services + repositories; the `GET /dashboard/{id}` read path uses a dedicated read-optimized aggregation query (a `DashboardReadRepository`) rather than reusing write-side repositories, since the dashboard joins ~10 tables.

## 1.5 Tech stack rationale (summary — full rationale in [10-design-decisions.md](10-design-decisions.md))

| Concern | Choice |
|---|---|
| Web framework | FastAPI (async, Pydantic v2 native) |
| ORM | SQLAlchemy 2.0 async + Alembic |
| Database | PostgreSQL (+ pgvector optional path) |
| Cache / rate limit / broker | Redis |
| Agent orchestration | LangGraph (stateful, cyclic, checkpointed) |
| Agent/LLM plumbing | LangChain (structured output, tool calling) |
| LLM | Gemma 3 / Gemma 3n, served via vLLM or Ollama |
| Vector store | ChromaDB (dev) → pgvector/Qdrant (scale path) |
| Auth | JWT (access + refresh), OAuth2 password/bearer flow |
| Containerization | Docker + Docker Compose (Postgres, Redis, API, worker, vLLM) |
| Background tasks | Celery or Arq (Redis-backed) for long pipelines |
| Observability | structlog + OpenTelemetry traces + Prometheus metrics |

Continue to [02-agent-architecture.md](02-agent-architecture.md).
