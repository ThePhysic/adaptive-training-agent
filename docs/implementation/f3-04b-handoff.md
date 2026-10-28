# F3-04B handoff — offline transport integration and final compatibility gate

Date: **2026-10-25**. Scope: **F3-04B only**, after acceptance of offline F3-04A.
Prepared for owner review. The F3-03C live **NO-GO** remains. No provider/count API
request, monetary spending, live grant/capability, account authorization, hosted
export, cloud resource, deployment, external data, commit or push occurred.
Completion does not authorize activation, compatibility execution or later work.

## Result and audit decisions

The counted Responses pathway now uses one shared **acknowledged claim→send**
boundary, retaining its existing adapter, PostgreSQL ledger, request budgets,
native-state validation and owned HTTP lifecycle. Full typed-Agent count/tool/
continuation/repair sequences run through actual local TLS and native SQL.
A dormant real-destination connector and credential/request policy are prepared,
but **cannot be activated**: both live and financial barriers are unconditional,
and replay/application assembly rejects the connector.

| Audited boundary | Smallest change / decision |
| --- | --- |
| Count and generation independently called `ledger.claim` then HTTP | Centralize claim acknowledgment, scope/payload check and final stop/deadline check in `ClaimedHTTP`; no duplicate claim/retry owner |
| Only mock full-Agent execution; TLS was separately exercised | Permit exact `LocalTLS` only for explicit counted replay with existing ledger/scope; use the same actual Agent/parser/validator, truthful replay label |
| Real destination/auth sender absent | Prepare `OpenAIHTTPS`, pure fixed-header request builder and one shared verified transport factory; no application route, provider-kind switch or live factory |
| SQL mode/quote is replay/synthetic-only | Preserve all tables, migrations, constraints and rate policy. Add an independent unconditional financial denial; do not reinterpret replay records as money |
| Financial/schema/provider prerequisites unresolved | Keep NO-GO. A later live authority/assembly source review is necessary; credentials or owner execution approval alone cannot activate this code |
| F3-04A source manifest covers provider source | Preserve original score artifact; add a current-source regression snapshot and assert every case/summary equals the accepted snapshot. No scorer/dataset/rubric expansion |

No new SDK/dependency, service, queue, worker, graph integration, cache, database
schema, planner, model tool or evaluation platform. Main application remains fake
only. The existing live gate, approval/Submit transactions, synthetic identity,
terminal-only publication and immutable records are unchanged.

## Files changed

| Path | Change |
| --- | --- |
| `src/future_training/providers/sender.py` | Dormant real connector, explicit redacted credential/request policy, independent financial deny barrier, local `ClaimedHTTP` |
| `src/future_training/providers/http.py` | Shared verified/no-proxy/zero-retry TLS transport factory; existing local-only HTTP bounds/lifecycle retained |
| `src/future_training/providers/responses.py` | Exact counted loopback connector acceptance; construct claim-aware HTTP for counted sessions |
| `src/future_training/providers/counted.py` | Route both operation kinds through acknowledged-claim boundary; preserve counters, immutable ticket and accounting; byte counters read from sender |
| `tests/test_prepared_sender.py` | 35 new offline destination/auth/extension/gate/payload/claim/privacy tests |
| `tests/test_sender_postgres.py` | 15 new real SQL/TLS sequence, failure, concurrency and shutdown tests |
| `tests/local_tls_doubles.py` | Optional in-memory request observer and per-request fault mode; no persistent request capture |
| `src/future_training/experiments/model_eval_assets.py` | Current score-reference filename only; asset generation/inputs unchanged |
| `scripts/evaluate_models.py` | Use that current reference; no new execution mode or scoring feature |
| `tests/test_model_evaluation.py` | Check current source provenance plus equality to original case/summary results; protected-file guard permits authorized provider/docs changes |
| `data/evaluation/model-v1/offline-scores-f3-04b.json` | Additive current-source synthetic regression evidence; original `offline-scores.json` unchanged |
| `data/evaluation/model-v1/README.md` | Explain original/current provenance snapshots |
| `contracts/provider-safety.md` | Current offline connector/claim/gate contract; no policy or financial authorization change |
| `docs/planning/19-f3-03c-pre-live-readiness.md` | Implemented-vs-provider-dependent checklist, missing live authority/assembly, exact one-request probe and owner gates |
| `README.md`, `docs/development.md` | Current offline status/usage |
| `web/scripts/browser-smoke.mjs` | New screenshot namespace only; application frontend unchanged |
| `docs/implementation/evidence/f3-04b-desktop.png`, `f3-04b-mobile.png`, `f3-04b-mobile-error.png` | New actual-browser regression images; prior evidence untouched |
| `docs/implementation/f3-04b-handoff.md` | This report |

