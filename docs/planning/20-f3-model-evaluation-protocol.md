# F3-04A — offline model evaluation protocol

Date: **2026-10-25**. Authorized scope: offline preparation only. F1/F2 and offline
F3-03D are owner-accepted. This protocol implements no live evaluation, judge,
provider sender, monetary authority or export. The live **NO-GO** and all live
allowances of **$0** remain. It supplements [17](17-f3-experiment-and-spend-plan.md)
without changing [domain 12](12-f0-domain-contract.md), [lifecycle 13](13-f0-candidate-approval-contract.md),
[budgets 14](14-f0-remaining-contract-clarifications.md), [offline amendments 18](18-proposed-token-admission-amendment.md)
or [provider safety](../../contracts/provider-safety.md).

## Evidence and current capability audit

An owner-reported manual synthetic counting request outside the application
returned `response.input_tokens=18`. No response capture, request equivalence,
usage receipt, tariff or retention evidence was independently inspected here.
There was no project-level generation. This is an **external manual observation**,
not a runner sample, smoke pass, model-quality result, count-price confirmation,
spend authorization or permission for another request.

| Existing component | Reuse and limit |
| --- | --- |
| Frozen `synthetic-v1` / deterministic `evaluation.evaluate()` | All 40 IDs, expectations, splits, source fingerprint and recorded outputs preserved. Software checks only. |
| Catalog / `plan_week` / independent `validate_plan` | Same 20 records, matrix, duration/exclusion/prescription rules for every variant. No new fitness rules. |
| Typed `Agent` / `FakeModel` | Actual bounded tool dispatch, parsing, repair, validation and request cleanup. Normal fake delegates to the baseline; quality is not independent. |
| `ResponsesReplay` / native fixtures | Actual adapter and completed-item stream checks through exact local MockTransport. Authored/template-derived outputs, never provider capture. |
| Count-aware pathway / PostgreSQL ledger | Existing 3/3/6, reserved liability and discrepancy/reconciliation tests retained. This evaluator uses the existing **uncounted replay** fixture allowance, not a new counting/ledger simulation or live authority. |
| Metadata-only tracing | Existing ring and safe console; canaries test both. Synthetic review content is an explicit local artifact, never a trace attribute. No hosted sink. |
| Internal result / HTTP SSE | Evaluator inspects typed `RunResult`, terminal state and no-publication. It does not fabricate `done`, candidates, approval or durable readback. Separate existing HTTP/browser tests cover those boundaries. |

All 40 legacy cases have already been inspected; historical `held_out` is a split
label, not evidence of developer blindness. Exact reachability, before scoring:

| Boundary | Development | Legacy held-out | Disposition |
| --- | ---: | ---: | --- |
| Saved-profile agent reachable | 19 | 9 | 24 plan / 4 clarification expectations combined |
| Profile schema rejected | 1 | 3 | Reject before provider; do not manufacture a saved profile |
| Unknown exclusions rejected on Save | 2 | 0 | Save boundary only |
| Supplied invalid proposal | 2 | 2 | Validator only, not generation input |
| `choices_declined` absent from `GenerateRequest` | 0 | 2 | Baseline-only abstention |
| Total preserved | 24 | 16 | Original 40/40 remains mandatory |

The existing F3-02 eligibility manifest is reused for every ID in run manifests.
This mapping is a static schema/catalog/API-shape audit, **not 28 new HTTP or live
generation trials**. Unsupported goals, missing structured profile fields and
invalid schedules cannot enter the saved-profile agent. Nonempty text always
causes clarification for a proposed plan. Medical abstention can be produced by
a provider outcome/refusal; the template does not parse clinical intent and
clarifies text. No arbitrary-text personalization is claimed. No explanation
field exists; the earlier optional explanation proposal is not ratified here.

## Dataset, provenance and freeze

New assets: [`data/evaluation/model-v1`](../../data/evaluation/model-v1/README.md),
version `model-evaluation-v1`. Manifest hashes cover exact scenario/output text,
catalog and prior fixture versions. The deterministic asset builder freezes
expectations before running a variant, and `--check` rejects drift. Input
feasibility preflight uses the accepted planner/validator; **no model result is
used to select or reject cases**. Case order/IDs are stable.

| Population | IDs/count | Coverage / interpretation |
| --- | --- | --- |
| Development matrix | `ME-D01-20` through `ME-D08-45`, 24 | Eight goal/equipment/experience rows × 20/30/45; schedules 2/3/4 days; familiar matrix analogues |
| Development controls | 16 `ME-infeasible-*`, `ME-text-*`, `ME-medical-scope`, `ME-refusal`, `ME-fault-*` | Zero/two eligible records, impossible duration, preference/injection/missing-detail text, abstention/refusal, malformed output, unknown tool, invalid args, owner arg, invalid exercise, incomplete, duplicate calls and transport failure |
| Exposed comparison candidates | `ME-C01`–`ME-C10`, 10 | All eight rows, presets/schedules, known ID exclusions and five feasible tag-exclusion cases; exact normalized profiles distinct from legacy/development |
| Genuine unseen held-out cases | **0 now** | None is invented or claimed sealed by this developer-authored work |

