# F0 blocker closure sheet — owner ratification and focused verification

**Status:** amended F0 proposal, **not approval to implement F1**. Historical reviews 07 and 11 remain unchanged; this sheet records proposed fixes and the next owner's decision.

| Review 11 issue | Resolution artifact | F1 proof |
|---|---|---|
| C1 HIGH | `12-f0-domain-contract.md`: eight-row matrix; typed bounds; exact seconds formula, limits, boundary and infeasible fixtures | F1-01 derives schemas from 12; F1-02 runs duration and catalog feasibility fixtures for each supported row |
| C2 HIGH | `13-f0-candidate-approval-contract.md`: per-lineage guard, expiry acceptance instant, revision publication vs approval, profile row lock and commit order | F1-03/F1-06 barrier-controlled revise/approve/expiry/profile races |
| C3 MEDIUM | `14-f0-remaining-contract-clarifications.md`: four typed terminal outcomes and incomplete EOF rules | F1-01/F1-05 contract and UI tests |
| C4 MEDIUM | `14`: model attempts include continuations; per-request vs per-lineage limits; no replay vs bounded internal retry | F1-01/F1-04 offline fake budgets and negative tests |
| C5 MEDIUM | `13`: committed owner-scoped idempotency lookup **before** transient candidate lookup; stable new-key conflict code | F1-06 lost response/restart and duplicate/mismatch tests |
| C6 LOW | Local-only `AGENTS.md` must be deliberately updated by the owner after F0 sign-off; do **not** commit it | `git check-ignore -v AGENTS.md`; current planning-only instructions remain until new authorization |

### Owner decision checklist

Sign off on the following before F1: (1) contract 12's scope, catalog coverage, workout bounds and arithmetic; (2) contract 13's single-process lifecycle, lock/transaction order, expiry policy, limits, approved-plan/idempotency retention; (3) contract 14's streaming outcome and request budgets; (4) already proposed explicit Save/Generate/Approve/Submit consent semantics, loopback synthetic identity, 14-day local metadata retention, no raw chat persistence, 30-minute candidate TTL; (5) F1 unit scope, whether to authorize **F1-01 only** or the full bounded **F1 offline slice**. These remain decisions for the repo owner; this ZIP cannot authorize spending, cloud, or external users.

### Targeted Codex verifier prompt (copy into Codex after applying amendment)

Read local `AGENTS.md`, revised `docs/planning/00–04`, `09`, historical `11`, and new `12–15`. Conduct a **strictly read-only** verification of blockers C1/C2 and clarifications C3/C4/C5. For each issue, report PASS or FAIL and quote the exact remaining contradiction, if any. In particular: independently recompute all duration example totals and boundaries; check that all eight domain-matrix rows are stated and feasibility is a conditional/catalog-tested claim; simulate revise-vs-approve and expiry-at-boundary orderings; verify owner-scoped idempotency lookup happens before candidate lookup; and compare stream terminal semantics and three-attempt budget wording against all earlier documents. If a contradiction remains, identify its file/heading and minimal change. **Do not edit any files, implement, install, call APIs, provision, commit, or push.** Stop after a concise verification response. Owner sign-off and F1 authorization happen separately.
