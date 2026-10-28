# F3-01 handoff — real-model experiment design and offline preparation

Date: 2026-10-24. Scope: **F3-01 only**. F1 and F2 are owner-accepted and closed.
F3-01 is documentation-only and ready for owner review. No provider integration,
live experiment, spending or hosted export has been enabled. No F3-02 work was
implemented. There are no migrations, dependency changes or new services.

## Deliverables and changed files

| File | Change |
| --- | --- |
| [17-f3-experiment-and-spend-plan.md](../planning/17-f3-experiment-and-spend-plan.md) | Source-backed provider comparison; source audit; versioned prompt/tool/schema/config and artifact designs; eligible evaluation populations; spend/uncertainty ordering; privacy destinations; measurable remaining F3 gates and role mapping |
| [README.md](../../README.md) | Records owner acceptance/closure of F2, current F3-01 preparation and continued disabled live/export state; links this handoff and plan |
| This handoff | Exact observed offline checks, audit reproduction, limitations and review decisions |

Read the local ignored instructions, F0 charter/architecture/evaluation/cost and
F3 gates, F1 work package and ratified contracts 12–14, F2 outline, final F1/F2
acceptance evidence and relevant F1-01 through F2-04 handoffs. Inspected actual
protocol, orchestration, budgets, read tools, schemas, profile Save, domain/eval,
observability, configuration and terminalization implementations. Historical
ratified/review/handoff records are unchanged. No source from sibling projects
was accessed.

The [plan](../planning/17-f3-experiment-and-spend-plan.md) contains the detailed
provider, pricing, schema, data-flow, experiment and acceptance tables. All future
artifact names and contract extensions in it are **designs**, not executable
scaffolding, installed schemas or passing adapter tests.

## Recommendation and material audit findings

Recommend one initial **OpenAI Responses / `gpt-6.1-sol` / low reasoning / Standard
tier** experiment, subject to owner approval. Current official alternatives,
prices, tool/structured-output/streaming features and privacy references are
linked beside their claims in the plan. Official documentation was read on
2026-10-24; no SDK or provider endpoint was invoked for research. Model access and
real request behavior were not verified.

The typed agent, read dispatcher, independent validator, catalog, baseline,
PostgreSQL authority, SSE/candidate lifecycle and F2 architectural decisions remain
appropriate. F2's cache rejection and isolated LangGraph comparison stand. The
important live-entry gaps are:

1. **Real input admission is unresolved.** Simulated UTF-8 quarters are not real
   tokens. A provider count endpoint would itself consume outbound requests;
   counting initial and continuation inputs separately would violate the existing
   three-call cap. F3-02 must establish a sound complete input bound or keep live
   blocked and return an explicit contract/design decision. No extra counting
   calls or budget exemption are adopted here.
2. **Real billing needs durable authority.** Existing metrics omit cache-write,
   reasoning and effective-tier details. Design reservations before network send,
   exactly-once settlement, restart-safe uncertainty retention, concurrent dollar
   ceilings and manual authoritative reconciliation. No such ledger is claimed
   implemented or tested.
3. **Provider formatting needs a translation boundary.** Current discriminated
   root unions/optional defaults need strict provider-schema projection; native
   reasoning/tool continuation items need bounded request-memory handling.
   Provider validity must never replace the independent domain validator.
4. **Evaluation eligibility and evidence need separation.** Preserve every frozen
   case, but only 28 are reachable through current saved-profile generation.
   Report the remaining 12 at their actual local/baseline boundaries. Arbitrary
   preference-text interpretation and an API decline flag are not implemented.
   The current output also has no model-authored explanation to score.
5. **Actual streaming, errors and usage are untested.** Later fixtures must cover
   refusal, incomplete/EOF, usage uncertainty, call-ID correlation, SDK retry
   suppression, cancellation and terminal-only publication before live entry.

These are identified prerequisites for future live work, not changes to the
accepted offline functionality or a claim that live use is safe today.

## Spend, privacy and experiment decisions

The proposal is **$1 for at most ten smoke generations**, followed only after
separate review by **$5 for at most 58 evaluation/stability generations**, with
**$6 lifetime, $2/day and $2/session** ceilings. All current allowances are $0.
At the reviewed Standard rates, the conditional worst-case cost is **$0.08 per
logical request**, including the highest permitted 30-minute cache-write rate
and all retries/repair/continuations within cumulative 16,000/4,000 token limits.
The 68-request proposal bounds token-rate charges at $5.44 under those conditions;
this is not measured billing or a tax-inclusive provider invoice guarantee.
Unknown charges retain reservations; cancellation is not proof of no charge.