There are **41 model-input tasks** (34 feasible plans, six clarifications and one
medical-scope abstention), plus **nine controlled provider fixtures** (refusal
and eight protocol/transport faults). The latter use valid profiles but cannot
be passed to a real model as if a desired malformed response were an input
constraint. They have no `expected.live` label and remain offline adapter tests.
Eligibility is fixed per row before scoring. Controls have per-variant expected
outcomes: the template cannot
experience a provider transport/refusal fault. Fault totals must not be ranked
as model-quality differences. Only the 34 normal feasible plan cases are matched
quality-eligible before human review. `ME-C10` exercises an owned preferences
read; other normal plan fixtures require a catalog read. Tool selection is
scripted here; genuine `auto` selection remains a future live requirement.

Clinical scope strings are minimal invented requests, not medical histories.
Boundary-only tests remain outside this dataset and retain their original
denominators. No random resplitting, backfilling failures, case omission or
best-of-N output selection is permitted.

## Development and independent comparison policy

The ten candidates are **not** renamed held-out. Their outputs are exercised
offline and visible. If only these cases are later used, report an exposed
comparison with no generalization claim. To meet document 17's independent
ten-case holdout target, an owner/independent curator must create and seal a new
version of ten feasible synthetic inputs after prompt/config/scorer freeze,
recording hashes, eligibility, exclusions and expectations before any model run.
That population is not secretly generated or scored here.

Development: use the 24 normal matrix cases plus 16 controls for prompt/debug
iteration. Retain each first result; a repair is part of the same bounded task,
not a new free success. Prompt changes apply to a newly named run with changed
hashes. Any inspected holdout failure becomes exposed and stays in the report;
a diagnostic rerun never replaces the first result. Keep legacy nine eligible
held-out cases, new ten independent cases and exposed candidates separate.

Future minimum quality study remains **20 preselected scenario pairs**, ten
development and ten independently sealed comparison cases (40 outputs). Select
ten development IDs before real generation, never by observed success. Existing
offline packets use the first ten stable `ME-D*` IDs and ten exposed candidates
for format practice; the first ten dev IDs do not alone span the whole matrix.
Run the broader 24-case coverage population separately. Aim for two authorized
internal reviewers on at least ten shared pairs; record owner-only bias otherwise.
No external recruitment or scoring has occurred.

Future hard held-out target remains at least **9/10** expected outcomes in the
new independently sealed set, and **9/9** in the separately reported legacy
reachable held-out subset. Every returned actionable plan must validate and all
critical authorization/privacy/write checks must pass. A tiny numerator does not
establish population reliability. Report exact successes and full denominator,
including refusals, timeouts, invalid output and missing results. No significance
or exercise-effectiveness inference follows.

## Runner and hard scorer

`scripts/evaluate_models.py` executes template, fake and replay against identical
typed saved-profile/request inputs. Normal fake uses the existing `FakeModel`;
explicit negative controls are scripted. Native replay uses the versioned output
fixture plus existing Responses item/usage envelopes and actual adapter. A
read-only synthetic profile fixture enforces Principal A ownership. No candidate
store, Save/Approve/Submit implementation, ledger write or credentials are added.

The one independent `score(Case, Observation, Catalog)` accepts the same bounded
record for a future imported `source=live` result. That label is not proof of
provenance. A separately authorized collector must supply verified captures of
final state, observed tool/argument verdicts, actual usage, counts and failures;
it must reuse this scorer rather than choose expected outputs. **No live
executor/import CLI exists now.**

Deterministic checks include strict JSON and no duplicate keys, final schema,
expected outcome, independent domain validation against original profile,
text clarification, supported clarification fields, abstention next step, final
ready/failed state, no publication, actual required tool names, argument/schema
and ownership-capability verdicts, checked tool results, counts and token bounds.
Completed native items remain subject to the existing parser. Unknown/write or
owner-bearing calls are denied. Raw arguments and native state do not enter
reports. Strict observation parsing rejects extras/coercions and byte bounds
apply to terminal output.

Two results are deliberately separate:

- **Handling passed:** expected safe final outcome with schema/domain/terminal/
  budget correctness. A rejected malicious model call may pass this software check.
- **Hard passed:** every model proposal and tool request also satisfies hard
  rules. Malformed/repaired-invalid/unauthorized proposals remain hard failures
  even when the application safely rejects or repairs them.

