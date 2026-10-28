# F3-04A handoff — offline model evaluation and experiment preparation

Date: **2026-10-25**. Scope: owner-authorized **F3-04A only**, following acceptance
of offline F3-03D. Prepared for review; this report grants no next milestone,
live request, spending, human recruitment, hosted export or deployment.
The live **NO-GO** and **$0** live generation/count/judge allowances remain.

## Result and architecture

Added a bounded evaluation extension under existing experimental infrastructure,
using the accepted catalog, baseline, schema parsers, typed Agent, actual read
dispatcher, Responses replay and independent validator. No second planner,
evaluation service/framework, extracted package, dependency, SDK, database write,
provider connector, financial capability, application route or UI feature was
introduced. Existing count-aware/financial/transaction/SSE guarantees are unchanged.

The new runner executes 50 cases through template, fake and native replay paths:
**150 offline software observations**. The scorer distinguishes safe handling
from hard correctness; deliberately invalid proposals and tool calls remain hard
failures even when safely rejected. Quality numbers are never generated. Future
approved real-output collection can reuse the same strict `Case`/`Observation`
scorer without implementing another scoring system. Accepting `source=live` in
that data type does not execute a provider or verify a claimed origin; the
execution interface rejects live selection.

The owner's manual outside-application count returning `response.input_tokens=18`
is recorded as an **owner-reported external observation**, not independently
captured/tested evidence. No project generation or count was made here. Counting
tariff, retention, full payload equivalence and genuine model behavior remain
unverified; that observation changes no gate or software/quality denominator.

## Exact changed files

| Path | Change |
| --- | --- |
| `src/future_training/experiments/model_eval_assets.py` | Deterministic new-case/fixture builder; normalized feasibility/exclusion preflight; explicit provenance/eligibility/exposure and hashes |
| `src/future_training/experiments/model_evaluation.py` | Actual-Agent offline execution, read-only owned synthetic profile, tool/proposal verdict capture, existing native replay transport, versioned manifests and full per-case results |
| `src/future_training/experiments/model_scoring.py` | Strict common observation contract, schema/outcome/domain/tool/authorization/budget/internal-terminal scoring; hard failures veto quality eligibility |
| `src/future_training/experiments/model_review.py` | Seeded balanced/shuffled blank practice packets, separate hidden key/empty registry, future rating checks and offline agreement arithmetic |
| `scripts/prepare_model_evaluation.py` | Generate/check only the new 50-case assets |
| `scripts/evaluate_models.py` | Offline-only CLI; timestamped ignored run/review artifacts; `--check`; explicit synthetic `--record-offline` maintenance flag |
| `scripts/check.py` | Both new drift/reproducibility checks added to existing local/CI sequence |
| `tests/test_model_evaluation.py` | 88 new software tests, including 50 cases asserting all three variants, negative score gates, exposure/coverage/hash drift, future data-only scoring, unexpected baseline outcomes and sink canaries |
| `data/evaluation/model-v1/scenarios.jsonl` | 50 predeclared typed cases and per-variant expected outcomes |
| `data/evaluation/model-v1/outputs.jsonl` | Authored template-derived structured fixture outputs, including an explicit invalid-plan control; no provider captures |
| `data/evaluation/model-v1/manifest.json` | Fixed 40/10 split, fixture/data/catalog/legacy hashes and exclusions |
| `data/evaluation/model-v1/offline-scores.json` | Reproducible per-case hard/handling results, provenance/config/source/version manifests; no human/quality ratings |
| `data/evaluation/model-v1/README.md` | Asset interpretation, reproduction and privacy instructions |
| `docs/planning/20-f3-model-evaluation-protocol.md` | Audit, exposure/holdout policy, scoring/rubric, future judge calibration, sample/financial planning and separate approvals |
| `docs/implementation/f3-04a-handoff.md` | This evidence/handoff |
| `README.md`, `docs/development.md` | Current offline scope and usage |
| `web/scripts/browser-smoke.mjs` | Add `f3-04a` screenshot namespace only; no frontend application behavior change |
| `docs/implementation/evidence/f3-04a-desktop.png`, `f3-04a-mobile.png`, `f3-04a-mobile-error.png` | New actual-browser regression images; historical evidence untouched |

