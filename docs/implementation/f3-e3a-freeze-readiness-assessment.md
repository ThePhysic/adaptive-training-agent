# F3-E3A — Evaluation freeze readiness

2026-10-27. Offline assessment only. F3-E2 is owner-accepted for its bounded
scope. No candidate is approved/replaced, curator appointed, genuine case created,
registered or opened, or human/model evaluation conducted by this assessment.

## Recommendation

**Technical snapshot: PASS. Final real-study freeze: DEFER.** The existing candidate
matches the current public configuration and is reproducible. Known necessary
interface/selection decisions would change that configuration. Preserve it as the
accepted E2 candidate; do not authorize genuine curation against an imminent replacement.
Independent custody and attestations are also not established by software tests.

Use the [owner/curator procedure](f3-e3a-owner-and-curator-procedure.md) to resolve
decisions. No technical check or this recommendation constitutes owner approval.
The [handoff](f3-e3a-handoff.md) records fresh validation and packaging evidence.

## Verified public configuration

Read-only `freeze()` twice and `check_freeze(saved_candidate)` succeeded without
writing the candidate. All99 selected source-file hashes match; changed/added/
removed frozen-file count0. Dirty accepted working-tree bytes are included.

| Item | Verified value or limit |
| --- | --- |
| Candidate | [E2 JSON](evidence/f3-e2-freeze-candidate.json), evaluation-configuration-freeze-v1, candidate_not_owner_approved |
| Configuration fingerprint | `59c62dba4099cbfcb24e84b213e3dc05d34fca4b3d75d62a3608a4cda025cea4` |
| Candidate raw-file SHA-256 | `ecaeb2db0cb4a309b9b20d3a7c63f203e09351b49848ef9677cb379e49530dfa` |
| Source/exposure | 99 files;47 distinct normalized schema-valid input identities from the90 rows in the two existing public populations; not47 independent observations |
| Scorer/rubric | model-hard-scorer-v1 / synthetic-plan-human-rubric-v1; existing APIs and versions remain compatible with their authored/exposed cases |
| Selection | Ten feasible held_out inputs, plan outcome;20 quality pairs including ten development; first results only; explanation clarity N/A |
| Monetary/live settings | Both false; no technical or financial live authority |
| Sealed metadata | sealed-evaluation-v2; <=32KiB/document; ten ordered entries, required references/pins, private keyed commitments/index; structural validation only |

Source: [E2 module](../../experiments/sealed_evaluation.py), `freeze_inputs`,
`freeze`, `check_freeze`, `SealedManifest`, `validate_manifest`. The fingerprint
binds canonical configuration plus raw file hashes; raw JSON-file hash is a different
quantity. Neither is a signature or approval. The E3A reports are not normative
inputs selected by the existing freeze function and do not silently amend it.
`freeze_inputs()` selects all application Python under src plus specified files/
asset directories; it does not automatically cover every future experiment module
or arbitrary study file elsewhere. Passing `check_freeze` cannot prove completeness
of a later changed execution path. Before final approval, review that path's actual
dependencies and explicitly bind any new bridge/configuration/selection artifact.

## Readiness and unresolved decisions

| Requirement | Current finding | Consequence before final approval |
| --- | --- | --- |
| Reproduce current snapshot | PASS: exact selected inputs and canonical configuration match | Retain current candidate unchanged |
| Preserve historical classifications/scorer | PASS for existing v1 inputs;50 authored =40 development+10 exposed comparison, original40 unchanged | Do not rename them unseen or claim software outcomes as model quality |
| Represent independent cases truthfully | OPEN: `model_scoring.Case` permits only developer-authored/exposed provenance; `score()` revalidates that exact type | Review a versioned independent-case envelope and minimal common-scorer seam before final freeze; no false-label projection or second evaluator |
| Opening/canonicalization contract | OPEN: `open_population()` always denies; exact full-case bytes, schema/IDs/expectations and authorized commitment-verification interface are not finalized | Set canonical encoding, size bounds, expected outcomes/tool requirements and exposure transition; test with non-final synthetic inputs before curation |
| Case-driven execution/evidence | OPEN for the future study: E1 observes a deliberately fixed-input SingleProbe, not an arbitrary sealed-population collector | Specify minimal authorized single-case execution/evidence interface; preserve intermediate failures, uncertainty, budgets and no publication. Do not broaden the probe now |
| Exact study selection | OPEN: candidate binds counts/rules, not ten selected development IDs, variant configuration/run order or a complete execution manifest | Owner preselects public development IDs and comparison rules before results; include the reviewed study artifact in the final freeze's actual input set |
| Freeze scope for future code | OPEN until final path exists: new files outside selected directories/exact paths may not alter the current fingerprint | Review dependency/input-set completeness, not just hash equality; do not assume a newly added experimental adapter is automatically bound |
| Coverage | Consistent as aggregate coverage; cannot mean a full8x3 duration cross-product in ten cases | Approve explicit interpretation below; no case selection or amendment occurs here |
| Model/transport/config | Asset records gpt-6.1-sol/default, reasoning low, tool_choice auto, parallel_tool_calls false, streaming true, store/background false; cache assumptions remain in versioned config | These are frozen offline assumptions, not verified provider availability/behavior; final provider/source configuration must be selected and reviewed |
| Provider prerequisites | Readiness19 still records counting tariff/ceiling/retention and authorized source/financial release as separate live blockers; no new external evidence inspected | Do not activate or price a study. Use exposed/fixed inputs for a separately authorized compatibility probe before settling the final model-study release |
| Custody/independence | UNVERIFIED: no nominated curator, witnessed custody, key recovery plan or independent attestation inspected | Owner must establish and approve them; no filesystem mode proves independence |