Proposed provider destination is exactly
`https://api.openai.com/v1/responses`, with synthetic bounded content,
`store=false`, no background mode or hosted tools. It is a global endpoint;
neither US-only processing nor ZDR is assumed. Provider abuse retention and
encrypted cache retention still require owner acceptance. Judge spending remains
$0, with its own later named-model/rate/call-count approval required.

The separate future observability proposal is metadata-only OTLP to
`https://us.cloud.langfuse.com/api/public/otel/v1/traces`; seven-day hosted
retention/deletion and numeric cost approval must be verified before enablement.
No exporter/account has been created or contacted. All configured current sinks
remain local, allowlisted and content-free. No prompts, plans, identities, keys,
native reasoning or raw exceptions may be exported. Exact local artifact/ledger
retention, destination inventory, canaries and emergency shutdown are in the plan.

Evaluation preserves the 40-case baseline, labels the legacy held-out set as
developer-exposed regression data, proposes ten distinct smoke cases and retains
F0's 20 matched template/model quality pairs. New held-out content requires
post-prompt-freeze curation and disclosed reviewer independence. Human scoring
uses anchored preference adherence, explanation clarity and useful variety;
an evaluation-only bounded explanation field requires ratification first.
Judge calibration is optional and separately approved, never a write authority.

## Commands and observed results

All commands ran from the workspace root on 2026-10-24. Nothing was installed.
The normal runner first hit Windows sandbox subprocess restrictions; its
approved normal-local-process rerun completed successfully.

```powershell
.\.venv\Scripts\python.exe scripts/check.py
```

First attempt: exit 1 at frontend `npm ... test` because esbuild child creation
returned `spawn EPERM`. Python tests/build/baseline were not reached in that
attempt. Second invocation of the **same command** with normal local process
access: **exit 0**, all below passed. This was a sandbox execution limitation;
no test or application code was modified to bypass it. The runner did not use
`--integration`, `--browser` or `--evidence`.

| Exact runner child command (executables resolved locally) | Observed result |
| --- | --- |
| `.\.venv\Scripts\python.exe --version` | Python 3.14.9 |
| `node --version` | v24.22.1 |
| `npm.cmd --version` | 11.19.1 |
| `.\.venv\Scripts\ruff.exe --version` | Ruff 0.17.2 |
| `npm.cmd --prefix web ls --depth=0` | Existing installed dependency tree resolved; no acquisition |
| `.\.venv\Scripts\ruff.exe check src scripts tests --no-cache` | Passed |
| `.\.venv\Scripts\ruff.exe format --check src scripts tests --no-cache` | 82 files already formatted |
| `.\.venv\Scripts\python.exe scripts/export_contracts.py --check` | Passed, no backend contract drift |
| `npm.cmd --prefix web run check` | TypeScript passed |
| `npm.cmd --prefix web run format:check` | Prettier passed |
| `npm.cmd --prefix web run check:generated` | OpenAPI TypeScript and runtime-validator drift checks passed |
| `npm.cmd --prefix web run test` | **85/85 passed**, zero failed/skipped/cancelled; 6.100 s |
| `npm.cmd --prefix web run build` | Passed; existing local assets built, no dependency download |
| `.\.venv\Scripts\python.exe -m pytest -q --basetemp=.cache/pytest-f107-unit --junitxml=.cache/f107/unit.xml` | **604 passed, 105 deselected**, zero skipped/failed/errors; 18.13 s pytest duration |
| `.\.venv\Scripts\python.exe scripts/evaluate_baseline.py --check` | **24/24 development, 16/16 legacy held-out**, zero failures; frozen result matches |
| `.\.venv\Scripts\python.exe scripts/measure_async_reads.py` | Five trials/mode, three reads/trial, 40ms mock delay/read; 5/5 correct in each, zero retries; peak inflight 1 versus 3; medians 140.435ms sequential / 47.238ms concurrent |

