# F3-02 handoff — offline Responses integration and durable spending controls

Date: 2026-10-24. Scope: **F3-02 only**, following owner acceptance of F3-01.
Recommendation: review the completed offline integration. **Live execution stays
blocked** because complete real-input admission has not been proved under the
ratified three-call limit. No counting call, live transport, active permit,
provider request, spending, hosted export, provisioning, commit or push occurred.

## Result and changed files

The existing typed Agent can now consume a separately labeled, request-local
OpenAI Responses **replay** provider backed exclusively by HTTPX MockTransport.
It still performs real local read-tool dispatch and independent plan validation.
A native PostgreSQL replay ledger reserves before the mock send, claims attempts
once, settles known usage atomically and retains unknown liabilities across
cancellation, lost acknowledgements and process restart. Application settings
remain fake-only; no new HTTP endpoint, model write tool or application planner
was added.

| Files | Purpose |
| --- | --- |
| `src/future_training/providers/__init__.py`, `responses.py` | Mock-only single-provider wire adapter, bounded stream parsing, native/local call correlation, request-local continuation and cleanup |
| `src/future_training/providers/schemas.py` | Strict provider projection of existing tool/output schemas, closed root envelope and disjoint discriminator conversion |
| `src/future_training/providers/accounting.py` | Typed actual usage partitions, total/cache/reasoning checks, exact fractional rates and upward-rounded microdollars |
| `src/future_training/providers/gates.py` | Default-off opt-in/shutdown supervision and unconditional unresolved-admission block; no live transport factory |
| `src/future_training/providers/artifacts.py`, `scripts/prepare_responses.py` | Reproducible versioned assets and check-only drift command |
| `src/future_training/persistence/spending.py`, `migrations/005_spending.sql` | Four empty replay-only control tables and native transaction/reservation/settlement/reconciliation implementation |
| `src/future_training/agent/protocol.py`, `budget.py`, `orchestration.py` | Explicit `replay` label, per-request provider state, distinct token metrics and known/unknown accounting; fake behavior retained |
| `src/future_training/observability.py` | Fixed replay model/prompt/tool/output labels and allowlisted token-kind/cache/reasoning counters; no content capture |
| `data/experiments/f3-02/v1/` | Five prompt/config/tool/output/manifest assets, four authored synthetic response JSON fixtures and provenance README |
| `tests/responses_doubles.py`, `tests/test_responses.py` | 57 provider, schema, artifact, budget, privacy and cancellation tests |
| `tests/test_spending_postgres.py` | 31 actual PostgreSQL ledger/concurrency/fault/restart tests |
| `tests/test_migrations.py`, `tests/test_profile_postgres.py` | Existing table inventories include authorized spending tables; original migration/restart assertions remain |
| `scripts/check.py`, `web/scripts/browser-smoke.mjs` | Shared asset drift check; scoped `f3-02` browser evidence names preserve historical screenshots |
| `contracts/provider-safety.md` | Implemented boundary, accounting/ordering contract, token-admission conflict, alternatives and limitations |
| `README.md`, `docs/development.md`, `docs/runbook.md`, this handoff | Current status, commands, recovery and review gates |
| `docs/implementation/evidence/f3-02-*` | New replay failure trace and three browser regression screenshots |

No root dependency/lock, frozen domain/schema/evaluation source, catalog, corpus,
baseline output, OpenAPI/TypeScript artifact, original migration or historical
planning/acceptance/handoff/evidence file changed. No packages were installed.

## Transport and compatibility decision