References: [common Case/score](../../src/future_training/experiments/model_scoring.py),
[E1](f3-e1-handoff.md), [protocol20](../planning/20-f3-model-evaluation-protocol.md),
[config asset](../../data/experiments/f3-02/v1/config.json),
[readiness19](../planning/19-f3-03c-pre-live-readiness.md) and
[remaining backlog A2–A6](f4-remaining-scope-backlog.md).

### Coverage interpretation for owner review

Ten independent feasible, adult synthetic inputs can cover each of the eight
supported goal/equipment/experience rows at least once, all20/30/45-minute presets
and2/3/4-day schedules somewhere in the population, plus feasible known-ID and
known-tag exclusions. Recommend at least one case with each exclusion type;
categories may overlap. This is an aggregate coverage rule, not24 independent
matrix-duration cells or every possible exclusion. The existing24 development
matrix cases separately provide the full8x3 coverage. No allocation/case is generated.

For the current plan-only quality population, use empty request_text and supported
structured preferences: the current scorer rejects a plan for nonempty text.
Clarification, infeasibility, medical abstention and protocol faults remain separately
reported development/control evaluations, not secretly added to the ten feasible
quality cases. Preserve protocol20's9/10 new and separately9/9 legacy targets,
all returned-plan validation and zero critical authorization/privacy failures.
Ten successes would not establish general reliability or fitness effectiveness.

This interpretation and exact development-ID selection require owner approval
and a future bound study artifact. Requiring all24 matrix-duration cells instead
requires an explicit population/manifest amendment, not stretching ten ordinals.

## Recommended sequence

1. Review this assessment; keep the current candidate unapproved. Decide study
   purpose, truthful case/scorer interface, canonicalization and exact public
   development selection. Resolve custody availability without transferring data.
2. Separately authorize a bounded offline interface milestone if desired: specify
   and test the independent-case/evidence bridge using synthetic non-final material,
   same hard rules, no content opener/live entrypoint. Review any necessary scorer
   boundary refactor and additive future manifest version. Never regenerate accepted
   historical snapshots to conceal changed source fingerprints.
3. In parallel, owner resolves provider terms, actual model configuration and
   separate compatibility/source approvals under readiness19. No provider action is
   authorized here. A real probe uses exposed/fixed synthetic input, not sealed cases.
4. After reviewed compatibility findings and necessary source/config changes,
   identify a stable final evaluation release and all relevant source/lock/study
   fingerprints. Approve its exact freeze through a private owner record. If live
   source release changes frozen src files, it requires a new candidate. Do not omit
   gate files to make the old fingerprint appear valid; retain closed runtime/
   financial controls until the separately authorized execution window.
5. Only then may an independently approved human acknowledge the freeze, verify
   custody and curate cases under a separate owner decision. Registration requires
   another explicit authorization and independently pinned metadata. Opening,
   evaluation and human collection remain further independent gates.

An owner can choose an offline-only study, but it still needs the truthful case
interface and selection decisions. It cannot yield real-model evidence. Approving
this snapshot simply as an engineering reference is different from commissioning
independent cases for the final study. Postponing curation now avoids predictable
recuration and does not block useful offline interface preparation.

## Owner decision matrix — none approved here

