# F0 — Reconciliation of Codex independent review

**Status:** proposed joint resolution, pending owner approval. Input: `07-codex-independent-review.md` (2026-10-23). Original planning proposal documents 00–04 were revised; historical 05/06 and Codex 07 remain unchanged.

## Summary: accept, adapt, defer

- **Accept:** D01 modular monolith, D02 narrow React, D03 request-scoped POST SSE, D05 PostgreSQL authority/ephemeral candidate, D06 one fake-first adapter, D07 early eval and minimal tracing, D09 bounded catalog, D10 application-owned approval, D12 gated pilot.
- **Accept with role-targeted adjustment:** D04 defer production LangGraph **but require a bounded hands-on graph/checkpoint comparison by F2/F3** rather than dropping framework learning. D08 defer AWS spend, but retain an explicit optional evidence track for operated AWS, not just a Terraform file.
- **Defer:** D11 shared evaluation-package extraction until second consumer is inspected and a concrete interface need appears.
- **Evidence adjustment:** mock-only F1 is valid local engineering evidence; full applied-AI role coverage is not claimed until an approved real LLM tool/structured-output experiment and one actual Langfuse/OTel tracing/evaluation integration have been demonstrated. User must opt in to spend/export before such work.

## Review issue resolution map

| Review item | Resolution in revised documents | Verification/evidence |
| --- | --- | --- |
| R1 transactional idempotency | `01` approval transaction, `02` F1 gate, `09` F1 tests | Concurrent same/different keys, rollback and restart retry yield one durable plan |
| R2 consent and storage | `00` explicit Save/Approve/Submit; `01` data inventory; `03` privacy | No raw prompt/chat retention; 30m in-memory candidate, clearly stated restart loss |
| R3 safety and supported scope | `00` bounded adult/general-goal envelope; `03` duration/safety fixtures | Invalid/infeasible/medical requests clarify/abstain; no training-safety claim |
| R4 budget ceilings | `04` whole-request limits and independent spend approvals; `09` egress tests | Limits hold under error/cancellation, no live invocation from CI |
| R5 access, telemetry, deletion | `01` two-local-principal isolation; `03` sink gate; `02` F5 | No wrong-owner access; exporters pass synthetic canary tests; pilot blocked until real auth |
| R6 streaming/run complexity | `01` direct POST SSE, no persistent run manager | Typed event/parser/error/EOF/abort tests, explicit no replay/resume |
| R7 early evidence | `02` F1 baseline/manifests/tracing; `03` 40-case design | Deterministic baseline and per-case scores from first working milestone |
| R8 authentic tools/fan-out/judge | `00` coverage table; `01` read-tool dispatch; `03` honest live gate; `02` F2 experiment | Recorded *real* model-selected tool only after approval; local HTTP fan-out labeled fake |
| R9 cloud risks | `04` priced F4 alternatives and resource categories; `02` F4 | Teardown, rollback/restore, measured recovery, delayed alarm warning |
| R10 defer premature add-ons | `01`,`02`,`04` no queue/vector DB/durable run/shared package by default | Each adoption needs documented problem and comparative evidence |

## Decisions that deserve owner attention before F1

1. **Supported envelope:** recommend adult general wellness, strength/conditioning goals, bodyweight or dumbbells, 2–4 days/week, 20/30/45 minutes, beginner/intermediate. Catalog record and prescription bounds require review; not a medical guarantee.
2. **Temporary draft model:** recommend 30-minute single-process candidate with owner/revision/hash and transparent loss on restart; no durable chat or checkpoints in F1.
3. **Approval identity:** recommend unique `(owner,candidate_identity)` plus `(owner,operation,idempotency_key)` + canonical payload fingerprint, one immutable snapshot, key retention with plan until deletion.
4. **Auth:** local synthetic principals and loopback-only F1; mandatory maintained real auth + CSRF/token policy before external users.
5. **Budgets/privacy:** recommend numerical caps in `04`, 14-day local metadata retention, no content export by default; separate explicit numeric approval for every live category.
6. **Proof standard:** count fake and local results honestly, do not infer agent quality from deterministic success, no AWS operations claim without apply and exercises.

These are recommended **F0 acceptance decisions**, not a hidden authorization to start implementation. The next step is a read-only consistency review (`10-final-consistency-review-prompt.md`) and then owner's explicit sign-off.
