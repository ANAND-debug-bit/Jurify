# 5. API Specification

> **Revision note (v2)**: adds a `language` field to request bodies that feed agents, splits the opposition/counter/judge branch into an explicit opt-in endpoint (Change 6), adds an evidence-resume flow (Change 7), and adds endpoints for emergency guidance and government scheme matching.

All endpoints are async, versioned under `/api/v1`, return JSON (except SSE streaming endpoints), and require a `Bearer` JWT except `/auth/*`. Rate limiting applies per-user via Redis token bucket (see [10-design-decisions.md](10-design-decisions.md)).

## 5.1 Auth

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/auth/register` | Create user |
| POST | `/api/v1/auth/login` | Issue access + refresh JWT |
| POST | `/api/v1/auth/refresh` | Rotate access token |
| POST | `/api/v1/auth/logout` | Revoke refresh token |

## 5.2 Case pipeline

| Method | Path | Purpose | Request | Response |
|---|---|---|---|---|
| POST | `/api/v1/case` | Create a new case shell, start the graph thread | `CreateCaseRequest{title?, incident_category?, preferred_language?, max_rounds?}` | `CaseCreatedResponse{case_id, status}` |
| POST | `/api/v1/case/intake` | Send/continue intake conversation (drives `case_intake` → `emergency_detection` → Supervisor; may be called repeatedly until `status` leaves `INTAKE_IN_PROGRESS`) | `IntakeMessageRequest{case_id, message, language?}` | `IntakeResponse{case_profile, missing_fields, status, emergency_guidance?}` (SSE variant streams agent tokens) |
| POST | `/api/v1/case/research` | Trigger/re-trigger Legal Research Agent + Verification Agent for a case already past intake | `{case_id}` | `VerifiedLegalResearchResult` |
| POST | `/api/v1/case/evidence` | Submit evidence items and trigger Evidence Analysis Agent. If the Supervisor previously paused the case awaiting evidence (`status = AWAITING_EVIDENCE_UPLOAD`), this call **resumes** the checkpointed graph from `evidence_analysis` rather than starting fresh (Change 7) | `SubmitEvidenceRequest{case_id, items: list[EvidenceInput]}` | `EvidenceReport{..., still_awaiting_upload: bool}` |
| POST | `/api/v1/case/risk` | Trigger Risk Assessment Agent | `{case_id}` | `RiskAssessment` |
| POST | `/api/v1/case/strategy` | Trigger Legal Strategy Agent | `{case_id}` | `StrategyPlan` |
| POST | `/api/v1/case/government-schemes` | Trigger/re-trigger Government Scheme Agent explicitly (also runs automatically in the main pipeline — see Change 5) | `{case_id}` | `GovernmentSchemeReport` |
| POST | `/api/v1/case/complaint` | Trigger Complaint Generation Agent for a chosen strategy | `GenerateComplaintRequest{case_id, strategy_option_id, document_type}` | `list[GeneratedDocument]` |
| POST | `/api/v1/case/lawyers/recommend` | Explicitly request Lawyer Recommendation Agent (Change 8 — user-requested path; also runs automatically when the Supervisor determines representation is needed) | `{case_id}` | `list[LawyerMatch]` |
| **POST** | **`/api/v1/case/stress-test`** | **NEW (Change 6)** — "Stress Test My Case" button. Runs the opt-in Opposition Lawyer ↔ Counter Strategy ↔ Judge subgraph against the case's existing checkpointed state; never runs automatically | `RunStressTestRequest{case_id, max_rounds?}` | `202 Accepted {task_id}` → poll `/case/{id}/status`, result in `StressTestResult{opposition_rounds, judge_opinion}` |
| GET | `/api/v1/case/{id}` | Fetch full case record (profile, timeline, status, `preferred_language`) | — | `CaseDetailResponse` |
| GET | `/api/v1/dashboard/{id}` | Aggregated read-model: everything above joined for the UI, translated to `?lang=` if provided (default: case's `preferred_language`) | — | `DashboardResponse` |
| POST | `/api/v1/case/{id}/run` | Fire the **main** graph end-to-end as a background task (intake → explainability; excludes the opt-in stress-test subgraph) | `{}` | `202 Accepted {task_id}` |
| GET | `/api/v1/case/{id}/status` | Poll background pipeline progress | — | `{status, current_node, progress_pct}` |
| GET | `/api/v1/case/{id}/stream` | SSE stream of node-transition events for live dashboard updates | — | `text/event-stream` |

Supporting resources:

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/lawyers` | Search lawyer directory (query params: `city`, `specialization`, `min_rating`, `language`) |
| GET | `/api/v1/case/{id}/documents` | List generated documents |
| GET | `/api/v1/case/{id}/documents/{doc_id}` | Fetch one document (rendered, translated per `?lang=`) |
| GET | `/api/v1/case/{id}/emergency` | **NEW** — latest `EmergencyAssessment` + `EmergencyGuidance` for the case, if any (owner-only, no auth delay tolerated — see design notes) |
| GET | `/api/v1/case/{id}/explainability` | **NEW** — full `ExplainabilityReport`, one item per major conclusion (Change 3) |
| GET | `/api/v1/case/{id}/logs` | Agent execution trace, including Supervisor routing decisions (for debugging/audit, owner-only) |

