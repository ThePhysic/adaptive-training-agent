# Final F2 offline acceptance evidence

Date: 2026-10-24. F1 and F2-01 through F2-03 are owner-accepted. F2-04 is implemented.
Recommendation: **the tested local offline F2 gates pass; submit F2-04 and F2
closure for owner review**. This report does not grant acceptance or authorize F3.

## Result and scope

The single-process synthetic workspace now supports the complete explicit journey:
**Save profile → Generate → Review → Revise → Approve → Durable readback/history →
Submit session completion and optional structured feedback → Durable record readback**.
Approval never implies completion. Session records reference real owned approved
snapshots, remain immutable and recover matching retries without duplicate writes.

F2 also delivered practical async fault handling, a measured rejection of catalog
cache adoption, and a real isolated LangGraph/SQLite checkpoint/restart comparison.
The application retains direct services, uncached catalog reads and typed agent
orchestration. Durable business records belong in PostgreSQL; graph checkpoints
remain synthetic experiment files with no application authority.

Exact F2-04 files, migrations, commands, cases and environment:
[F2-04 handoff](f2-04-handoff.md). Operation and cleanup:
[runbook](../runbook.md). Ratified F1 evidence remains historical and unchanged:
[F1 acceptance report](f1-acceptance-report.md).

## Final measured regression populations

| Population | Final observed outcome | Meaning |
| --- | --- | --- |
| Routine application Python | **604/604 passed**, zero skips/errors, 15.95 s | Includes contracts, lifecycle, tools, privacy, fakes and separately labeled reference tests |
| PostgreSQL/integration/browser | **105/105 passed**, zero skips/errors, 39.10 s | Actual native SQL, real HTTP/ASGI, faults/restarts and installed Chrome |
| Isolated LangGraph tests | **47/47 passed**, zero skips, 15.98 s | Real graph/checkpointer with synthetic data; separate dependency environment |
| Frontend client/React | **85/85 passed**, zero skips/cancellations, 5.014 s | Deterministic client/DOM tests; real browser is separately included above |
| Frozen evaluation | **24/24 development; 16/16 held-out** | Expected template outcomes unchanged; not real-model trials |

There are **709 root Python tests** in disjoint routine/integration selections,
plus 47 isolated experimental cases. F2-04 adds 33 routine, 31 native SQL/HTTP and
16 frontend cases. Existing six specification/reference cases are not SQL approval
proof. Benchmark cases and browser assertions are not added again to inflate test
denominators. Expected evaluation error outcomes count as correct handling, not
successful workout plans.

TypeScript, strict OpenAPI/TS/runtime-validator generation, Ruff lint/format,
Prettier, frontend build, local launcher smoke and evaluation reproducibility
checks all passed through the existing shared runner. Summed runner child-command
elapsed time was 81.537 s; the isolated graph run is additional. Hosted CI was not
dispatched; these are measured local CI-equivalent checks.

Frozen evaluation distribution remains: development 16 plan/6 clarify/2 error;
held-out 8 plan/4 clarify/2 abstain/2 error. No domain rules, examples, source
fingerprints, corpus records, catalog entries, result files or dependency locks
were changed to improve results.

## F2 gate matrix

| Gate | Evidence and observed result | Boundary |
| --- | --- | --- |
| Async I/O, independent reads and dependencies | F2-01 typed local HTTP adapters; barriers/controlled clocks prove three independent reads overlap and profile-dependent filtering waits | Controlled Mock/ASGI transports; no operated external-service traffic |
| Cancellation, faults and budgets | Structured child cleanup, partial/unavailable/integrity distinctions, deadline tracing fixes and current regressions pass | Cooperative code and single process; no OS firewall or malicious-callback termination claim |
| Bounded cache decision | F2-02 audited real 20-record work before prototyping; equivalent outputs/capacity/invalidation/concurrency tests; no consistent native API gain | Prototype remains experimental; no application cache, Redis or personalized-data caching |
| Stateful graph learning | F2-03 actual LangGraph/SQLite checkpoints, dynamic interrupt, original interpreter exit, fresh-process resume and repeat-read inspection | Synthetic isolated files; no production resume, graph adoption or business-effect authority |
| Explicit completion/feedback | F2-04 forms appear only for durable approved readback; unselected status, optional bounded feedback, explicit Submit and readback | Synthetic self-report; does not verify physical exercise or establish training quality |
| Native SQL correctness | Atomic immutable record/key pair, actual-session/snapshot references, owner/key/session uniqueness, matching retry and conflicting-write tests | Tested native transactions and controlled driver faults, not every physical crash/network failure |
| Authorization and privacy | Wrong-owner/absent plan both 404; typed extra-field/health-note rejection; no model write tools; private responses; canaries absent from both local sinks | Synthetic header is not production authentication; no external users |
| Browser integration | Real TCP HTTP + installed Chrome: approval/session lost responses and retries, immutable later readback, mobile skipped submission, owner switch, error/recovery | One Windows Chrome installation/viewport simulation; no device/browser population claim |
| F1 preservation and operations | All prior lifecycle/approval/profile/SSE/token/tool/admission/native fault tests pass; readiness checks migration 004; frozen baseline unchanged | One API process; no replica/worker/production readiness claim |
| Reproducibility and scope | Exact commands/versions in handoff; additive migration; root locks and prior contracts unchanged; no new services/dependencies | Hosted/fresh Linux CI execution unverified; no live models, exports, cloud or deployment |

