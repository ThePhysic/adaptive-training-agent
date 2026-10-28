# F3-E6 — Bounded synthetic opening and collection contract

2026-10-27. Offline only. No design direction is treated as ratified study approval.
No genuine case/key/attestation, registration/opening, provider request, money or
human collection is enabled. The existing E2/E4/genuine openers and live/financial
source denials remain unchanged and effective.

## Supported slice and trust

`experiments/opening_collection.py` integrates the existing E4 canonical fixture
contract and E1 actual counted-probe recorder. The only executable slot is public
fixture-01 / ME-D01-20: the exact existing compatibility profile, empty text,
revision1, replay variant. No extension to other inputs, model variants or live
AuthoritySpec is inferred. Full10+10 execution remains a future reviewed decision.
Ten known public controls are integrity-checked, not curated or labelled unseen.

`Preparation` contains ten immutable canonical byte strings, E2-shaped synthetic
manifest/pins and an unapproved freezev3 configuration. Reuse E4 canonicalization,
E2 models/digests and the fixed nonsecret content key. Verify every ordinal,
full-content/input HMAC, root, context, exposed-input index, configuration and
selection. Reject noncanonical committed bytes instead of rewriting them. All
accepted contents still have developer_fixture/synthetic_fixture origin.

Opening produces a separate immutable `OpenedSimulation`, retaining the **original
bytes exactly**. Never change origin state/opening_ref inside those committed bytes.
The receipt binds study, configuration, selection, population root, exact case/
ordinal, content/input commitments, replay variant, financial-scope digest, stable
logical-execution identity and operation simulate_counted_probe_once, plus UTC
window <=30 minutes. No arbitrary command, path or profile argument exists.

`SyntheticAuthority` is an explicit trusted test actor, not a real human identity.
It authenticates a receipt using a **different public nonsecret fixture HMAC key**
and a separately held issued-digest pin. A reference/source string or even a valid
tag on an unissued body is insufficient. The fixed keys are intentionally public;
this proves internal message integrity/binding under the fixture trust anchor,
not cryptographic protection from a malicious same-process developer, independent
custody or human authorization. No real signing/key-storage mechanism is chosen.
There is no active genuine issuer, trust-store import, genuine opener or live key.

Validate receipt/preparation before the first claim, after claim waiting and again
when collecting. Expiry/source/selection/financial mismatch stops; never reissue
automatically. Opening itself confers no execution permission outside this simulation.

## Durable first-result ownership

Use the existing local PostgreSQL connection/transaction infrastructure and an
experimental `experiment_e6_first` table. It is allowed **only** in the existing
disposable integration schemas `f103_test_<32hex>`, never public/application state.
No application migration is added and no approved-plan/business data is changed.
Initialization is explicit, idempotent and cannot clear any row.

The supported workflow has one fixed study/ordinal/variant slot. Its primary key
is constant1, deliberately independent of caller receipt, configuration, project,
run identifier or output directory. Before native execution:

1. Mark the owning collection handle used, authenticate opening and instantiate
   the existing fresh-probe recorder without executing it.
2. Check the disposable SQL namespace and exclusively create/flush/fsync an
   append-only fence under `.cache/f3-e6/attempt-fences`, keyed only by that schema.
   The path is not caller-selectable; partial files also block reuse.
3. Verify fresh simulation financial authority, then INSERT and acknowledge COMMIT
   of binding/receipt digest with disposition claimed_unknown. Binding includes
   exact study/configuration/selection/case/ordinal/variant/logical execution and
   native AuthoritySpec fingerprint. An unacknowledged COMMIT cannot release work.
4. Recheck receipt and whole-request deadline; only then run the single probe.

Both the fixed SQL key and local fence survive new handles, new receipt windows,
IDs and working directories. The fence also blocks a restart after a lost rollback
acknowledgement with no committed SQL row. No reset/delete/retry API is provided.
Database/schema/workspace administrator tampering is outside this test trust model;
copying/deleting authoritative storage is not prevented by Python. A failure before
any fence could be created is known pre-release; this handle remains used. No
durability claim is made for bytes that never reached either storage system.

