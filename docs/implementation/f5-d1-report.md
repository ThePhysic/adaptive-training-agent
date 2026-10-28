# F5-D1 demonstration and engineering readiness

2026-10-27 local execution. Implemented for independent review; no next milestone
or external execution is authorized. This report concerns the **offline synthetic
application**, not production readiness, fitness effectiveness or model quality.

## Demonstrated application

The actual built React UI, loopback Uvicorn/FastAPI and native PostgreSQL completed
Save → fake generation/SSE → one revision → explicit approval → lost-response
same-key recovery → durable history → immutable profile snapshot → session feedback
→ page refresh/readback → owner switch → injected Save failure and explicit recovery.
The installed Chrome passed twice with zero runtime errors and external page requests;
the backend checked one approved plan/key/audit and two session records/keys, with
no plan for the other principal. Health and readiness were both 200 against the
same disposable schema. This is integrated browser/TCP/SQL evidence, not a claim
deduced solely from unit tests. There was no manual human usability session.

The [application projection](evidence/f5-d1-application.json),
[desktop](evidence/f5-d1-desktop.png), [mobile](evidence/f5-d1-mobile.png) and
[failure view](evidence/f5-d1-mobile-error.png) were captured from that application.
They contain public synthetic examples only. Preferences changing to 30 minutes
while the saved plan still shows 20 is intentional immutable readback.

No production feature defect was found in this bounded journey. Targeted engineering
corrections improve the reliability of the evidence:

- The browser fixture previously used owned test repositories but the default
  development database for readiness. Its probe now uses its owned connection and
  migration history; both health and readiness must pass before Chrome starts.
- The release drill previously fixed historical F4 image tags. It now accepts
  explicit local current/comparison image selections, preserving defaults,
  `--pull never`, exclusive port checks, ownership and retained volumes. A new
  regression verifies the selection without launching Docker.

The expanded full routine suite also exceeded the shared runner's old 180-second
phase allowance. Ordinary checks remain 180 seconds; routine/integration test
phases now have finite 2400/900-second allowances, with mocked regression tests
proving native nonzero failures still stop later acceptance checks. Individual
application, SQL and browser deadlines are unchanged. No CI run is claimed.

The browser additionally checks real page-refresh recovery without automatic
approval. Only two finite diagnostic stages and the F5 screenshot prefix were
added. No source under `src/`, migration, business rule, approval/first-result
contract, original scorer or live/financial gate changed.

## Recovery and measured local operation

The [current-source container evidence](evidence/f5-d1-local-release.json) records
an actual non-root Docker release using new tags, each attested against 75 current
application/migration/catalog/asset files. Existing F4 images were detected as
stale and were not presented as current evidence or retagged.

The existing drill verified native connection termination and graceful in-flight
stop produce errors, not fabricated plans; DB unavailability leaves health 200 and
readiness 503; recovery returns readiness; forced app crash/restart preserves
immutable records. A quiesced 79,989-byte backup restored into a separate empty
database with counts 1/1/1/1/1 for plan/key/audit/session/session-key, nine migrations,
same-key recovery and owner isolation. Restore time was about 0.285 seconds;
dump time about 0.378 seconds. These exclude startup and operator time. The browser
and restore scenarios use different disposable data and have different session
denominators. The old/new image switch uses identical schema/business source and
different release labels; it is not a schema downgrade. An altered migration
checksum refused startup. No existing data volume was deleted.

Measured workload: four warm-up requests, then 60 generations at concurrency one
and 60 at concurrency two with distinct principals, zero errors, zero retries and
no artificial provider delay. Application catalog reads remain uncached.

| Concurrency | Requests | Full generation p50/p95 ms | First status p50/p95 ms |
| --- | --- | --- | --- |
| 1 |60 |41.93 /85.90 |8.88 /13.46 |
| 2 |60 |51.14 /58.86 |10.46 /13.70 |

The first SSE status is useful progress feedback, not a first actionable plan or
LLM token. A separately observed cold generation was 46.17 ms and revision 46.87 ms.
Backend RSS was 73,644 KiB (high-water 74,292 KiB); a Docker snapshot showed app
67.57 MiB and PostgreSQL 42.78 MiB under separate 512 MiB/one-CPU limits. Sampling
methods differ. Windows AMD64 host: 16 logical CPUs, about 31,963 MiB RAM; Docker
Linux engine 29.9.1. The routine Python suite was also running on this host.
These small local fake-provider measurements are illustrative, not isolated
benchmarks, real LLM latency, throughput capacity or production SLOs.

## Evaluation and trace demonstration

The [fresh evaluation projection](evidence/f5-d1-evaluation-walkthrough.json)
comes from E9/E10 tests freshly executed in this milestone. Ten public cases perform
21 count +21 generation =42 mocked operations with native SQL accounting. Nine
2/2/4 cases hard-pass; a 3/3/6 case retains its intermediate rejection and hard-fails
despite its valid final plan. Known synthetic holds remain 21,000 micro-units and
actual total remains unknown. Cancellation/uncertain-commit tests retain claims
and liabilities; no failed request is assumed free.

