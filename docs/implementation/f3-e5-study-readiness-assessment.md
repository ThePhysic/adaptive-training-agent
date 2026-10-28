# F3-E5 — Offline study readiness assessment

2026-10-27. Documentation and offline verification only. No freeze approval,
genuine cases/keys/attestations, opening/registration, human judgments, external
requests or monetary authority. Existing studies, candidates, rules and records
are unchanged. Recommendations below are not amendments or authorizations.

## Decision-ready conclusion

**The synthetic engineering baseline passes; genuine study execution and final
freeze remain NO-GO.** E4 resolved the synthetic case/scorer seam and exact public
development selection. The remaining critical path is owner/provider decisions,
one bounded implementation of the actual opening/collection seam, a separately
authorized compatibility request, final source review/freeze, independent curation,
then first-result collection and real human review. Another general infrastructure
or IAM investigation is unnecessary for this path.

Use the [decision register](f3-e5-owner-decision-register.md) to make the human
choices and the [execution backlog](f3-e5-evaluation-execution-backlog.md) to
authorize discrete next steps. Fresh validation is in the [handoff](f3-e5-handoff.md).

## Verified repository facts

| Area | Actual state / authoritative reference |
| --- | --- |
| Cases/scorer | [E4 contract](f3-e4-contract.md), `CaseContent`/`canonical_fixture`/`verify_fixture_population` in [independent_cases.py](../../experiments/independent_cases.py); v1 Case unchanged, shared `_score` in [model_scoring.py](../../src/future_training/experiments/model_scoring.py). Pure scoring labels do not authenticate origin |
| Genuine access | Both `open_independent` and E2 `open_population` deny; `score_facts` denies independent_opened. The verifier accepts only fixed public fixtures and a public nonsecret test key. No genuine collector exists |
| Selection | [study-v1](../../data/evaluation/study-v1/selection.json): ten named development IDs plus ten future independent ordinals,20 matched template/model pairs,40 planned outputs; status proposal_not_owner_approved |
| Freeze | [E4 candidate](evidence/f3-e4-freeze-candidate.json) reproduces and matches all111 inputs; fingerprint `efbbe0dc28781ff952e60c7368e02c31b773858e78383c5b413015b31f434234`; still candidate_not_owner_approved |
| Historical integrity | E2 candidate byte-identical; its current-source check is intentionally obsolete after E4. E4's [additive compatibility record](../../data/evaluation/study-v1/legacy-compatibility.json) permits exactly three source provenance differences, no changed150 results/summaries |
| Model assumptions | [config.json](../../data/experiments/f3-02/v1/config.json) requests gpt-6.1-sol/default, reasoning low, tool_choice auto, streaming on, store/background off, parallel_tool_calls false, implicit30m cache. This is an offline asset, not provider confirmation |
| Request policy | [provider safety](../../contracts/provider-safety.md):30s total,3 generations/3 counts/6 combined,4 read dispatches,16,000 inference-input/4,000 output total,2,000 per-attempt output, one semantic repair/transport retry,1 concurrent/principal and2 globally |
| Financial/live safety | Durable claim/reservation and uncertainty controls exist offline; independent source denials remain closed. Count-specific tariff/maximum/retention remain unverified in repository evidence; all live spending allowances remain USD0 |
| Custody/review | [E2 curator](f3-e2-curator-procedure.md), [E3A owner procedure](f3-e3a-owner-and-curator-procedure.md), [human materials](f3-e2-human-review-materials.md): independent human and private custody required, no genuine population or human judgments established by these artifacts |

No fresh provider documentation/account evidence was fetched. The reported manual
count of18 outside the application is historical owner-attested behavior, not
tariff, retention, generation, model-quality or permission evidence.

## Study consistency findings

| ID | Finding | Assessment and required disposition |
| --- | --- | --- |
| S1 | Exact public selection is predeclared and mechanically justified | No new outcome-based selection was performed. All ten are already exposed; they cannot estimate unseen generalization. Keep their labels and report development/independent results separately |
| S2 | Aggregate coverage is valid, not complete factorial coverage | Ten profiles cover eight rows; goals/equipment/experience each5/5. Durations20/30/45 occur4/3/3; days2/3/4 occur3/3/4. Rows1/8 have two cases, others one. Duration and schedule are associated in this selection. Report these deliberate convenience-sample limitations; no population weighting or causal effects |
| S3 | Constraint/tool breadth gap in the public ten | ID/tag-exclusion counts are0/0; all require search_exercises, none requires get_user_preferences. This does not invalidate the feasible quality subset. Independently verify the future ten's promised exclusions and retain separately declared controls for broader tool/constraint claims; do not retrofit the public set based on results |
| S4 | Forty output slots are not forty independent quality judgments |20 matched case pairs,10 independent cases. All40 slots stay in hard/missingness reports. Quality only for valid hard-passing normal plans; paired preference comparisons additionally need both eligible outputs. Missing/abstained/ineligible are separate, clarity N/A. Reviewer slots must be declared before collection |
| S5 | Primary selection is not the entire protocol20 workload | It contains no exact legacy9 ID list,24-case matrix complement or seven model-input control run manifest. [Protocol20](../planning/20-f3-model-evaluation-protocol.md) proposes69 total tasks with development-output reuse. A first20-pair result must not be called full acceptance; exact additional tranches/reuse need owner decisions |
| S6 | First-result policy exists, actual study enforcement does not | E4's exclusive records reject wrong identity/variant/provenance and replacement, but are optional pure-fixture persistence. They do not establish a real pre-send claim, an immutable study-wide schedule, or absence of prior runs. Future collection must durably bind study/case/variant/logical request before send and retain failures/uncertainty without replay |
| S7 | Committed origin transition needs an explicit design decision | `CaseContent.origin` includes state/opening_ref in full committed bytes. Mutating sealed_unopened into opened state would change the HMAC. Recommend verify and retain original sealed bytes, issue a separate reviewed opened capability/receipt, and keep mutable authorization out of the committed payload. This is a proposal, not a silent contract edit |
| S8 | Frozen code is not yet the genuine study path | Current fixed-input SingleProbe/Rehearsal cannot execute arbitrary independent cases, and E4 FixtureEvidence is declared synthetic data. Do not invent missing raw tool observations or promote it to actual provider evidence. Implement only the demonstrated missing seam, reusing counted execution, recorder, SQL and common scorer |
| S9 | Approving this candidate now would be premature | Genuine path/source-gate/model changes will change frozen files. Final study scope, effective model and provider terms remain unresolved. Complete necessary source review before curation; do not omit gate files or silently rebind cases after source changes |
| S10 | Opaque pins are integrity checks, not independent custody | Hash/HMAC equality cannot verify curator honesty, semantic novelty, secret custody or complete prior exposure history. Independent human attestation/witness and later recomputation remain necessary; source-code/test success is not that evidence |

