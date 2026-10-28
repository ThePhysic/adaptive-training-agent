# F3-E5 — Owner decision register

2026-10-27. Every decision below is **UNRESOLVED / not approved here**. Facts are
from the public repository; defaults are recommendations. No real model/version,
count tariff, retention entitlement, curator identity or human rating is verified.
Read with the [assessment](f3-e5-study-readiness-assessment.md) and
[sequenced backlog](f3-e5-evaluation-execution-backlog.md).

Legend: **O** owner decision; **V** later verified official/account/support evidence;
**C** independent curator/custody/witness action; **I** separately authorized offline
implementation. Public documentation must not contain actual identity/account/
credential/key/pin/reviewer records. No operation follows from a recommendation.

| ID / decision and why | Existing evidence | Options / tradeoff | Recommended default and justification | Required evidence / authority; blocks |
| --- | --- | --- | --- | --- |
| D1 — provider/model/version | Existing Responses/counting adapter and AuthoritySpec bind OpenAI gpt-6.1-sol/default; no actual generation evidence | Keep implemented path; choose another model/provider only with explicit new compatibility/integration scope | Keep the implemented single-provider path provisionally; obtain exact supported requested ID and effective revision. Do not invent a snapshot ID or call an alias immutable | O+V: dated model/access/endpoint/schema evidence; blocks final config, smoke and freeze |
| D2 — model revision uncertainty | Config has model string, no verified immutable snapshot | Documented stable snapshot if offered; alias with explicit version/time uncertainty | Prefer a verified snapshot compatible with existing adapter; otherwise record requested/effective identifiers/date and limits. Any model change needs new configuration/source review, not automatic fallback | O+V; blocks reproducibility claim and final model binding |
| D3 — generation settings | Low reasoning, strict schema, tool_choice auto, serial tool calls, store/background false, streaming,30m implicit cache; no temperature/seed | Retain exact settings; tuning temperature/reasoning/cache adds compatibility and accounting changes | Keep settings, leave temperature/seed absent. No deterministic claim; do not add unsupported parameters simply for experiments | O+V, I if changed: exact wire compatibility/usage/cache handling; blocks final source/prompt/config freeze |
| D4 — request limits/tool behavior |30s;16k/4k cumulative;2k output/attempt;3 count+3 generation/6 combined;4 reads;1 retry/repair;1/principal,2 global. Model cases require catalog search, template exempt | Preserve; amendment is separate if evidence reveals infeasibility | Preserve all limits. Genuine tool choice must be observed, not pre-dispatched or forced to fake a success. One failed/clarified/refused smoke stops for review | O acknowledges scope; V from separately authorized probe, no new inference limits here; blocks live acceptance |
| D5 — counting tariff and monetary ceiling | CountBound unknown; prepared/simulation ledger is not money; code's conditional Uµ=80,002+3*Cµ | Verified maximum+terms; retain NO-GO if unavailable; separately review another approach instead of assuming free | Keep all live ceilings0. Owner obtains count-specific tariff/maximum/billing treatment and current generation/cache/tier prices before choosing exact project/day/session/grant numbers | O+V: dated provider/account/support evidence, exact task counts, rounding/tax/FX treatment; blocks every live reservation/permit |
| D6 — uncertainty/stop ownership | Sent/unpriced counts retain full hold; discrepancies freeze; unknown commits fence/reconcile. Socket cancellation is not refund | Retain conservative holds; provider/account evidence may later reconcile actual charges | Keep one operator and named stop/reconciliation owner, no unknown=zero, no whole-request retry/top-up. Distinguish local accounting from provider-enforced caps | O+V: operator/window/emergency procedure, provider limits and reconciliation source; blocks real send and post-fault continuation |
| D7 — privacy/retention/destinations | Synthetic-only, no hosted export; store:false is requested, not an account retention guarantee. Counting-specific retention unresolved | Accept verified provider retention for synthetic data; use account controls only if established; otherwise defer | Approve only exact two Responses POST destinations/account routing, synthetic payload scope, retention/deletion and processor terms after evidence. No reasoning, prompts, plans, private IDs in ordinary telemetry | O+V: endpoint/account-specific retention/access/deletion and cache terms; blocks smoke and any real study |
| D8 — primary population/selection | Exact ten public development IDs, ten future ordinals;20 pairs/40 outputs; all cases plan-only and exposed dev controls | Accept proposal with stated limits; redesign before results and before curation | Retain selection-v1 as the small convenience-sample study. Do not optimize it after observing model results. Keep dev/independent denominators separate | O: exact selection hash, variants and limitations accepted privately; blocks final study manifest/freeze |
| D9 — broader acceptance/reuse | Protocol20 proposes69 tasks; accepted new9/10, legacy9/9 and24-case coverage/control goals are separate. New selection does not name the extra IDs | Stage first quality20, then explicit complements/legacy/controls; authorize all proposed tasks with sufficient ceiling; or explicitly limit claims | Stage exact populations, reuse ten dev matrix outputs once if release/config identical, retain9/9 legacy target separately. Decide additional IDs/tranches before budgeting; no69-task blanket run or silent omission | O: bound legacy IDs, coverage/control complements, reuse accounting and claims; blocks full protocol acceptance and total budget |
| D10 — independent curator/conflicts | No independent person attested; Codex-generated/exposed cases cannot be unseen | Independent human not involved in tuning; if unavailable, honest exposed-only comparison | Choose independent human with structured-domain/validation and custody competence, private conflict declaration. Do not appoint by this document or equate knowledge of coverage with case leakage | O+C: identity/independence and freeze acknowledgement before creation; blocks genuine curation and independent claim |
| D11 — custody/recovery | E3A offers separate encrypted device/account or independent encrypted storage with trusted independent plaintext environment; no OS isolation attested | Existing independent device best; removable encrypted storage only with independent workspace; shared developer host insufficient | Use existing independent device if available, one protected recovery copy, named viewers and retention/incident policy. No new hosted service/VM/platform by default | O+C: witnessed dummy access/recovery rehearsal, no developer key/plaintext access; blocks genuine case/key creation and handling |
| D12 — coverage/exposure attestation | Public index has47 normalized identities; HMAC metadata cannot prove hidden novelty/coverage or complete prior private exposure | Independent curator+witness; sole-curator assurance with explicit limitation if owner accepts | Require ten feasible novel synthetic inputs covering eight rows/presets/schedules and feasible ID/tag exclusions. Curator checks full exposure history and near-duplicates, not just hashes. No Codex case selection | O+C: signed/authenticated attestation, private audit, bounds/pins; blocks genuine registration and unseen label |
| D13 — commitment/opening semantics | Committed CaseContent contains origin state/opening_ref; genuine paths denied | Preserve immutable sealed contents with external opened receipt; changing contents requires new commitments and must not fake continuity | Adopt original-bytes verification plus separately authorized receipt/capability design before curation. Never mutate committed origin merely to open. No caller ref/string alone grants authority | O then I: reviewed transition, original HMAC/input/root verification, tamper tests; blocks genuine interface and final freeze |
| D14 — actual evidence/first-result binding | E1 records actual fixed-probe facts; E4 consumes declared fixture facts. Neither is an actual arbitrary-case study executor | One bounded reuse-based collector; no generic runner/service. Spec-only closure would leave real evidence missing | Implement only this demonstrable seam: exact case/run/financial binding, full observed proposals/tools/terminal/SQL uncertainty, pre-send one-shot ownership and immutable first result | O then I, later separate live authority: synthetic faults/restart/double-run evidence; blocks real-case study collection |
| D15 — reviewers/independence | Rubric has3 applicable dimensions; clarity N/A. No reviewers/ratings. Curator independence is a different role from reviewer independence | Two internal reviewers preferred; one owner reviewer gives weaker, disclosed evidence | Resource minimum: R1 all20 pairs, R2 predeclared even-numbered10 shared pairs =180 planned dimension slots; two on all20 =240. These are proposed roles, not people. Disclose developer/curator conflicts; never call owner-only review independent | O plus actual people: private allocation matrix and consent/scope; blocks human collection and agreement claims |
| D16 — blinding/analysis/denominators | Existing practice packet uses old first-ten dev IDs, not new selection. Selection fixes20/40 and missingness rules | Bound new selection-aware packet; preserve old packet as practice | Separate hidden variant/case/reviewer keys from reviewers, balanced A/B, freeze ratings before unblinding. Preserve every planned slot and first outcome; quality only hard-eligible; means/paired differences descriptive, no clinical/generalization claim | O then I only for missing packet/import adaptation: real judgment provenance, per-dimension eligible/rated/missing and paired denominator, raw disagreements retained; blocks quality report |
| D17 — final freeze/change control | E4 candidate valid, unapproved; genuine path/model/source-release changes are still needed | Final approval after exact study release; reference-only acknowledgement now; formal scoped-freeze amendment would be another decision | Defer final study freeze. Finish necessary implementation/review before curator work; approve exact release/selection hashes via separate owner record, not by changing literal candidate/proposal statuses | O: scope, source/lock/study/candidate fingerprint plus review record; C acknowledgement after approval; blocks commissioned curation |
| D18 — post-freeze drift/results | Rebinding would erase integrity/exposure; first results must remain | Abort/invalidate and new independent disposition; preserve old released study. No tuning on failures and replacing them | Any relevant source/model/prompt/rate/selection drift stops before send/opening. Retain old pins/results/holds; separately decide incident/invalidation/new study. Revealed cases remain exposed even if deleted | O+C where custody/exposure affected; blocks any continuation after drift or uncertainty |