There are no migrations. Existing 001–008, all ledger/approval/completion SQL,
domain schemas/catalog/duration, generated public contracts, prompt/schema/config
assets, F1 40-case corpus, F3-04A 50-case corpus/expectations and original score
artifact, graph environment, dependencies/locks and historical handoffs are
unchanged. Only an additive score snapshot records changed provider source.

## Implemented transport and financial boundaries

`OpenAIHTTPS.handle_async_request` validates destination, then uses the exact
existing `LiveGate.check` method and the independent financial deny function
before creating a pool, building auth headers, resolving DNS or connecting.
The existing `LivePermit` descriptor contains no approved monetary authority;
even a hypothetical positive descriptor cannot pass the unconditional gate.
The unit fault that makes the first check permissive still hits financial denial.
No environment or credential activation switch, live issuer or live Agent/HTTP
assembly exists. `OfflineHTTP` and `ResponsesReplay` reject this connector.

The prepared request builder allows only POST HTTPS/443 on `api.openai.com` at
`/v1/responses` and `/v1/responses/input_tokens`. It validates URL/body first,
uses only an explicit bounded ASCII credential, discards incoming Authorization,
Cookie, Host/private headers, rejects routing/SNI/trace extensions and constructs
fresh fixed MIME/identity-encoding/timeouts. The credential wrapper has redacted
representation and no environment lookup or serialization/logging integration;
close drops its reference, without claiming Python memory zeroization.

The shared HTTPX transport factory uses verification, `trust_env=False` and
`retries=0`. Local TLS additionally rechecks certificate/hostname verification and
rewrites the actual destination to literal `127.0.0.1:<test-port>`, stripping auth.
The existing owned client disables redirects/proxies, rejects compressed bodies
before decompression, caps count at 1,024 bytes and generation stream at 65,536,
and preserves frame/native/normalized/tool-result limits. It closes/awaits once
for the complete counted session. Local tests verify the loopback hostname;
**no provider TLS handshake/authentication or post-activation socket path ran**.

`ClaimedHTTP` accepts only the same exact mock/local connectors. Before claiming
it checks financial scope and reprojects the frozen generation body to verify
the count body, without changing either byte sequence or persisting a payload
hash. It awaits the existing cancellation-safe claim transaction, rechecks
stop/deadline and only then enters bounded HTTP. The caller no longer claims
separately. Count/combined counters remain conservatively consumed; body-byte
metrics advance only after definitely acknowledged claim. Every continuation,
repair and safe retry still needs its fresh count/pair. No automatic retry or
recovery work was added.

Original limits remain **3 counts /3 generations /6 combined**, **16,000 input /
4,000 output** inference, 2,000 output per attempt, 30 seconds, four reads, one
shared retry, one repair, one/principal and two globally. Budget/token/revision
ownership remains with the accepted Agent. SQL cleanup may drain its existing
bounded critical section after deadline without granting another send.

## Observed native fault and concurrency evidence

These are **actual PostgreSQL and actual loopback TLS** assertions, not the
routine protocol recorder or specification/reference model. Existing isolated
schema fixtures create replay projects with invented positive test ceilings;
they are not live monetary grants and are dropped afterward.

