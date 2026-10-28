# F3-03A handoff — offline token admission and pre-live safety review

Date: 2026-10-24. Scope: **F3-03A only**. F3-02 is owner-accepted for offline use.
Recommendation: review and decide on the proposed amendment. The work establishes
a concrete count-aware design and mock evidence; it does **not** ratify six calls
or make live execution ready. No provider/count endpoint was invoked, spending
occurred, permit was activated, hosted sink was enabled, or F3-03B work began.
No install, cloud provisioning, commit or push was performed.

## Deliverables and decision

- [Proposed amendment 18](../planning/18-proposed-token-admission-amendment.md):
  official source review, full field mapping, proposed 3-generation/3-count/6-total
  policy, failure rules, durable counting-cost design and the **pending F3-03B
  authorization checklist**. It explicitly leaves existing ratified contracts
  and runtime limits unchanged.
- [Reproducible experiment evidence](evidence/f3-03a-token-admission.json): actual
  mock routes under the existing total-three limit, separately labeled pure
  six-call reference calculation, invented positive count liabilities and zero
  live requests.
- This handoff: changed files, observed checks, safety findings and review gates.

**Conditional resolution:** exact counting can replace local estimates only for
an unchanged, supported request and a correct provider counter. Four wire calls
are needed for count → tool-generating model response → recount → final response.
The current three-total-call policy cannot support that path. Recommend the
separate 3/3/6 policy **only after owner ratification**, with original inference,
deadline, retry/repair/tool and concurrency caps retained. Unknown counting price,
retention and unimplemented durable count accounting continue to block live use.

## Files changed and scope

| Files | Change |
| --- | --- |
| `src/future_training/experiments/token_admission.py` | Request-local MockTransport-only protocol, immutable payload/projection binding, strict count replies, accepted total-three enforcement, safe failure and pure proposed-policy model |
| `scripts/measure_token_admission.py` | Reproducible metadata-only experiment; `--write-evidence` writes only its new artifact, `--check` verifies exact output |
| `tests/test_token_admission.py` | **69** offline protocol/binding/fault/boundary/admission/privacy/reference checks |
| `src/future_training/providers/accounting.py` | Normalize omitted TTL breakdown only for an explicit integer zero write total; unknown/nonzero writes remain fail-closed |
| `src/future_training/providers/responses.py`, `tests/responses_doubles.py` | Explicit JSON request content type and mock header assertions; no new transport or permission |
| `tests/test_spending_postgres.py` | One native SQL regression showing known zero writes settle a nonzero actual inference cost |
| `scripts/check.py` | Add check-only token experiment to the shared offline sequence |
| `web/scripts/browser-smoke.mjs` | Allow `f3-03a` evidence names so the regression run does not overwrite accepted screenshots |
| `docs/planning/18-proposed-token-admission-amendment.md`, this handoff, `README.md` | Proposal, current status and review/readiness boundaries |
| `docs/implementation/evidence/f3-03a-token-admission.json`, `f3-03a-desktop.png`, `f3-03a-mobile.png`, `f3-03a-mobile-error.png` | New experiment/browser evidence only |

No dependency/lock, API/schema artifact, migration, core Agent/Budget/admission,
live gate, ratified contract 12–14, accepted provider-safety contract, F3-01 plan,
frozen corpus/catalog/baseline source/result or historical report/evidence changed.
No new application endpoint/provider mode, count-ledger schema, queue, service,
framework, graph or durable generation state was introduced.

## Independent source and compatibility review