There are no migrations in this work unit. All eight existing migrations,
provider safety/ledger implementations, domain source/schema, catalog, frozen
v1 corpus/baseline, OpenAPI/TypeScript generated contracts, application frontend,
root/graph dependencies and historical implementation/review records are preserved.
Local ignored caches contain detailed run/pytest/build/browser outputs only.

## Dataset coverage, eligibility and exposure

Original 40 remain exactly **24 development / 16 legacy held-out** with original
IDs/expectations. Their existing eligibility manifest is reused in every new run:
28 saved-profile agent cases, four schema rejects, two unknown-exclusion Save
rejects, four supplied-proposal validator cases and two baseline-only decline
cases. Development/legacy-held-out eligible counts are 19/9. This is static
schema/catalog/API-shape classification, not 28 newly observed live/HTTP trials.

New `model-evaluation-v1`: **40 development / 10 comparison candidates**.

- 24 development matrix cases cover all eight rows × all three duration presets
  and 2/3/4-day schedules.
- Six model-input clarification cases cover zero/two eligible exercises, impossible
  duration and preference/injection/missing-detail free text. The existing agent
  clarifies text; no natural-language preference interpretation was added.
- One synthetic medical-scope model-input case expects provider abstention; the
  template only clarifies text, honestly recorded as a different baseline behavior.
- Nine controlled provider fixtures cover refusal plus eight malformed/tool/
  ownership/constraint/incomplete/duplicate/transport faults. They have no live
  expected-outcome label and are excluded from future model-input denominators.
- Ten additional feasible candidate inputs span all eight rows, schedules/presets,
  known ID exclusions and five feasible tag exclusions. Exact normalized inputs
  differ from all legacy/development profiles. One exercises owned profile read;
  other normal plan cases require catalog read.

Thus **41 model-input tasks + nine controlled response/fault fixtures** are
executed offline. All are developer-exposed. Genuine unseen held-out cases: **0**.
An independently curated/sealed ten-case version after prompt/config freeze is
required for document 17's blind target; exposed candidates are never relabeled
unseen. New exclusions/expectations are frozen before variant scoring, with no
model-result-based selection. First-run/rerun and population reporting policies
are explicit in [protocol 20](../planning/20-f3-model-evaluation-protocol.md).

```text
scenarios.jsonl SHA-256
924da3e63dc3b73d4d29dc3e03dfb07648c5774bc436aa15e94f0666359feef9
outputs.jsonl SHA-256
65bd945978645a9ccb9bce3125a1d0c977066dae6da7ae2e6efc6d8ded98fd49
legacy corpus SHA-256 (unchanged)
c340a3761c3b6e1732f56e36e28bf4a9e985fe11235e67c4aea75855555c7d91
catalog-v1 SHA-256 (unchanged)
9f1e38c5e5e55eec28a663c4bd9dd50b031370895702ebaf9cf6283fda4e216a
```

## Deterministic evaluation outcomes — not model quality

| Evidence type | Cases | Expected safe handling | Hard correctness | Actual outcomes | Quality-eligible plans / ratings collected |
| --- | ---: | ---: | ---: | --- | --- |
| Deterministic template | 50 | 50/50 | 50/50 | 43 plan, seven clarify | 34 / **0** |
| Fake/scripted fake | 50 | 50/50 | **44/50** | 34 plan, six clarify, five abstain, five error | 34 / **0** |
| Authored native replay | 50 | 50/50 | **44/50** | 34 plan, six clarify, five abstain, five error | 34 / **0** |
| Actual project model generation | **0** | Not measured | Not measured | None | **0** |