| Scenario | Observed outcome |
| --- | --- |
| Two-generation count→tool→recount→continuation | Actual Agent returns valid unpublished plan; 2 counts/2 generations/4 HTTPS requests, one read, 2,000 input/200 output; every server request observes its committed `sent` row and monotonic wire ordinal |
| Same sequence plus invalid plan and one repair | 3/3/6, one repair, 3,000/300; independent validator rejects invalid intermediate output, final valid unpublished plan; no seventh send |
| Payload equivalence at TLS receiver | Each count equals projection of its corresponding generation's nine common fields, including ordered native continuation; original schemas unchanged |
| Settlements and client lifecycle | One client per run, closed after exit; history/pending/ticket cleared; each generation settles to invented **2,770 µUSD**, each count remains `responded_held` **1,000 µUSD**, actual cost NULL |
| Lost claim COMMIT ACK | Zero HTTP requests/client creation; ledger fence; fresh repository observes count `sent` at 1,000; abandonment cannot release it |
| Lost rollback ACK | Zero HTTP; fence; fresh repository observes reserved count, then explicit ordered reconciliation/abandonment releases only proven-unsent work |
| Disabled before claim | No transport; proven-unsent reservations can become `not_sent` |
| Cancellation immediately after acknowledged claim | No socket/client creation; count remains `sent`; no cancellation refund |
| Emergency stop during claimed count TLS stall | Disable commits, owned task cancels/is awaited, socket/client/native state cleaned; one request, count `sent`1,000 and generation `not_sent`60,000 retained state; no retry |
| Emergency stop during claimed generation TLS stall | Two requests; count `responded_held`1,000 plus generation `sent`22,500, actual NULL; no refund, orphan task or subsequent request |
| Two barrier-started senders, same operation | Real project lock/one-shot claim permits exactly one request; other sender denied |
| Exhausted replay grant | No pair, zero count/generation/wire requests |
| Wrong hostname, redirect, interrupted body, oversized count, compressed body | Error, one count/zero generations, no retry; wrong hostname has zero completed HTTP requests, others one; fresh repository retains sent count1,000 and proven-unsent generation state |

For `not_sent` rows, 60,000 is the retained `reserved_micro` column, **not an
outstanding liability**; proven-unsent generation contributes zero. Sent/held
rows retain their full maximum with `actual_micro=NULL`. Cancellation/transport
failure never releases the claimed count or generation hold.

Existing 206 native tests also pass: transaction/idempotency ordering, profile
Save races, candidate publication/expiry/revision, restart and lost responses,
mixed budgets/rollover, discrepancy persistence/freeze, unknown COMMIT and repeated
cancellation remain intact. The new 15 tests strengthen transport integration;
they do not prove provider billing, arbitrary power loss or multi-worker safety.

New routine tests additionally cover exact URL/method/path/port substitutions,
hostile headers/extensions, credential injection/bounds/redacted repr, immutable
count/body/scope mismatch before claim, blocked/ambiguous/exhausted claim and
barrier-proven acknowledgment ordering. The in-memory recorder in those cases is
protocol evidence only; the native table above establishes SQL behavior.

## Privacy, evidence and evaluation preservation

New synthetic credential canaries are absent from actual loopback request headers,
safe console and trace ring; untrusted input auth/cookie/Host is discarded. Existing
secret/PII/error/native-state canary and external egress tests all pass across both
configured sinks. No hosted sink or provider receipt/private billing identifier
is introduced. Opaque native state exists only in the current request and clears
on exit; no raw content, payload hash or credential enters ordinary telemetry.
Test request capture is in memory only and is never exported as an artifact.