The async runner output is a repeat of controlled local fake-transport work,
not a new provider performance result. No wall-clock pass threshold is used.
Full command/status/timing JSON and routine-test XML are local ignored files
`.cache/f107/check-results.json` and `.cache/f107/unit.xml`. Prior tracked F1/F2
evidence was not rewritten. No new PostgreSQL/browser or isolated graph run was
needed for documentation-only changes; the 105 integration tests were expressly
deselected, not reported as passed. Six existing reference/specification tests
inside the routine population remain distinct from native SQL proof. No hosted
CI, model quality test or real billing test ran.

### Reproduce the read-only corpus eligibility audit

The following is the same classification used by the executed Python stdin audit
(the original command additionally printed every case ID and price arithmetic):

```powershell
@'
import sys
from collections import Counter
sys.path.insert(0, "src")
from pydantic import ValidationError
from future_training.domain.catalog import load_catalog
from future_training.evaluation import load_scenarios
from future_training.schemas import ProfilePreferences
catalog = load_catalog()
_, cases = load_scenarios(catalog)
counts = Counter()
for case in cases:
    if case.task == "validate":
        reason = "validator_only"
    else:
        try:
            profile = ProfilePreferences.model_validate(case.profile)
        except ValidationError:
            reason = "profile_rejected"
        else:
            if catalog.unknown_exclusions(profile):
                reason = "save_rejected"
            elif case.choices_declined:
                reason = "decline_flag_not_in_agent_api"
            else:
                reason = "agent_reachable"
    counts[(case.split, reason)] += 1
print(sorted(counts.items()))
'@ | .\.venv\Scripts\python.exe -
```

Observed counts: development **19 reachable / 1 schema rejection / 2 Save
rejections / 2 validator-only**; held-out **9 reachable / 3 schema rejections /
2 validator-only / 2 baseline-only decline cases**. This is static reachability
classification, not 28 observed live HTTP/model successes. Future actual runner
must verify the mapping at HTTP boundaries.

The executed stdin audit also used `Decimal` to check full-token ordinary
input/output cost **0.072**, 30-minute-write worst case **0.080**, and the proposed
two-call example **0.0315**. These are arithmetic checks, not dollar-budget or
provider-usage implementation tests. Dataset/catalog fingerprints match those in
the plan and the accepted frozen manifest.

Final documentation checks:

```powershell
git diff --check
git status --short
git check-ignore AGENTS.md
```

Observed: whitespace check passed; exactly the three files above changed;
`AGENTS.md` remains ignored and untracked. A read-only Python stdin check loaded
all three documents as UTF-8, checked code-fence balance/trailing whitespace and
resolved **27 local Markdown links**, all passing. It also asserted the exact
changed-file set and $4.64/$5.44 proposal arithmetic. All 16 child commands in the
successful runner had exit 0; their elapsed-time sum was **43.803 s** (not a
provider latency measurement). Root lock hashes remain:

```text
uv.lock
a56c144811ce65504791a4a259715950d89e5195089f3dcb441f52ffef47849a
web/package-lock.json
cc7282b0a959a2724d73267c22a679005e2d0dde040e58b2c32a9d75185d3ccf
```

No source/schema/contract artifact, migration, test, frozen result, lock or prior
evidence file changed. Local ignored build/test outputs are the only generated
files. Git emitted its existing LF-to-CRLF working-copy notice for README; it did
not report a whitespace error.

## Limitations and readiness

F3-01 defines contracts, experiment populations and approval gates; it implements
no SDK adapter, live counter, dollar ledger, prompt loader, scorer extension or
OTLP exporter. Existing fake behavior and frozen evaluation artifacts are intact.
No claim of live API compatibility, maintained SDK resolution on this interpreter,
model-selected real tool behavior, clinical suitability, hosted retention,
provider-enforced spend cutoff, real-model latency/quality or AWS operation is
made. Mutable model aliases and developer-exposed legacy cases limit
reproducibility/generalization even after a future experiment.

Ready for **F3-01 review** and a separately authorized **offline F3-02** if the
owner accepts the plan. Live entry remains blocked until real token admission,
strict continuation/schema mapping, durable spend correctness and explicit
provider/model/privacy/numeric authorization are satisfied. Pending owner
decisions and the remaining work units are in sections 11–12 of the plan.
No real-user data, live provider request, paid call, hosted export, provisioning,
commit or push occurred. Stop after F3-01; no F3-02 authorization is inferred.
