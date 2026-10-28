# F3-E4 — Independent-case, study and additive freeze contracts

2026-10-27. Offline synthetic rehearsal only. No final case/key/attestation,
genuine registration/opening, live execution, money or human judgment is created.
The accepted E2 candidate remains historical and unapproved; it is not overwritten.

## Common scorer seam

`model_scoring.Case`, its literals and `score()` remain the v1 developer-authored/
exposed boundary. `score()` revalidates v1 inputs then calls `_score`. The existing
hard-rule function body is moved verbatim into `_score`; `score_facts` revalidates
provenance-free `ScoringFacts` and Observation then calls that same body. No second
scorer, altered budgets, domain rule or authorization check is introduced.

Facts are **not authenticated provenance**. A source/split label accepted by this
internal pure scoring API is not proof of live execution or authorized opening.
`score_facts` currently rejects independent_opened outright as an additional source
barrier; the label cannot activate it. A future genuine capability/source change
requires separate review.
The experiment bridge always reports synthetic_fixture and
synthetic_not_model_or_human_evidence. It never projects independent cases into a
falsely labelled v1 Case. Existing public cases retain development/comparison_candidate
and developer_exposed_not_blind. The future genuine path is absent.

## Independent-case-v1 canonical contents

Defined in `experiments/independent_cases.py::CaseContent`. Strict, no extra fields,
UTF8 only/no BOM/UTF16, duplicate-key-safe finite JSON, <=8192 bytes. Request text
must be empty and expected outcome plan for this ten-case quality population.
Domain schemas remain the ratified ProfilePreferences/catalog/validator/planner.

| Field | Meaning |
| --- | --- |
| version | independent-case-v1 |
| case_id / ordinal | Synthetic fixture-NN or future sealed opaque ID; ordinal1–10 |
| profile / request_text | Existing typed synthetic preferences, defaults materialized, empty text |
| expected_outcome | plan; failure/control evaluations remain separate existing populations |
| required_tools | One or two distinct existing read-tool names; no writes/owners/URLs |
| coverage | Distinct matrix/duration/schedule plus actual ID/tag-exclusion categories; no invented coverage flag |
| checks | all_common_hard_checks_v1, no selectable subset or disabled hard checks |
| catalog_sha256 | Exact catalog content fingerprint |
| freeze_sha256 / selection_sha256 | Exact additive configuration and complete study-selection bindings |
| origin | Kind/state, public fixture reference or future attestation/opening references; references alone authenticate nothing |

Origin states distinguish developer_fixture/synthetic_fixture, independent_curator/
sealed_unopened, and independent_curator/opened_separate_authorization. Independent
states require attestation, and opened state additionally requires opening reference.
These are **contract shapes only**; no reference string grants authority. Every
current callable verifier rejects both independent states. `open_independent` and
the existing `sealed_evaluation.open_population` unconditionally deny. No genuine
case loader/path argument, registry writer or provider runner is added.

`canonical_fixture` accepts only the ten already exposed public development inputs
named in the study artifact, with their exact profiles/tool requirements and fixture
ordinal-to-ID mapping. No new independently curated input can enter under a renamed
synthetic label. It independently checks catalog hash and baseline feasibility.
Sort exclusions, tool names and coverage; materialize all profile defaults; use
existing canonical JSON (sorted keys, compact separators, ASCII JSON escapes,
finite numbers, no trailing newline). Key order/whitespace and permitted collection
order differences therefore produce the same committed bytes. Types and duplicate
fields are never repaired/coerced. Constraints/checks/identity/bindings are included,
not just the profile. No unrestricted health notes or explanation field exists.

## Synthetic integrity rehearsal

`verify_fixture_population` takes ten in-memory byte strings plus E2-shaped opaque
manifest/index/pins and the v2 configuration. It has no case pathname or callback.
It reuses E2's strict models, canonical digest and purpose/freeze-bound HMAC primitive.
The only key used is public `bytes(range(32))`, explicitly nonsecret; no genuine key
argument or key-generation function exists. Test metadata is synthetic_test with
synthetic references and no curator/owner approval.

Verification requires exact current freeze/study, manifest and independently supplied
synthetic pins, ordered ordinals1–10, root/commitment/context equality, canonical full
case HMAC, normalized input HMAC and ten distinct input identities. Exposure index
is recomputed from the known public input identities using the same nonsecret key.
Unlike a genuine unseen population, **known exposure overlap is required here**:
these are public controls, never an independently sealed population.
The six E2 metadata coverage labels are a synthetic envelope-shape test, not a
claim that these development controls satisfy final ID/tag-exclusion coverage.
E2's genuine metadata overlap rejection is unchanged. Wrong keys/contexts/ordinals, partial cases,
substitution, altered content or exposed content relabelled independent are rejected.

The receipt is synthetic_integrity_verified_not_independent, not an opening permit.
Every scoring call repeats verification rather than trusting a caller's verified
boolean or source string. No genuine case or attestation is generated by tests.
This tests integrity logic, not human independence, custody or real provider behavior.

## Evidence and first results

`FixtureEvidence` requires explicit Observation fields; default-true proposal and
no-publication flags cannot fill missing evidence. Complete observations, response
coverage and proposal response ordinals are required, with at most three responses
and four tool attempts. Tool arguments/capabilities are independently checked by
the existing `check_call`; claimed verdicts must agree. Result validity remains a
recorded synthetic verdict, not an assertion of actual dispatcher execution.