| Decision | Recommended default | Alternative / tradeoff | Dependency and evidence needed | If postponed |
| --- | --- | --- | --- | --- |
| Study purpose and freeze timing | Defer final real-study freeze until interfaces/model release stable | Reference-only approval now documents bytes but cannot authorize later changed-source evaluation | Resolve OPEN items above; independently reviewed release/candidate | No genuine curation; offline design continues |
| Independent-case/scorer seam | Truthful versioned envelope reusing unchanged hard-rule logic | Offline exposed study only; cannot claim independent holdout | Synthetic bridge tests, strict provenance and legacy compatibility; explicit source scope | New population cannot be honestly scored |
| Full-case canonicalization | Fixed reviewed schema, UTF8 canonical bytes and bounds before HMAC creation | Ad hoc files risk ambiguous commitment/opening | Curator-readable schema and verifier exercised on synthetic sentinels | No final commitments |
| Selection and coverage | Aggregate ten-case coverage above; predeclare ten public development IDs and variants before outputs | Full24-cell heldout requires amendment; first-ten IDs alone lack full row coverage | Versioned selection manifest actually included in new freeze | No final study denominator/curation brief |
| Provider/model/cache assumptions | Keep current asset as assumption; decide final settings only from reviewed compatibility/terms | Different model requires new config/freeze, not fallback mid-study | Readiness19, requested/effective model/tier/cache/usage evidence and budget approvals | Live NO-GO; no positive permit |
| Curator independence | Human not involved in prompt/scorer tuning; privately disclose conflicts | Owner/developer authoring yields an exposed comparison, not independent curation | Identity/conflict attestation and acknowledgement of exact final freeze | No independent population claim |
| Custody | Existing independently controlled encrypted device/account (optionA) | OptionB removable encrypted storage with independently controlled working environment | Owner-witnessed access/key/recovery/retention checks | No plaintext creation/transfer |
| Witness | Second independent witness checks hidden coverage/overlap/HMAC mapping | Curator alone leaves assurance single-person; explicitly disclose and obtain owner risk decision | Witness identity/conflict statement and bounded checklist, no secret content in public record | Metadata cannot prove hidden checks |
| Key backup and retention | Curator primary plus one encrypted independent backup; owner approves exact retention/access | No backup risks irrecoverable commitments; shared developer backup defeats custody | Private recovery demonstration using non-final dummy bytes; deletion/incident policy | No genuine keys/cases |
| Attestation and pins | Authenticated human channel; owner privately pins exact freeze/root/manifest/index before registration | Unsigned opaque refs alone are not approval | Human acknowledgement, attestation, witnessed digests and custody record | Registration blocked |
| Opening and human review | Separate exact population/operator/run/reviewer/retention approvals; first results retained | No opening leaves engineering evidence only | Authorized verified bridge and release, actual judgment provenance, full denominators | No model or human quality claim |

No cloud IAM inventory, administrator permission, hosted service or installation
is needed to make these offline decisions. No person is appointed by the matrix.

## Adversarial stop conditions

| Risk | Stop and preserve |
| --- | --- |
| Premature approval | Missing final schema/selection/release or any mismatch: keep candidate/reference and decision pending; no curation |
| Conflicted curator / false independence | Unresolved involvement, relationship or attestation: do not claim independently sealed; owner may explicitly choose exposed-study label |
| Developer receives hidden content | No IDE/chat/agent/cloud upload, public source path, shared terminal or archive. On any exposure stop; private incident and finite invalidation through separately authorized handling, never relabel unseen |
| Incomplete exposure history | Missing prior opened/exposed/invalidated input audit, inconsistent key context or doubtful semantic novelty: no unseen approval. Fixed public index alone is insufficient |
| Key loss/compromise | Stop opening/registration; keep commitments/history, verify independently held backup. No fresh-key replacement of an existing commitment. Compromise threatens confidentiality and requires new disposition |
| Source drift after curation | Any relevant file/config/prompt/scorer/selection drift: no automatic rebind. Preserve old population/freeze, review invalidation and independently curate only under a new explicit decision |
| Disappointing first result | Retain failure, repair and unknown costs; no best-of-N replacement, new-ID rerun, denominator pruning or feedback into sealed-case tuning |
| Archive/log disclosure | Default-error tracebacks/local-variable debugging/raw metadata printing or renamed private files could disclose content. Stop before sharing; path filters are not content/OS isolation |
| Partial registration / changed pins | Keep exclusive records/markers and original owner pins. No delete/reset/new-directory bypass; no reopening command supplied here |

Historical NO-GO decisions and accepted synthetic evidence remain intact. This
assessment neither requests live authorization nor closes any provider/custody gate.
