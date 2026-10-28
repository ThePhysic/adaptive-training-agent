# F0 — Reconciled architecture proposal

**Status:** proposed F0 baseline, implementation blocked until owner approval.

## Modularity and authority

```text
React + TypeScript (narrow review/approval interface)
  | HTTPS JSON + direct POST text/event-stream (fetch + AbortController)
  v
One Python FastAPI process, localhost-bound synthetic identity for F1
  |-- API and owner authorization
  |-- Request-scoped typed orchestration, provider adapter (fake default)
  |       |-- validated, bounded READ tools (catalog; profile/history)
  |       |-- versioned prompt and typed plan candidate
  |       `-- independent deterministic validation / bounded repair
  |-- Ephemeral candidate store (single process; TTL ~30min)
  |-- Domain approval transaction and owned plan-history services
  |-- Local evaluation/template baseline + metadata-only spans
  v
PostgreSQL: explicitly saved profiles; immutable approved plans;
            approval/idempotency/audit; completion/feedback (F2)

Later opt-in: real provider, LangGraph comparison, Langfuse single export path,
short-lived AWS deployment (only after separate gate).
```

The backend is a **modular monolith**. A model may suggest a plan and choose read-only catalog tools; it cannot approve, persist, select identity or relax deterministic constraints. The database is authoritative for user-owned durable records, **not** a LangGraph checkpoint or an SSE `done` event.

## Proposed modules, not premature package boundaries

1. `api/` — strict request/response contracts, identity/authorization, SSE, error mapping, limits.
2. `domain/` — supported vocabulary, catalog provenance and constraint validator, duration formula, bounded prescription templates.
3. `agent/` — explicitly named request states, fake/real model adapter interface, validated read-tool dispatcher, repair and whole-request budget owner.
4. `persistence/` — explicit profile Save, plan approval transaction, immutable history, idempotency and audit.
5. `evaluation/` — local datasets, template baseline, scorers, manifests, honest evidence classification.
6. `observability/` — local metadata-only stage/request correlation; one future Langfuse/OTel export path, disabled by default.
7. `web/` — profile save, progress/review/revise/approve/history, cancellation and errors.

No separate worker, broker, Redis, vector DB or persisted run manager in F1. The F2/F3 **LangGraph comparison** remains a deliberate learning exercise; a graph does not own approved-plan persistence or replace authorization.

## State/data/consent ownership

| Record | Initial persistence | Source of consent and authority |
| --- | --- | --- |
| Versioned curated catalog | Local checked-in data or DB, with source/license/version | Maintainer-curated; untrusted descriptions never become instructions |
| Profile | PostgreSQL, revisioned | Explicit user **Save** action; owner derived from server identity |
| Generation request / free-form conversation | Not stored by default | Used transiently to generate; redact/sanitize logs and provider data per separately approved policy |
| Candidate and revision | Single-process bounded in-memory store; proposed 30-min TTL | Generation permits temporary processing, **not** durable approval; owner + opaque ID + revision + canonical hash + snapshot/context versions |
| Approved plan | Immutable PostgreSQL snapshot | Explicit **Approve** action, revision-bound transactional commit |
| Approval/audit/idempotency | PostgreSQL, in same transaction as plan | Minimal records retained with approved plan until account deletion; no secret-bearing content |
| Completion/feedback | PostgreSQL from F2 | Explicit separately authenticated **Submit** action |
| Local operational traces | Allowlisted metadata with separate proposed 14-day retention | No raw user text, prompt, plan, tokens, HTTP headers, URLs with PII or exported user identifiers by default; external export separate approval |

Candidate validity/revision/expiry is now governed by [`13-f0-candidate-approval-contract.md`](13-f0-candidate-approval-contract.md): one in-process guard per lineage; old candidate is superseded **only upon successful revision publication** under that guard; approval holds the same guard across a bounded database transaction. Failed revision does not invalidate the still-live old candidate. Profile freshness is locked/compared at DB commit, while catalog/validator versions remain fixed for the process lifetime. No persistent chat, checkpoint or draft without a newly approved data policy.

The in-memory candidate store is **intentionally single-process**. Enforce one API worker and localhost-only development binding; restart or TTL expiration loses unapproved candidates. User must regenerate/review. Multi-replica deployment requires a separately reviewed persistent candidate architecture and retention/consent rule.

## Request-scoped orchestration and SSE

Named stages: `authorize → context read → bounded model read-tool selection / draft → validate (optional one repair) → ready | failed | cancelled`. Approval is a *different HTTP request* and a database transaction. Only independent reads may overlap; profile-dependent catalog filtering waits for profile resolution. Optional history read failure may degrade explicitly; profile/catalog errors cannot produce a misleading plan.

**Candidate routes (review and lock during F1 contract task):**

- `GET /api/v1/profile`; `PUT /api/v1/profile` for explicitly saved revisioned preferences.
- `GET /api/v1/exercises` for bounded, filtered catalog reads.
- `POST /api/v1/drafts/stream` for request-scoped SSE generation (no durable run ID).
- `POST /api/v1/drafts/{candidate_id}/revise/stream` for one bounded revision producing a **new** candidate and invalidating the old one.
- `POST /api/v1/drafts/{candidate_id}/approve` for explicit transactional idempotent commit.
- `GET /api/v1/plans/{plan_id}` and `GET /api/v1/plans` for authoritative durable read/history.
- F2: `POST /api/v1/plans/{plan_id}/completions` and `/feedback`.
- `/health` and `/ready` with distinct liveness/readiness semantics.

Browser client: `fetch` POST stream with `AbortController` and a real SSE parser handling split UTF-8 sequences, multi-line `data`, arbitrary chunk splits and bounded buffered event sizes. Native `EventSource` is not the chosen POST-with-body client. Use the typed terminal outcome contract in [`14-f0-remaining-contract-clarifications.md`](14-f0-remaining-contract-clarifications.md): `done.payload.outcome = plan | clarify | abstain | error`; only `plan` has a validated draft and an approvable candidate; missing `done` at EOF disables approval. `done` means generation terminated **not plan approved**. Do not render unvalidated partial plans as actionable. Heartbeats are metadata-only.

Auth/input failures **before** streaming return standard HTTP errors; failures **after** headers use sanitized typed SSE errors, with unexpected EOF treated as incomplete. Disconnect/cancel releases/awaits local tasks and provider connections; upstream cancellation cannot guarantee a refund or suppression of an already-issued request. No replay/resume or automatic **whole-request** generation retry in F1. Bounded provider continuation, one repair or transport retry all consume the **same three-provider-attempt request budget**, per contract 14; user-triggered generation/revision is a new request.

Use a FastAPI release with documented SSE support, select/lock a compatible version in F1. FastAPI's native SSE documentation notes addition in 0.135.0: https://fastapi.tiangolo.com/tutorial/server-sent-events/. No version assumed installed at F0.

## Model read tools and validator

- `search_exercises(filters)` — **actual model-selectable** bounded read call validated against server-derived supported equipment/exclusions, with opaque stable IDs and strict result caps.
- `get_recent_workouts(limit)` — optional app-controlled owned history read; may be a tool only if it adds real value; server chooses owner, never model text.
- `get_user_preferences` — service-owned read, not model-supplied identity.
- Application validator always runs, regardless of model tool behavior. A purported `validate_plan` call cannot bypass enforcement.
- **Never register** `approve_plan`, `submit_plan`, `record_feedback`, or other durable writes as model tools in F1.

Fake provider must model the same typed tool-call/result envelopes, usage counters, finish reasons and error taxonomy that a real adapter will later expose. Reject unsupported fields, unknown tools/IDs, unbounded arguments and attempts; distinguish validation errors, provider refusal, transport errors, timeout, cancellation and exceeded budget. Do not design a general multi-provider framework.

## Approval transaction: required in F1

The normative concurrency and procedural contract is [`13-f0-candidate-approval-contract.md`](13-f0-candidate-approval-contract.md). F1 must implement and test it, including:

1. Authenticate and compute a bounded canonical fingerprint; **query committed owner-scoped idempotency result before accessing the transient candidate**. Matching committed retry returns the same plan after expiry/restart; mismatched payload returns `409 idempotency_mismatch`.
2. For a new key, acquire the in-process **per-lineage guard**, check candidate ownership, state/revision/hash and expiry **at guard acquisition**, and prevent revision publication or expiry during the bounded DB transaction.
3. Revalidate against the frozen catalog/validator, lock the owned profile row in the transaction and compare the saved-profile revision. Commit a unique immutable plan, approval identity, idempotency result and minimal audit together; DB commit is the approval linearization point.
4. Successful revision publication winning the guard first supersedes the old candidate. Approval winning first prevents subsequent revision publication. Failed revision does not revoke a still-valid old candidate. Different-key approval loser gets stable `409 candidate_already_approved`.
5. Barrier/fake-clock tests prove both race orders, expiry acceptance edge, Save-vs-Approve, same/different key conflicts, rollback and persisted restart retry. No exactly-once LLM/network claim.


## Deployment/resilience boundary

Local development in Docker/Compose, one API process, PostgreSQL; tests/CI offline with no credentials and network egress prohibited. F4 may choose a priced, approved single-host AWS topology or ECS/Fargate and managed database only after confirming the state/replica and security implications. A local Docker demo is not a production deployment.