Six hard failures per fake/replay are intentional and retained separately:
malformed output (`proposal_schema`/`proposal_domain`), unknown write tool
(`authorization`/`tool_arguments`), invalid arguments (`tool_arguments`), owner
argument (`authorization`/`tool_arguments`), unknown exercise (`proposal_domain`)
and duplicate tool call (`proposal_schema`). Their expected safe terminal
dispositions pass the software handling gate; **none can earn a quality score**.
Refusal/incomplete/transport failures also remain non-plan/no-quality outcomes.
Template provider-fault immunity is not ranked as superior model quality.

The shared scorer revalidates terminal JSON/schema, output/profile constraints,
duration/exclusions via the authoritative validator, clarification fields,
abstention next step, actual read-tool argument/capability/result verdicts,
required tools, counts/token limits and internal terminal integrity. Prior invalid
proposals remain hard failures after repair. UTF-8 bounds, ambiguous duplicate
JSON, unexpected candidate fields, incomplete/failed plan state, publication,
over-budget counts and missing required tools fail closed. The evaluator does
not create approval-eligible candidates or fake HTTP/SSE terminal evidence.

Future live outputs use this same observation/scoring contract with independently
collected provenance, counters and actual/uncertain usage. The present runner
uses **uncounted native replay** fixture allowances and invented cache/reasoning
usage. It does not pretend to demonstrate count admission, billing or real
provider behavior; existing count-aware native tests remain separate evidence.

## Review artifacts, rubrics and manifests

Version `synthetic-plan-human-rubric-v1` anchors 1/3/5 (2/4 intermediate) for
preference adherence, perceived usefulness and plan variety. They are subjective
software-plan judgments, not medical/clinical effectiveness. Explanation clarity
is **N/A** because no explanation field exists; the earlier optional proposal was
not implemented or silently ratified. `validate_ratings` rejects any clarity
number, incomplete/noninteger/out-of-range rating or hard-failed/non-plan result.
There are no actual human scores, reviewer identities or judge results.

Each timestamped local run prepares 20 practice pairs (first ten fixed dev IDs +
ten exposed candidates), template versus authored native replay: 40 blank
variant forms. Seed **30401** shuffles pair order and balances A/B orientation ten
each. Reviewer files omit case/split/variant/model labels. Private mapping and
empty reviewer registry are separate; future reviewer tokens must be assigned
outside the packet. Only `reviewer/` should be shared internally after separate
scoring preparation. Reproducible masking is not cryptographic secrecy; identical
template-derived plans are expected and no real-model blindness is claimed.

Future optional judge calibration is a design, not an executor: use actual
human-scored development labels, freeze judge assets, then compare per dimension
on 20 held-out outputs. Agreement helper computes exact/within-one fractions,
MAE, signed bias and disagreement indices, rejecting empty/unmatched input.
Its unit inputs are synthetic test labels, never observed agreement. Protocol 20
defines repeated-rating reliability, order/label/verbosity bias tests, disclosure
of uncertainty and the >=80%-within-one supplementary-use threshold. Separate
judge/privacy/numerical approval is mandatory; hard failures cannot be rescued.

Detailed measured run:
`.cache/f3-04a/20261025T175643651095Z/run.json`, UTC start
`2026-10-25T17:56:43.651095+00:00`, end `17:56:45.770735+00:00`.
Its `reviewer/packet.json`, `reviewer/blank-scores.json`,
`private/blinding-key.json` and `private/reviewer-registry.json` are ignored local
synthetic artifacts, not uploaded evidence or ordinary logs. New runs use new
directories and preserve previous packets/ratings; manual retention is 14 days.

Run manifest includes all case eligibility/exposure, dataset/catalog/assets,
scorer/validator/template/duration/rubric versions, review seed, source revision
plus dirty/source digests, lock/runtime/OS, provider config/rate-assumption version,
usage provenance and zero allowances. Source snapshot digest:
`018bcb6006882b74cdec0d1d4edcf4fc33c9329f4dc394631812a79dcf2e0c3b`.
Working base HEAD was `7e5272499c16180a9811abc2f8e0c4bde308f2e0`; dirty files are
accounted by content hashes, not an implied commit. Per-case outputs distinguish
template/fake/replay, actual outcomes, all failures, simulated/invented usage,
uncertain attempts and finish reasons, elapsed time and no monetary authority.
Stable regression comparison excludes wall time/runtime/OS/dirty/HEAD labels,
while checking code-content hashes. No live output capture/import path is enabled.