After collection, an UPDATE may store one bounded result only while the exact
binding/receipt and claimed_unknown disposition match. recorded never returns to
claimed_unknown and cannot be replaced. SQL failure/timeout/ambiguous COMMIT leaves
the claim/fence in force; caller receives an uncertain stop, not a clean failure
or zero-cost result. Readback is bounded/read-only and never resumes execution.
Missing/unknown claim result has unknown accounting, not invented zero usage.

Claim/result tasks reuse existing shield-and-await ownership, with5s outer SQL
bounds and statement/lock timeouts3s/1.5s. Cleanup remains owned and bounded; no
worker/recovery service. If a claimed process dies before result persistence,
readback retains claimed_unknown; native ledger rows retain charges/holds. Lost
terminal evidence cannot be reconstructed from expectations or used to permit replay.
All test schemas are removed by their existing fixture lifecycle; local synthetic
fences are retained for review, not automatically reset. Retention/disposal of those
nonsecret development fixtures is manual and does not alter any historical claim.

## Actual counted execution and scoring

Call the unchanged exact SingleProbe/ResponsesProbe/AuthorityLedger simulation path
with exact MockTransport or existing LocalTLS. No new transport, scheduler,
accounting algorithm or accepted provider type. The receipt binds the exact
AuthoritySpec fingerprint; the existing ledger separately binds its native single
logical run and enforces all3-count/3-generation/6-combined, token/retry/repair and
reservation-before-send controls. No positive live authority is created.

The whole30s deadline starts before first-claim work. An outer watchdog owns that
window; the recorder only **shortens** the existing shared Agent/session deadline
to the same expiry before admission, never extends it. This preserves remaining
count/continuation/repair time and existing admission limits. Shielded bounded SQL/
evidence cleanup may finish after request cancellation; no further send follows.

Reuse E1 Rehearsal's actual native response/proposal observation and checked tool
results from continuation context. Do not reconstruct raw arguments that E1
intentionally omits from packets. Validate the complete E1 packet, SQL accounting
and expected public case binding. Recompute the original common score via
ScoringFacts/synthetic_fixture, not a falsely labelled independent v1 Case.
The original hard-rule body is unchanged. Intermediate proposal/agent rejection
verdicts remain hard failures after a valid final plan. Missing/contradictory
evidence or final source/preparation drift cannot become a complete score.

Keep actual E1 packet and E6 score distinct: packet observations are actual local
fixture execution; transport/model responses are authored synthetic fixtures;
SQL values are actual simulation accounting, not money or provider billing;
human quality remains null. Unknown usage, count holds, discrepancies/freeze,
reconciliation and cancellation stay explicit. Outcome uncertainty and unpriced
financial holds are distinct; successful counts do not prove a free request.

## Provenance, privacy and further approval

Results are labelled actual_local_simulation_not_real_model_or_human_evidence and
simulation_not_money. Detailed synthetic results stay in the disposable SQL schema
or explicitly local ignored artifacts, not telemetry/public case packets. Finite
outer failure codes never print SQL exceptions, raw prompts/arguments, private IDs,
receipts, control-plane digests or native reasoning. No new logger/exporter exists.
Any public evidence is a bounded numeric/verdict projection with source versions,
not full execution payloads or an independent evaluation population.

Freezev3 is additive and unapproved: include current E4 input closure plus E6 code,
test and this contract, and preserve prior candidates byte-for-byte. New code means
the historical E4 current-source check is expected to be stale; do not rewrite it.
Source integrity is a trusted review mechanism, not OS containment/attestation.

Separate future approvals remain: exact source release; final freeze; independent
curator/custody; genuine creation/registration; genuine opening/authentication;
provider terms/privacy; numerical money; actual study execution; human collection.
The10+10 selection is still a proposal. Before broader collection, owner must review
a versioned case-specific financial authority/input binding and genuine receipt
authentication/custody. This fixed control rehearsal chooses neither and cannot
operate them. No new genuine trust anchor or whole-study executor is introduced.