The F3-04A artifact hashes all provider sources, so provider changes necessarily
change run provenance. Rather than overwrite accepted evidence or ignore source
hashes, `SCORE_REFERENCE` names additive `offline-scores-f3-04b.json`; the unchanged
runner and new assertion require **all 150 cases and every summary** to equal
the historical F3-04A artifact. Inputs, expectations, scorer, eligibility/exposure,
human rubric and execution variants are unchanged. This is provenance maintenance,
not further evaluation-framework development or a model trial.

Current source digest:
`295b8bef3f7565047a1ecfb88b3736fedf6eea3c865c91ec5758103e8ad13f99`.
Working base HEAD: `352f92248f008587c1108d6170b6ea6b768c7b95`, with current dirty
source hashes recorded, not an implied commit. Detailed synthetic run remains at
`.cache/f3-04b/20261025T182841293496Z/`. Fake/replay/template results remain
50/50 expected handling each; hard passes template50, fake44, replay44 with the
same six intentional malformed/unauthorized hard failures per model-fixture path.
All quality scores stay null. No actual-model/human/judge result is claimed.

## Commands and observed validation results

Environment: Windows 11, Python **3.14.9**, Node **24.22.1**, npm **11.19.1**,
Ruff **0.17.2**, HTTPX **0.28.1**, local PostgreSQL **18.6**. Existing dependencies
were reused; nothing installed or downloaded. Existing Docker engine was available
but required local pipe permissions. Cached startup recreated/started the project's
PostgreSQL container with its persistent volume and no image pull.

```powershell
docker compose up -d --pull never postgres
.venv/Scripts/ruff.exe check src scripts tests --fix --no-cache
.venv/Scripts/ruff.exe format src scripts tests --no-cache
.venv/Scripts/python.exe scripts/evaluate_models.py --record-offline --output .cache/f3-04b
.venv/Scripts/python.exe scripts/migrate.py
$env:FATA_BROWSER_EXECUTABLE='C:/Program Files/Google/Chrome/Application/chrome.exe'
$env:FATA_BROWSER_EVIDENCE_STAGE='f3-04b'
.venv/Scripts/python.exe scripts/check.py --integration --browser

# From the existing separate experiments/langgraph environment:
.venv/Scripts/python.exe -m pytest -q --basetemp=../../.cache/pytest-f304b-graph --junitxml=../../.cache/f304b-graph.xml
```

Migration result: `{'applied': []}`. Full shared checker: **22 child commands,
all exit 0**, summed elapsed **156.769 s**. Exact expanded checks:

| Command | Observed result |
| --- | --- |
| Python/Node/npm/Ruff `--version`; `npm.cmd --prefix web ls --depth=0` | Versions above; existing locked tree resolves |
| `.venv/Scripts/ruff.exe check src scripts tests --no-cache` | Passed |
| `.venv/Scripts/ruff.exe format --check src scripts tests --no-cache` | **119 files** formatted |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | Public contracts unchanged |
| `.venv/Scripts/python.exe scripts/prepare_responses.py --check` | Five existing assets match; live false |
| `.venv/Scripts/python.exe scripts/measure_token_admission.py --check` | Historical F3-03A evidence unchanged; its old-policy labels remain historical |
| `.venv/Scripts/python.exe scripts/prepare_model_evaluation.py --check` | Frozen 50-case assets unchanged |
| `.venv/Scripts/python.exe scripts/evaluate_models.py --check` | Current source snapshot matches; all 150 case/summary results unchanged |
| `npm.cmd --prefix web run check` | TypeScript passed |
| `npm.cmd --prefix web run format:check` | Prettier passed |
| `npm.cmd --prefix web run check:generated` | OpenAPI/TS/runtime validators match |
| `npm.cmd --prefix web run test` | **85/85 passed**, zero skips/cancellations; command elapsed **4.536 s** |
| `npm.cmd --prefix web run build` | Passed |
| `.venv/Scripts/python.exe -m pytest -q --basetemp=.cache/pytest-f107-unit --junitxml=.cache/f107/unit.xml` | **942 passed, 221 deselected**, zero errors/skips; **24.33 s** |
| `.venv/Scripts/python.exe scripts/smoke_local.py` | health200/readiness200/invalid422; safe correlated console; owned API child stopped |
| `.venv/Scripts/python.exe -m pytest -q -s -m integration --basetemp=.cache/pytest-f107-integration --junitxml=.cache/f107/integration.xml` | **221 passed, 942 deselected**, zero errors/skips; **101.61 s** |
| `.venv/Scripts/python.exe scripts/evaluate_baseline.py --check` | **24/24 development +16/16 legacy held-out**, zero failures; original result unchanged |
| `.venv/Scripts/python.exe scripts/measure_async_reads.py` | Five correct trials/mode, three mocked 40ms reads/trial, no retries, peaks1/3; medians **139.197/47.333 ms** sequential/concurrent; no real-provider performance claim |
| Isolated graph pytest command above | **47 passed**, zero errors/skips; **14.94 s** |

