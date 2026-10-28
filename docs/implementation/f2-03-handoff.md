# F2-03 handoff — Contained LangGraph comparison

Date: 2026-10-24. Status: complete for owner review. F2-04 has not begun.

## Outcome and recommendation

**Retain the accepted typed workflow in the application.** The contained graph
demonstrates real SQLite checkpoints, dynamic interruption, interpreter exit,
restoration in a new interpreter and validated completion. These are useful
capabilities, but the accepted product requires bounded request-local generation,
explicit cancellation and transient candidates. It does not currently require
durable generation resumption. Graph adoption would add persistence/privacy and
replay obligations without solving an unmet product requirement.

The experiment is implemented, not a reference model or placeholder. It is under
[`experiments/langgraph`](../../experiments/langgraph/README.md), with a separate
environment and lock. The application never imports it. No candidate publication,
profile Save, approval, durable user-plan write or business action is available
to its nodes. No production adoption is proposed by this handoff.

## Changed files

| Paths | Change |
| --- | --- |
| `experiments/langgraph/pyproject.toml`, `uv.lock` | Separate pinned experimental environment; root manifests/locks untouched |
| `experiments/langgraph/spike.py` | Synthetic fixtures, strict checkpoint payload/ledger, seven-node graph, SQLite runtime, bounded resumption, offline guards and metadata inspection |
| `experiments/langgraph/run.py` | Real process-restart demonstration, equivalent-scenario comparison, typed-cancellation demonstration, timing, explicit evidence export and scoped cleanup |
| `experiments/langgraph/tests/conftest.py`, `tests/test_spike.py` | Selector-loop/egress test setup and 47 experimental tests |
| `experiments/langgraph/README.md` | Pre-install design, checkpoint/privacy boundaries, source references and reproducible commands |
| `docs/implementation/evidence/f2-03-demo.json`, `f2-03-compare.json` | Actual restart inspection; per-case outcomes/accounting; raw timings, dependencies and source/lock provenance |
| `docs/implementation/evidence/f2-03-{desktop,mobile,mobile-error}.png` | New installed-browser regression screenshots |
| `web/scripts/browser-smoke.mjs` | Allow the new screenshot stage, preserving historical evidence |
| `README.md`, `docs/development.md`, `docs/runbook.md`, this handoff | Current status, installation, execution, diagnosis, cleanup and decision |

No application Python source, migrations, domain rules, generated contracts,
frozen evaluation/catalog/results or historical implementation evidence changed.
No main dependency upgrade, graph/checkpointer registration, new service, queue,
Redis, worker, endpoint or user flow was introduced. `AGENTS.md` remains ignored.

## Documentation and dependency choices

Reviewed the approved F0/F2 plan, contracts 12–14, F1 execution/acceptance evidence
and accepted F2-01/F2-02 handoffs. The existing `Run` already supplies strict fake
provider framing, read-tool validation, independent domain checking, bounded
repair/retry, cancellation, admission and authoritative publication boundaries.
The selected workflow exercises these capabilities without duplicating a planner.

