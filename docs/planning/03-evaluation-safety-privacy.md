# F0 — Revised evaluation, safety, privacy and telemetry design

**Status:** F0 proposed controls; no tests or results have been executed by these planning documents.

## Scope and model-agnostic safety boundary

This app makes bounded **general adult wellness** suggestions. The system must abstain or request clarification on injury rehabilitation, diagnoses, pregnancy-specific adaptations, contraindications, medications, treatment plans or other medical contexts. Do not collect medical histories. Adults may specify normal exercise dislikes or catalog exclusions; do not present unsupported medical accommodations as guarantees. No training effectiveness, clinical safety, or qualified-coach endorsement is implied.

Catalog content requires stable IDs, provenance/license, equipment requirements, supported goal/experience tags, exercise type, bounded prescription templates, and explicit exclusion tags. Every supported output passes a *deterministic* validator independent of model decisions. The validator's declared checks are not a substitute for professional fitness assessment.

Define and test: exact sessions/week, allowed gear, stable catalog IDs, disallowed exercise tags, prescription template bounds, duration estimate with warm-up/work/rest/transition/cooldown, duplicate/range constraints, and out-of-envelope abstention. Reject silent relaxation of user requirements.

## F1 benchmark design

- Start with **40 hand-designed synthetic task cases**: 24 development, 16 held out. Include successful combinations, impossible combinations, missing/conflicting fields, equipment exclusions, boundaries and duration arithmetic, malformed/unknown tools, prompt injection, medical redirection and privacy/ownership attacks. Quality cases stay distinct from API/concurrency fault tests.
- Each fixture stores input, expected *outcome category* (plan, clarify, abstain, error), supported constraints and applicable exact checks, not an exact single correct workout.
- Maintain a deterministic template planner using the same catalog and validator as agent variants. Version its configuration and do not give it artificially fewer abilities.
- Offline fake provider by default; hard fixtures are CI regression gates. Its performance and outputs **do not prove** LLM reasoning, preference usefulness, real streaming latency or cost.
- Report hard correctness separately: 100% of final actionable plans satisfy deterministic constraints; all designated auth/write/privacy fixtures pass. An invalid proposal may be rejected; that is not a valid final plan.
- Proposed held-out expected-outcome success >=90% on eligible cases, with exact fraction/denominator, no critical faults. A 16-case set cannot justify population reliability. Report missing/unsupported case outcomes, not just plans generated.

### Quality scoring and human review (F3)

Use anchored 1–5 rubric dimensions: **preference adherence**, **explanation clarity**, **useful variety**. Avoid unqualified 'effectiveness' or clinical safety scores. Preserve means, medians, per-case failures and uncertainty; report constraints and error cases separately from quality numbers.

Start with 20 scenario pairs (template versus actual model if permitted): 10 development pairs for rubric calibration and 10 held-out pairs for comparison (40 outputs). Randomize/blind variant labels. Aim for a second human reviewer on at least 10 shared pairs; otherwise disclose owner-only bias. Baseline wins and neutral outcomes are valid evidence.

A paid LLM judge is optional under its own approval. Freeze judge settings/rubric after calibrating on development examples. Compare 20 outputs from the 10 held-out human-scored pairs. Report exact and within-one agreement, mean absolute error, disagreements and bias tests (order/verbosity). Proposed supplementary-use threshold: >=80% agreement within one score point **per dimension**; do not treat this tiny study as general validity. The judge never authorizes writes or declares training safety. If not run, mark judge quality unverified.

## Real provider evidence and spend gate

Proposed staircase **after owner explicitly authorizes model/model price, category budget, data destination, credentials and opt-in**:

1. <=10 synthetic live smoke cases covering real tool selection, structured output, invalid tool recovery, streaming and usage.
2. Diagnose failures and freeze provider/model/settings, prompt, schema and catalog version.
3. Compare deterministic template with one model/prompt variant on matched cases and matched scorers; repeat an unstable subset if affordable.
4. Record all attempts, repair, retry, finish reason, provider usage vs estimated charges and failed-task cost. Never run unbounded sweeps.

Record manifest: source revision, dataset split/hash, catalog/prompts/tool schemas/validators/scorers versions, provider/model/settings, dependency lock, timestamps, run type (`fake|recorded|live`), sample selection and excluded cases. Temperature 0 does not make all live results reproducible.

## Privacy/data minimization