`quality_eligible` requires hard pass + normal valid plan. `quality_scores` is
always null in automatic reports. Errors/non-plan outcomes and hard failures
cannot receive a passing quality number. A high human mean cannot override a
hard failure. Per-case failures and full populations are retained; handling
percentages are not mislabeled model reliability or quality ratings.

The evaluator observes existing 3-generation/4-tool/1-retry/1-repair/16k-input/
4k-output limits. It adds no parallel runs, retries or budget reset. The counted
3/3/6 contract stays unchanged and is covered by existing offline SQL/protocol
regressions, not falsely claimed exercised by uncounted replay evaluation.

## Human rubric and blinded packets

`synthetic-plan-human-rubric-v1`, anchored ordinal 1–5. Scores 2/4 mean intermediate
between adjacent anchors, with a short structured disagreement category recorded
in future scoring notes rather than unrestricted health text.

| Dimension | 1 | 3 | 5 |
| --- | --- | --- | --- |
| Preference adherence | Supported stated preferences poorly reflected | Checked preferences met, limited tailored choice | Clear coherent choices reflecting all stated supported preferences |
| Perceived usefulness | Hard to use as a bounded schedule | Usable schedule with understandable structure | Especially easy to follow within stated goals/time/equipment; subjective only |
| Plan variety | Needless repetition despite available alternatives | Reasonable selection diversity within catalog | Purposeful variety consistent with supported constraints and available records |
| Explanation clarity | Misleading/contradictory explanation | Understandable with omissions | Concise accurate account of selection/schedule and limitations |

**Clarity is N/A for every current output**: no model-authored explanation exists.
Absent content is not a score of 1 or 5, and no template prose is invented to
manufacture a comparison. Do not infer hidden reasoning from a plan. The other
dimensions apply only to valid plans and reflect perceived usefulness/variety,
not qualified prescription, safety or clinical effectiveness. Contract 12 permits
repeated exercises across days; low variety is a subjective judgment, not a hard
violation. Supported ID/tag exclusions are hard rules, not a preference tradeoff.

Each ignored timestamped run writes `reviewer/packet.json` and blank score forms,
plus `private/blinding-key.json` and an empty separate reviewer registry. Twenty
pair orders are seeded/shuffled; variant A/B assignment is balanced ten each.
Public packets omit case/split/variant/model identities, usage and failure-source
labels. Reviewers receive only `reviewer/` and the rubric; the operator withholds
`private/`, source reports and expected labels until ratings are frozen. Reviewer
tokens are assigned privately later; no fictitious reviewers or scores exist.
The seed is presentation-only and is not a model seed or cryptographic secrecy.
Equal template-derived outputs may be visually identical; blindness is not proven.

New runs get distinct UTC directories and do not overwrite prior packets/ratings.
Keep synthetic detailed artifacts local for **14 days**, then explicitly remove
the exact run directory after review; no automatic cleanup worker or external
upload. Tracked fixtures/sanitized synthetic regressions remain version history.
Do not use these content-bearing artifacts as ordinary logs/traces.

Future scoring reports per-case/per-dimension values, means/medians, paired
wins/ties/losses, missingness and reviewer agreement, retaining failures outside
quality averages. Report sample sizes and shared-case counts; no pseudo-replication
from repeated model runs or paired labels. Current artifacts contain **zero**
human observations and **zero** judge observations.

## Optional judge calibration — design only

Separate owner/model/privacy/numerical authorization required; no judge transport
or tool authority is implemented. Calibrate on genuinely human-scored development
outputs, then freeze judge prompt/config/rubric before scoring the 20 outputs from
ten sealed held-out pairs. Use same eligible dimensions and N/A policy. Human
ratings remain primary and disagreements are not silently adjudicated by a model.

The offline arithmetic helper supports exact and within-one agreement, MAE,
signed directional bias and explicit >1-point disagreement indices. Unit labels
are fabricated **test inputs**, never evidence of human/judge agreement. Compute
metrics per dimension and separately per reviewer. Examine pair-clustered
uncertainty, rating distributions, ceiling effects and weighted ordinal kappa
where estimable; no agreement claim when labels/matching counts are missing.

Future reliability checks: repeated scoring of a predeclared subset, A/B order
swap, blinded model-label swap and matched factual content with shorter/longer
wording if explanation content is later approved. Look for order, self-preference,
verbosity and refusal bias; report disagreements and negative results. Judge
supplementary-use target is >=80% within one point **in each dimension** with no
hard-failure pass. Failure rejects judge use; tiny-sample success is not validation
for other tasks. No judge score may authorize business writes.

## Manifests, artifacts and reproducibility

Each local run records dataset version/hash and IDs/splits/eligibility/exposure,
catalog version/hash, scorer/validator/duration/template versions, code revision
plus dirty/source-file hashes, dependency lock hash, Python/OS, frozen prompt/
tool/output/config hashes, configured requested model/tier, evidence type and
synthetic fixture provenance. Canonical JSON hashes identify versioned synthetic
assets; no prompt/payload hashes are logged to telemetry.