Root selections are disjoint, **1,163 Python tests** (942 routine +221 integration),
including **50 new tests** (35 routine +15 native). Existing specification/reference
tests remain distinct from native SQL evidence. The 150 evaluation observations,
40 baseline cases and 47 isolated graph tests are not pooled as model trials.
Hosted CI was not triggered; these are local CI-equivalent results.

Targeted development runs:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_counted_responses.py tests/test_responses.py tests/test_provider_hardening.py --basetemp=.cache/pytest-f304b-target
# 134 passed, 3.33 s
.venv/Scripts/python.exe -m pytest -q tests/test_prepared_sender.py --basetemp=.cache/pytest-f304b-sender-r2 --junitxml=.cache/f304b-sender.xml
# 35 passed, 1.84 s
.venv/Scripts/python.exe -m pytest -q tests/test_model_evaluation.py tests/test_prepared_sender.py --basetemp=.cache/pytest-f304b-unit-r3 --junitxml=.cache/f304b-unit-r3.xml
# 123 passed, 3.83 s
.venv/Scripts/python.exe -m pytest -q -m integration tests/test_sender_postgres.py tests/test_counted_spending_postgres.py tests/test_discrepancy_postgres.py --basetemp=.cache/pytest-f304b-native-r2 --junitxml=.cache/f304b-native-r2.xml
# 83 passed, 39.27 s before the final generation-stop case
.venv/Scripts/python.exe -m pytest -q -m integration tests/test_sender_postgres.py --basetemp=.cache/pytest-f304b-native-r3 --junitxml=.cache/f304b-native-r3.xml
# Final new file: 15 passed, 8.80 s
```

The first native new-file development run had nine cases, all passed (6.12 s).
Initial non-elevated pytest temp paths hit Windows WinError5; Docker pipe access
was denied without local permissions. Re-running authorized offline checks with
subprocess/temp/pipe permissions passed. Initial one-line lint/import formatting
issues were corrected before the full run. These are environment/development
outcomes, not passing first runs or provider requests. No automatic approval
review rejection occurred.

## Browser, sources and cleanup

Actual installed Chrome repeated the existing SQL-backed Save → Generate → Revise
→ lost approval response → explicit same-key retry → readback → profile change
→ immutable history → completion retry → owner switch/mobile recovery journey.
Runtime errors0, external page requests0, horizontal overflowfalse; immutable
record/table-count assertions pass. New screenshots:
[desktop](evidence/f3-04b-desktop.png), [mobile](evidence/f3-04b-mobile.png),
[mobile failure](evidence/f3-04b-mobile-error.png). Mobile failure was visually
inspected: failed B Save leaves generation/approval disabled. These are existing
fake-application regressions, not a live-provider UI feature.

OpenAI Docs skill used for read-only official documentation on **2026-10-25**:
[Responses create](https://developers.openai.com/api/reference/python/resources/responses/methods/create),
[count reference](https://developers.openai.com/api/reference/python/resources/responses/subresources/input_tokens/methods/count),
[counting guide](https://developers.openai.com/api/docs/guides/token-counting),
[API authentication overview](https://developers.openai.com/api/reference/overview),
[the configured model](https://developers.openai.com/api/docs/models/gpt-6.1-sol).
These support paths, request/response/auth format and model documentation only;
no account access, tariff/retention or real compatibility is established. The
expanded count page exceeded fetch limits; the Python reference was opened.
The guessed `/api/reference/authentication` URL returned404; the actual official
navigation resolved to the overview. No API or credential probe followed.

Post-run read-only native SQL found **zero rows in all seven spending tables**
and **zero `test_%` schemas**. No live authority schema or positive monetary permit
exists. `docker compose stop postgres` succeeded, preserving the volume; the
Docker Desktop engine was not shut down. Existing launcher/browser cleanup owns
its children. Final Git/link/privacy-preservation checks are recorded below.

Final checks observed **21 changed/new files**, all listed above; six Markdown
files passed strict UTF-8, fence/trailing-whitespace and **61 local-link** checks.
`git -c core.safecrlf=false diff --check` and `git diff --quiet --cached` passed;
nothing staged. `git check-ignore AGENTS.md` returns the local file and
`git ls-files AGENTS.md` returns nothing. Read-only `git diff --quiet --` over
the frozen corpus/catalog/assets/old scores, original migrations, domain/Agent/
persistence code, generated contracts/frontend, locks, graph and historical
handoffs/plans17/18/20 passed. The existing LF→CRLF notices are working-copy
configuration notices, not content/whitespace failures.

Workspace-filtered `Get-CimInstance Win32_Process` found **0** remaining task-owned
Chrome processes; smoke reported the owned API child stopped. Root locks remain:

```text
uv.lock: a56c144811ce65504791a4a259715950d89e5195089f3dcb441f52ffef47849a
web/package-lock.json: cc7282b0a959a2724d73267c22a679005e2d0dde040e58b2c32a9d75185d3ccf
```

## Final live decision and owner gates

Ready for **F3-04B offline review**; live execution remains **NO-GO**. This is a
prepared connector plus tested local integration, not an active live sender or
claim that authorization/configuration alone can now run a probe. Missing live
authority and truthful experiment assembly require separate owner-authorized
source/schema review; unconditional barriers must never be patched away for use
with replay grants. No such implementation/activation is included here.

Provider-dependent blockers remain: verified count tariff and maximum `C`,
endpoint-specific retention, actual account/model access, generation/cache price
and privacy acceptance, returned model/tier/usage/cache shape, count/actual equality,
encrypted continuation/schema compatibility and real latency. The owner-reported
manual external count18 establishes none of these for this application's flow.

The [updated checklist](../planning/19-f3-03c-pre-live-readiness.md) specifies one
future logical request using the fixed synthetic strength/bodyweight/beginner,
two-day/20-minute/no-exclusion profile. Target genuine auto catalog selection,
checked continuation and independently valid unpublished plan; expected2/2/4,
maximum3/3/6. Operator, <=2-hour UTC window, endpoints, data/privacy terms,
asset hashes and **four exact project/grant/day/session dollar limits** require
explicit sign-off after the missing assembly is separately reviewed.

Proposed ceiling remains **80,002 +3*Cµ microdollars** ($0.080002 +3*C) per logical
request, subject to verified prices/tax/FX/surcharges and owner approval. C is
unknown, so no positive permit or zero-count-price assumption is proposed for
activation. Local accounting is not an invoice/provider cutoff guarantee.

Any count/usage/model/tier/cache/native/privacy/authorization mismatch, exhausted
budget, uncertain SQL/send, deadline or operator stop halts; cancel/await owned
work, clear native state and retain uncertainty, with no replay/top-up/fallback.
Stop after the single separately authorized probe for review. No live evaluation,
broad sampling, judge, external-user pilot, hosted observability, AWS or later
milestone is implemented. No real-model quality or production-scale claim.