## Next owner-facing approval boundary

All boxes remain unchecked. An owner response can accept a design choice without
authorizing execution. Do not publish private names, keys, account data or genuine
attestations as part of that response.

**Ready for owner design decisions from existing evidence:**

- [ ] D3–D4: retain current settings/limits provisionally, absent temperature/seed,
  auto tool choice, no unapproved fallback or expanded retry.
- [ ] D8–D9: choose exact claim/tranche scope, retain20-pair proposal or request
  an explicit pre-result amendment; commission the additional public-ID/reuse manifest.
- [ ] D10–D12: choose the independence/custody assurance required and whether
  suitable independent people/device access are available. This does not appoint
  anyone or authorize real case/key creation.
- [ ] D13–D14: accept the proposed original-commitment/external-opening-receipt
  semantics and authorize only the bounded offline integration described in backlogB2.
- [ ] D15–D16: decide reviewer resources, allocation and descriptive analysis policy;
  no judgments or participant recruitment follow automatically.
- [ ] D17–D18: keep final freeze deferred and preserve source-change/first-result rules.

**Still requiring research/verification, not approval by software:**

- [ ] D1–D2: owner supplies official/account evidence of exact model/revision/access,
  supported settings and effective response identifiers. No invented version/snapshot.
- [ ] D5–D7: owner supplies count tariff/maximum and retention evidence plus current
  model/cache/tier/data-handling terms. A count of18 tokens is insufficient.

**Independent action required later:**

- [ ] Qualified human accepts independence/conflict/custody duties; dummy rehearsal
  precedes genuine material. After final owner-approved freeze only, commission
  curation with exact attestation/coverage/exposure-history and witnessed pin requirements.

**Separate permissions required before any execution:**

- [ ] Exact source-release review, provider/privacy access and positive numerical
  project/day/session/grant authorization, operator/window/stop and endpoints for
  one compatibility probe. No broad study permission or automatic retry.
- [ ] Final freeze ratification, curator acknowledgement, genuine case creation,
  registration, opening, each study tranche and human collection are distinct gates.

Safe next Codex work requires a new explicit offline implementation authorization
for B2 only; no generic transport/ledger/evaluation rebuild is needed. This task
does not request live permission, resolve choices by default, or authorize that work.