E10's packet exposes nine eligible practice pairs. Two scripted dummy ratings and
one abstention leave 33 missing and four ineligible reviewer slots out of 40 public
practice slots; dummy mean 4 is arithmetic only. Twenty primary study pairs are
planned, but ten independent cases remain absent. Genuine judgments are zero and
genuine quality stays null. Source/selection bindings, immutable first results and
historical freeze candidates remain intact; no freeze was approved.

The [fresh failure trace](evidence/f5-d1-failure-trace.json) reuses the existing
induced-failure assertion: ScriptedFake emits a tool call, invalid final and invalid
repair, producing `semantic_repair_exhausted` and `done(error)` with three attempts,
one tool and one repair. Twelve correlated, content-free spans explain the failure.
This trace is a local ASGI experiment; the UI demonstration separately used real
loopback TCP. No hosted Langfuse/OTel export or native reasoning capture occurred.

## Readiness by category

Fresh validation: **2598 distinct selected Python tests /2609 passing executions**,
including all 401 non-browser integration cases and the installed browser twice;
**131 frontend tests**, frozen **40/40** and **150/150** comparison dispositions.
The original routine invocation passed 2193 cases in 1321.56s; three newly added
routine cases were run separately. Exact commands, overlaps, deselections and
development failures are in the [handoff](f5-d1-handoff.md) and
[validation record](evidence/f5-d1-validation.json). These are freshly executed
local checks, not a hosted CI or independent quality result.

| Category | Implemented and freshly exercised | Remaining limits / required work |
| --- | --- | --- |
| A Core application | Structured adult profile Save, deterministic plan, supported clarification/abstention, immutable approved history and explicit session records | Free text is not a general trainer. Supported domain is intentionally bounded; no fitness effectiveness claim |
| B Frontend/backend | Built React against real HTTP/SSE and SQL in installed Chrome; desktop/mobile, full refresh and owner switch; frontend tests/build | One browser/OS freshly exercised. Broader accessibility, browser and manual usability review is release polish, not an observed blocker |
| C Agent/state | Typed orchestration, terminal-only publication, one revision, bounded tool/repair/deadline/concurrency, cancellation tests | Candidates and page-local keys are transient. There is no durable generation resume or multi-process deployment; adding either is new scope |
| D Approval/persistence | Browser same-key recovery; native concurrency, rollback/reconciliation and fresh-process key readback; restore preserves snapshots and session records | Synthetic identity is not production auth. No public exposure/external users permitted. Schema rollback is not implied by image rollback |
| E Reliability | Real dependency interruption/recovery, crash, graceful stop, strict readiness, controlled cancellation, duplicate/conflict and uncertain accounting tests | Controlled local faults are not production chaos/availability or arbitrary power-loss proof |
| F Evaluation | E9 counted replay/holds/intermediate failures, shared scorer, E10 blinded dummy imports, immutable first result; frozen baseline/comparisons checked | No unseen population, genuine judgments, real-model results or verified provider billing. Genuine trust/opening/collection gates remain separate |
| G Local release/DX | Locked environment, current source-attested non-root images, health/migrations, restore, bounded workload, scoped cleanup and runbook | Existing prerequisites required; build steps network-disabled but BuildKit queried registries. Not a fresh-install/air-gapped/hosted-CI reproduction |
| H Documentation/portfolio | New reproducible runbook, screenshots, failure story, numerical evidence and validation handoff; README links current evidence | A short narrated capture and concise portfolio case study remain presentation work. Do not market synthetic evidence as genuine AI quality |

No arbitrary completion percentage is assigned. The bounded local synthetic slice
is demonstrated; full original F3 applied-AI acceptance remains incomplete because
its genuine model/human/export evidence has not been authorized or established.
F5 external-user feedback, clinical benefit, production deployment and cloud
operation are not inferred from this exercise.

## Prioritized remaining work

1. **Required engineering fixes:** none observed blocking this offline journey.
   Keep the new isolation/image-selection assertions. Final selected validation
   and environmental limits are recorded in the handoff; any failure remains a
   blocker rather than a reason to regenerate old evidence.
2. **Presentation/release polish:** one bounded manual acceptance/narrated capture,
   short architecture/evidence map and an honest limitations page. Validate the
   chosen source/release in the existing CI under separate push authorization.
   No extra evaluation dashboard, service or planning-only milestone is needed.
3. **Deferred independent evaluation:** review actual genuine authoring/opening and
   human-result provenance boundaries, choose the real model/settings/study,
   explicitly freeze, then separately authorize family-curator appointment,
   disclosure/custody, human-only creation and genuine review collection. No
   private material or curator was accessed here.
4. **Deferred real-model work:** resolve support Case 18223129 counting tariff,
   bounded liability, current account/model compatibility, retention/privacy,
   source release and numerical spending approvals. Only then separately authorize
   one bounded compatibility request before any study tranche. NO-GO persists.
5. **Optional:** AWS deployment/IAM discovery, hosted observability, judge calls,
   Redis, queues and additional orchestration. They do not block this local slice.

The smallest practical next milestone is presentation and reproducible release
packaging of this already functioning slice, with explicit approval for any human
or hosted activity. This report authorizes nothing beyond F5-D1.