One local timing observation per case, heterogeneous 50-case workload, no warm-up
or benchmark claim: template median **1.732 ms** (0.090–6.653), fake **10.346 ms**
(4.732–16.733), replay **23.996 ms** (13.093–34.086). Modes run template/fake/replay
in that order and reuse normal process caches. These are local harness
durations including different protocol work, **not model latency or speedup**.

## Exact validation commands and observed results

Environment: Windows 11 build 26200; Python **3.14.9**, Node **24.22.1**, npm
**11.19.1**, Ruff **0.17.2**, HTTPX **0.28.1**, PostgreSQL **18.6**. Dependencies
and locks unchanged; nothing installed or downloaded. Existing local OpenSSL/TLS
fixtures run as part of routine Python checks. Docker's engine was initially
unavailable; `docker desktop start` and the cached-image startup below succeeded.

```powershell
docker desktop start
docker compose up -d --pull never postgres
.venv/Scripts/python.exe scripts/migrate.py
.venv/Scripts/ruff.exe check src scripts tests --fix --no-cache
.venv/Scripts/ruff.exe format src scripts tests --no-cache
.venv/Scripts/python.exe scripts/prepare_model_evaluation.py
.venv/Scripts/python.exe scripts/evaluate_models.py --record-offline

$env:FATA_BROWSER_EXECUTABLE='C:/Program Files/Google/Chrome/Application/chrome.exe'
$env:FATA_BROWSER_EVIDENCE_STAGE='f3-04a'
.venv/Scripts/python.exe scripts/check.py --integration --browser

# Existing isolated environment, from experiments/langgraph:
.venv/Scripts/python.exe -m pytest -q --basetemp=../../.cache/pytest-f304a-graph --junitxml=../../.cache/f304a-graph.xml
```

The successful final shared run executed **22 child commands, all exit 0**,
summed elapsed **160.571 seconds**. Exact expanded children/results:

| Command (root unless stated) | Observed result |
| --- | --- |
| `.venv/Scripts/python.exe --version`, `node --version`, `npm.cmd --version`, `.venv/Scripts/ruff.exe --version` | Versions above |
| `npm.cmd --prefix web ls --depth=0` | Existing locked dependency tree resolves |
| `.venv/Scripts/ruff.exe check src scripts tests --no-cache` | Passed |
| `.venv/Scripts/ruff.exe format --check src scripts tests --no-cache` | **116 files** already formatted |
| `.venv/Scripts/python.exe scripts/export_contracts.py --check` | Passed; no public contract drift |
| `.venv/Scripts/python.exe scripts/prepare_responses.py --check` | Five existing assets match; live false |
| `.venv/Scripts/python.exe scripts/measure_token_admission.py --check` | Historical F3-03A evidence matches; its old-policy labels are historical, not current policy |
| `.venv/Scripts/python.exe scripts/prepare_model_evaluation.py --check` | 50 cases, fixed assets match |
| `.venv/Scripts/python.exe scripts/evaluate_models.py --check` | All 150 deterministic case/variant records match; expected failures retained |
| `npm.cmd --prefix web run check` | TypeScript passed |
| `npm.cmd --prefix web run format:check` | Prettier passed |
| `npm.cmd --prefix web run check:generated` | OpenAPI/TypeScript/runtime validators match |
| `npm.cmd --prefix web run test` | **85 passed**, zero failures/skips/cancellations; **5.546 s** |
| `npm.cmd --prefix web run build` | Passed |
| `.venv/Scripts/python.exe -m pytest -q --basetemp=.cache/pytest-f107-unit --junitxml=.cache/f107/unit.xml` | **907 passed, 206 deselected**, zero errors/skips; **24.81 s** |
| `.venv/Scripts/python.exe scripts/smoke_local.py` | health200/readiness200/invalid422; safe correlation/console, owned API process stopped |
| `.venv/Scripts/python.exe -m pytest -q -s -m integration --basetemp=.cache/pytest-f107-integration --junitxml=.cache/f107/integration.xml` | **206 passed, 907 deselected**, zero errors/skips; **99.37 s**; actual PostgreSQL/HTTP/installed Chrome |
| `.venv/Scripts/python.exe scripts/evaluate_baseline.py --check` | **24/24 dev + 16/16 legacy held-out**, zero failures; original result unchanged |
| `.venv/Scripts/python.exe scripts/measure_async_reads.py` | Five correct trials/mode, three 40ms mocked reads/trial, zero retries, peaks1/3; seq/concurrent medians **141.384/46.613 ms**, not external-service performance |
| Isolated graph pytest command above | **47 passed**, zero skips/errors; **18.65 s** |