Per case: expected/actual outcome, all hard verdicts, proposal/argument failures,
validated output, dispatch/generation/count/combined/repair/retry counters, token
provenance, invented replay cache/read/write/reasoning accounting, uncertain
attempts/finish reasons, terminal scope, zero external cost/no authority and
elapsed milliseconds. Full local run adds UTC start/end. Frozen scores exclude
wall times/OS/working-tree status/HEAD label (source hashes remain checked), so
reproducibility does not require identical
scheduling. Local timings are not model/network latency or a performance study.

Missing/uncertain actual usage is never zero-cost evidence. A future live
collector must add requested/effective model/tier verification, all actual/unknown
usage and reservation/settlement state from the authoritative ledger using
restricted local identifiers; ordinary traces/reviewer packets must not acquire
private billing IDs, native reasoning or credentials. No opaque continuation
state is persisted by this runner. Existing financial holds cannot be repurposed.

## Readiness and separately required approvals

Offline readiness: reproducible 50-case assets and 150 case/variant checks,
negative scoring gates, versioned manifests, blank blinded artifacts, legacy
eligibility audit and frozen-40 preservation. There is no actual-model quality,
human usefulness, real cost/latency, judge reliability or fitness-effectiveness
evidence. This milestone stops for review.

Before a real compatibility probe: all [checklist 19](19-f3-03c-pre-live-readiness.md)
provider/access/privacy/count-price/live-authority/transport/emergency requirements
and exact numerical owner approval still apply. A count-only manual observation
does not satisfy them. Conservative proposal remains `$0.080002 + 3*C` per logical
request; **C is unverified**, so no positive permit can be proposed for activation.

Only after a separately authorized successful genuine-tool smoke and review,
authorize a named real evaluation run: frozen assets/datasets/selection/exclusions,
actual generation/count maximum, exact grant/project/day/session ceilings,
operator/time window/stop conditions and approved synthetic data destinations.
Initial population proposals: 28 eligible legacy regressions, 24 development
matrix coverage cases, seven model-input development controls plus nine separate
offline provider fixtures (distinguish injected faults from spontaneous model
errors), and 20 preselected quality pairs using ten dev
plus ten newly sealed cases. Some development IDs overlap the coverage run;
declare reuse rather than bill/score duplicate first results silently. Any
stability repetitions need explicit case IDs/sample count and spending allowance.

For planning only, 28 legacy + 24 matrix + seven model-input controls + ten newly
sealed cases imply at most **69 first logical tasks** if all are run separately;
the ten development quality cases reuse preselected matrix outputs. That is at
most **207 generation + 207 counting = 414 combined operations** under existing
caps, not an execution authorization. Using the accepted conservative bound,
proposed maximum is `$5.520138 + 207*C`, excluding a separate compatibility smoke,
judge, tax/FX or surcharges. This already exceeds document 17's historical $5
evaluation-stage proposal before counting. A smaller explicitly chosen population
or a separately approved revised numerical budget is required later; do not
silently activate or enlarge the old proposal. Unknown C prevents numerical
activation now. No spending-policy amendment is ratified by this arithmetic.

Expected future outputs: immutable first-run manifest, complete per-case actual
usage/cost/latency and hard results, failures/repair traces without private content,
blinded human forms and frozen ratings, comparison report with denominators and
limitations. NO-GO triggers remain mismatched counts, unexpected model/tier/cache
pricing, missing usage, uncertainty, malformed/inconsistent streams, stale
constraints, invalid actionable plans, authorization/privacy fault, exhausted
limits or operator shutdown. No automatic top-up, model fallback or whole-run
retry. Live evaluation, judge, hosted export, real users, AWS and F3-05 remain
separately authorized work.

## Applied AI evidence mapping

| Objective | F3-04A evidence | Still unverified |
| --- | --- | --- |
| Reproducible evaluation | Versioned inputs/fixtures/scorer, source manifests, drift checks, full per-case denominators | Hosted/live-run repeatability and held-out generalization |
| Agent tools and structured outputs | Actual local Agent/adapter/dispatch, independent validator and negative fixture scoring | Genuine model-selected tools and constraint adherence |
| Product judgment | Anchored rubric, N/A clarity, blinded randomized practice packets | Actual human preference/usefulness judgments; no fitness effectiveness |
| Reliability/privacy | Existing SQL/SSE/budget regressions, both-sink canaries, no live executor | Provider account/retention/pricing, operated external traffic |
| Performance/cost discipline | Labeled local run durations, unknown usage/liability preserved, operation-count arithmetic | Actual inference latency, uncertain-charge reconciliation with provider |
| Judge calibration | Offline agreement arithmetic and predeclared bias/reliability procedure | Any judge quality, calibrated agreement or stability observation |
