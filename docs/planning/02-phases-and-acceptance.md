# F0 — Revised phases and evidence gates

**Current authorization:** F0 reconciliation and independent consistency check only. All targets are proposed, not results. No implementation, installs, commits or paid services are authorized by this document.

## Common evidence rule

Each milestone records exact commands, environment/dependency lock, data/config/source versions, fixture count and denominator, observed outcomes, failure samples, limitations and owner approval. No equivalence between fake/live data, local/hosted services, or a Terraform plan/applied infrastructure.

## F0 — Reconciliation and owner sign-off

**Deliver:** original independent review retained as `07`; revised 00–04 and planning index; explicit D01–D12 outcomes and outstanding assumptions (`08`); bounded F1 task contract (`09`); independent consistency review (`11` after Codex runs `10`).

**Gate:** owner explicitly ratifies the **fully specified** supported matrix, prescription bounds and duration arithmetic in `12`, candidate approval/revision/expiry and idempotency ordering in `13`, and typed SSE/budget semantics in `14`; also consent/TTL, local auth, metadata retention and milestone boundaries. No unresolved high-risk issue without a testable mitigation. Owner separately approves F1 implementation by explicit instruction and deliberately updates local-only `AGENTS.md`.

**Excluded:** application implementation, dependencies, live calls, hosted telemetry, cloud, sibling repository inspection without authorization.

## F1 — Offline vertical slice with correctness and baseline

**Build:** one FastAPI process, PostgreSQL, narrow React app; authoritative F0 contracts `12–14` drive schemas and fixtures; strictly typed profile Save/catalog read; deterministic template baseline; fake-by-default agent with genuinely dispatchable bounded read tool and final typed plan; request-scoped POST SSE; review and bounded revise; transient expiring immutable candidates; explicit transactional Approve; durable immutable history. Include metadata-only local traces, prompt/tool/schema/catalog version manifests, an initial **40 synthetic cases (24 development, 16 held-out)**, deterministic validation and basic budget enforcement.

**Gate:**

- Runs without provider credentials, external egress or billable services. CI fails if live mode or unexpected egress is attempted.
- All designated hard schema/constraint/write/ownership/privacy tests pass. Every final plan presented as actionable satisfies all supported deterministic constraints; unsupported/medical requests clarify or abstain.
- Every Save, Approve and later Submit action is explicit. No raw chat or draft is durably stored by default.
- Two-principal ownership tests; **barrier-tested revise/approve, profile-save/approve, expiry boundaries and committed-key-before-candidate retry**; stale/forged/expired candidate rejects; one approved plan across concurrent approval keys; matching idempotency retry returns same result after process restart and lost response; mismatch is 409; rollback produces no partial records.
- SSE parser handles split boundaries, `plan | clarify | abstain | error` terminal outcomes, stop/disconnect, typed errors and incomplete EOF (including draft without done); `done` is never displayed as approval; candidate loss is a known regenerate/review path.
- Whole-request deadline, tool/attempt/token/concurrency caps are tested in fake mode; no paid model accidentally enabled by `.env` or SDK defaults.
- Frozen version manifest, template baseline and local eval runner produce per-case results and reproducible totals. No claim of real-model quality.

**Excluded:** cloud, durable model generation/resume, separate queue, external users, production LangGraph, live-model/judge evidence.

## F2 — Fault tolerance and focused orchestration learning

**Build:** async I/O fault matrix, cancellation propagation, bounded retry ownership, concurrent-read experiment, cache only for clearly keyable catalog reads, completion/feedback submission, operational failures and recovery runbooks. Add a **contained LangGraph workflow spike** over synthetic scenarios to compare typed orchestration with a graph/checkpoint path; keep it out of the authoritative approval transaction and main path unless a concrete advantage is proved.

**Gate:** all named failure scenarios from `09` have asserted outcomes, deterministic concurrent overlap test, no orphaned local tasks on disconnect, no duplicate/partial approvals; reports compare cache and async orchestration with identical workload. LangGraph spike demonstrates at least one checkpoint/restart/resumption case and records added state/dependencies/complexity; recommendation to keep or reject graph in primary app is evidence-based.

**Excluded:** persistent conversation memory, production durable runs unless separately designed/approved; a framework badge unsupported by working code.

## F3 — Real applied-AI quality evidence and observability

**Build:** frozen rubric/dataset split; human-scored template vs model comparisons; explicit small budget-approved live LLM experiment exercising real selected tool calls and structured outputs; optional separately approved calibrated judge; one Langfuse/OTel export path with retention/redaction and injected leak canaries; a trace-driven failure investigation and prompt/tool iteration.

**Gate:** all designated hard constraints/privacy fixtures pass; report exact eligible-case expected-outcome successes/denominators (proposed target >=90% held-out, no critical failure), anchored per-case human scores including neutral/negative results, model/tool/provider configurations and all retry costs. Diagnose one controlled failure through correlated traces without exporting raw content. Optional judge scores require their own calibration and explicitly labelled uncertainty. Every enabled telemetry sink passes canary and exporter-unavailability tests.

**Future-ready label:** real LLM tool behavior and one real tracing/eval integration must be demonstrated to claim broad Future-specific applied-AI readiness; if user withholds spend/export consent, F3 may be functionally complete offline but these specific claims remain **unverified**. The user controls spending separately.

## F4 — Measured local operations and optionally operated AWS

**Build:** locked builds, Docker local release, CI, health/readiness, migration/rollback, backup/restore drill, latency/cost/retry/cache benchmarks, error tracing. Compare AWS topology options with named region, traffic, retention, recovery objectives and dated official pricing; only after explicit numeric budget/region/privacy approval may Codex provision Terraform-managed short-lived resources.

**Gate:** local build/deploy/rollback and restore evidence, measured p50/p95 with workload/caveats (target at least 100 successful local generation observations plus failures), cold/warm cache comparison and task denominator; cancellation/fault and teardown runbooks. If AWS is approved and applied: record deployment, HTTPS/IAM/secrets, migrations, rollback/restore, teardown and residual resource/billing checks. A Terraform plan without apply remains **planned AWS**, not AWS-operated.

**Excluded:** mandatory cloud costs, unmeasured high availability/scale guarantees, running permanent idle infrastructure for portfolio optics.

## F5 — User feedback and portfolio case study

**Build:** feedback loop and defined task metrics from synthetic use first; optionally recruit ~3–5 consenting adults after independent approval of external auth/isolation, consent and withdrawal, source/processor destinations, retention/backup expiry, deletion/export, incident path and supported adult scope. Document one product hypothesis, measurement, change and follow-up result.

**Gate:** invited/enrolled/completed/attrition counts and carefully defined approval/usefulness/feedback metrics, reproducible architecture/runbooks and one candid failure-to-improvement story. If no pilot approved, report synthetic-only limitations and do not invent customer outcomes.

**Excluded:** exercise effectiveness/clinical benefit claims or statistical-significance claims from tiny pilots.

## Scope control

No milestone approval authorizes paid services, telemetry export, external participant access or AWS provisioning. They each require a separately explicit owner decision, with budget ceiling, model/region/destination and deletion/teardown conditions. Milestone implementation also requires its own owner go-ahead.