Disjoint root selections total **1,113 Python tests** (907 routine +206 integration),
including **88 new routine cases**. The 150 evaluator observations and 40 baseline
records are separate populations, not added again as pytest tests or pooled with
real-model/human quality. Existing specification/reference obligations remain
reference evidence; actual SQL correctness is the separate native integration
population. No new SQL correctness claim is inferred from the evaluator's
read-only synthetic profile fixture.

Development checks also ran `pytest -q tests/test_model_evaluation.py` using
`.cache/pytest-f304a-eval` and `-r2` basetemp paths: **81 passed** at those earlier
revisions (3.67/3.48 s). Five final drift/import tests raised the final denominator
to 86. Final review corrected a template-outcome mapping that would mislabel
unexpected baseline errors as clarification; two added regression tests preserve
error/abstention without substituting an outcome, giving **88** new tests.
The 150 fixture outcomes did not change. The final shared suite was repeated
after this source correction. Initial non-elevated checks hit
Windows `spawn EPERM` for esbuild, Docker pipe access denial and pytest temporary
directory WinError5; the authorized suite was rerun with local process permissions.
These were environment failures, not passing test runs or provider requests.
Initial lint/import-format issues were fixed before the final successful checks.

The preceding full successful run at 86 new tests observed 905 routine /206
integration /85 frontend passes (25.68/100.64/35.642 s; 192.646 s child-command
sum). It is retained here as development history, not substituted for the final
post-correction 907/206/85 results above. The 47-case graph environment was
unchanged by that evaluator-only correction and passed separately as recorded.

## Persistence, privacy, browser and preservation evidence

Migration command returned `{'applied': []}`. Native tests apply existing migrations
inside isolated schemas and drop fixtures. Read-only post-run inspection found
zero leftover `test_%` schemas and zero rows in each of `spend_projects`,
`spend_grants`, `spend_sessions`, `spend_attempts`, `spend_pairs`,
`spend_operations`, `spend_observations`. No grant/permit was activated. The full
206-case population preserves existing approval/Submit concurrency, rollback,
lost-response/restart, uncertain COMMIT, discrepancy freeze/hold, mixed counting,
shutdown, expiry and owner-isolation assertions. These are controlled real SQL
tests, not provider billing/power-loss/multi-worker proof.

New canaries exercise both fake/replay with credential/PII strings in request
text, injected attributes and runtime errors. All are absent from **both**
configured local sinks (bounded ring and safe console), and raw text is absent
from the resulting sanitized case record. Existing provider/TLS/HTTP/privacy/
DNS/socket/credential-cannot-enable-live regressions all pass. No sink/exporter,
raw prompt/profile/plan telemetry, native reasoning persistence or private
billing identifier is introduced. Tracked plan fixtures are reviewed synthetic
content; detailed review packets remain local restricted experiment artifacts.

Installed Chrome exercised actual SQL-backed Save → Generate → Revise → lost
approval response → explicit same-key retry → durable readback → profile change
→ immutable history → completion retry → owner switch/mobile error recovery.
Observed runtime errors **0**, external page requests **0**, horizontal overflow
**false**; isolated records `(plans,keys,audit,sessions,session_keys)=(1,1,1,2,2)`.