S7–S9 block genuine final freeze/execution. S3/S5 need explicit claim scope and
execution-tranche decisions; no study artifact was edited. S1/S2/S4/S10 are
limitations/controls to retain rather than reasons to build more infrastructure.

## Provider settings and cost interpretation

Temperature and seed are absent. The counted payload validator rejects unsupported
fields; do not infer temperature0, determinism or acceptance of arbitrary settings.
Max output is set per attempt within the existing ceiling, and native continuation/
count payloads remain bound. Recommended settings are to retain this single-provider
configuration conditionally, pending owner-supplied official/account verification
and one separately authorized compatibility probe. No model/version quality claim
or current price recommendation is made from a dated source constant.

Future provider data destinations remain exactly POST
`https://api.openai.com:443/v1/responses/input_tokens` and POST
`https://api.openai.com:443/v1/responses`. Synthetic profiles/request instructions,
catalog read results and bounded request-local native continuation can reach the
provider under a later approval. Expected answers, curator/key/commitment metadata
and reviewer labels must not enter prompts; account routing/authentication remain
private control-plane data. Verify counting, cache and generation retention terms
separately. Local review outputs need an explicit private retention/access plan;
no content goes to ordinary traces, hosted Langfuse, AWS or public review archives.
Actual model-output content can reveal sealed inputs, so do not upload it to
Codex for debugging before the independent study's first results are frozen.

At the **recorded, unverified-for-live rate card only**, code uses USD/M tokens:
ordinary input2, cached reads0.10,30m writes2.50,12h writes5, output10. The approved
request shape admits30m caching only; unexpected model/tier/cache/usage must freeze
authority and retain liability, not silently reprice or free holds. Reasoning tokens
remain within output. Count success containing a number alone is not free billing.

Let Cµ be an independently verified maximum charge per count, in integer
microdollars. Conditional one-logical-request bound is `Uµ = 80,002 + 3*Cµ`.
This includes conservative per-attempt rounding; cancellation, missing usage or
uncertain COMMIT never authorizes release/retry. It is not a provider-enforced cap.

| Planning population only | Conditional maximum, excluding taxes/FX/surcharges |
| --- | --- |
|20 paired-study model tasks; templates cost no provider requests |1,600,040 +60*Cµ microdollars |
|20 model tasks plus one separate compatibility smoke |1,680,042 +63*Cµ |
|20 model tasks+9 separately executed legacy held-out tasks+one smoke |2,400,060 +90*Cµ; reuse must be predeclared, not counted as new independent samples |
|Protocol20 proposed69 tasks, no smoke |5,520,138 +207*Cµ; this already exceeds its historical USD5 stage proposal before counting |

The69-task proposal is not mandatory blanket execution authorization. Pick exact
tranches and reuse before permission or budgeting; cannot silently drop accepted
targets while claiming full completion. Unknown Cµ and uncertain current model/
cache pricing mean **no numerical positive permit is ready**. Owner must approve
exact project/day/session/grant ceilings, per-task reservations and total workload
only after verification. Credits and historical AWS proposals are not authorization.

## Readiness and next boundary

Ready now: decide study purpose, existing public selection/limitations, required
claim scope, review plan, custody option and the proposed immutable-case/opened-
receipt semantics. None is approved by this file. Provider model/tariff/terms
evidence and actual independent people/custody require external human action.

After those choices, authorize one bounded offline integration task for actual
case opening/recording/first-result binding with synthetic fixtures only, while
runtime money/network stay denied. Its scope and source-release review must settle
before a final candidate is ratified and genuine curation begins. Provider smoke,
genuine curation/registration/opening, study spending/execution and human collection
are distinct later approvals. AWS, hosted tracing, a judge and larger-scale
sampling are not prerequisites for the first genuine quality result.