Every intermediate proposal's schema/domain verdict is ANDed with the recorded
aggregate before the common scorer. Earlier invalid proposals remain hard failures
after a valid final plan. Missing response/proposal/tool coverage, terminal evidence,
uncertainty or accounting yields incomplete/no score or a finite rejection, never
an implicit pass. Template has no provider operations; its one proposal uses
ordinal0. Fake/replay proposal ordinals match their declared response positions.

Accounting is bounded explicit synthetic charged/held numbers or null. Unknown
usage/liability remains unknown; actual_total_micro stays null, not zero-cost
evidence. No SQL/billing verification is invented. Existing E1 native accounting
fixtures retain authoritative simulation evidence and are regression-tested separately.
No failed/unpriced counted request is inferred free. Pure fixture verdicts are
not real execution attestation, even when completely internally consistent.

Results retain proposal verdicts, counters and uncertainty. Hard failures remain
separate from handling and null quality scores. `retain_first` uses bounded
case/variant/provenance-bound synthetic records; mismatched identity or an attempted
live relabel is rejected before creating a file. It uses
configuration/selection fingerprints in retained headers, strict header fields
and argument types, and
exclusive fsynced local writes under ignored `.cache/f3-e4`; an existing/partial
file blocks replacement, including after write failure. There is no retry, executor
or automatic new run. Caller filesystem edits/new-directory workarounds are not
prevented by a Python API; owner-retained study/first-result records remain necessary.

## Exact study selection-v1

`data/evaluation/study-v1/selection.json` is a proposal, not owner approval. Ten
existing public IDs are fixed before any model evaluation: ME-D01-20, ME-D02-30,
ME-D03-45, ME-D04-20, ME-D05-30, ME-D06-45, ME-D07-20, ME-D08-30, ME-D01-45,
ME-D08-20. Selection uses eight rows with rotating preset, then two end-row
extensions, **not observed output/model performance**. All eight rows, three presets
and2/3/4-day counts are covered. Historical first-ten review packet practice is
unchanged; this new study is a distinct additive proposal.

Twenty matched pairs =ten public development+ten future independent ordinals.
Compare template/model for the same case/constraints; rehearse template/fake/replay
separately with accurate synthetic labels. Development list precedes independent
ordinal order; odd pair template first/even pair model first. Human presentation
remains separately blinded/counterbalanced using existing conventions, not execution
labels. No actual pair, reviewer or judgment is created here.

Hard denominator40 outputs retains missing/errors/refusals/cancellations; independent
9/10 and legacy reachable9/9 targets remain separate. Human-quality denominator is
every predeclared reviewer/case/variant/dimension slot, with three applicable rubric
dimensions and explanation clarity N/A. Missing/abstained/ineligible remain distinct;
no imputation, quality rating from a status label or denominator pruning. Quality
eligibility still requires hard pass and valid normal plan. Aim for two internal
reviewers on at least ten shared pairs; none are appointed. First result per
case/variant remains even if unfavorable; no best-of-N substitution.

## Additive configuration-freeze-v2

New `freeze()` never replaces/approves E2's candidate. It binds the original raw
candidate hash, all current E2 inputs, all public experimental Python recursively,
the E4 test/specification and every study-v1 artifact, including compatibility
metadata. Source/selection changes invalidate it. Scorer interface version is
common-scoring-facts-v1; hard scorer/rubric remain v1. Relevant new experiment
modules now enter the boundary automatically; manual review of future external
dependencies is still required. No arbitrary metadata field can open content.

The old candidate's current-source check is expected to reject after the authorized
scorer-interface change; its bytes and historical status remain intact. Both
candidates remain candidate_not_owner_approved. Final curation still waits for
owner approval, human custody/attestation, stable provider/config/source decisions
and separately authorized genuine opening. Do not omit source gates to preserve an
obsolete fingerprint. No positive spending/live gate is introduced.

## Historical score compatibility

No historical dataset, manifest or result snapshot changes. The additive
legacy-compatibility.json binds the exact old score-file hash/manifest hash and
the current source manifest. `compatible_score_reference()` permits changes only
to source_files/source_sha256 for exactly the three reviewed scorer/asset/CLI
files. Everything else and every150 case result/summary must match the old reference.
`evaluate_models --check` checks that exact new provenance and old behavior, rather
than hiding arbitrary drift. Changed/extra sources, asset/config/model/price fields
or old reference tampering fail. The old raw snapshot still describes old source;
new current runs do not pretend to have those original hashes.

## Privacy and later genuine opening

No logger/exporter/network dependency added. Fixed finite errors and opaque model
repr; raw synthetic details may exist only in explicit local artifacts, never
ordinary telemetry. Actual future cases/keys/reviewers stay outside developer/Git
workspaces; archive path filters are defense in depth, not OS isolation.

A future genuine opening requires independent human approval/custody and source
review, exact authenticated attestation/pins/config, exposure-history/coverage and
canonical commitment recomputation, immutable first-result selection and a truthful
opened-case capability. No caller-provided state/ref alone suffices. Real-model
execution additionally needs provider terms, exact monetary/source/privacy/outbound
approvals. None is provided by this contract or the synthetic rehearsal.