- [Desktop](evidence/f3-04a-desktop.png): original 20-minute approved snapshot
  remains visible beside current saved 30-minute preferences; completion is
  separate and explicit.
- [Mobile](evidence/f3-04a-mobile.png).
- [Mobile error](evidence/f3-04a-mobile-error.png): failed B Save leaves generation
  and approval disabled.

Desktop and mobile-error images were visually inspected. These are unchanged
fake-application regression behavior, not a new evaluation UI or live-model UI.
No historical image was overwritten. Hosted CI was not dispatched; this is its
local equivalent, with two additive evaluation commands.

Read-only Git/UTF-8/link/whitespace preservation checks and final service cleanup
are recorded below. Root lock hashes remain:

```text
uv.lock: a56c144811ce65504791a4a259715950d89e5195089f3dcb441f52ffef47849a
web/package-lock.json: cc7282b0a959a2724d73267c22a679005e2d0dde040e58b2c32a9d75185d3ccf
```

Final local checks:

```powershell
git diff --quiet -- data/evaluation/v1 data/evaluation/results data/catalog data/experiments src/future_training/evaluation.py src/future_training/domain src/future_training/providers src/future_training/agent src/future_training/persistence src/future_training/schemas.py migrations contracts uv.lock web/package-lock.json web/src experiments/langgraph docs/implementation/f3-03d-handoff.md docs/planning/17-f3-experiment-and-spend-plan.md docs/planning/18-proposed-token-admission-amendment.md docs/planning/19-f3-03c-pre-live-readiness.md
git -c core.safecrlf=false diff --check
git diff --quiet --cached
git check-ignore AGENTS.md
git ls-files AGENTS.md
docker compose stop postgres
```

Observed: protected-file/frozen-evidence diff and whitespace checks passed;
nothing staged; AGENTS remains ignored/untracked. Five changed/new Markdown
files passed strict UTF-8, fence balance, trailing-whitespace and **57 local-link**
checks. There are exactly **21 changed/new files**, all listed above. Final
post-regression read-only SQL again found zero rows in all seven spending tables
and zero fixture schemas. `docker compose stop postgres` succeeded, preserving
its volume; Docker Desktop's engine itself was not shut down. A workspace-filtered
`Get-CimInstance Win32_Process` inspection found **0** remaining task-owned Chrome
processes; the smoke launcher reported its API child stopped. No ongoing task
orphan/service was added. No commit or push.

## Limitations and readiness

Ready for **F3-04A review** and later independently curated/scored preparation.
Not ready to execute live evaluation. There is no real model-selected tool,
actual generation/cache usage/latency/quality, human preference/usefulness,
judge calibration, exercise-effectiveness, hosted observability or AWS evidence.
The exposed synthetic/template-derived suite establishes evaluator software
behavior; it cannot predict actual model performance or unseen generalization.
No explanation is available to score. HTTP/SSE/SQL claims come from existing
separate native tests, not the unpublished evaluation result.

The proposed full future population is at most 69 logical first tasks with
preselected development quality outputs reused: 28 legacy +24 matrix +seven
model-input controls +ten independently sealed new cases. Existing caps imply at
most 207 generation +207 counting =414 operations, before a separately approved
smoke/repetition/judge. Conservative generation ceiling is **$5.520138**, plus
**207*C** for a verified count maximum C. This exceeds the historical $5 stage
proposal even before counts. A smaller named population or separately approved
budget revision is required; no spending policy is changed or active permit
proposed while C/retention are unverified.

All provider/account/count-price/privacy/transport/live-authority/emergency
prerequisites in [checklist 19](../planning/19-f3-03c-pre-live-readiness.md) remain.
A separately reviewed real sender/capability, explicit numerical owner limits,
synthetic destinations and successful genuine-tool compatibility smoke must
precede any live evaluation. Prompt/config/scorer freeze, independent case seal,
actual human scoring and separate judge approval remain owner decisions.
No implementation of F3-04 live execution, F3-05 or later work follows. No live
API/count requests, spending, active permits, external users/data, hosted export,
cloud provisioning, deployment, commit or push occurred. Stop for review.