## Consolidated async, cache and graph evidence

**F2-01:** [handoff](f2-01-handoff.md), [audit](f2-01-async-audit.md),
[recorded comparison](evidence/f2-01-async-comparison.json). Three reads/trial,
40 ms deliberately delayed I/O/read, five trials per mode. Historical medians
were 139.624 ms sequential and 47.173 ms concurrent; the final shared-check repeat
observed **138.717/46.327 ms**, both 5/5 correct with zero retries and peak inflight
1/3. Controlled-clock evidence separately demonstrates 120/40 ms logical elapsed
work and drained children; elapsed ratios are not fragile test assertions.
Diagnosed cancellation/deadline trace ordering was corrected in F2-01 and retained.

**F2-02:** [decision](f2-02-cache-decision.md), [handoff](f2-02-handoff.md),
[raw component comparison](evidence/f2-02-cache-comparison.json),
[native API comparison](evidence/f2-02-native-api-comparison.json).
The bounded version/digest/filter-keyed prototype had eight default entries and a
64 KiB logical payload cap. Across 216 cases, outputs remained equivalent. Warm
component pipeline median improved by only **0.2062 ms**; cold operation cost more.
The 720 native fake-provider API measurements showed variable round differences
and no consistent gain. Keep the simpler uncached application. These are historical
F2-02 measurements; the final acceptance run repeats correctness checks, not a
new production performance study. The prototype never caches profiles, plans,
candidates, approval/idempotency decisions or owner history.

**F2-03:** [handoff](f2-03-handoff.md),
[restart evidence](evidence/f2-03-demo.json),
[14-scenario comparison](evidence/f2-03-compare.json).
All equivalent outcomes and complete accounting matched. Three actual interpreters
demonstrated persisted gate → resume → repeat-read, preserving context hash and
provider/read counters without an extra call. Safe-node failures resume explicitly;
uncertain pending provider/tools fail closed instead of silently replaying.
Historical timing was 11.716 ms typed versus 158.809 ms graph + SQLite median,
20 samples/mode after five warm-ups. The graph measurement includes additional
durability, setup and restoration checking; it is not equal-durability pure
framework overhead. Keep typed application orchestration: current short-lived
requests do not require durable generation resumption.

All three accepted decisions are preserved. No new caching, graph worker,
checkpoint authority, queue, Redis or backend service was introduced by F2-04.

## Completion/feedback correctness and fault evidence

The [contract](../../contracts/completion-feedback.md) was defined before
persistence. Status is completed/partial/skipped, with optional easy/moderate/hard
effort and integer 1–5 rating. Skipped feedback must be null. One numbered session
of a particular approved snapshot has one immutable revision-1 record, created
with expected revision 0. There is no unrestricted note field, recurrence calendar
or silent correction. Server-generated timestamp provides minimal audit metadata.

Migration 004 inserts record/key atomically, verifies actual approved-session
membership and snapshot revision/hash, enforces owner/key and session uniqueness,
and rejects mutation. An owned key transaction lock precedes committed lookup;
the session transaction lock serializes different-key contenders. No profile lock
or candidate-memory finalization is involved. Current profile/catalog changes
cannot rewrite the approved plan or submitted record.