## 5.3 Design notes

- **Per-agent POST endpoints exist alongside the single `/case/{id}/run` orchestrator endpoint** deliberately: the per-agent endpoints support re-running one stage (e.g., user adds evidence later, only `evidence` + everything downstream needs to re-run — see cascade note below), while `/run` is the "just do the whole pipeline" convenience path most clients will use after intake.
- **Cascading re-runs**: calling `/case/evidence` after risk/strategy already ran marks those downstream stages `stale` (not deleted) in the response `CaseDetailResponse.stale_stages`; the client decides whether to re-trigger them. This is a service-layer rule (`CaseService.mark_downstream_stale`), not a DB trigger — keeps it explainable and testable.
- **Long pipeline runs go through background tasks** (Celery/Arq), not a blocking request — `/case/{id}/run` and `/case/stress-test` return `202` immediately with a `task_id`; the client polls `/case/{id}/status` or subscribes to `/case/{id}/stream`. Only the per-agent single-step endpoints (`/case/research`, `/case/risk`, etc.) may respond synchronously, since a single agent call is bounded (~seconds). `/case/stress-test` is backgrounded specifically because it can involve up to `max_rounds` × 2 agent calls plus the Judge Agent — noticeably longer than a single-agent call, and it's explicitly user-triggered so a 202-and-poll UX (a visible "stress test running…" state) is expected, not a surprise.
- **`/case/evidence` is dual-purpose by design** (Change 7): the same endpoint both submits fresh evidence *and* resumes a paused case. The service layer checks `case.status == AWAITING_EVIDENCE_UPLOAD` to decide whether this is a resume-from-checkpoint or a first submission — no separate `/case/evidence/resume` endpoint exists, because from the client's perspective "the user just added evidence" is the same action either way; only the graph-internal handling differs.
- **`/case/intake` response can carry `emergency_guidance`** inline rather than requiring a second round-trip to `/case/{id}/emergency` — emergency guidance must reach the user as fast as possible (§3.7 of the workflow doc), so it rides on the same response that triggered detection. `/case/{id}/emergency` exists for the dashboard to re-fetch it later, not as the primary delivery path.
- **Streaming**: `/case/intake` and `/case/{id}/stream` use Server-Sent Events, not WebSockets — SSE is one-directional (server→client), simpler to load-balance (works over plain HTTP/1.1 keep-alive), and matches the actual need (token streaming + node-transition events); no bidirectional channel is required.
- **`language` request field**: optional on every endpoint that accepts free text (`/case/intake`) or renders content (`/dashboard/{id}?lang=`, document fetch). When omitted, falls back to `case.preferred_language`, then `user.preferred_language`, then `DEFAULT_LANGUAGE` from config. See [12-multilingual-architecture.md](12-multilingual-architecture.md) for the detection/translation pipeline this feeds.
- **Auth model**: `python-jose`-issued JWTs, `sub=user_id`, short-lived access token (15 min) + rotating refresh token stored hashed in Redis with TTL — stateless verification on every request, revocation only needed for refresh tokens.
- All list/collection responses are paginated (`limit`/`offset` or cursor for `agent_logs`) — no unbounded `SELECT *`.

Continue to [06-folder-structure.md](06-folder-structure.md).
