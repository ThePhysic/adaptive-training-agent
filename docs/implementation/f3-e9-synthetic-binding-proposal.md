# F3-E9 — Proposed additive synthetic case-binding contract

2026-10-27. **PROPOSED, not ratified or implemented.** This document supplies the
specific decision required by E9's stop-on-contract-change clause. Nothing here
grants authority. Existing E6 and provider-safety contracts remain unchanged.

## Decision to review

Authorize a **separate, explicitly replay-only** ten-public-case binding/collection
contract. Keep SingleProbe, AuthoritySpec, ProbeSession, E6's fixed receipt/slot and
both independent live/financial denials unchanged. Reuse ResponsesReplay counted
mode and CountedSpendingLedger, not authority_fixture or live account records.

Alternative1: generalize AuthoritySpec/ProbeSession/E6 in place. Reject for this
increment: it changes the accepted compatibility financial/input capability and
risks making replay records appear eligible for live scope. Alternative2: only
loop E4 declared FixtureEvidence. Reject as the completion strategy: already
possible, but does not demonstrate actual counted evidence or pre-send ownership.
No new database service, scheduler, transport, scorer or model CLI is needed.

## Exact proposed scope

- Only the ten exact named, already-exposed development profiles and ordinal map
  in `study-v1/selection.json`, verified by canonical_fixture. No novel input,
  arbitrary case path, independent origin, free text, revision or previous plan.
- Replay variant only; template/fake comparisons continue using existing tools.
  This rehearsal has ten scheduled replay slots, not20 independent pairs or a
  genuine study. Any future template/result import must preserve evidence type.
- Synthetic content key/context and a separately issued synthetic receipt; no
  secret generation, human authorization inference or genuine trust-store import.
- Fixed synthetic study/population identity. Receipt must bind ordinal/case,
  original canonical/input/root commitments, exact source/configuration/selection,
  operation, replay-only financial scope and UTC window. No mutable origin field.
- Existing mock transport and counted replay accepted types only. Prefer exact
  MockTransport first; reuse LocalTLS fixtures for boundary regressions. No network
  connector injection, account routing, credentials or positive live authority.
- Limits unchanged:3 counts/3 generations/6 combined,16k/4k cumulative inference
  tokens,2k output/attempt,30s whole request,4 reads, existing retry/repair/admission.
  No whole-case replay, automatic next-case retry or error-triggered replacement.

## Ownership and result semantics to approve

1. Pin the entire ten-slot schedule and source/configuration once in the supported
   isolated synthetic run. Bind exact per-case financial run identity before any
   count. Configuration, receipt, output directory and caller run IDs are binding
   fields, **not alternative slot identities**.
2. Each stable `(ordinal,replay)` slot has an exclusive durable claim before
   provider release. Use existing bounded SQL transactions and append-only fence
   primitives in disposable test schemas, with additive experimental state only.
   Do not repurpose E6's slot1 or remove/reset any old fence/record.
3. Unacknowledged claim COMMIT prevents release. Partial writes or uncertain
   outcomes prevent replacement after restart. New handles/receipts/directories
   must not bypass the same authoritative schedule/slot. Scope is the supported
   single-process local design; administrator deletion/replacement is not prevented
   by a Python API and must not be claimed otherwise.
4. Replay-only paired reservations/one-shot send claims remain authoritative.
   Use existing synthetic count quote with explicit nonmonetary provenance. Source
   identity cannot convert synthetic holds into real money. No settlement based
   on cancellation, missing usage, zero dashboard activity or expected outputs.
5. Collect actual normalized response/proposal/tool/continuation/terminal facts
   through a reviewed reuse of E1's observer. Factor only necessary common
   recording/row-validation logic; preserve E1's exact fixed-probe checks. No
   defaults for missing observations and no second hard scorer/accounting system.
6. Store the bounded first result/evidence exactly once with its binding and
   verified common score. Readback recomputes consistency and rejects conflicts;
   it cannot send or fabricate a terminal outcome. Retain intermediate failures,
   uncertainty, charged/held subtotals, discrepancies and cleanup status.

Proposed dispositions, kept separate from hard/handling/quality scores:

| Disposition | Required evidence / interpretation |
| --- | --- |
| not_started | Scheduled slot without claim; no execution evidence, not success |
| indeterminate | Claim exists with missing/contradictory terminal/evidence or uncertain persistence; unknown accounting remains unknown |
| interrupted | Actual observed cancellation/interruption retained with available counters/holds; delivery/refund never inferred |
| failed | Actual failed terminal or validated hard-failing result; retain exact reason/verdict and any liabilities |
| completed | Complete, consistent observed terminal; refusal/non-plan or hard failure cannot become quality eligible merely from this label |

Classification rules must avoid overlap: explicit interruption first; otherwise
missing/contradictory evidence is indeterminate; complete evidence uses actual
terminal and hard verdict. A verified hard failure can have complete evidence.
Neither completion nor failure proves zero cost or real-model quality.

A consolidated summary must include all ten scheduled slots; separate observed,
scored, hard-passing, failed, interrupted, indeterminate and not-started counts.
Quality scores remain null. Show known charge and known-held subtotals plus the
number of unknown-liability slots. Total actual cost remains null while any count
is unpriced or liability unknown. Preserve exact per-case explanation pointers,
not prompts/native reasoning/private billing IDs in ordinary logs. Duplicate
identical submissions are recognized without execution; conflicts stop. No later
submission may replace a first failure or missing result.

## Direct implementation task after approval

Relevant files: an experiment-only multi-case binding/collector beside
`opening_collection.py`; narrowly shared recording helpers in `counted_probe.py`
only if required; existing ResponsesReplay/CountedSpendingLedger interfaces;
focused synthetic/native SQL tests. Do not alter the original hard-rule body,
production domain/approval rules, provider gates, old migrations or historical
evaluation artifacts. No general execution CLI or case-discovery framework.

Acceptance must demonstrate distinct public profiles with actual2/2/4 sequences
and at least one3/3/6 repair retaining its earlier failure, native replay SQL
liabilities, consistent per-case shared scores and the ten-slot consolidated
summary. Include concurrent duplicates/conflicts, claim/result lost acknowledgments,
partial writes, restart readback, cancellation/timeouts/shutdown/cleanup, missing
observations, wrong case/configuration/scope and genuine/live access attempts.
No unstarted or uncertain slot may be counted as passed or free. Instrumentation
must not preselect tool success, bypass authorization or synthesize missing facts.

Preserve E6 fixed-control regressions,40/40 baseline,150 comparison dispositions,
hard-rule AST and all denials. Preserve old candidates byte-for-byte; introduce a
new additive unapproved candidate after source stabilization if new experimental
files invalidate current source bindings. No final freeze is approved by testing.

Estimated focused implementation/review preparation:1–2 engineering days, with
native fault validation dependent on the existing local PostgreSQL engine. This
is an estimate, not a promise or spending plan. No provider-support answer or
curator action is needed. **Owner review/ratification of this offline-only binding
and explicit implementation authorization is the sole new decision requested for
that task; it must not include live/genuine/monetary approval.**
