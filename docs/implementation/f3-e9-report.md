# F3-E9 — Synthetic workflow assessment and contract stop

2026-10-27. **Stopped before executor changes at the requested review boundary.**
This is not a claim that a generalized counted workflow or E9 engineering
completion has been implemented. No account requests, money, genuine cases/keys,
curator activity, freeze approval, source-denial release, commit or push.

## Concrete blocking finding

The existing fixed-control restriction is an input/authority contract, not just a
loop around ten calls:

| Actual source | Enforced restriction |
| --- | --- |
| `providers/authority.py::AuthoritySpec` and `frozen_assets` | input_version is literally compatibility-profile-v1; the input version participates in reviewed asset/authority fingerprints |
| `providers/probe.py::ProbeSession._payload` / `FixedProfile` / `SingleProbe` | Only the approved profile, revision1, empty text, no previous plan; exact probe type, single logical run |
| `experiments/counted_probe.py::offline`, `Rehearsal`, `accounting` | Exact fixed probe, simulation AuthorityLedger, authority_fixture provenance and probe-authority SQL binding; profile/terminal/score selector fixed to that public control |
| `experiments/opening_collection.py::Receipt`, `binding`, DDL | fixture-01/ordinal1/replay receipt; constant primary-key slot1 and schema-derived exclusive fence; stable binding cannot be changed into a retry identifier |
| [E6 contract](f3-e6-opening-and-collection-contract.md) | Only that slot may execute; full ten-case input/authority binding is explicitly a future reviewed decision |

A local synthetic check supplied the **existing public ME-D02-30** profile to
ProbeSession._payload: rejected `invalid_request` before SQL or transport. The
same check proposed input_version synthetic-study-cases-v1: Pydantic rejected it.
Neither test sent anything or created a claim/authority. These are observed local
rejections, not new provider/account evidence.

The user's E9 instruction requires stopping if generalization needs a meaningful
change to an established authorization contract. Broadening the receipt, financial
input binding and durable slot satisfies that condition. Therefore no generic
runner, monkeypatch, subclass bypass, changed literal or new claim directory was
introduced. Existing stopped/uncertain claims are untouched.

## Existing alternatives assessed

| Capability | Already works | Why it does not by itself finish the requested integration |
| --- | --- | --- |
|50-case template/fake/replay comparison | Actual local typed Agent/common scoring;150 fixed dispositions | Existing replay path is not this study's counted per-case receipt/first-result/evidence collector |
| E4 public canonical population and score_fixture | Ten distinct known exposed controls, integrity checks, declared evidence, common scorer, exclusive result retention | Declared proposal/tool/accounting fixtures are not observed counted executions; retention is not a pre-send study-wide claim |
| General ResponsesReplay(counted=True) and CountedSpendingLedger | Bounded synthetic counted execution, exact mocks/local TLS, replay-only SQL accounting | Can accept multiple synthetic profiles already. It has no E6 case/receipt/first-result binding or compatible generalized E1 observer. It is not legitimate to relabel it as that completed seam |
| E6 native integration | Actual local opening/claim/2- or3-generation execution/SQL accounting/shared score | Exactly one supported profile/slot; cannot repeat its run under another case label |
| E8 practice kit | Git-free public canonicalization/domain/commitment practice | Not a genuine authoring interface, execution collector or custody attestation |

General synthetic replay does **not** require live money or provider clearance.
There is a feasible additive implementation, described in the
[review proposal](f3-e9-synthetic-binding-proposal.md), which preserves the old
probe and uses existing replay-only components. What needs owner review is its
new explicit case/receipt/retention contract, not a new provider policy or service.
Creating another declared-evidence demo now would duplicate E4 instead of closing
the missing actual-execution seam.

## Result handling: current state versus remaining work

E1/E6 retain intermediate verdicts, native counters, terminal evidence, known and
held/unknown simulation liability. E4 has strict per-case scoring and exclusive
fixture-result retention. The common scorer already rejects hard failures and
incomplete evidence; its hard-rule body need not change.

Still missing is a single reviewed multi-case ownership/result envelope linking
those actual observations to each case before execution, with read-only recovery,
duplicate/conflict detection and a consolidated summary that retains scheduled
missing/indeterminate slots. E9 does **not** invent these results or promote E4
declared counters into native SQL evidence. The proposal specifies dispositions
and denominators so the next authorization can directly implement them.

## Shortest remaining engineering path

| Area | Smallest necessary remaining increment | External dependency |
| --- | --- | --- |
| Offline multi-case engineering | Approve the additive synthetic-only binding below, then implement/test actual counted observations and immutable per-case results for the ten existing public controls; no new transport/scorer | Owner contract/source review only; no provider or curator needed |
| Genuine study source readiness | Separately review dormant novel-case validation/canonicalization, genuine receipt/attestation trust and case-specific authority; bind complete future source before final freeze | Owner decisions; no genuine data needed to test code synthetically |
| Human-result handling | Selection-aware blinded packet/import and denominator/first-result checks using synthetic blank/missing forms; actual judgments remain absent | Later reviewer allocation/collection approval; no fabricated ratings |
| Local demo / portfolio release | Rehearse the existing save→generate→revise→approve→readback→completion journey, show fake/replay provenance, failed case/unknown hold and documented recovery; publish a concise reproducible evidence map | Separate bounded local demo/release authorization; no AWS or live model required |
| Real-provider compatibility | Verified account/model/settings, counting maximum/billing/retention, privacy, exact source release, numerical ceilings and one logical probe | Provider/account evidence plus separate owner approvals; still NO-GO |
| Independent population | Human-only authorship by proposed family curator after stable final freeze; conflict/custody/exposure review, genuine creation/commitment/registration/opening | Independent human and separate approvals; no involvement needed now |

Offline engineering-complete must name which genuine interfaces are deliberately
denied versus implemented dormant; passing synthetic tests cannot assert real-model
compatibility, custody, independence, quality or production readiness. The primary
study remains20 pairs;69-task/broader targets stay separate. AWS deployment,
hosted observability, judge calls, extra caching/graph work and additional services
are optional to this immediate path and are not prerequisites for the proposed
synthetic increment.

**Recommendation:** one approval of the concrete synthetic contract, then one
bounded implementation task with the proposal's acceptance suite. No further
exploratory infrastructure/planning milestone is justified. See
[handoff](f3-e9-handoff.md) for fresh validation, preservation and review package.