Used the openai-docs skill and current official documentation; exact links and
supported field tables are in [amendment section 2](../planning/18-proposed-token-admission-amendment.md#2-independent-documentation-review).
Read local instructions, F3 plan 17, both prior F3 handoffs, contracts 12–14 and
provider safety; inspected actual generation, schema, usage, gates, budgets,
spending, traces and regression implementations before editing.

Verified that the count reference lists input/instructions/model, tool schemas /
selection/parallelism, reasoning and structured text settings. It also accepts
broader conversation/reference/personality inputs that this project deliberately
excludes. Counting does **not** list all generation transport/storage/output/cache
options. Blindly copying the generation body would therefore be incorrect.
Exact reply shape is an object tag and integer count, with no usage/cost/model /
payload-binding receipt. Model-specific acceptance and exact encrypted-state
behavior remain unverified by real requests.

Two concrete compatibility corrections were implemented within offline scope:

1. The prior adapter passed serialized JSON bytes without a JSON content-type
   header. Generation now explicitly sends `application/json`; the count experiment
   negotiates JSON for counting and event-stream for generation. Mock handlers
   assert these headers, fixed endpoint/method and absence of authorization.
2. Official response examples explicitly report zero cache writes without a
   per-TTL detail object. The parser now accepts that mathematically known zero.
   It does not infer missing totals or unknown/nonzero pricing partitions. Six
   negative cases retain fail-closed behavior. Native SQL settles the example to
   **2,620 microdollars**, not zero, using invented fixture usage/rates.

A read-only schema audit found **32 declared output object properties** and
**seven maximum conservative container levels** after reference expansion,
within the current documented 5,000/ten bounds. Existing strict schema / domain
tests pass. This does not demonstrate provider-side schema compilation, account
access, model acceptance, latency, or quality.

Remaining compatibility assumptions are explicit: alias/tokenizer stability,
count-versus-actual-input equality, exact native encrypted-item acceptance,
generation-only option omission from counting, effective defaults, live usage
shape, and legitimate mixed commentary/tool output rejected by the current
narrow adapter. Fail-closed rejection is preferable to silently discarding
provider state. Any extension needs bounded fixtures and review before live use.

## Implemented mock experiment versus specification-only evidence

`CountedMockWire` is a request-local experimental interposer before the existing
`ResponsesReplay`. It accepts only local HTTPX MockTransport, never reads a key,
and is not registered as an application provider. The original typed Agent still
owns admission, deadline, tools, independent validation and cleanup. Each active
request gets its own wire instance; concurrent reuse rejects before another count.

The full generation body is prepared/serialized once. Its count projection
copies the nine supported fields without altering text, schemas, item order or
native state. Normalization (`truncation=disabled`) occurs before freezing both
bodies. After freezing, any changed generation byte sequence, including a new
serialization, invalidates the binding. Tests mutate every counted **and**
generation-only option and verify unchanged native reasoning/function IDs/results.
No payload/hash/opaque state appears in experiment reports or ordinary sinks.

| Case | Actual mock calls | Observed outcome |
| --- | --- | --- |
| Initial valid plan | One count + one generation | Independently valid unpublished plan; 1,000/100 invented generation input/output; positive invented count liability retained |
| Model tool call then continuation | One count + one generation; one genuine local validated read dispatch | Typed `ratified_combined_call_limit` failure; second count is avoided because its generation cannot fit the remaining slot; no candidate |
| Invalid duration requiring repair | One counted generation, repair counter consumed locally | No new count/generation pair can fit; fail rather than changing limits or substituting a template |
| Malformed/unavailable count | One count only | No generation, no hidden retry; positive count liability retained |
| Missing generation usage | Count + generation | Full admitted inference allowances retained as unknown; count is not presumed free |
| Exact 16,000 input count/report | Count + generation | Supported plan passes with explicit replay allowance 16,000 |
| Deliberately wrong report 16,001 after a 16,000 count | Count + generation | Error; actual 16,001 retained without clamping or further dispatch, not falsely described as an enforced retrospective cap |
| Hanging count | One count, cancelled by fake-clock deadline or caller | Transport awaited/cleaned, admission released, no generation; no timing-dependent sleep assertion |
| Concurrent counts | Existing one/principal and two/global Agent admission | Same-principal overlap denied while counting; separate principal/wire requests finish independently |

The six-call sequence is **pure reference evidence**, labeled
`pure_reference_no_transport`, with one `contract_spec` test. It allows
count/model/tool/count/model/repair/count/model under proposed counters, rejects
seventh calls and excess reads/repair/retry, and proves no active policy was
changed. It makes **no HTTP request**, even through a mock, under a six-call mode.
The accepted runtime continues enforcing three combined calls.

The experiment's count money holds are **in-memory invented reference amounts**,
not PostgreSQL count correctness or provider prices. The current ledger remains
generation-specific; no count is disguised as a generation row. The proposal
requires a mixed-kind durable journal and paired reservation ordering only after
ratification and separate implementation authorization.

## Failure, spending and privacy findings

Count errors, redirects, wrong MIME, malformed/duplicate/extra fields, oversized
replies, invalid numeric types/bounds, connection loss, cancellation and mismatches
stop before further generation. Count success does not grant a reusable ticket
for retry, continuation or repair. No count retries are implemented in the
prototype; the existing single-retry maximum remains unchanged, not mandatory.
Every operation remains within the original request deadline/admission lifetime.

The exact counter is a provider contract, not an adversarial token-proof oracle.
If actual usage differs, already consumed tokens/charges cannot be undone. The
future design must retain actual values, freeze affected spending and stop;
there is no claim that mocks prove a hard server-side 16,000 ceiling. All ordinary
software admission checks and the 4,000 output/three generation/four tool/one
repair/one retry bounds remain enforced in their existing code.

**Counting is not proved free.** No official endpoint-specific tariff/maximum
charge or retention guarantee was established. Missing documentation is not zero
cost or inheritance of generation `store=false`. Both endpoint paths need separate
explicit data-destination approval. Before counting, the proposal requires a
verified count-charge maximum plus the worst paired generation dollar hold.
Count reply numbers cannot settle billing; acknowledged valid counts with held
cost require a distinct reviewed ordering from unknown/no-response attempts.

The proposal gives formulas and an explicitly hypothetical `C=$0.01` sensitivity:
up to $0.11/logical request, $1.10/ten-case smoke and $7.48/68 requests. Conditional
grant options are $1.25 smoke / $6.50 later evaluation / $8 lifetime / $2 daily /
$2 session. **None is authorized**, and no price/ceiling proof exists for `C`.
The prototype's $0.001 synthetic hold has no relationship to real pricing.
Default live allowance stays $0; verified pricing, durable count operations and
explicit owner authorization are separate prerequisites.

Synthetic canaries in opaque state, logs and result representations pass against
both configured local sinks. No raw prompt/workout/native reasoning, credentials,
raw exceptions, private billing identifiers or payload hashes enter reports /
ordinary traces. The existing egress tests continue rejecting external sockets,
DNS/fetch and credential-triggered activation. Captured request bodies exist only
inside synthetic assertion fixtures. No hosted sink, durable draft or conversation
was added; all live gates remain disabled and unchanged.

## Commands, observed checks and environment

All commands ran locally on 2026-10-24. Official documentation browsing made no
provider request. Existing dependencies were used without installation.

```powershell
.venv/Scripts/python.exe scripts/measure_token_admission.py --write-evidence
.venv/Scripts/python.exe scripts/measure_token_admission.py --check
.venv/Scripts/python.exe -m pytest -q tests/test_token_admission.py --basetemp=.cache/pytest-f303a-targeted
.venv/Scripts/python.exe -m pytest -q tests/test_token_admission.py tests/test_responses.py --basetemp=.cache/pytest-f303a-headers
.venv/Scripts/python.exe -m pytest -q tests/test_token_admission.py -m contract_spec --basetemp=.cache/pytest-f303a-reference

docker compose up -d --pull never postgres
.venv/Scripts/python.exe scripts/migrate.py
$env:FATA_BROWSER_EXECUTABLE='C:/Program Files/Google/Chrome/Application/chrome.exe'
$env:FATA_BROWSER_EVIDENCE_STAGE='f3-03a'
.venv/Scripts/python.exe scripts/check.py --integration --browser

experiments/langgraph/.venv/Scripts/python.exe -m pytest -c experiments/langgraph/pyproject.toml experiments/langgraph/tests -q --junitxml=.cache/f303a-graph.xml
```

Targeted outcomes: **69/69** new offline tests, **126/126** combined token/provider
checks after the header correction, **1 reference passed / 68 deselected** for
the explicit reference selection. Migration returned `{'applied': []}`; five
existing migrations remain, with no new DDL or default grant. The first full suite
passed before the final header audit; the final full rerun verifies the correction.

The final shared rerun exited **0**, all **20 child commands** passing. Their
summed elapsed time was **97.594 s**, not provider latency. Exact child commands
and final results:

| Command / check | Final observed result |
| --- | --- |
| `.venv/Scripts/python.exe --version`, `node --version`, `npm.cmd --version`, `.venv/Scripts/ruff.exe --version` | Python 3.14.9 / Node 24.22.1 / npm 11.19.1 / Ruff 0.17.2 |
| `npm.cmd --prefix web ls --depth=0` | Existing supported dependency tree resolved; no installation |
| `.venv/Scripts/ruff.exe check src scripts tests --no-cache` | Passed |
| `.venv/Scripts/ruff.exe format --check src scripts tests --no-cache` | 96 files already formatted |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | Passed; public contracts unchanged |
| `.venv/Scripts/python.exe scripts/prepare_responses.py --check` | Existing five assets match; live false |
| `.venv/Scripts/python.exe scripts/measure_token_admission.py --check` | New evidence matches exactly; current limit three, proposal unratified, zero live requests |
| `npm.cmd --prefix web run check` | TypeScript passed |
| `npm.cmd --prefix web run format:check` | Prettier passed |
| `npm.cmd --prefix web run check:generated` | OpenAPI/TypeScript/runtime-validator drift checks passed |
| `npm.cmd --prefix web run test` | **85/85 passed**, zero skipped/cancelled; 4.636 s |
| `npm.cmd --prefix web run build` | Passed; existing app assets built |
| `.venv/Scripts/python.exe -m pytest -q --basetemp=.cache/pytest-f107-unit --junitxml=.cache/f107/unit.xml` | **730 passed, 137 deselected**, zero errors/skips; 17.03 s |
| `.venv/Scripts/python.exe scripts/smoke_local.py` | health200 / ready200 / invalid422; safe correlated console; owned API process stopped |
| `.venv/Scripts/python.exe -m pytest -q -s -m integration --basetemp=.cache/pytest-f107-integration --junitxml=.cache/f107/integration.xml` | **137 passed, 730 deselected**, zero errors/skips; 52.56 s; actual PostgreSQL/HTTP/installed Chrome |
| `.venv/Scripts/python.exe scripts/evaluate_baseline.py --check` | **24/24 development, 16/16 legacy held-out**, zero failures; frozen result unchanged |
| `.venv/Scripts/python.exe scripts/measure_async_reads.py` | Both modes 5/5 correct, no retries; three 40ms mock reads/trial; medians 140.856ms sequential / 46.863ms concurrent; peak inflight 1 / 3 |

There are **867 root Python tests**, in disjoint 730/137 selections, plus the
separate 47 graph and 85 frontend cases. This unit adds 69 routine and one native
case. Seven routine reference/specification cases (six existing plus the new
marked count-policy model) are not native SQL proof. Detailed ignored output is
`.cache/f107/check-results.json`, unit/integration JUnit files and
`.cache/f303a-graph.xml`. Do not pool targeted reruns or individual benchmark
observations into test denominators. Async timings remain synthetic local
regressions, not real counting/model performance. Hosted CI was not dispatched.

The isolated graph suite passed **47/47**, 17.02 s. No graph source/dependency or
main-path adoption changed. Native SQL tests retain their distinction from mock /
specification evidence; the single new PostgreSQL test concerns zero-write
normalization, **not** implementation of the proposed count ledger.

New browser regression evidence: [desktop](evidence/f3-03a-desktop.png),
[mobile](evidence/f3-03a-mobile.png), [mobile error](evidence/f3-03a-mobile-error.png).
These exercise the existing fake-provider workflow, owner isolation and immutable
readback; they are not real-model/counting UI evidence. Prior screenshots/traces
and the frozen 40-case evidence are retained unchanged. No old F1/F2/F3 evidence
flag or `--evidence` runner option was used.

Final local inspection: PostgreSQL **18.6**, **five** applied migrations, zero
leftover fixture schemas and public project/grant/session/attempt counts
**(0,0,0,0)**. No active/funded provider permit or development reset exists.
Dependency lock SHA-256 values remain:

```text
uv.lock
a56c144811ce65504791a4a259715950d89e5195089f3dcb441f52ffef47849a
web/package-lock.json
cc7282b0a959a2724d73267c22a679005e2d0dde040e58b2c32a9d75185d3ccf
```

`git diff --check` passed. Explicit frozen-path checks found no differences in
accepted provider safety, contracts 12–14, plan 17/prior F3 handoffs, migrations,
core Agent/Budget/gates, domain/schema/evaluation sources, old experiment assets,
catalog/corpus/results, locks or generated public contracts. Three changed/new
Markdown files passed UTF-8/fence/whitespace checks and **29 local links** resolved.
`AGENTS.md` stays ignored and untracked. `docker compose stop postgres` completed,
preserving its image/volume; task-owned browser process count was **0** and the
launcher smoke stopped its API child. No service remains running for this unit.

## Readiness and remaining decisions

F3-03A is ready for owner review of the **proposal**, with live gates still closed.
The unresolved decisions are: explicit 3/3/6 ratification and inference-count
semantics; count charge/retention evidence; separately authorized durable mixed-kind
reservation implementation and review; exact provider/model/project access;
fresh price/asset/privacy review; numeric funding and an emergency-stop permit.
The [F3-03B checklist](../planning/18-proposed-token-admission-amendment.md#8-f3-03b-pre-live-authorization-checklist)
lists all gates and conditional numeric options. Its entries remain pending.

No accepted F1/F2/F3-02 behavior or ratified policy was weakened to make the
experiment pass. No F3-03B implementation, provider call, monetary spending, active
permit, hosted telemetry, external-user data, provisioning, commit or push occurred.
Stop after F3-03A for review and ratification.
