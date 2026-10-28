# F0 — Reconciled decisions, risks and cost controls

**Status:** recommended decision register; owner must explicitly ratify the full F0 package before F1. Numbers are proposed initial engineering limits, not proof of adequacy. See `08-reconciled-decisions.md` for R1–R10 mapping.

## D01–D12 register

| ID | Recommended disposition | Contract / adoption trigger |
| --- | --- | --- |
| D01 — topology | **Keep** modular monolith | One FastAPI service and database, no worker until justified by durable background task |
| D02 — UI | **Keep, narrow** React/TS | Profile Save, progress, review/revise, Approve, owned history, cancellation; defer dashboards/chat memory |
| D03 — streaming | **Change** to direct POST SSE | No run creation/subscription/replay; final validated draft event; approval via separate JSON endpoint |
| D04 — LangGraph | **Defer in main path, require bounded comparison** | Typed states in F1; F2/F3 synthetic LangGraph checkpoint/resumption experiment and explicit adopt/reject comparison |
| D05 — source of truth | **Keep** PostgreSQL, transient candidates | Profile and approved plan authoritative in DB; immutable in-memory draft TTL; no duplicate checkpointer business state |
| D06 — provider | **Keep, strengthen** fake-first one-provider adapter | Typed tool-call/result, usage/finish reason/errors; actual model-selected read tool in approved live experiment |
| D07 — evaluation/telemetry | **Change sequencing** | Local baseline/corpus/metadata spans F1; one cost/privacy-approved Langfuse export integration F3 |
| D08 — cloud | **Defer provision, retain learning goal** | Local Docker first; compare priced AWS topologies before separate AWS budget/apply approval |
| D09 — catalog | **Keep, bound** | ~20–40 reviewed original/licensed records and explicit supported goal/equipment/experience envelope |
| D10 — approval | **Strengthen, move to F1** | Only server-owned transactional Approve, immutable revision/hash, owner checks, unique candidate+idempotency identity |
| D11 — shared evaluator | **Defer extraction** | Reuse patterns first; extract reusable package only after independently inspected second consumer exists |
| D12 — pilot | **Keep, gated** | Adult volunteers only after real auth, consent, processor/retention, deletion/backup and incident support proof |

## Spend isolation: four permissions that do not follow from F1 approval

1. **Live model interactive use:** named provider/model, region/destination/data handling, official prices checked at use time, explicit numeric ceiling, approved enable switch and credentials.
2. **LLM judge / large-scale evaluation:** a *different* numeric ceiling and experiment plan; never automatically included with interactive approval.
3. **Hosted telemetry/Langfuse:** configured exporter destination, retention, cost, metadata allowlist, leakage canaries, explicit opt-in.
4. **Cloud/AWS:** named region and priced topology, dollar ceiling, estimated operating period, role/resource inventory, rollback/teardown and residual-charge check; no `terraform apply` before permission.

External user pilot is a **fifth distinct permission** and requires completed privacy/auth release criteria even if provider/cloud access is already approved.

### Proposed limits, ratify at F0

| Guardrail | Proposed initial limit |
| --- | --- |
| One generation wall-clock deadline | 30 seconds total |
| Model-selected read tool calls | <=4 across whole run |
| Semantic structured-output repairs | <=1 |
| Transport-level retry budget | <=1 across whole run |
| Provider attempts including tool continuation, repair and retry | <=3 in total per request (every outbound call counts; see `14`) |
| Cumulative tokens (whole request) | <=16,000 input and <=4,000 output |
| Live concurrent runs | <=1 per local principal, <=2 globally |
| Ephemeral candidate lifetime | ~30 minutes, bounded entries/bytes |
| Operational metadata local retention | proposed 14 days |

No key or installed SDK alone may enable live usage; CI must deny external egress. Design one retry owner and disable/count nested library retries. Invalid constraints aren't retryable. A timeout/cancellation still may incur an external model charge. Real spend requires persistent/concurrency-safe *dollar* budget reservations against quoted worst-case attempt usage and delayed charge reconciliation; token caps are **not** a monetary guarantee. In F1 (fake mode) prove configuration/limits/fail-closed behavior; implement and verify durable live-dollar reservations **before** any approved provider use.

Cache only versioned static catalog reads first. Key by full relevant filters + catalog version and invalidate on change. Do not share owner-specific generation results across users. Report latency/cost with whole test-population retries and failures in numerator, and a clearly defined success denominator.

## Candidate AWS choices for F4 (neither approved)

- **Local Docker Compose:** best default learning/deploy/test environment; no AWS operations claim.
- **Single short-lived AWS host with app/DB containers:** simpler topology but shared failure domain and owner responsible for TLS, patching, backup and volume recovery; synthetic owner demo only.
- **ECS/Fargate + managed PostgreSQL + HTTPS ingress:** more complete operational practice but meaningfully more infrastructure, IAM/network/storage and idle expense. Only choose if educational value warrants cost.

Before selecting, obtain dated official AWS prices for compute, DB idle/storage/backups, network/ingress/NAT, ECR, logs, secrets and lingering resources. Budget alarms are delayed alerts, **not hard caps**. Demonstrate teardown and inspect billed leftovers.

## Blocking risks and mitigation

| Risk | Earliest blocking gate | Required mitigation |
| --- | --- | --- |
| Duplicate/forged approval | F1 | Atomic unique DB constraints, revision/hash/version binding and restart retry |
| Silent constraint relaxation / medical overreach | F1 | Narrow envelope, checked templates, validator, out-of-scope fixtures |
| Consent vs persistence confusion | F1 | Explicit Save/Approve/Submit; transient drafts and separate retention inventory |
| Unbounded API usage | F1 configuration; live permission gate | Whole-request cap, fake-first, fail-closed SDK and category budget reservation |
| Meaningless agent evidence | F1 baseline, F3 real model | Test a template baseline, verify actual model-selected tools and compare traces |
| Data export leakage / cross-user access | F1 for local; F3 and F5 for external | Two-principal tests, allowlist-only metadata, sink canaries, real auth before pilot |
| Framework-driven complexity | F1 / F2 | Typed orchestration and a contained measurable LangGraph comparison |
| Cloud cost / fragile recovery | F4 before apply | Priced topology, region, backups, teardown, IAM, migration/rollback/restore proof |

## Pending owner choices

Proposed defaults are concrete but not independently approved: exact supported envelope and duration templates; single-process candidate TTL; local synthetic identity mechanism; POST SSE/route contract; retry/token/concurrency caps; metadata retention; approval fingerprint and idempotency lifetime. The F0 owner approval may ratify all as one bounded baseline or require edits. There is **no** approved live provider, judge, hosted telemetry, AWS budget, or external pilot at F0.

## Review 11 closure clarification

The numerical controls above apply **per generation/revision request**, including fake tests and all provider continuations; they do not grant live spending. One successful revision maximum is enforced **per candidate lineage** (contract `13`). Candidate expiry acceptance and approval ordering are defined in `13`; stream terminal outcomes, cancellation and no-whole-request-replay are defined in `14`. Contract `12` supplies domain rules formerly reserved for F0.