Native/HTTP tests assert matching same-key races return the same record, conflicting
keys/fingerprints return precise 409 errors and invalid references insert nothing.
Independent sessions reach a barrier concurrently. Pre-COMMIT and deferred-COMMIT
faults leave no partial pair. A fresh interpreter recovers the original key after
lost acknowledgement. Repeated cancellation and HTTP cancellation wait for owned
critical work before propagating, allowing a subsequent explicit same-key retry.
An uncertain still-open transaction blocks the retry at its real PostgreSQL lock;
controlled original commit and rollback both lead to exactly one final record/key.

[New native fault trace](evidence/f2-04-session-trace.json): eight correlated spans
across three ASGI requests show **503 pending → 200 matching retry → 200 GET**.
The first native COMMIT succeeded before acknowledgement loss; there was exactly
one record and one binding throughout recovery. Initial/retry/read handler times
were **34.500 /18.204 /20.357 ms**, each one observation. Trace data contains fixed
stage/reason/HTTP status and opaque correlations, never feedback or user/plan/key
identity. Local trace and console canaries pass; no hosted export is configured.

Controlled failures are distinguished from physical packet, server-power or disk
crashes. SQL constraints are not a security boundary against privileged DDL.
The existing single-process synthetic deployment remains the supported scope.

## UI, migrations and operational evidence

Actual browser flow includes a completed session with moderate effort/rating 4,
deliberately lost success and exact retry, then changed current profile with old
plan/session readback and mobile skipped-session Submit. Final fixture counts
were `(approved,approval-key,audit,session,session-key)=(1,1,1,2,2)`. Other-owner
switch clears the previous view; a failed profile Save does not silently succeed.
No completion is recorded merely by approval, rendering or selecting values.

New screenshots: [desktop](evidence/f2-04-desktop.png),
[mobile](evidence/f2-04-mobile.png), [mobile error](evidence/f2-04-mobile-error.png).
Desktop/mobile were visually inspected. Programmatic checks report zero page
runtime errors, zero external page requests and no horizontal overflow.

Observed migration application: `004_session_records.sql` only. Repeat application
was a no-op with all four checksums intact. Prior 31 OpenAPI components and nine
paths compare structurally unchanged; the three new operations are additive.
Root dependency locks and frozen source/data are unchanged. The application
environment has no LangGraph installation; its experiment remains separately locked.

Final development approved/key/audit/session/session-key counts were all zero;
test schemas were cleaned up. PostgreSQL is stopped with its volume/image preserved.
Owned API/browser processes are stopped; no volume reset, commit or push occurred.
The [runbook](../runbook.md) covers installation/startup/migration, Submit/retry,
readback, diagnostics, tests, retention and stopping services.

## Remaining limitations and F3 planning readiness

- All provider behavior is fake/offline. No actual model tool selection, adaptation,
  personalization, live streaming quality, tokenizer charges, human ratings,
  judge calibration or real-model comparison was measured.
- Catalog/prescription rules are bounded software fixtures, not qualified exercise
  review or clinical guidance. Submitted status/ratings are synthetic self-reports.
- Corrections, repeat occurrences, deletion/export/backup suppression and production
  retention require explicit later design. Local records/key bindings persist
  together until deliberate development reset; no automatic secure erasure.
- Synthetic localhost selectors do not establish production identity. External-user
  consent, adult enrollment, withdrawal, real authentication, data handling and
  qualified content review gates remain unsatisfied and separately required.
- No production scale, multi-worker support, hostile-host isolation, hosted
  observability operation, operated AWS infrastructure or external deployment.
  Local guards are cooperative; hosted Linux/fresh-runner execution is unverified.
- Performance measurements describe their small controlled/local workloads only.
  They cannot be extrapolated into real-model or production speedup claims.

No known local F2 specification/implementation blocker remains from these checks.
After owner acceptance, F3 planning can define a concrete real-model question,
matched evaluation/rubric and named provider/model/data destination. Live use still
requires separate authorization, official pricing, a numeric spend ceiling and
durable reservations/reconciliation for uncertain charges. LLM judge and hosted
telemetry each need their own approval and evidence plan; credentials alone must
never enable them. Real-user enrollment remains behind its later release gate.

**Stop after F2-04 for review. No F3 implementation, live call, hosted export,
cloud provisioning or external enrollment is authorized by this report.**
