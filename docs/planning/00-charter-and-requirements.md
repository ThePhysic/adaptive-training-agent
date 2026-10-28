# F0 — Revised charter, scope, and Future requirement mapping

**Status:** reconciled proposal; owner sign-off pending. Codex independent review: `07-codex-independent-review.md`. Decision rationale: `08-reconciled-decisions.md`.

## Why build this?

Build one working, bounded, personalized **adult general-wellness workout planning** application to practice applied AI end-to-end: typed Python APIs, genuine read-only model tool calling, structured outputs, streaming, deterministic checks, explicit state changes, meaningful evaluation, privacy-aware tracing, controlled real-model experiments, and eventually reproducible operation. The point is professional engineering experience and defensible evidence, not inventing an agent framework, reproducing an employer product, or making medical claims.

The user has other relevant portfolio projects (visual inspection, computer use, security agents); reuse concepts and independently inspected suitable code only. Do not assume reusable packages without examining exact files, licenses and tests. Other repositories are outside scope unless the owner provides read-only paths and authorizes inspection.

## Supported user-facing envelope (proposed F0 baseline)

- **Population:** self-identified adults 18+ seeking *general* non-medical fitness planning. The product is not for clinical, rehabilitative, pregnancy-specific, or injury-management planning. No medical history, diagnosis, prescription, biometrics or dietary information should be requested.
- **Goals:** `general_strength` or `general_conditioning`. Do not claim that a suggested plan is clinically safe, exercise-science validated, or will achieve a training outcome.
- **Equipment:** `bodyweight` or `dumbbells_and_bodyweight`; model exercises accordingly. Catalog includes explicit equipment requirements and exclusion tags.
- **Schedule:** 2–4 days per week, 20, 30 or 45 **planned** minutes per session. These are proposed UI presets; out-of-envelope requests must clarify or decline rather than silently change values.
- **Experience:** `beginner` or `intermediate`; prescriptions come from bounded, reviewed templates. No aggressive progression, maximal efforts, or specific injury adjustments.
- **Preferences/exclusions:** selected catalog IDs or supported tags, with bounded counts. Arbitrary free text may express preferences but cannot silently create new constraint semantics.
- **Catalog:** begin with approximately 20–40 original/licensed, reviewed exercise records and a documented supported goal/equipment matrix. If it cannot meet a constraint, do not invent an exercise or relax the constraint.
- **Duration:** validator accounts for warm-up, prescribed work/rest, transitions and cooldown, with an explicitly documented calculation and rounding tolerance. A planned duration is an estimate, not a measured completion time.

**F0 domain contract now specified for owner ratification:** see [`12-f0-domain-contract.md`](12-f0-domain-contract.md). It defines all eight matrix rows, exact prescription fields, duration arithmetic and boundary fixtures. Its more precise limits supersede the summary above. These are product-scoping/fixture rules—not verified fitness-safety conclusions. F1-01 derives types from contract 12; do not defer substantive domain decisions to F1-02.

## Single user journey

1. A synthetic local principal explicitly **saves** supported profile preferences. No health history required.
2. User requests a weekly plan via a simple UI. Independent context reads and a bounded **read-only** exercise-catalog tool supply the planner.
3. A template baseline and a fake-by-default agent can produce typed proposals; a live provider later must demonstrate **actual model-selected tool calls** in approved tests. All output passes an independent deterministic validator.
4. The API streams typed **progress** followed by **one final validated candidate**, or a classified error. No unvalidated plan fragment is treated as actionable. A stream finishing is never approval.
5. User reviews and optionally requests one bounded revision; revision produces a new immutable candidate identity. User deliberately approves the exact reviewed candidate.
6. Approval atomically commits an immutable snapshot, bound to owner/candidate revision/hash and idempotency key; repeat or racing approval requests cannot duplicate the plan. Read and history work after process restart.
7. Subsequent completion/feedback submission (F2) is a separately authorized action. External participants require the F5 privacy/authentication release gate.

## Future role coverage and evidence quality

| Requirement | Evidence to implement | Limit of a local/mock-only result |
| --- | --- | --- |
| Python, Pydantic, async HTTP | Typed FastAPI service, strict contracts, async I/O and failure/cancellation tests | No large-company service ownership |
| Agents with tool/function calling | Model-selected bounded catalog read, validated arguments, structured final proposal | Fake dispatch does not prove real LLM tool choice |
| Parallel API orchestration | Controlled overlap/cancel/failure tests with independent fake HTTP reads; live integrated fan-out if later justified | Local fakes are not production external-service traffic |
| Streaming | POST SSE with `fetch`, typed events, incomplete-stream and cancellation tests | Local SSE doesn't prove real provider stream quality |
| Evaluation and judge | 40-case synthetic corpus, template baseline, human rubric; later small live model and optionally calibrated judge | Offline tests cannot establish model helpfulness or judge behavior |
| Tracing and operations | Correlated allowlisted metadata traces, diagnosed fault; later real Langfuse export | Local traces do not prove hosted observability |
| Cost and performance | Whole-run deadline/attempt/tool/token/concurrency caps; measured latency and cost per task | Fake provider timings/costs must be labeled simulated |
| LangGraph or similar | Typed orchestration in F1 plus bounded LangGraph checkpoint/resumption comparison in F2/F3 | No production LangGraph claim unless actually integrated |
| AWS/IaC | Cost-approved Terraform plan, deployment, rollback, teardown and restore drill (F4) | Terraform alone does not prove AWS operation |
| Product collaboration | Synthetic UX feedback initially; later consenting adults and measured iterations | Small pilot does not prove exercise or clinical effectiveness |

## Non-goals and non-negotiables

- No medical assessment, injury-specific recommendations, personal health records, medications, biometrics, dietary prescriptions, claimed safety certification, or training-effectiveness claims.
- No autonomous write tools or model-controlled authorization. Only explicit application-level approval commits plans.
- No queue, vector database, multiple LLM providers, self-hosted Langfuse, persistent conversation memory, durable run replay, native mobile app, broad exercise marketplace, or premature microservices in F1.
- No real user data, paid model/LLM judge, hosted telemetry, or AWS resources without separate approval and source/destination/retention review. Local tests/CI run with zero credentials and blocked external egress.
- No importing secrets, real user data or logs from sibling projects; no code reuse without inspected provenance/license and compatibility.

## Completion labels (avoid misleading claims)

- **F1 local vertical slice:** complete offline mocked/synthetic correctness, not real model competence.
- **Future-targeted applied AI evidence:** measured *real* model tool calls, structured outputs, evaluations, at least one real traced and diagnosed failure, and a defended framework tradeoff, contingent on explicit live/telemetry approvals.
- **AWS operations evidence:** achieved only after actual approved deployment, testing, rollback/restore and teardown; a plan is not sufficient.
- **Product outcome evidence:** achieved only after consented participation and clearly defined non-clinical measurements.
