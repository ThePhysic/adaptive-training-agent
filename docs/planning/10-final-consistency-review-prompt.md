# F0 — Final Codex consistency check (review only)

## Purpose

Review the reconciled F0 plan **after** the independent `07-codex-independent-review.md`. The objective is to catch contradictions, missing high-risk acceptance tests, unsupported claims and unwanted work—not to restart architecture ideation or begin feature implementation.

## Scope and rules

Read local `AGENTS.md`, root `README.md`, `docs/planning/README.md`, original review `07`, reconciled documents `00`–`04`, `08` and `09`, plus historical `05` and `06` for provenance. Do not treat the initial prompt as current instruction. Do not implement code, create dependencies, inspect sibling repositories without express read-only permission, provision resources, call APIs, install tools, push, or commit. Write only `docs/planning/11-final-consistency-review.md` unless the owner separately authorizes a specific edit.

## Check these topics

1. Every independent-review HIGH issue R1–R5 has an explicit, testable F1 or release gate and no contradictory persistence/authorization requirement.
2. Candidate ephemeral storage and restart behavior are coherent with approval identity, idempotency history, single process and later AWS replica topology.
3. SSE route, client and error contract can actually work; no accidental run-ID/replay dependency or `done=approved` assumption.
4. Budget controls cannot be bypassed by nested retries, concurrency, cancellation or implicit SDK/environment configuration; F1 offline versus later live monetary gates are explicit.
5. Original Future role coverage remains credible despite deferring LangGraph in the main path, and the bounded F2/F3 LangGraph spike demonstrates real learning without unnecessary graph persistence in domain authority.
6. Synthetic/fake/local, real provider, live judge, external telemetry, AWS applied and consenting-user evidence are consistently distinguished.
7. The supported envelope, catalog, duration math, privacy/retention rules and opt-in actions are specific enough for F1 to start without guessing. Identify any required owner choices missing.
8. Updated docs are mutually consistent; historical review remains unchanged; AGENTS.md stays ignored; no scope creep to clinical advice, queues or microservices.
9. Identify risks introduced by proposed F1 complexity. Recommend smaller F1 units if possible **without** deferring correctness controls.
10. Check current stable Python/FastAPI/Pydantic/Langfuse/LangGraph compatibility questions for later F1/F3 (advice only; no installs or pinning in F0).

## Output

Write `11-final-consistency-review.md` with:

- Verdict: `READY FOR OWNER APPROVAL` or `REVISE BEFORE APPROVAL`.
- Issue table: severity (HIGH/MEDIUM/LOW), doc/heading, issue, exact proposed fix, blocking gate.
- Explicit pass/fail for R1–R10 and D01–D12 consistency, citing local doc sections.
- Minimum required owner sign-offs before F1.
- Optional suggestions separated from blocking changes.
- Confirm that no implementation, installs, spending, provisioning, commits or pushes occurred.

Stop after writing the report; do not edit the reconciled plans automatically.