Official package metadata checked on October 24 lists stable **LangGraph 1.2.17**
(October 24 release) and **langgraph-checkpoint-sqlite 3.1.2** (October 12 release),
both Python >=3.10. These versions were resolved and tested with the project's
Python 3.14.9 and Pydantic 2.14.1, rather than assuming compatibility from metadata.
Sources: [LangGraph package](https://pypi.org/project/langgraph/),
[SQLite checkpointer package](https://pypi.org/project/langgraph-checkpoint-sqlite/).

The separate lock resolves checkpoint 4.3.0, aiosqlite 0.22.1, langchain-core 1.7.0,
LangSmith 0.14.12 and their transitive dependencies. `uv pip check` verified all
**55 installed distributions**. The application environment has 29: the experiment
adds 29 distribution names and omits three application/dev names (Click, Ruff,
Uvicorn). Its Starlette is 1.10.0 versus the root's unchanged 1.9.0. Both sides of
the graph/typed comparison run in the **same isolated environment**; the full app
regression runs in the original environment. These are not interchangeable locks.
The complete installed version inventory is in the comparison JSON.

SQLite was chosen because it provides actual local file persistence without
another service or use of application PostgreSQL state. Its async saver is used
with `durability="sync"`. Checkpoint payloads contain JSON-compatible primitives;
the official JsonPlus serializer uses MessagePack with strict allowed modules
(`allowed_msgpack_modules=None`) and no pickle fallback. This follows the
[checkpointer package's deserialization guidance](https://pypi.org/project/langgraph-checkpoint-sqlite/).
No LangGraph SDK/server, model integration, Studio or hosted tracing is used.

The [official interrupt documentation](https://docs.langchain.com/oss/python/langgraph/interrupts)
explains that `Command(resume=...)` resumes an interrupt by restarting its node.
The gate therefore performs no business action before `interrupt()`, and that
call is outside broad exception handling. Checkpointing supplies graph-state
persistence; it does not make external effects exactly once. General background:
[LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence).

## Implemented graph and preserved limits

The seven nodes are `context`, `reserve_model`, `model`, `reserve_tool`, `tool`,
`gate` and `validate`. Conditional edges handle tool continuations, one semantic
repair, one transport retry and terminal outputs. The selected fixed fixture is
an adult, beginner, bodyweight strength profile with two 20-minute sessions;
alternative scenarios change controlled provider behavior or fixed synthetic
request text. No arbitrary profile, request, graph state, thread or provider is
accepted by the command interface.

Reuse includes the existing `Agent.session()`, `Budget`, `FakeModel`/
`ScriptedFake`, typed provider envelopes, `ReadTools.dispatch/checked_bytes`,
catalog, baseline and independent validator. The graph also reuses `Run._validate`
for accepted clarification/abstention/constraint policy. That private-helper
coupling is a deliberate spike limitation, guarded by equivalent-scenario tests;
no application refactor was needed to make it public.

Provider orchestration is explicit graph code rather than nesting `Run._call`'s
retry loop. This is necessary to checkpoint a reservation **before** each attempt.
The graph owns the only provider retry; no graph node RetryPolicy, SDK retry or
whole-request replay is configured. Duplicate tool IDs, malformed output,
underreported/overrun usage and tool results follow the accepted rules.

Each active invocation acquires the application's existing shared admission:
one per principal, two globally. The fixed fixture permits only principal A;
B is used for negative ownership tests. Pausing/cancellation releases admission;
resumption reacquires it. This is an offline harness, not another HTTP generation
entry point or production authentication mechanism.

The persisted ledger retains all provider/tool/retry/repair/token counters and
pending token reservations. Limits remain **30 seconds, four read dispatches,
three provider attempts, one transport retry, one repair, 16,000 input/4,000 output
simulated tokens**. Reported overages are retained and fail the run, never clamped.

Wall and monotonic starts persist across a same-machine, same-boot interpreter
restart. Resumption uses the greater elapsed duration, rejects negative elapsed
values and never resets the original 30-second allowance. Initial checkpoint
loading has a two-second bound; active work uses the existing deadline watchdog.
Using a shared monotonic clock across processes follows the
[Python clock contract](https://docs.python.org/3.14/library/time.html#time.monotonic).
OS reboot, machine transfer and long human waits are outside this design.

If a fresh invocation finds a pending provider/tool operation, it **does not
redispatch**. An uncertain provider keeps its worst-case reserved tokens and is
classified uncertain; a reserved read remains charged. The run terminates with
`uncertain_operation_not_replayed`. This deliberately sacrifices possible recovery
to preserve bounded accounting. It does not claim exactly-once external execution.

Restored context is checked against fixed profile/request/policy, catalog digest,
catalog revision and prompt/tool/output/model/validator versions. Retained tool
messages are checked again against the original tool/result validator. Completed
plan reads are independently revalidated; an altered duration is rejected. There
is no candidate store, approval port or application persistence writer to invoke.

## Reproducible real checkpoint → restart → resume

Run from repository root using the separate environment:

```powershell
experiments/langgraph/.venv/Scripts/python.exe experiments/langgraph/run.py demo --write-evidence
```

The parent creates a unique `.cache/f203/restart-<uuid>.sqlite`, launches `start`,
waits for that interpreter to exit successfully, then launches `resume` and
`repeat` in two more interpreters. It asserts three different PIDs, compares the
restored context hash/counters **before execution**, checks completion and proves
the repeat does not add a provider call. This is not resumption in a retained live
graph object. The original process exits normally after its persisted interrupt;
this demonstration does not simulate power loss or kill the SQLite writer mid-COMMIT.

[Observed raw restart evidence](evidence/f2-03-demo.json):

| Phase | PID | State / next | Provider / tools | Checkpoints / writes |
| --- | ---: | --- | --- | --- |
| Start, then process exit | 34980 | `gate` / `gate` | 1 / 1 | 7 / 13 |
| New process resume | 15540 | `end` / none | 2 / 1 | 11 / 22 |
| Third process repeat read | 35800 | `end` / none | 2 / 1 | 11 / 22 |

The pause and fresh process's pre-execution context SHA-256 both equal
`d26b0cb3605936732a2a16cd31685e0affab581e3923cd58bb395c04be16db1d`.
The completed/repeated output hashes match, with 4,458 input/415 output simulated
tokens, no retries/repairs/uncertainty. SQLite contains only `checkpoints` and
`writes`; `PRAGMA integrity_check` returns `ok`. Observed main/WAL/SHM totals during
the three inspections were 312,936 / 369,968 / 258,048 bytes respectively. WAL is
accounted for separately; the first 4,096-byte main file is not the complete
persistence footprint. The unique database and sidecars were deleted afterward.

For manual inspection, use `start`, `inspect`, `resume`, `repeat`, `cleanup` with
the same bounded `--database manual-demo` name, as documented in the runbook.
Resumption must occur within the original deadline. Inspection reports metadata,
counts, stages and hashes, never checkpoint bodies or workout content.

## Equivalent scenarios, failures and replay

[Raw comparison](evidence/f2-03-compare.json) records **14/14 identical output
objects and 14/14 identical complete budget metrics**, including finish reasons
and uncertain attempts. Expected errors count as successful scenario assertions,
not successful plans. Each side uses equivalent fixed fakes and expected outcomes.

| Scenario | Observed outcome / reason | Attempts / tools / retries / repairs |
| --- | --- | --- |
| Normal | plan | 2 / 1 / 0 / 0 |
| Fixed unsupported text | clarify | 2 / 1 / 0 / 0 |
| Refusal | abstain | 1 / 0 / 0 / 0 |
| Invalid output then repair | plan | 3 / 1 / 0 / 1 |
| Invalid twice | error: `semantic_repair_exhausted` | 3 / 1 / 0 / 1 |
| First transient failure | plan, one uncertain attempt | 3 / 1 / 1 / 0 |
| Two transport failures | error: `transport_retry_exhausted` | 2 / 0 / 1 / 0 |
| Malformed provider bytes | error: `malformed_provider_response` | 1 / 0 / 0 / 0 |
| Model asks for `approve_plan` | abstain after an error result; no write | 2 / 1 / 0 / 0 |
| Fifth read requested | error: `tool_budget_exhausted` | 2 / 4 / 0 / 0 |
| Fourth provider request needed | error: `provider_budget_exhausted` | 3 / 3 / 0 / 0 |
| Reported token overrun | error: `reported_token_overrun` | 1 / 0 / 0 / 0 |
| Mismatched tool identity | error: `tool_result_mismatch` | 1 / 1 / 0 / 0 |
| Malformed tool schema | error: `invalid_tool_result` | 1 / 1 / 0 / 0 |

The overrun retains actual reported 16,001 input/4,001 output tokens and makes no
further call. Two uncertain transport attempts consume the full reserved 4,000
output tokens; there is no uncounted third retry.

Additional observed experimental assertions (all passed):

- A deliberately thrown `GateFault` leaves next node `gate`, one completed provider/read and no business effect. A newly initialized runtime resumes that safe failed node with `None`, finishing at two providers/one read. This failure-recovery test uses fresh objects in one process; the separate dynamic-interrupt demo above uses real interpreter restarts.
- Cancellation while a provider is blocked preserves `pending=provider`, one attempt and its reservation. A fresh runtime makes zero new calls, returns the uncertainty error and records one uncertain attempt. Tool cancellation similarly preserves one dispatch and does not repeat it. Barriers/events control entry and release; no sleep-based ordering assertions.
- Pause/resume under repair, transient failure and exhausted-read scenarios preserves exact original accounting. A second start is rejected. Completed repeat reads leave counts and output unchanged.
- A same-principal concurrent invocation is refused by shared admission; cancellation releases it. An event-driven clock expires a stalled provider and leaves the pending reservation intact.
- Expired wall time, negative elapsed time, monotonic expiry despite only five seconds of wall elapsed, and monotonic regression all fail closed. The watchdog/expired-entry boundary was corrected after the initial deadline case exposed a classification race.
- Final independent revalidation crossing the original deadline cannot return a result; a subsequent read cannot reset that deadline. A controlled clock asserts both boundaries.
- Wrong principal, stale source/version/scenario, changed profile/request/system, altered retained tool content and altered completed plan duration cannot produce a usable result. Invalid resume content such as `approve=true` returns an error and grants no authority.
- Supplying synthetic provider credentials and enabled tracing variables still yields only fake execution. Hosted tracing is explicitly disabled in scope; socket connects, UDP sends and DNS paths are denied. Alternate DNS guards and absence of credential canaries from inspection/database bytes are asserted.

The typed cancellation demonstration pauses at the corresponding continuation,
after one provider/read. Cancellation closes the run and a second `execute()` is
rejected. A deliberate **new request** succeeds with two providers/one read; it
repeats work rather than resuming. These actual counters are in the comparison
report. This is correct accepted application behavior, not a typed-flow defect.

## Side-by-side assessment

| Area | Accepted typed flow | Contained LangGraph implementation |
| --- | --- | --- |
| Correctness | Authoritative tools/domain validation; bounded outcomes | Equivalent 14-case outputs and accounting; same validators plus restoration checks |
| State/lifetime | Request-local canonical preview; cancellation discards run | Explicit checkpoint payload, versioned ledger, SQLite retention, resumable safe gate |
| Recovery | One bounded provider retry; new request after cancellation | Same retry cap; safe-node restart and dynamic resume; pending effects fail closed |
| Business authority | SSE publication and PostgreSQL approval remain separate | No candidate or approval access; checkpoint completion is only an unpublished result |
| Debugging | Small explicit state sequence and existing local spans | Saved `next`, state history, ledger and table counts survive process exit; more framework and serializer stack frames |
| Complexity | 489 physical lines in orchestration module | 678 in spike including fixtures/ledger/graph/runtime, plus 310 in CLI/evidence harness; reuses typed private validation helper |
| Dependencies | Original 29-distribution environment | Separate 55 distributions; SDK/tracing packages present transitively but disabled/unused |
| Product fit | Matches short-lived request/Stop semantics | Valuable for a future durable-wait/resume requirement, currently absent |

Line counts include comments/fixtures and differ in responsibility; they are not
cyclomatic-complexity scores. They make the additional implementation and harness
visible rather than pretending checkpointing removed policy code.

Debugging exposed two concrete integration pitfalls: SQLite WAL initialization
needed an explicit commit after its page-limit pragma, and Python's synchronous
SQLite transaction context did not close the inspection connection. The latter
initially prevented file deletion on Windows. Explicit connection closure fixed
it; the process-demo test asserts cleanup. These were experimental defects,
corrected before final evidence. Strict serializer loading, state inspection and
existing tool/validator errors were useful; replay-safe reservations and deadline
restoration still required application-specific code.

### Local timing, with proportional claims

Same fixed valid-plan workload, no injected I/O delay, five unmeasured warm-ups
per mode, 20 samples/mode, alternating pair order. Both construct a fresh fixture
and Agent. Graph timing additionally includes graph compilation, SQLite open/setup,
synchronous checkpoints, restoration guards and close. Both timings include fake
execution and real independent validation. Imports are already warm; no browser,
HTTP or application PostgreSQL request is timed. Raw nanoseconds are retained.

| Mode | Measured samples | Failures | Median ms | Nearest-rank p95 ms |
| --- | ---: | ---: | ---: | ---: |
| Typed | 20 | 0 | 11.71560 | 13.2958 |
| Graph + SQLite | 20 | 0 | 158.80865 | 179.8566 |

This measures the cost of the additional persistence/guard capability in this
harness, not pure framework overhead with equal durability. One workstation,
20 samples, uncontrolled host scheduling/storage load and warm imports do not
establish production latency, throughput, real-model quality/cost or statistical
significance. No timing threshold or performance claim is added to CI. Saved
timings from earlier code/review passes were superseded by the final-source run;
source/lock hashes in the report identify that run.

## Exact commands and observed checks

Dependency acquisition, once, using the authorized separate environment:

```powershell
uv lock --project experiments/langgraph
uv sync --project experiments/langgraph --frozen --python .venv/Scripts/python.exe
```

The resolver acquired CPython 3.14.9 while locking; sync used the existing project
interpreter and created only the separate environment. It resolved 57 lock
packages and installed 55 distributions. No application lock/environment was
changed. Routine commands do not acquire dependencies. The following offline
compatibility checks passed after pointing uv's cache into the workspace:

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.cache/uv'
uv pip check --python experiments/langgraph/.venv/Scripts/python.exe
uv lock --project experiments/langgraph --check --offline --python .venv/Scripts/python.exe
.venv/Scripts/ruff.exe format --check experiments/langgraph --no-cache
.venv/Scripts/ruff.exe check experiments/langgraph --no-cache
experiments/langgraph/.venv/Scripts/python.exe -m pytest -c experiments/langgraph/pyproject.toml experiments/langgraph/tests -q --junitxml=.cache/f203/tests.xml
experiments/langgraph/.venv/Scripts/python.exe experiments/langgraph/run.py demo --write-evidence
experiments/langgraph/.venv/Scripts/python.exe experiments/langgraph/run.py compare --write-evidence
```

Final experimental result: **47 passed in 19.77 s**, zero failures/skips. These
are actual LangGraph/SQLite tests. They are separate from root application tests
and are not silently skipped or presented as PostgreSQL proof. Earlier formatting,
setup/cleanup and expiry findings were corrected; all final commands above passed.
An initial compatibility command using uv's external default cache lacked access;
the explicit workspace-cache commands above succeeded without changing permissions.

Existing regressions used the cached local PostgreSQL image and installed Chrome:

```powershell
docker compose up -d --wait --pull never postgres
Remove-Item Env:FATA_F2_EVIDENCE -ErrorAction SilentlyContinue
$env:FATA_BROWSER_EVIDENCE_STAGE='f2-03'
$env:FATA_BROWSER_EXECUTABLE='C:/Program Files/Google/Chrome/Application/chrome.exe'
.venv/Scripts/python.exe scripts/check.py --integration --browser
```

The shared runner exited zero with these observed results:

| Command/check | Result |
| --- | --- |
| Version checks and `npm --prefix web ls --depth=0` | Passed; supported installed versions |
| `ruff check src scripts tests --no-cache` | Passed |
| `ruff format --check src scripts tests --no-cache` | Passed, 77 files |
| `python scripts/export_contracts.py --check` | Passed; no API/schema drift |
| `npm --prefix web run check` | Passed TypeScript |
| `npm --prefix web run format:check` | Passed Prettier |
| `npm --prefix web run check:generated` | Passed generated OpenAPI/TS/validator checks |
| `npm --prefix web run test` | **69 passed**, no skips/cancellations; 3.829 s reported duration |
| `npm --prefix web run build` | Passed |
| `python -m pytest -q --basetemp=.cache/pytest-f107-unit --junitxml=.cache/f107/unit.xml` | **571 passed**, 74 integration tests deselected, 15.91 s |
| `python scripts/smoke_local.py` | Health/readiness 200; canary 422; correlation and safe console true; own API process stopped |
| `python -m pytest -q -s -m integration --basetemp=.cache/pytest-f107-integration --junitxml=.cache/f107/integration.xml` | **74 passed**, 571 routine tests deselected, 28.48 s; actual PostgreSQL/browser tests |
| `python scripts/evaluate_baseline.py --check` | Frozen development **24/24**, held-out **16/16**, no drift |
| `python scripts/measure_async_reads.py` | F2-01 regression: both modes 5/5 correct, three GETs/trial, zero retries, peak inflight 1/3 |

The runner resolves Python/Ruff to `.venv/Scripts` and npm to installed `npm.cmd`.
Ignored check reports/JUnit remain under the existing `.cache/f107/` path; new
experimental JUnit is `.cache/f203/tests.xml`. **645 root Python + 47 experimental
tests passed in disjoint suites**, without pooling them with evaluation scenarios
or claiming reference-model tests establish native SQL transaction correctness.

The installed browser repeated Save → Generate → Review → Revise → lost approval
response → same-key retry → durable readback → profile change → immutable history
→ owner switch. Assertions found no runtime errors, external page requests or
horizontal overflow; mobile error recovery and same-key retry passed. Screenshots:
[desktop](evidence/f2-03-desktop.png), [mobile](evidence/f2-03-mobile.png),
[mobile error](evidence/f2-03-mobile-error.png). No UI functionality was changed.

Final migration check `python scripts/migrate.py` returned `{'applied': []}`.
Native aggregate checks found zero leftover F1/F2 fixture schemas and public
approval/key/audit counts `(0,0,0)`. Root lock hashes match accepted F2-02 evidence;
`find_spec('langgraph')` is false in the application environment. Frozen paths and
historical evidence remain unchanged. Source/artifact provenance and `git diff
--check` were verified. `AGENTS.md`, environments and checkpoint files stay ignored.

Both earlier diagnostic SQLite leftovers were removed through the scoped
`cleanup --database <name>` command. Demo/comparison/test fixtures remove their
own databases and WAL/SHM files. No `.sqlite` file remains in `.cache/f203/`.
Process inspection found zero task-owned Chrome processes; the smoke stopped its
API child. `docker compose stop postgres` completed, preserving the volume/image.

Environment: Windows 11 build 10.0.26200; 16 logical CPUs, AMD64 Family 25 Model
116 Stepping 1; Python 3.14.9; SQLite 3.53.1; uv 0.13.5; Node 24.22.1; npm 11.19.1;
Ruff 0.17.2; PostgreSQL 18.6; installed Chrome 155.0.8059.85. Full experiment
package versions and code/lock hashes are in the comparison JSON.

## Retention, limits and readiness for F2-04

Each database permits one fixed thread; the CLI rejects a second start and exposes
no old checkpoint IDs, time travel or arbitrary state updates. Payloads are bounded
to 128 KiB, graph execution to 64 steps/invocation, and SQLite's main database to
4,096 pages (16 MiB at its default 4 KiB page size). WAL/SHM and Python memory are
outside that page cap; inspection reports them separately. This is not a global
disk/RSS quota. Repeated fault invocations are operator actions, not background
retries or an unbounded service.

Only synthetic fixture context, messages, proposals, versions, timestamps and
accounting are stored. These are **content-bearing experiment checkpoints**, not
metadata-only telemetry and not authorized real-user storage. Reports retain only
allowlisted stages/reasons, counters, versions, dependency/source metadata, opaque
hashes and process IDs. They contain no raw prompts, profile/plan bodies, credentials
or application user/candidate/approved-plan identities.

Completed test/demo/comparison files are deleted; manually started files require
explicit named cleanup even after their 30-second execution deadline. There is
no cleanup daemon, secure erasure, production retention policy or untrusted
checkpoint-import support. Local files and caller code are trusted; arbitrary
privileged file edits are not a supported authorization boundary. Strict loading
and context checks do not make this a hostile-host sandbox. Network guards are
cooperative process patches, not an OS firewall; no security/operation claim is
made for unused transitive SDKs outside that guarded harness.

Only normal interpreter exit at a safe interrupt is demonstrated across real
processes. Failed-node, cancellation and uncertain-operation cases use controlled
faults and newly initialized runtimes; physical disk failure, power loss, concurrent
multi-process writers, OS reboot and real remote-provider reconciliation remain
unverified. There is no exactly-once external-effect or business-persistence claim.

The existing F1 transaction/lifecycle/ownership/request-budget/tracing guarantees,
F2-01 async behavior and F2-02 uncached decision remain intact with passing
regressions. No known F2-03 blocker remains. A future graph adoption would require
an actual durable-work requirement and a separately reviewed checkpoint ownership,
retention, deadline, replay and source-provenance policy. It is not needed to begin
the independently scoped F2-04 contract work.

Ready for owner review and, **only after separate authorization**, F2-04. No live
provider call, hosted export, cloud provisioning, deployment, external-user data,
commit or push was performed. Stop after F2-03.
