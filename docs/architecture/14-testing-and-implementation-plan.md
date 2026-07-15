# 14. Testing Strategy & Implementation Plan (Changes 13, 14)

## 14.1 Testing strategy

Testing is not a phase at the end — every module below ships with its own tests in the same unit of work that introduces it (Change 13). Five test categories, each with a distinct purpose and a distinct place in `tests/`:

| Category | Location | Scope | Speed | Depends on |
|---|---|---|---|---|
| **Unit** | `tests/unit/` | Single function/class in isolation — domain entities, one agent's `_build_input`/`_parse_output`, one Supervisor routing decision given a hand-built `CaseState` | Milliseconds | Nothing external — LLM calls are mocked/faked |
| **Agent** | `tests/unit/agents/` | One agent's full `run()` against a **fake LLM** that returns canned structured output — verifies prompt construction, retry-on-invalid-schema, logging side effect | Milliseconds | Fake `ChatModel`, no network |
| **Graph** | `tests/unit/graph/` | Routing logic in isolation — `supervisor_route()` given various `CaseState` fixtures returns the expected node; `route_adversarial_loop` bounds correctly at `max_rounds` | Milliseconds | Fake agents wired into a small test graph |
| **Repository** | `tests/integration/` | Real SQL against a real (ephemeral) Postgres — repository methods actually persist/query correctly, migrations apply cleanly | Seconds | testcontainers Postgres |
| **API** | `tests/e2e/` | Full FastAPI app + real DB + faked LLM layer — a request hits a route and the whole service→repository→graph chain executes | Seconds | testcontainers Postgres + Redis, `httpx.AsyncClient` |

**Fake vs. mock LLM**: agent and graph tests use a `FakeChatModel` (a `BaseChatModel` subclass returning a pre-registered structured response per test) rather than `unittest.mock.Mock` — this exercises the *actual* LangChain `.with_structured_output()` code path (including Pydantic validation) instead of bypassing it, so a schema mismatch between an agent's prompt-building and its own output contract is caught by the test, not just by production traffic.

**What is explicitly not covered by automated tests**: actual Gemma output quality/correctness (a legal reasoning judgment call, not a unit-testable assertion) — that's evaluated separately via a golden-case eval set (a future addition, not part of this architecture pass) and manual review, not `pytest`.

## 14.2 Definition of "module complete"

A module is not done until:
1. Code compiles / imports cleanly (`python -m app.<module>` or equivalent has no import errors).
2. `mypy` passes on the module (or the codebase's agreed strictness level).
3. Unit tests for the module exist and pass.
4. Where the module touches the DB, an Alembic migration exists and applies cleanly against a fresh database.
5. Nothing downstream that depends on this module is left half-wired (no dangling imports of not-yet-built code left in a broken state — stub with a clear `NotImplementedError` and a tracking note if a forward dependency is unavoidable).

## 14.3 Implementation order (Change 14)

Strict order below. **Stop after each numbered module, verify per §14.2, run its tests, report status, then proceed** — this applies even when consecutive modules are small, per explicit instruction not to generate unfinished or unverified code.

1. **Config** — `core/config.py`, `.env.example`, settings tests
2. **Logging** — `core/logging.py` (structlog config, request-id correlation)
3. **Dependency Injection** — `core/container.py` skeleton (wiring added incrementally as each layer exists)
4. **Database** — `database/session.py`, `database/base.py`, `database/unit_of_work.py`, Alembic bootstrap
5. **Models** — SQLAlchemy ORM models for all tables in [04-database-design.md](04-database-design.md) (v2, including new tables), + initial migrations
6. **Schemas** — Pydantic v2 DTOs per [08-pydantic-schemas.md](08-pydantic-schemas.md) (v2, including new schemas)
7. **Repository Layer** — domain repository interfaces + SQLAlchemy implementations
8. **Services** — application services (no agents wired yet — services can be tested against repository fakes first)
9. **LangGraph** — `graph/state.py`, empty `graph_builder.py` skeleton, checkpointer wiring (nodes added as their agents are built)
10. **Supervisor Agent** — `agents/supervisor_agent.py`, `prompts/supervisor.py`, `schemas/routing.py`, routing unit tests (built early since almost every later node's conditional edge depends on it)
11. **Intake Agent** — Case Intake + Emergency Detection + Emergency Agent (grouped: all three are part of the intake turn, §3.7)
12. **Research Agent** — Legal Research Agent + RAG retriever/vectorstore wiring
13. **Verification Agent**
14. **Evidence Agent** — Evidence Analysis Agent + the adaptive pause/resume node (Change 7)
15. **Risk Agent**
16. **Strategy Agent**
17. **Complaint Generator**
18. **Government Scheme Agent**
19. **Lawyer Recommendation** — including the Supervisor-conditional trigger logic
20. **Explainability Agent**
21. **Opposition Module** — Opposition Lawyer + Counter Strategy + the opt-in stress-test subgraph (Change 6)
22. **Judge Agent**
23. **Dashboard** — `dashboard_service.py` read-model aggregation + `i18n` render-time translation wiring
24. **Authentication** — JWT issuance/verification, `/auth/*` routes
25. **Background Workers** — Celery/Arq wiring for `/case/{id}/run` and `/case/stress-test`
26. **Docker** — Dockerfiles + docker-compose per [13-configuration-and-devops.md](13-configuration-and-devops.md)
27. **Tests** — any cross-cutting/e2e gaps not already covered incrementally by §14.1–14.2 (this step is a sweep, not where testing *starts*)
28. **Documentation** — README, API docs (OpenAPI is auto-generated by FastAPI; this step covers anything OpenAPI doesn't capture — setup instructions, runbooks)

## 14.4 Why this order

- Config → Logging → DI → Database → Models → Schemas → Repositories → Services builds strictly bottom-up through Clean Architecture's dependency rule (§1.2) — nothing in this stretch depends on anything not yet built.
- LangGraph's skeleton (9) comes before any agent so `CaseState` exists as a stable contract before agents are written against it.
- Supervisor (10) comes before the pipeline agents it routes between (11–20) deliberately, even though it's "meta" — every conditional edge added from module 11 onward needs `supervisor_route()` to already exist to wire against.
- Intake/Emergency (11) before Research (12) before Verification (13) before Evidence (14) mirrors the actual data dependency chain in `CaseState`.
- Opposition/Judge (21–22) are last among agents because they're the opt-in subgraph — nothing else in the main pipeline depends on them, so building them last carries zero risk to the critical path.
- Dashboard (23) comes after all content-producing agents exist, since it aggregates all of them.
- Auth (24) is placed after the domain pipeline rather than first, despite being conceptually independent, because it has no dependency on cases/agents at all — building it in parallel-conceptually-but-sequentially-here avoids context-switching away from the agent pipeline mid-build; routes can be stubbed with a dev-only bypass until 24 lands if needed for manual testing earlier.
- Background workers (25) come after the endpoints they backgrounds exist for `/case/{id}/run` (needs the full main graph) and `/case/stress-test` (needs the subgraph from 21).
- Docker (26) comes after there's a working app to containerize, not before.

Continue to implementation — Module 1 (Config) begins next.