Distinct user actions: **Save profile**, **Generate transient proposal**, **Approve exact plan**, **Submit completion/feedback**, **Consent to live provider data processing**, **Consent to external telemetry**, **Join pilot**. Do not collapse them into one blanket consent. Never infer approval from model text, streaming done, or a graph checkpoint.

| Data | F1 default | External pilot requirement |
| --- | --- | --- |
| Profile | Persist only after Save; versioned, owned | Clear disclosure, export and deletion |
| Generation prompt/conversation | No raw retention; transient processing | Disclose any upstream model destination and processor handling separately |
| Candidate | Bounded in-memory ~30min, single worker, no resume after restart | Decide durable draft policy before replicas/replay; not in initial scope |
| Approved plan/audit/key | Transactionally persisted; until user deletion | Document retention, idempotency records and deletion mechanics |
| Completion/feedback | F2 explicit Submit | Own-record access plus retention/deletion |
| Local operational spans | Allowlist only; proposed 14-day retention | Retention/export sinks and processor inventory |
| Provider/hosted telemetry | Disabled by default | Destination review, opt-in, canary tests, deletion/limits |
| Backups | Local/dev data as configured; no real users | Numeric expiry, restore-and-deletion suppression rules |

Do not export raw prompts, plans, model outputs, arbitrary headers, user identities, URL/query values or exception strings by default. Pseudonymization can still expose linkable behavior. Avoid regex-only redaction: use allowlisted span attributes/events, disable content capture/auto-instrumentation not proven safe, and test **all** configured sinks separately. Provider-side data transmission cannot be made safe merely by masking application logs. No raw user content in tracked test evidence.

Before external enrollment: real maintained auth (not synthetic header) with defined cookie/CSRF or bearer policy, cross-user isolation, adult consent and withdraw, data inventory/processor destinations, export/deletion, backup expiration, retention and incident contact. Validate that restoring backup does not silently resurrect deleted users, or document/implement suppression workflow. No pilot or public hosting until this gate passes.

## Required threat and reliability tests

- Prompt injection in request/catalog/model outputs cannot cause writes, choose identity, widen allowed tools, change budget or weaken constraints.
- All profile/candidate/approval/history/feedback requests use server-derived owner; wrong-owner opaque IDs cannot disclose contents, including error differences.
- Immutable approval identity: stale profile/catalog/validator or candidate revision/hash, expired/forged candidate, concurrent same/different keys, transaction rollback, lost response/retry after restart, and deletion.
- Provider errors: malformed final output, unknown/oversized tool call, hanging transport, 429/5xx, timeout, budget exhaustion, cancellation and partial SSE stream. Classify rather than silently fabricate a plan.
- Client security: streamed hostile text cannot execute HTML/script or create unsafe links. UI never treats raw token deltas as validated workouts.
- Telemetry canary: synthetic injected PII/secret-like strings are absent from all logs, spans, exceptions, tracing exporters and URL fields; exporting service failing cannot block an approval commit.
- Cache keys include catalog version and relevant filters; personalized output caching deferred until ownership/consent and version isolation are proven.

Use fake clocks, explicit concurrency barriers and in-process/fake HTTP transports; don't rely on fragile sleeps in CI. Test service and HTTP boundaries where they differ.

## Local traces and future Langfuse

F1 metadata-only correlation: request ID, stage, timestamp/duration, prompt/model/tool/catalog/validator version, bounded error code, tool/result count, attempt count, estimated/provider-reported tokens and estimated cost. Link an approval stage to its generation by opaque candidate ID **without exporting raw candidate content or direct user identity**.

F3: select ONE compatible Langfuse SDK/OTel path, pin an actively supported stable version at implementation time, approve destinations/retention and test all sinks. Langfuse supports experiments over locally maintained datasets; do not rebuild dataset infrastructure solely for a dashboard. Follow the current SDK docs rather than assuming older versions and interfaces: https://langfuse.com/docs/observability/sdk/overview and https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk.

## F0 domain contract incorporated

See [`12-f0-domain-contract.md`](12-f0-domain-contract.md) for binding supported matrix, prescription bounds, duration formula, exclusions, inclusive preset tolerances and hand-computed boundary examples. Treat them as software constraints, not medical/clinical proof. C3 clarification/abstention terminal outcomes are specified in [`14`](14-f0-remaining-contract-clarifications.md).
