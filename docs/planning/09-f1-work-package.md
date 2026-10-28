# F1 — Offline vertical slice: execution specification (NOT YET AUTHORIZED)

**Purpose:** Convert the reconciled F0 design into concrete, inspectable work when and only when the owner explicitly authorizes F1 and updates local `AGENTS.md`.

## Proposed implementation sequence

| Work unit | Deliverable | Proof needed |
| --- | --- | --- |
| F1-01 contracts and environment | **Implement approved contract `12` domain types, `13` lifecycle/approval identities and `14` stream/budget types before other schemas;** Python/TS locks; local Docker/Compose PostgreSQL; strict Pydantic profile/catalog/draft/error types; seed catalog provenance | Offline startup; migrations; schema negative/unknown-field tests; no credentials or egress |
| F1-02 baseline and validator | **Implement exact formulas/boundaries in `12`, not invent them;** duration calculator; reviewed bounded prescriptions; deterministic template planner; 40 synthetic cases | Hard constraint and unsupported-request fixtures, frozen manifest and per-case baseline output |
| F1-03 identity and persistence | Loopback synthetic identity, versioned explicit profile Save, owned read/history, **per-lineage guard + TTL/revision/reservation state from `13`** | Cross-user tests, candidate caps, revision-publish-vs-expiry barriers, restart-loss behavior |
| F1-04 typed agent flow | Fake default model adapter, real-adapter-shaped tool-call protocol, read-tool dispatch, validated output and repair | Fake tool-selected read and malformed/unknown-call/timeout/budget tests; no autonomous writes |
| F1-05 SSE and web | Direct POST stream, **four terminal outcomes from `14`**, typed client, stop/disconnect, narrow review/revise UX | Chunk/parser/EOF-after-draft bounds, cancellation and no incomplete plan approvable |
| F1-06 approval | **Apply `13` owner-scoped idempotency lookup before transient candidate, lineage lock through transaction, profile row version lock**, immutable readback | Barrier-controlled approve/revise and profile-save races, expiry edge, same/different key races, rollback, restart response-loss retry |
| F1-07 integration, local spans, CI | Metadata correlation, reproducible end-to-end baseline, no egress and stress/fault checks | One owner-visible working journey and complete evidence report with limitations |

Recommended order: **F1-01 → F1-02 → F1-03 → F1-04 → thin F1-06 approval transaction → F1-05 UI/SSE → remainder of F1-06 and F1-07 evidence**. Begin minimal metadata spans with the first backend endpoint. **F1 completion requires all gates**. Do not commit/push or enable cloud/live provider unless separately authorized by the owner.

## API candidates to freeze early

`GET/PUT /api/v1/profile`, `GET /api/v1/exercises`, `POST /api/v1/drafts/stream`, `POST /api/v1/drafts/{id}/revise/stream`, `POST /api/v1/drafts/{id}/approve`, `GET /api/v1/plans`, `GET /api/v1/plans/{id}`, `/health`, `/ready`. The F1 implementation review must finalize status/error schemas, route shapes, and limits before UI/API divergence.

Approval POST requires authenticated principal + opaque candidate identity + revision + canonical content hash + unique idempotency key. Server validates against owned immutable snapshot and versions, not an arbitrary client-submitted plan. Successful retries use the persisted key result even after candidate-store loss. Candidate may not be approved by tool messages or model-generated text.

SSE envelope and terminal discriminated outcomes are normative in `14`: `done.payload.outcome = plan | clarify | abstain | error`; only a validated completed `plan` can be approved. The `draft` preview has no approval-addressable identity; the `done(plan)` payload reveals candidate ID/revision/hash only after server terminalizes and publishes the candidate. At most one validated `draft` per stream; a `draft` without `done` at EOF is **incomplete and non-approvable**. No event replay or durable generation before approval.

## Acceptance and fault matrix

- **Baseline:** 40 versioned synthetic tasks, 24 development and 16 held out; full hard-constraint and abstention/clarification checks; same catalog/template/validator for baseline and agent.
- **Privacy:** requests with fake secret/PII canary never appear in local logs or spans; no unapproved durable draft/chat; user deletion rules documented; two principals cannot access each other's candidate, profile or plans.
- **Persistence:** concurrent approval (same key vs different key), stale profile/catalog, old candidate revision, forged key/hash, rollback on DB failure, response lost after commit, restart retry, lost pre-approval candidate.
- **Tools:** unknown name and args, too many reads, oversized result, bad provider output and refusal, malformed JSON/structured response; validator rejects violations and may do at most one bounded repair.
- **Streaming:** client abort and server task cleanup, 429/5xx/timeout, malformed chunks/split Unicode, multi-line SSE, oversized event, final draft or typed error and terminal completion, no actionable unsafe partial tokens.
- **Budget:** proposed 30s overall, <=4 reads, <=3 provider attempts, <=1 transport retry, <=1 semantic repair, <=16k input and <=4k output tokens, <=1 concurrent run/principal and <=2 global; SDK nested retries disabled or accounted for. Negative tests prove fail-closed even if a test supplies credentials.
- **CI:** no external egress or credentials, determinism independent of system clock and network. Include exact execution commands and dependencies/versions in evidence. Claims limited to fake/local evidence.

## F1 review report format

For each unit: changed paths, concise contract summary, exact test command and result counts, current limitations, costs (zero external by default), screens/UI evidence where relevant, unresolved issues, and recommendation for owner approval of the next unit. If a real model, Langfuse export, AWS, or external user becomes necessary, **stop and request a new category-specific approval**.

## Freeze-before-code priority

The owner must ratify `12`/`13`/`14` during F0. They supersede unspecified domain constraints, approval ordering, and SSE/retry budget ambiguities in older documents. F1-01 must not reinterpret their scope. No implementation or tool access authorized merely by creating this package.
