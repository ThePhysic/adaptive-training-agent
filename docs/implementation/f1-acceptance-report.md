# Final F1 offline vertical-slice acceptance evidence

Date: 2026-10-24. Scope: owner-authorized F1-07, with F1-01–F1-06 already accepted.
Recommendation: **local offline F1 gates pass within the tested synthetic,
single-process scope; submit for owner review**. This report does not grant
approval, authorize F2 or claim production readiness.

## Measured result

The complete local workflow works through actual HTTP and installed Chrome:
**Save profile → Generate → Review → Revise → Approve → Durable readback → History**.
Explicit approval writes a server-owned validated immutable snapshot, key binding
and audit atomically. A lost successful response recovers with the same key.
Later profile changes leave stored snapshots unchanged. Other principals cannot
read or approve another owner's data. Incomplete streams stay non-approvable.

Final validation: **577 Python tests** (504 routine +73 local integration),
**69 frontend tests**, zero skipped/failed. Six of the routine Python cases are
reference-model obligations, not SQL implementation evidence. Native PostgreSQL,
ASGI/browser, schema/contracts and reference-model evidence remain distinguished.
The frozen 40-case evaluation separately remains **24/24 development, 16/16 held
out**. These denominators are not pooled or presented as real-model trials.

Exact commands, versions and changed paths:
[F1-07 handoff](f1-07-handoff.md). Installation, startup, migration, diagnosis,
shutdown and restart/recovery: [local runbook](../runbook.md).

## Gate matrix

| F1 gate | Evidence and outcome | Boundary |
| --- | --- | --- |
| Environment, strict schemas and contracts | Python/JS locks retained; strict negative tests and generated OpenAPI/TS/validators pass | No new dependency or real SDK |
| Domain/catalog coverage | Frozen 20-record catalog; eight matrix rows × three presets; duration boundaries, exclusions and infeasibility tests pass | Software-fixture validity, not exercise safety certification |
| Deterministic baseline | Development 24/24 and held-out 16/16; exact source/catalog/corpus/results unchanged | Deterministic template evidence only |
| Identity/profile persistence | Loopback opt-in fails closed; two-principal ownership, optimistic Save, native SQL and true process restart pass | Synthetic selector is not a credential |
| Transient lifecycle | Capacity/TTL/revision/reservation/expiry/concurrency/cancellation regressions pass | One process, no durable drafts or multi-worker support |
| Typed orchestration | Fake protocol, read-only tool validation, repair/retry and conservative attempt/token accounting pass | Does not demonstrate real model-selected tools or personalization |
| SSE and client | Four outcomes, strict chunks/Unicode/bounds, EOF/Stop/late-delivery tests; terminal-only candidate eligibility pass | A returned send cannot guarantee browser receipt |
| Atomic approval | Real PostgreSQL unique constraints, profile-row ordering, races, rollback, lost responses, restart and unknown-COMMIT reconciliation pass | Controlled transaction/transport faults, not physical server/power crashes |
| Durable read/history | Owned native SQL and immutable stored versions; pagination and later profile/catalog-change tests pass | Opaque ID ordering, not chronological history |
| Local observability | Correlated stage spans, fixed metadata allowlists, measured durations/budgets/versions and diagnosed induced failure pass | No hosted export or distributed tracing operation |
| Privacy and egress | Canaries absent from both configured sinks; credentials cannot enable live mode; Python/JS socket/DNS/UDP/fetch probes pass; browser page egress zero | Cooperative test guards, not an OS firewall |
| Liveness/readiness and faults | Healthy launcher 200/200; schema faults and a real stopped-DB probe return ready503/health200; connection kill recovers; stalled probes/bodies/providers clean up | Local dependency readiness, not product/security certification |
| End-to-end browser | SQL-backed approval/same-key retry/readback/history, owner isolation, immutable snapshot, mobile failure/recovery and overflow checks pass | Installed Chrome on this Windows host, not a browser/device matrix |
| Reproducible CI | Pinned workflow parsed; shared full offline runner passed locally | Hosted Linux job not triggered; fresh runner execution unverified |

Frozen outcomes: development 16 plan/6 clarify/2 error; held-out 8 plan/4 clarify/
2 abstain/2 error. Expected error cases are documented evaluation successes, not
failed tests. No dataset changes were made to improve scores.

## Diagnostic failure and trace evidence