Retain already pinned **HTTPX 0.28.1** in the existing development dependency
group; do not add an SDK or change the application lock merely to exercise the
wire protocol. One POST/SSE endpoint with no retries is sufficiently narrow for
the existing transport. Current official [HTTPX releases](https://github.com/encode/httpx/releases)
list 0.28.1 as latest; [package metadata](https://github.com/encode/httpx/blob/0.28.1/pyproject.toml)
requires Python >=3.8. Installed metadata agrees, and the new tests run on
Python **3.14.9**. This is observed compatibility, not a claim that older release
classifiers independently certify every Python 3.14 transport behavior.

Official [async HTTPX](https://www.python-httpx.org/async/) and
[mock transport](https://www.python-httpx.org/advanced/transports/) documentation
supports the chosen lifecycle. The adapter constructs its own client, disables
environment proxies/redirects and accepts exactly MockTransport, including a
second check before use. There is no SDK retry layer, arbitrary base URL,
credential lookup, default socket transport or key setup. The only encoded URL is
`https://api.openai.com/v1/responses`, used as an in-memory mock request address.
Official documentation browsing is distinct from invoking that endpoint.

The prepared configuration retains `gpt-6.1-sol`, low reasoning, default/Standard
tier, text/strict local function tools, `store=false`, background off, streaming,
`tool_choice=auto`, parallel calls off and 30-minute upstream cache mode. Provider
capabilities/account access and real protocol compatibility remain unverified.
No alternative model, built-in tool, region, cache experiment or hosted sink was
enabled. Prices remain dated assumptions from approved plan 17, not measured costs.

## Provider, validation and privacy evidence

Four **authored synthetic** fixtures model a catalog call with dummy encrypted
state, valid plan, refusal and incomplete response. They are not captured real
responses. Prompt/config/tool/output assets and fixtures have manifest digests;
the manifest maps all 40 frozen cases to their correct execution boundary.
Source labels distinguish template/fake/replay/live. Its current source is replay,
live is false, and explanation clarity remains N/A without a new explanation
contract. No held-out cases or baseline expectations were changed.

Observed provider evidence:

- Native `call.synthetic/one` maps to local `call-1`; the existing read dispatcher
  validates arguments/results and the continuation returns the original native
  ID. The second mock request carries ordered dummy reasoning/function items and
  the checked local tool result. Two requests, one dispatch, valid plan, no
  candidate publication from internal generation.
- Per-request state permits the same native ID in two concurrent principals'
  separate sessions, rejects cross-attempt duplicate native calls, and rejects
  duplicated/unmatched tool results before another request. Session exit clears
  native items on success, failure and cancellation; concurrent admission remains
  shared with the existing Agent.
- Terminal snapshots supply authoritative output/usage; argument/text deltas do
  not dispatch or publish. Split UTF-8/chunks, multiline/CRLF framing, malformed
  order/encoding/events, duplicate terminal, EOF and byte limits are exercised.
  Intermediate cumulative usage is not summed. Refusal becomes abstention;
  incomplete output becomes typed failure. Semantic invalidity uses the existing
  single-repair path and unchanged domain validator.
- Unknown/write tools, owner arguments, malformed JSON and invalid types cannot
  gain capabilities. HTTP 301/4xx/429/5xx and interrupted transports cannot silently
  retry. Unknown charge/usage stops this replay run, retaining its full allowance.
  Existing fake transport retry tests retain the one-owner/one-retry guarantee.
- Whole-request tool/attempt/input/output limits, fake-clock deadline, explicit
  cancellation and principal admission are exercised through the existing Agent.
  Replayed reported tokens are labeled `provider_reported_replay`; fake token
  metrics remain `simulated_utf8_quarters`.
- Numeric usage validates ordinary/cache-write/cache-read partitions, total
  counts and reasoning as a subset of output. The invented fixture's 1,000 input /
  100 output tokens, including 20 reasoning tokens, price to **2,770 microdollars**
  at the fixture rate card; reasoning is not billed twice. This is arithmetic on
  invented data, not an observed provider invoice.

[Replay failure trace](evidence/f3-02-replay-failure-trace.json) records two
deliberately invalid-exercise responses: authoritative validation rejects both,
one repair is consumed and the terminal outcome is `error`, reason
`semantic_repair_exhausted`. It reports 2,000/200 replay-reported input/output
tokens, zero real provider requests and no candidate. The root cause is the
synthetic invalid proposal; the correct response is rejection, not weakening
the validator or substituting a template. This is replay diagnostics, not a
spontaneous real-model failure or a real tool-choice demonstration.

Canaries in dummy encrypted state and private billing-like identifiers are absent
from both configured sinks (bounded local spans and safe console), including
result representations. Existing prompt/body/exception/credential/identity and
Python/JavaScript egress canaries also pass. Only reviewed version labels and
numeric accounting counters were added to tracing. No raw response, prompt,
workout, reasoning, credentials, private billing IDs or exception strings are
logged/exported. There is no hosted sink. Test handlers explicitly capture
synthetic requests for assertions; they are not application logging.

## Token admission: unresolved conflict, enforced safe outcome

The investigation found no official complete local bound for the selected model's
role/schema/tool formatting and opaque continuation state. Text tokenization,
UTF-8 byte ratios and an empirically generous margin do not prove the required
real-input ceiling. The documented exact input count is a remote request;
[OpenAI explains these limitations](https://developers.openai.com/api/docs/guides/token-counting).

Initial count → model-selected call → continuation count → final model response
requires **four outbound calls**, before repair/retry, versus the ratified **three**.
No counting request was made or exempted. Fake/replay allowances do not solve
this conflict. `LiveGate.check()` refuses even a hypothetical approved permit
with `real_input_admission_unproven`; normal settings reject live mode and no
live-capable transport can be constructed.

Owner alternatives are in [provider safety](../../contracts/provider-safety.md):
obtain a complete documented bound/provider-enforced input cap; separately ratify
a count-aware combined-call budget (potentially six total for three counted
generation attempts, with explicit retry/pricing/privacy rules); or remain offline
and reconsider a compatible provider. **No amendment is adopted.** 30 seconds,
four reads, three attempts, one repair/retry, 16,000/4,000 tokens and admission
limits remain unchanged. F3-03 live execution is not ready merely because these
offline tests pass.

## Migration, durable state and native fault evidence

Migration **005_spending.sql** adds `spend_projects`, `spend_grants`,
`spend_sessions`, `spend_attempts`, composite foreign keys, unique attempt/run
identities and constrained accounting states. It inserts no row. Project mode
has a SQL `replay`-only check; a live mode update is rejected. Default startup has
no grant/session or allowance. Five migrations are applied in local development;
repeat migration returns `{'applied': []}`.

Project-row locking serializes reserve/claim/settle/shutdown across repository
objects. Reservation includes all project/day/grant/session liabilities before
adding the proposed amount. A one-shot durable send claim precedes the mocked
transport. Matching attempt and settlement retries recheck committed state under
that lock; different fingerprints conflict. Unknown sent claims never expire or
refund automatically. SQL statement/lock limits plus a five-second owned-operation
timeout bound cooperative transaction work; caller cancellation drains it and
propagates, including simultaneous commit failure. Cleanup can finish after the
generation deadline; no transport is admitted after the deadline recheck.

| Actual PostgreSQL scenario | Observed result |
| --- | --- |
| Three simultaneous reservations, each scoped limit tested separately | Exactly one `reserved`, two `spend_exhausted`; one row; no oversubscription |
| Matching concurrent attempt IDs | Second connection visibly waits in `pg_blocking_pids`; both recover same reservation, one row |
| Different fingerprint / repeated settlement | Conflict on changed allowance/usage; identical settlement returns 2,770 once, including after repository restart |
| Lost reservation COMMIT acknowledgement | No transport; repository fenced; reconciliation finds committed row; retry does not duplicate it |
| Rolled-back/unknown reservation COMMIT | No transport; reconciliation sees no row after transaction ordering resolves; safe reserve can retry |
| COMMIT still in flight, then commit or rollback | Fresh connection actually blocks behind project row; cannot conclude absence until original transaction ends |
| Lost one-shot claim acknowledgement | State remains `sent`, 22,500 reserved microdollars; repeated claim/release/next run attempt rejects |
| Lost settlement acknowledgement | Reconciliation finds committed settlement; exact retry returns existing 2,770 without another debit |
| Cancellation during reservation/settlement COMMIT | Owned SQL finishes before cancellation propagates; reserved or settled authoritative state retained |
| Cancellation plus rollback failure | Cancellation wins; uncertainty fence remains until explicit database reconciliation |
| Actual child interpreter exits after committed claim | New runtime reads `sent` with full 22,500 liability; no release or next attempt is allowed |
| Midnight before send claim | Rebase checks new day's existing liability; claim denied until legitimate unsent reservation is released |
| Session expiry/new session | Expired session cannot add work; previous unknown liability survives the new session/day and restart |
| Unexpected model/tier/12h cache or usage over allowance | Project frozen durably, full sent reservation retained; new repository also refuses work |
| Missing usage or cancelled mock HTTP after send claim | No fabricated free response; full default 35,000 liability remains |
| Database unavailable or failed reserve | Zero transport requests; sanitized typed error, no raw driver exception |
| Emergency disable after reservation | Repeated stop is safe; reserved attempts cannot claim a send; unsent release remains explicit |

These **31 native tests** use real local PostgreSQL connections and controlled
barriers/driver faults, not fake SQL or a reference ledger. The abrupt-process
case demonstrates exit after a known durable claim, not arbitrary power loss.
Real billing/receipt reconciliation is unverified and intentionally has no API
calls. PostgreSQL reconciliation establishes transaction state only; unknown
provider charges remain reserved without authoritative usage. Ledger rows contain
minimal local opaque metadata and numeric usage, with no raw content or provider
receipt IDs. Resolved metadata retention is a manual 90-day proposal; unresolved
records are retained, with no background purge/recovery service.

## Exact commands and final outcomes

All commands ran locally on 2026-10-24. Normal process access was used for cached
Docker, esbuild, PostgreSQL and installed Chrome. No acquisition command, hosted
CI dispatch or dependency install ran.

```powershell
docker compose up -d --pull never postgres
.venv/Scripts/python.exe scripts/prepare_responses.py
.venv/Scripts/python.exe scripts/prepare_responses.py --check
.venv/Scripts/python.exe scripts/migrate.py

$env:FATA_BROWSER_EXECUTABLE='C:/Program Files/Google/Chrome/Application/chrome.exe'
$env:FATA_BROWSER_EVIDENCE_STAGE='f3-02'
$env:FATA_F302_EVIDENCE='1'
.venv/Scripts/python.exe scripts/check.py --integration --browser

experiments/langgraph/.venv/Scripts/python.exe -m pytest -c experiments/langgraph/pyproject.toml experiments/langgraph/tests -q --junitxml=.cache/f302-graph.xml
```

Asset generation wrote five files; check mode passes. Migration initially returned
`{'applied': ['005_spending.sql']}`; repeat returned no changes. The final shared
runner and isolated graph suite exited **0**. Final shared child commands/results:

| Exact command/check | Result |
| --- | --- |
| `.venv/Scripts/python.exe --version`, `node --version`, `npm.cmd --version`, `.venv/Scripts/ruff.exe --version` | 3.14.9 / 24.22.1 / 11.19.1 / 0.17.2 |
| `npm.cmd --prefix web ls --depth=0` | Existing tree resolved, no installation |
| `.venv/Scripts/ruff.exe check src scripts tests --no-cache` | Passed |
| `.venv/Scripts/ruff.exe format --check src scripts tests --no-cache` | 93 files already formatted |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | Passed, no public contract drift |
| `.venv/Scripts/python.exe scripts/prepare_responses.py --check` | Five assets match, live false |
| `npm.cmd --prefix web run check` | TypeScript passed |
| `npm.cmd --prefix web run format:check` | Prettier passed |
| `npm.cmd --prefix web run check:generated` | OpenAPI TypeScript and runtime-validator drift checks passed |
| `npm.cmd --prefix web run test` | **85/85 passed**, no skipped/cancelled; 6.120 s |
| `npm.cmd --prefix web run build` | Passed, existing assets built |
| `.venv/Scripts/python.exe -m pytest -q --basetemp=.cache/pytest-f107-unit --junitxml=.cache/f107/unit.xml` | **661 passed, 136 deselected**, no skips/errors; 19.17 s |
| `.venv/Scripts/python.exe scripts/smoke_local.py` | health200 / ready200 / invalid422; correlated safe console; owned API child stopped |
| `.venv/Scripts/python.exe -m pytest -q -s -m integration --basetemp=.cache/pytest-f107-integration --junitxml=.cache/f107/integration.xml` | **136 passed, 661 deselected**, no skips/errors; 55.89 s; actual native SQL/HTTP/installed Chrome |
| `.venv/Scripts/python.exe scripts/evaluate_baseline.py --check` | **24/24 development, 16/16 legacy held-out**, zero failures; unchanged artifact |
| `.venv/Scripts/python.exe scripts/measure_async_reads.py` | Five trials/mode, three 40ms mock reads/trial, both 5/5 correct, no retries; medians 139.403ms sequential / 47.349ms concurrent, peak inflight 1 / 3 |
| Isolated graph command above | **47/47 passed**, 19.22 s, synthetic checkpoint environment only |

There are **797 root Python tests**, in disjoint routine/integration selections,
plus 47 isolated graph cases and 85 frontend cases. F3-02 adds 57 routine and
31 native cases; do not add targeted reruns or baseline cases to inflate totals.
Six existing specification/reference tests remain distinct from actual SQL proof.
All 19 shared commands exited zero; summed child time **107.141 s**, not provider
latency. Ignored detailed results are `.cache/f107/check-results.json`,
`unit.xml`, `integration.xml`, and `.cache/f302-graph.xml`.

Targeted bring-up commands also ran:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_responses.py --basetemp=.cache/pytest-f302-replay-final
.venv/Scripts/python.exe -m pytest -q -m integration tests/test_spending_postgres.py --basetemp=.cache/pytest-f302-pg-final
node web/node_modules/prettier/bin/prettier.cjs --write web/scripts/browser-smoke.mjs
git diff --check
```

The final provider-only run passed 57/57. The targeted native run passed 30/30
before the cancellation-plus-commit-failure regression was added; the final full
suite includes all 31. Earlier bring-up exposed incorrect fixture assertions
about catalog IDs/stats/tracer APIs and a Windows child-loop choice; those were
corrected. Full validation first stopped on browser harness formatting, then on
an old restart table-inventory assertion. Both were corrected without weakening
restart, ownership or immutable-record checks. No final check remains failing.

No `--evidence` flag or old F1/F2 evidence switch was used. F3-02 switches write
only new files. [Desktop](evidence/f3-02-desktop.png),
[mobile](evidence/f3-02-mobile.png) and [mobile error](evidence/f3-02-mobile-error.png)
show the existing synthetic workflow. Installed Chrome verified explicit Save →
Generate → Revise → Approve/same-key retry → immutable readback/history →
completion/feedback and owner switch: zero runtime errors, zero external page
requests and no horizontal overflow. This remains fake-provider browser evidence;
no new provider UI or real-model streaming result is claimed.

Final inspection found PostgreSQL **18.6**, five applied migrations, no leftover
test schemas, public ledger counts **(0,0,0,0)** and approved/key/audit/session/key
counts **(0,0,0,0,0)**. No development reset occurred. Lock SHA-256 values remain:
`uv.lock` = `a56c144811ce65504791a4a259715950d89e5195089f3dcb441f52ffef47849a`;
`web/package-lock.json` = `cc7282b0a959a2724d73267c22a679005e2d0dde040e58b2c32a9d75185d3ccf`.

Observed host: Windows 11 build 10.0.26200; installed Chrome
155.0.8059.85. A read-only documentation check validated six changed/new Markdown
files, 43 local links, UTF-8, fence balance and trailing whitespace. It verified
the four fixture hashes, the 40-case eligibility manifest, seven allowlisted
failure-trace spans and all final runner denominators. `git diff --check` passed;
the explicit frozen-path/lock/generated-contract diff was empty. `AGENTS.md`
remains ignored and untracked. Git's existing LF-to-CRLF notices are not check
failures. `docker compose stop postgres` completed with image/volume preserved;
the launcher/browser tests stopped their owned processes. No service was added
or left running for this unit.

## Remaining limits and readiness

F3-02 implements a real wire parser/adapter and real SQL accounting **with fake
transports and invented billing data**. It establishes no genuine model-selected
tool behavior, model quality, live pricing enforcement, account access, TLS/pool
performance, provider retention, hosted tracing or AWS experience. Native SQL
ordering is tested across repository objects; the application still supports
only one process and synthetic local identities. Cooperative mocks/egress guards
are not an OS firewall or a hostile-code sandbox. No real-user release gate moved.

Live entry remains blocked on accurate complete input admission, separate owner
authorization, a reviewed live transport/permit, fresh price/privacy review and
numeric funding. The ledger's `replay`-only SQL mode cannot become a live budget
through credentials or an environment toggle. Real billing reconciliation and
receipt handling need explicit future review; unknown charges must remain held.
Explanation clarity/human quality, real model latency and S01 model-selected
tool evidence are still unverified. The existing approval reconciliation, immutable
records, owner isolation, terminal-only candidate publication, request ceilings,
frozen baseline and F2 decisions retain their regression evidence.

Ready for **F3-02 owner review**. A separately authorized F3-03 can proceed only
after the token-admission decision and other live gates are satisfied; this
completion does not authorize any call or spending. Stop after F3-02.