[Failure trace](evidence/f1-07-failure-trace.json): ten metadata-only spans in one
HTTP request. The scripted fake requests a catalog tool, then twice supplies an
invalid exercise ID. Validation rejects both proposals. With one repair consumed,
the final state is `failed`, reason `semantic_repair_exhausted`, terminal outcome
`error`; no candidate is published. It consumes **3 provider attempts, 1 read tool,
1 repair, 0 retries, 7308 input/787 output simulated tokens**, all within ratified
request caps. Version identifiers are captured without output content. HTTP 200
is transport status; final business outcome is correctly error. Measured request
duration: **22.180 ms**, a single observation.

[Native vertical trace](evidence/f1-07-vertical-trace.json): 48 spans across nine
actual HTTP requests and native SQL operations, with parent/child correlation
also spanning the owned approval task. No owner/candidate/plan ID, content hash,
idempotency key, raw request/body, SQL text or exception text appears in telemetry.

## Local latency/operation measurements

Final trace samples, Windows Python 3.14.9/native async Psycopg against cached
PostgreSQL 18.6 on localhost; fake model only. Each row is **one observation**;
these are elapsed handler/component durations, not independent percentiles.
Nested durations overlap and must not be summed as separate work.

| Native HTTP operation/component | Observed milliseconds |
| --- | ---: |
| Initial profile Save | 19.504 |
| Generate through terminal send | 87.905 |
| Revise through terminal send | 104.552 |
| Approval HTTP request | 77.339 |
| Approval transaction component (within that request) | 29.809 |
| First durable readback | 16.833 |
| History | 28.247 |
| Wrong-owner read (404) | 26.009 |
| Later profile Save | 15.988 |
| Stored snapshot read after Save | 40.348 |

The shared final check run took approximately **67.711 seconds** summed across
child commands: routine pytest 12.49 s, integration pytest 29.69 s, frontend test
duration 4.342 s; command startup/build/lint add overhead. Build output is about
343.7 KiB JS/5.7 KiB CSS before compression. No cloud/provider spend was incurred.
No load, throughput, scalability, real-token cost or real-model latency claim is
supported by this small local sample.

## UI evidence

- [Desktop, width 1440](evidence/f1-07-desktop.png).
- [Mobile, width 390](evidence/f1-07-mobile.png).
- [Mobile Save failure](evidence/f1-07-mobile-error.png).

All were visually inspected. Programmatic checks found no horizontal overflow,
zero page runtime errors and zero external page requests. The UI approved only
after complete review, recovered a deliberately lost successful approval response
using the same key, read one durable record and displayed its original 20-minute/
revision-1 snapshot beside current 30-minute/revision-2 preferences. Switching to
B removed A's plan/history. An injected first B-profile Save failure left generation
and approval disabled; explicit retry persisted B revision 1 using real SQL.
Approval table counts stayed exactly `(1,1,1)` in that isolated browser fixture.

## Fault scope and remaining limits

The final run preserves every accepted F1-06 native race/fault scenario: same-key
initial misses and guard recheck, different fingerprints/keys, publication/approval
both orders, TTL boundaries, profile Save row locks both orders, lost COMMIT/HTTP
response, true interpreter restart, rollback, pending reconciliation and later
recovery. Deferred SQL triggers/barriers hold an actual COMMIT and prove repeated
caller cancellation cannot release the guard prematurely. A new real
`pg_terminate_backend` test confirms failure and fresh-connection recovery without
changing saved state. These are real PostgreSQL assertions; proxy faults still
do not equal physically severed packets, server crash, power loss or every shutdown.

No known local F1 blocker remains from the observed checks. Remaining boundaries:

- Hosted CI has not run; Linux/fresh dependency acquisition/system Chrome availability
  are unverified. The checked-in workflow and local equivalent are the evidence.
- No real LLM adaptation, quality, human ratings, clinical suitability, qualified
  exercise-content review, paid tokenizer accounting or participant trial.
- No production identity/access/deletion policy, external-user enrollment,
  adversarial process isolation or production retention guarantee. Local synthetic
  data retention/reset rules are documented; no reset was executed.
- No production scale, multi-worker/replica semantics, durable draft/run/checkpoint,
  queue, Redis, recovery worker, hosted Langfuse/OTel export or AWS operation.
- Diagnostics are bounded and ephemeral; loss/truncation may require reproducing
  a synthetic failure. Local console logging omits raw exception text intentionally.
- Keys are page-local; after reload use owned history. Approval already in flight
  may finish after connection loss. No automatic generation replay or reconnection.

The supported local development slice is ready for F1-07/final F1 owner review.
The local DB container is stopped with its volume preserved; no test browser or
smoke API process remains. No commit/push or F2 work follows from this report.
