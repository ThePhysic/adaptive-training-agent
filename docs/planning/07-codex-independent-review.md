# Codex independent review — Future Adaptive Training Agent

Review date: 2026-10-23. Stage: F0, review only. Recommendation: **revise the plan before approving F1**. This report proposes decisions and gates; it does not approve implementation or spending.

## 1. Executive judgment

The project is a credible applied AI engineering exercise if it proves one reliable profile-to-draft-to-approval journey. The modular monolith is appropriate. The largest risk is building infrastructure around an agent before establishing what the model adds over a deterministic planner.

Top three strengths:

1. The [charter](00-charter-and-requirements.md) defines a coherent journey, a bounded domain, and explicit non-goals. A curated catalog and independent validator make failures inspectable.
2. The [architecture proposal](01-architecture-proposal.md) puts authorization and durable writes under application control. It correctly distinguishes streamed events from committed state and questions dual state ownership.
3. The [evaluation and cost proposals](03-evaluation-safety-privacy.md) favor synthetic data, offline CI, a fake provider, versioned evidence, and approval before live spending. These are valuable engineering constraints.

Top three concerns:

1. **High — persistence and approval are underspecified.** F1 persists plans, but idempotency is delivered in F2. “Explicit approval before saving” also conflicts with implicitly persisting drafts, conversations, runs, and checkpoints before approval. Decide which records may exist, for how long, and under which consent before building schemas.
2. **High — evidence arrives too late.** Evaluation, tracing, budgets, and baseline comparison cannot wait until F3/F4. Mocks prove application behavior under scripted outputs; they do not prove model tool selection, personalization, refusal, latency, or cost. A working mock demo alone is insufficient applied AI evidence.
3. **Medium — the proposed stack exceeds the current workflow.** A graph checkpointer, persistent run manager, separate SSE subscription, two telemetry integrations, and cloud services create several lifecycle problems for a short drafting request. None is yet justified by measured requirements.

Evidence reviewed: local instructions, root README, and every existing document in `docs/planning/` (README and 00–06), plus the official references linked below. Repository inspection found planning material and no application implementation, dependency manifest, tests, or deployment artifacts. No role posting or named sibling repository was supplied. Therefore role coverage below maps the requirements in the charter/review assignment, not an independently verified employer posting. No runtime, load, safety, model-quality, price, or reuse result is claimed as measured.

## 2. Requirement mapping

All evidence in this table is **proposed**, not already demonstrated.

| Requirement | Concrete evidence deliverable | Missing item in current plan | Recommendation |
| --- | --- | --- | --- |
| Typed Python, Pydantic, async APIs | Validated request/tool/result schemas; async service and provider adapter; contract tests | Coercion/unknown-field policy, error taxonomy, cancellation propagation | Reject unsupported fields/arguments, distinguish malformed input from provider failure, and test actual async I/O boundaries |
| Tool-calling agent and structured outputs | One model-selected catalog read, bounded dispatch, typed final plan, bounded repair | A fixed sequence of application reads could be mislabeled tool calling | Keep deterministic orchestration but include a small read-tool loop; record actual model tool decisions in an approved live experiment |
| Prompt engineering | Versioned prompt, tool schema, model settings, catalog version, failure-led revisions | Prompt ownership and change comparison are implicit | Keep prompts reviewable; compare one prompt/tool change with identical scenarios and scorers |
| Parallel async API orchestration | Sequential vs concurrent independent read experiment; timeout and sibling-cancellation tests | Profile-dependent catalog search is not independent; parallel DB reads are not external API fan-out | Parallelize only independent profile/history reads where useful; use local fake HTTP adapters for transport tests and label their limits |
| Streaming UX | Typed SSE contract, streamed progress, browser integration, stop/disconnect tests | POST client choice, buffering, event size limits, terminal semantics | Start with direct POST streaming using browser fetch; final validated plan is a distinct event |
| Durable state and human approval | Immutable approved snapshot; transaction and race tests; restart/readback evidence | Approval revision binding, idempotency lifetime, crash boundaries | Deliver atomic approval in F1; recover approved data, while interrupted generation may explicitly fail |
| Evaluation and scoring | Template baseline, versioned synthetic corpus, hard checks, anchored quality rubric, held-out comparison | No concrete initial gate; “effectiveness” can imply unsupported fitness outcomes | Begin fixtures and baseline in F1; score preference adherence and usefulness, not clinical or training effectiveness |
| LLM-as-judge | Frozen judge rubric/config, human comparison, disagreement examples | Optional spending can leave this skill entirely unproven | Keep optional but explicitly mark unfulfilled without a real judge experiment; never use judge scores for write authorization |
| Observability and debugging | Correlated request/tool/model/validation/approval spans and one diagnosed failure | F3 is late; overlapping exporters can leak or duplicate data | Instrument minimal metadata in F1; add one Langfuse export path in F3 |
| Retry, caching, token/cost control | Whole-request budgets, fault tests, cache experiment, cost ledger | Layered retries, failed-attempt cost, cache isolation and invalidation unspecified | One retry owner; cache catalog reads first; measure rather than assume savings |
| Prototype to operation | Local runbook, migration/rollback and restore drill; measured bounded load | Deployment terminology could overstate production readiness | Make claims proportional to the environment and tested recovery guarantees |
| AWS and Terraform | Reviewed IaC, applied deployment evidence, teardown and residual-resource check | An IaC plan alone does not establish operated AWS experience | Make AWS an optional, separately approved evidence track; clearly label local-only completion |
| Product collaboration and iteration | Hypothesis, pilot protocol, task observations, prioritized change, follow-up measurement | Product discovery starts only in F5 | Review UX assumptions with synthetic tasks in F1; external participants still require the release gate |

The strongest portfolio narrative is an observed failure, its trace, a targeted change, and a reproducible comparison. Listing more frameworks does not substitute for this evidence.

## 3. Decisions: D01–D12

| ID | Judgment | Rationale and tradeoff | Minimal alternative / decision trigger |
| --- | --- | --- | --- |
| D01 | **Keep** modular monolith | One domain and short bounded generation do not require distributed execution. A process can fail mid-generation, which must be explicit | One backend, one database; add a worker only after a measured requirement for work surviving requests |
| D02 | **Keep**, narrow UI | React/TypeScript can demonstrate typed streaming and approval UX, but a broad chat product distracts | Profile, draft/revise/review, approval, history; defer rich chat memory, dashboards and advanced editing |
| D03 | **Change** streaming/run design | Async FastAPI is suitable; durable run creation plus a subscriber introduces scheduling, subscription races and recovery obligations | Direct POST SSE with fetch; separate approval/readback JSON endpoints; reconsider run APIs when background execution or replay is required |
| D04 | **Defer** LangGraph | The current path is mostly linear; human review can occur between two ordinary HTTP requests | Typed orchestration functions plus explicit states; compare graph adoption later against one specified recovery problem |
| D05 | **Keep**, clarify ownership | PostgreSQL is defensible for transactions, ownership and concurrent approval. A graph sharing the database still creates logical duplication | One authoritative domain schema; transient draft state initially. SQLite is simpler for a disposable demo but would require later PostgreSQL concurrency verification |
| D06 | **Keep**, strengthen adapter | Fake-by-default supports deterministic CI; one provider avoids portability work | Expose typed tool calls, structured output, usage, finish reason and classified errors; avoid a universal multi-provider abstraction |
| D07 | **Change** sequencing | Local fixtures must remain usable without Langfuse; independent telemetry stacks add work | Local evaluator and metadata spans first; one exporter/integration later; separate export approval and retention settings |
| D08 | **Defer** deployment, **keep** AWS learning goal | No region, budget, uptime requirement or participant load is approved | Local container deployment first; compare short-lived single-host AWS with ECS/Fargate plus managed DB before selecting |
| D09 | **Keep**, bound claims | A small original catalog makes provenance and constraints testable; breadth limits usefulness | Start with about 20–40 reviewed records and an explicit supported equipment/goal matrix; unsupported combinations produce clarification or no plan |
| D10 | **Keep**, strengthen contract | Human approval must bind to exactly what was reviewed and cannot be forged by model text | Server-owned immutable candidate revision, atomic commit, owner checks and idempotent retry; no model write tool |
| D11 | **Defer** package extraction | No source was inspected and no second consumer is established | Reuse concepts; inspect named paths and licenses later; extract only when two concrete consumers justify an interface |
| D12 | **Keep**, specify prerequisites | An external pilot introduces privacy, access and support obligations | Consenting adults, tested auth/isolation, consent/withdrawal, deletion/export, retention, clear limits and incident contact before enrollment |

Reject for the initial scope: a queue without a background-work requirement, multiple model providers, vector retrieval for a tiny catalog, autonomous plan submission, framework selection justified only by role keywords, and claims that a workout validator establishes physical safety.

## 4. Architecture analysis

### Minimal credible MVP and module boundaries

Use one FastAPI backend, a narrow React UI, PostgreSQL, a versioned catalog, one deterministic template planner, and a fake model adapter. Support general adult weekly planning within a declared goal/equipment/session envelope. Include a bounded catalog read tool, typed generation, independent validation, revision, explicit approval, and approved history. A bounded revision request can include the previous candidate; persistent conversation memory is unnecessary.

Keep six responsibilities visible: API/authentication; orchestration/provider adapter; domain schemas/catalog/validator/template planner; persistence/approval service; offline evaluation; telemetry. The orchestration layer may propose data. Only the domain approval service may commit a plan. This boundary matters more than folder names.

Postpone durable agent resumption, replayable event logs, conversational memory, external integrations, complex feedback analytics, self-hosted telemetry infrastructure, cloud hosting and external participants. Add simple completion/feedback logging after the approval path is reliable, by F2. There is no evidence yet for Redis, vector databases, a broker, or multiple backend services.

### Data ownership and consent

Distinguish **drafting**, **saving preferences**, **approving a plan**, **logging completion**, and **consenting to external telemetry**. These are different actions. The proposal's broad ban on “unapproved durable writes” needs a precise definition: approval-related audit/idempotency records are legitimate transactional side effects, while a generated conversation is not implicitly authorized for storage.

Recommended F1 interpretation: explicit profile Save permits profile persistence; starting generation processes the submitted preferences but does not durably save the conversation/candidate; plan Approve saves only the exact approved snapshot and its minimal audit/idempotency metadata. Completion/feedback requires its own explicit submit action. Persisting drafts later requires a disclosed retention/consent decision. No full chat history by default.

| Data | Authority and lifetime | Required invariant |
| --- | --- | --- |
| Catalog | Versioned original/licensed records, copied to DB or loaded locally | Stable IDs, source/license, equipment semantics and version are inspectable |
| Profile | PostgreSQL after explicit Save; revisioned | Server-derived owner; requests use a consistent profile snapshot |
| Candidate | Bounded, expiring server memory for initial single-process MVP | Owner, opaque ID, immutable revision/hash, validation version and expiry bind approval |
| Approved plan | PostgreSQL immutable snapshot, with source versions | Later catalog/profile changes cannot silently rewrite history |
| Approval/idempotency/audit | PostgreSQL, same transaction as plan creation | Same successful approval maps to the same plan; no partial audit or duplicate write |
| Completion/feedback | PostgreSQL after explicit submit | Owned plan/session reference, bounded structured fields, independent retention |
| Telemetry | Allowlisted operational metadata; separate retention | No raw profile, prompt, output, token, or user identifier exported by default |

The in-memory candidate store is a deliberate limit: single backend process, bounded entries/bytes, short TTL (proposed 30 minutes), and loss on restart. It is not a durable workflow. An expired/lost candidate requires regeneration and fresh review. If multiple replicas or resume-after-restart becomes required, approve a database-backed candidate design and its consent rules first. Do not hide this limitation behind an API returning a run ID.

### Request execution, SSE and recovery

Prefer `POST /api/v1/drafts/stream` for request-scoped generation; `POST /api/v1/drafts/{id}/approve` for approval; and `GET /api/v1/plans/{id}` plus history for durable readback. Exact route naming remains an F0 decision. No persistent run manager is needed for this baseline.

Use fetch streaming with an abort signal and an SSE parser that handles split UTF-8, multi-line events and chunk boundaries. Native EventSource is designed around a URL and reconnecting GET; its constructor provides neither a request body nor arbitrary authorization headers. A POST stream therefore needs an appropriate client. The [HTML standard](https://html.spec.whatwg.org/multipage/server-sent-events.html) defines event framing and reconnection. [FastAPI's SSE documentation](https://fastapi.tiangolo.com/tutorial/server-sent-events/) supports POST streams and identifies native SSE support as added in 0.135.0; select and lock a compatible stable release during F1, rather than assuming examples work with older installations.

Contract: a versioned envelope with request ID, monotonic sequence, event type and typed payload. Emit `status`, at most one final `draft`, or `error`, followed by terminal `done` when transport permits. `done` means generation ended; it never means approval. Do not stream unvalidated plan fragments as actionable advice. Token deltas are optional; progress plus a final validated plan is sufficient initially. Heartbeats contain no user data. Bound event size, stream lifetime and client buffering.

Before streaming starts, authorization/input failures use normal HTTP errors. After headers are sent, use a sanitized typed stream error; an unexpected EOF remains an incomplete request. Cancellation/disconnect cancels and awaits outstanding local tasks, releases provider connections and never approves. Cancellation cannot guarantee reversal of a provider call or its charge. Record unknown usage conservatively.

F1 explicitly offers **no event replay and no automatic generation retry**. A broken stream offers user-triggered retry; a completed approval with a lost response is retried using its original idempotency key. An authoritative plan read confirms persistence. Do not promise an authoritative durable run lookup while choosing ephemeral generation. If the original run-ID design is retained, first specify job ownership, start-before-subscribe behavior, bounded event storage, polling, cancellation, worker lease/restart handling and multi-process routing. A POST returning 202 alone creates none of these guarantees.

### LangGraph, concurrency and model tools

A typed sequence with named states is enough: authorize/read context → bounded tool/draft loop → validate → ready or failed/cancelled. Approval is a separate application transaction. Proposed graph adoption trigger: demonstrate a required multi-step restart/resume scenario that materially simplifies with checkpoints, then compare dependencies, state duplication, debugging and migration burden. Keep the same domain contracts and evals for the comparison. [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence) distinguishes thread checkpoints from longer-lived stores; neither should replace the approved-plan authority. [Interrupt documentation](https://docs.langchain.com/oss/python/langgraph/interrupts) notes that resumed nodes re-execute, so effects require idempotency. A graph interrupt is not authentication, consent, or a database transaction.

Profile and recent-history retrieval may be independent. Catalog filtering based on that profile is downstream; do not race it with unresolved equipment/exclusions. Optional history failure can degrade to a clearly disclosed profile-only draft; profile/catalog failure must stop or ask for missing information. Bound query sizes and connection use; never share a mutable database session across concurrent tasks. Do not hold a transaction open during generation or human review.

The catalog model tool accepts filters within server-derived constraints; it cannot relax equipment/exclusions or select an owner. Validate every call, reject unknown tools, cap results and tool steps, and treat returned descriptions as untrusted data. Validation runs unconditionally in application code even if a model declines to call a validation tool. Remove approval and feedback writes from the model's exposed tool list.

For parallel API evidence, test two independently awaited HTTP read adapters using local fake transports and controlled delays/failures, with an overlap barrier rather than brittle CI timing thresholds. This proves orchestration mechanics, not a live external integration or a product speedup. Do not introduce a permanent service solely to manufacture fan-out. Report any unmet external integration requirement honestly.

### Approval, authorization and idempotency

Use server-derived identity on every profile, stream, candidate, plan, feedback and history operation. IDs are references, not authorization. For local F1, a loopback-only synthetic identity adapter is acceptable if startup fails when that adapter is selected for external binding. Test at least two synthetic principals. Before real users, use maintained authentication integration rather than building password handling; decide same-origin secure-cookie/CSRF behavior or bearer-token handling explicitly.

Approval sequence:

1. Authenticate, authorize candidate ownership, and bind the request to the displayed immutable candidate ID, revision and content hash. The confirmation control is a deliberate user action; model text or a graph resume payload cannot confer authority.
2. Revalidate the server-owned snapshot, expiry and supported constraints. If profile/catalog/validator revisions invalidate the preview, reject as stale and require a new review; never silently substitute another plan. Re-check relevant versions at commit to close concurrent-edit races.
3. Within one transaction, claim a unique `(owner, operation, idempotency_key)` with a canonical request fingerprint, create the immutable approved plan, mark the candidate approval identity unique, and record minimal audit/result data. Roll everything back on failure. Database uniqueness is the final concurrency guard, not a pre-insert application lookup. [PostgreSQL constraints](https://www.postgresql.org/docs/current/ddl-constraints.html) and [INSERT conflict handling](https://www.postgresql.org/docs/current/sql-insert.html) provide the relevant primitives; fingerprint validation remains application logic.
4. Same key and fingerprint returns the original result; same key with different content returns 409. Concurrent keys for the same candidate revision still yield one approved plan. Deliberately saving a later revision requires a new review and identity.
5. After commit but before response loss, retry still returns the original plan after restart, even if the transient candidate is gone. Authenticate and check the persisted idempotency result before requiring a live candidate for a previously successful request. Unknown keys require a valid live candidate.

Propose retaining successful idempotency bindings with the approved plan, subject to account deletion; expired transient candidates cannot be re-approved. Store only a bounded key and fingerprint, never approval credentials in traces. Guarantee one database effect for the defined approval identity, not exactly-once delivery or exactly-once provider execution.

## 5. Safety/privacy

The fitness boundary must be part of product behavior and fixtures. Support adults seeking general planning; do not request diagnoses, injury histories, medication, biometric records, or treatment constraints. A medical/rehabilitation request must receive a conservative out-of-scope response and appropriate professional referral without generating a bespoke treatment plan. Do not attempt to diagnose or claim a classifier guarantees safety. Avoid expanding the supported population without a separate review.

Define a machine-readable supported constraint vocabulary: permitted goals, days, session durations, equipment, experience bands and exercise exclusions. Specify duration arithmetic, including rest/warm-up/transitions, rounding and tolerances; distinguish estimated planned duration from actual execution time. Define what to do when the catalog cannot satisfy a request. Contradictions and infeasible combinations must yield clarification or an explicit unsupported result, never silently relaxed constraints.

Schema-valid sets/repetitions/intensity are not evidence of suitable training. Use reviewed bounded prescription templates for the initial supported scope, avoid aggressive automatic progression, and let the model choose/explain within those bounds. Catalog content needs provenance, units, equipment interpretation and exclusion tags. Deterministic checks verify only declared constraints; they do not certify physical safety. “Effectiveness” should be renamed unless a qualified review and valid outcome method are separately established.

Threat controls and release evidence:

| Boundary | Required behavior and test |
| --- | --- |
| Untrusted prompt/catalog/model text | Injection fixtures cannot select another owner, widen tools, override hard constraints or trigger writes; tool call IDs/counts/arguments are validated |
| UI rendering | Treat streamed/model text as untrusted; no raw HTML execution, unsolicited executable links or credentials embedded in rendered content; test hostile markup |
| Multi-user access | Wrong-owner IDs fail uniformly for candidates, plans, feedback and streams; pagination cannot disclose another user's records |
| Approval | Stale, changed, expired, forged and concurrent approvals cannot alter the reviewed payload or create duplicates |
| Telemetry and errors | Capture only allowlisted fields; injected synthetic secret/PII canaries are absent from all log/span/error/export sinks, including URLs and exception messages |
| Unsolicited sensitive text | Do not persist the raw request or emit it in errors/traces. Minimize what is sent upstream; disclose that filtering is imperfect and provider processing is a separate consent/data-flow decision |
| Deletion | Delete owned profiles/plans/feedback/candidates and applicable traces/checkpoints; prevent deleted data being reintroduced from restored backups |

Default telemetry should include request/trace IDs, stage, bounded error code, model/prompt/catalog versions, counts, durations and usage totals. Pseudonymous identifiers can still link activity; keep identity mapping out of external traces. Sanitization by regex alone is inadequate. SDK auto-instrumentation, HTTP headers, DB query parameters, span names/events and provider errors are all possible leakage paths. [Langfuse masking documentation](https://langfuse.com/docs/observability/features/masking) explicitly limits the scope of its hooks and notes separate exporters can receive unmodified spans. Test each configured sink; do not assume a Langfuse mask covers all OTel output.

Before an external pilot, approve a data inventory, processor destinations, retention periods, consent/withdrawal text, deletion/export procedure, backup expiry, adult participation limits and incident contact. Proposed starting policy for owner consideration: no raw-chat retention; candidates expire after 30 minutes; operational metadata expires after 14 days; approved records persist until user deletion or a stated pilot end date; backup expiry is stated numerically. These are proposals, not established policies or compliance claims. Account deletion must describe backup limitations and suppress restoration of deleted records.

## 6. Evaluation and quality

### Separate application correctness from model quality

A small catalog, template planner and fake provider are adequate for F1. They permit reproducible validation, UX, failure and persistence tests without spend. They do not establish general fitness usefulness, robust natural-language understanding, real provider streaming, or a calibrated judge. Do not increase the corpus to 500 mostly redundant scenarios to imply confidence.

Start with **40 synthetic cases: 24 development and 16 held out**, selected for distinct failure modes. Include feasible plans, infeasible combinations, missing/conflicting fields, equipment/exclusion edge cases, boundary durations, unsupported goals, malformed outputs, unknown tools, injection attempts, medical requests and privacy attacks. Keep API race/fault tests separate from task-quality cases so a large integration-test count cannot inflate quality claims. Each scenario declares expected outcome and applicable checks, not one exact “correct” workout.

Build a deterministic template baseline in F1 using the same catalog, supported constraints and validator. Do not quietly give it fewer capabilities or a different input. Compare constraint success, clarification/refusal correctness, human-rated preference adherence/usefulness, latency and cost. A template win is a useful result: retain it for simple requests and bound any claimed model benefit to cases showing evidence.

Use three score groups, reported separately:

- **Hard correctness:** 100% of final exposed plans meet supported deterministic constraints; invalid drafts may be repaired or rejected. All designated permission/write/privacy fixtures pass. Infeasible/out-of-scope cases are scored against their expected abstention/clarification, not penalized for lacking a plan.
- **Task quality:** anchored 1–5 scores for preference adherence, explanation clarity and useful variety. Report eligible-case counts, mean/median, per-case failures and uncertainty; do not average away a hard failure. A proposed initial target is at least 90% expected-outcome success on eligible held-out cases, with exact numerator/denominator and no critical failures. This small set does not demonstrate population-level reliability.
- **Operations:** report request success, time to first useful update, completion latency, attempts, token totals and estimated/provider-reported cost. Define whether “success” means validated candidate, approval, or logged completion; publish each denominator.

### Human and judge design

Before seeing variant labels, humans score paired outputs from template and model with anchored examples; randomize display order. Begin with 20 scenario pairs (40 outputs): 10 development scenarios for rubric calibration and 10 held-out scenarios for comparison. Prefer a second reviewer on at least 10 shared scenario pairs. If only the owner scores them, disclose the limitation rather than calling it independent validation.

If judge spending is approved, calibrate on development examples, freeze its rubric/config, and evaluate the 20 outputs from the 10 held-out human-scored pairs. Report exact agreement, agreement within one point, mean absolute error and important disagreements; add weighted agreement statistics only if the sample supports interpretation. A proposed criterion for using judge scores as a supplementary summary is at least 80% agreement within one point in each dimension on that subset; otherwise report them as exploratory and retain human scoring. This small calibration sample cannot establish general judge reliability. Test order sensitivity, preference for verbosity and model-family bias with a few reversed/shortened pairs. Never let judge output decide authorization, physical safety or constraint validity. Without a live judge, mark judge calibration as unverified.

### Reproducibility and experiment progression

Record dataset split/hash, catalog version, code revision (or source hash before commits exist), prompt/tool/schema/scorer versions, provider/model identifier, generation settings, dependency lock and run timestamp. Live results are not deterministic merely because temperature is low. Preserve sanitized synthetic artifacts, failures and excluded cases; cached/replayed fixtures verify regression mechanics, not fresh model behavior.

Progress after explicit spend approval: (1) at most 10 synthetic live smoke cases; (2) stop and diagnose schema/tool failures; (3) run baseline and one justified prompt/tool variant on the same frozen cases; (4) repeat a small unstable subset; (5) add a judge only if it answers a defined question. Precompute worst-case calls/tokens including repair, retry and judging; do not run an unrestricted model sweep.

Offline regression gates start in F1: no hard failures; expected validation/abstention outcomes on every designated fixture; deterministic fake runs reproduce. F3 requires a paired comparison with failures and per-case scores, including a negative or neutral result if that is what the evidence shows. If live approval is withheld, complete the offline harness but label real model quality and judge behavior unverified.

### Observability and fault evidence

Correlate request → context/tool reads → provider attempts → validation/repair → candidate → approval transaction. Keep generation and approval traces linked by opaque candidate identity without exporting content. Include stage timings, finish reason, retry cause, constraint error code and budget consumption. Logs/spans must explain an induced failure without raw prompts. A telemetry exporter outage must not block approval; bound export queues/retries and report dropped telemetry. [Langfuse experiments](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk) can use local datasets, so central dataset hosting is unnecessary for the baseline.

Required F1/F2 tests: invalid provider output; unknown/oversized tool call; hanging context call; exhausted budget; 429/5xx/timeouts; disconnect/cancellation; database unavailable; stale revision; concurrent same/different approval keys; rollback before commit; response lost after commit; process restart after commit; candidate lost before approval; and cross-user reads/writes. Test both service and HTTP boundaries where they carry different guarantees. Use deterministic barriers, fake time and local transports for fault tests. These are proposed tests, not executed F0 results.

## 7. Cost and operations

### Zero-spend default and bounded live requests

Offline tests and CI must start without credentials, use local/fake adapters, disable external exporters and reject unexpected external network calls. Supplying an API key alone must not enable live mode. Require an explicit provider opt-in plus approved category ceiling; interactive generation, evaluation/judging, telemetry hosting and cloud are separate categories. CI must not inherit an owner's live-provider configuration.

Proposed initial engineering limits, to ratify at F0: 30-second overall generation deadline; at most 4 read-tool calls; one semantic repair; one transport retry across the whole run; at most 3 provider attempts total including retries/repair; cumulative 16,000 input and 4,000 output tokens; one concurrent live run per local user and two globally. Tune only with evidence. All nested SDK retries must be disabled or counted by one owner. Retry only classified transient failures within the remaining deadline; honor retry delays only if the deadline permits. Invalid user constraints are not retryable.

These token/request limits are not dollar approval. Before live mode, estimate worst-case spend using a selected provider/model's current official prices, reserve budget atomically before each attempt, and stop if the remaining allowance cannot cover its maximum. Track failed, cancelled and unknown-usage attempts conservatively. A process restart must not reset an approved session/daily allowance; concurrent requests cannot each spend the full remaining balance. Local metering is an engineering control, not a guarantee that every remote charge is known immediately.

Cache static catalog/filter results first. Key by catalog version and all relevant filters; invalidate on version change. If experimenting with generated-plan caching, include owner/consent boundary, profile/constraint/catalog/prompt/model versions and TTL; never share personalized outputs across users by default. Approval always revalidates regardless of cache origin. Compare cold/warm latency and quality at a stated hit rate; provider prompt-cache discounts must be measured and supported by current provider documentation before claiming savings.

Cost per successful task = all generation/repair/retry cost for the test population divided by its defined successful tasks; report judge cost and cloud/telemetry recurring cost separately. Do not hide unsuccessful requests or divide by only cached successes. Distinguish estimated tokens/prices, provider usage and reconciled charges. With zero successful tasks, report total spend and an undefined ratio.

### Cloud alternatives and operating proof

No cloud choice or price is approved. Compare these alternatives at F4 with a named region, hours of operation, traffic, storage, retention and recovery objective:

| Option | Value | Cost/operations tradeoff |
| --- | --- | --- |
| Local Docker/Compose | Reproducible development, fault and restore demonstrations | No hosted availability or operated AWS evidence |
| Short-lived single AWS host running app and PostgreSQL containers | Small topology for an owner-only synthetic demo; exercises Terraform and host recovery | Single failure domain, patching/TLS/volume-backup responsibility; unsuitable for stronger availability claims without added work |
| One ECS/Fargate backend serving the built UI, plus managed PostgreSQL and HTTPS ingress | Managed container/DB operations and a fuller AWS learning artifact | More resource/network/IAM dependencies and recurring idle costs; choose only when their learning value fits the approved budget |

A non-AWS hosted service may reduce effort, but does not satisfy AWS evidence. For ECS, a load balancer is an explicit topology/cost decision; [AWS documents load balancing as optional](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-load-balancing.html). Validate the chosen HTTPS ingress, SSE buffering/timeouts, DB reachability and secret delivery instead of copying a topology. Avoid adding NAT gateways, separate workers or multiple replicas without an explicit need and priced design.

The cost sheet must include compute, idle database, storage/snapshots/backups, public addressing, ingress/load balancer, NAT or endpoints if used, egress, container registry, logs/metrics, secrets, DNS/domain if needed, hosted tracing and any retained resources after shutdown. No numeric cloud estimate is defensible before choosing these assumptions; obtain dated official pricing before approval. [AWS Budgets](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html) reports delayed cost updates and notifications, so an alarm is not a hard spending cap. Add a scheduled stop/teardown procedure, limited capacity/traffic, resource inventory and residual-resource checks.

F4 proof should include pinned build artifacts, migration and backward-compatibility decisions, image rollback, least-privilege IAM, HTTPS, bounded connection pools, liveness vs readiness, secrets outside Terraform output/logs, protected IaC state, and a backup restore drill. Specify recovery objectives before deployment; proposed owner-demo targets are restore within 60 minutes and at most 24 hours of data loss, subject to approval and actual drill results. A single-host demo cannot claim high availability. Rollback must account for schema compatibility; restoring a database is not an ordinary app rollback.

Benchmark after correctness gates: fixed synthetic workload, hardware/runtime/provider settings, concurrency, warm-up, request count and cache state. Use at least 100 local successful-generation observations plus failure counts for an initial latency report; distinguish fake-provider timing from approved live samples. Set a latency target after the initial measured baseline. Report p50/p95 and time-to-first-useful-update; an immediate heartbeat is not useful progress or a completed task.

## 8. Revised phase plan

All numbers below are proposed acceptance targets, not observed results. Each phase requires an evidence record with exact commands, source/config versions, observed counts, failures and limitations. Owner approval of a reconciled F0 plan and deliberate authorization of the next milestone remain prerequisites.

| Phase | Outcome and scope | Measurable gate | Deliberately excluded |
| --- | --- | --- | --- |
| **F0** | Resolve supported scope, consent/storage, state/stream design, approval contract, eval seed specification and cost categories | Owner records decisions for every High item in section 10; chooses baseline and auth boundary; ratifies limits/retention and revised milestones; no unresolved High issue lacks a testable mitigation; local instructions deliberately authorize only the next milestone | Application code, dependency/account setup, API use and provisioning |
| **F1** | Offline vertical slice: typed profile/catalog/template/fake agent, bounded read-tool dispatch, validator, POST SSE, review/revise/approval/history; minimal spans; 40-case corpus | Runs with no API keys/external egress; request/token/tool/deadline/concurrency limits and opt-in tests pass; supported final plans pass every hard check; explicit Save/Approve boundaries demonstrated; two-principal ownership tests; same/different-key approval races yield one plan; transaction rollback and lost-response retry after restart pass; stream/error/stop UI works; template/fake baseline and version manifest recorded | Durable runs/checkpoints, cloud, external users, claims about real model quality |
| **F2** | Reliability: stress budget enforcement, async fault behavior, completion/feedback, concurrency/retry/cache experiments, broader restart recovery | All named fault cases in section 6 have asserted outcomes; no orphan local tasks after cancellation; retry/tool/token/deadline limits hold under concurrent tests; failed approval leaves no partial records; committed approval survives restart; lost candidate produces a clear regenerate/review path; independent-read overlap proven without brittle timing | Automatic continuation of generation across crashes unless separately justified; unnecessary queues |
| **F3** | Quality and tracing evidence: frozen splits/rubrics, human review, optional approved live provider and judge, one export path | Paired template/model or clearly labeled fake comparison on identical cases/scorers; all designated hard/security fixtures pass; expected-outcome target and exact counts reported; human-scored sample and judge agreement/disagreements if enabled; one induced failure explained by correlated trace; every sink passes leakage canaries and exporter-outage test | Claims of validated fitness outcomes, broad model generality, centrally hosted datasets by default |
| **F4** | Reproducible operation, measured optimization, optional AWS/IaC track | Local build/deploy/rollback and restore drill pass; cost/latency/cache experiment includes baseline, denominator and failure costs; cloud requires separate dated price/ceiling/privacy approval before apply; if applied, recreate/rollback/teardown and inspect residual resources; report measured recovery and latency | Mandatory cloud spend, unmeasured production-scale or high-availability claims |
| **F5** | Product learning and honest case study | Before enrollment, tested real auth/isolation, consent/withdrawal, export/deletion, approved retention and support path; target 3–5 consenting adults if approved; record invited/enrolled/completed counts, acceptance/logging/usefulness definitions, attrition and one evidence-led iteration; clearly label small-sample or synthetic-only results | Clinical benefit claims, unapproved health-data collection, statistical significance claims from a tiny pilot |

F3 evaluation design and F4 operational hooks begin in F1; later phases deepen evidence rather than introduce basic controls. A small live smoke experiment may occur during F2 only under separate spend/privacy approval; no live experiment is implied by approving implementation. A withheld live/cloud/pilot approval narrows the evidence claim and does not justify bypassing the gate.

## 9. Reuse

**Verified within this repository:** the charter, architecture alternatives, role mapping and threat/evaluation categories are useful specification inputs. Their paths are linked throughout this report. No reusable application package, CI workflow, Docker configuration, evaluation runner or provider integration was found in the reviewed repository. The existing root ignore rules exclude the local instruction file; no Git settings change is needed for this review.

**Unverified:** the visual-inspection, computer-use and security-agent projects mentioned in [the charter](00-charter-and-requirements.md) may contain useful patterns, but no sibling paths or access authorization were supplied. None was searched or inspected. Their completion, compatibility and licensing are unknown.

Later, with named read-only paths, inspect: provider adapters and retry ownership; async cancellation tests; fixture/evaluator interfaces; deterministic CI and secret handling; log redaction; approval/idempotency transactions; Docker/IaC runbooks; and licenses/transitive dependencies. Record exact source/version, test evidence, retained assumptions and adaptation cost before copying. Prefer a small inspected pattern over extracting a shared package. Do not import prior user data, credentials or logs as fixtures.

## 10. Actionable changes and owner decisions

Severity describes consequences if unresolved, not a verified vulnerability in nonexistent code. High items block the relevant gate; Medium items risk misleading evidence or avoidable complexity; Low items are optional. Effort is relative planning/implementation effort (S: narrow contract or check; M: several connected boundaries; L: operational or evaluation work), not a time estimate.

| Rank / ID | Severity; impact; effort | Required change and rationale | Tradeoff and measurable acceptance |
| --- | --- | --- | --- |
| 1 / R1 | **High**; incorrect/duplicate approval; M | Amend proposed F1 scope in [02](02-phases-and-acceptance.md) to include transactionality, immutable revision binding, idempotency and lost-response recovery | More initial DB work; one plan across same/different-key races, zero partial records, durable retry result after restart |
| 2 / R2 | **High**; unauthorized retention/privacy; M | Reconcile “before saving” with profile/draft/run/checkpoint/audit persistence in [00](00-charter-and-requirements.md), [01](01-architecture-proposal.md) and [03](03-evaluation-safety-privacy.md) | Transient drafts lose resume capability; approve a data inventory and consent/lifetime for every record class, with no raw-chat storage by default |
| 3 / R3 | **High**; unsupported plan behavior; M | Define supported population, constraints, prescription bounds, duration arithmetic and infeasible/out-of-scope outcomes in [00](00-charter-and-requirements.md) / [03](03-evaluation-safety-privacy.md) | Narrower breadth; named boundary fixtures reject/clarify rather than relax constraints; no claim of physical-safety certification |
| 4 / R4 | **High**; uncontrolled live spend; M | Move whole-request deadline, attempts, tool/token/concurrency limits and live opt-in into F1; strengthen [04](04-decisions-risks-costs.md) | Less autonomous repair; CI rejects egress, nested retries stay inside global caps, concurrent live budget reservations cannot overspend the approved allowance |
| 5 / R5 | **High before external users/export**; disclosure/access risk; L | Define real auth, consent, deletion and every telemetry/provider destination in [03](03-evaluation-safety-privacy.md) | Defer pilot/export until ready; all wrong-owner tests fail safely, all sinks pass canaries, deletion and restore suppression are demonstrated |
| 6 / R6 | **Medium**; excess lifecycle complexity; S/M | Replace default run/checkpointer design in [01](01-architecture-proposal.md) with request-scoped streaming and separately committed approval, or justify retaining it | Interrupted generation restarts manually; document no replay/resume, and test restart/cancel/EOF outcomes. Retaining runs requires the lifecycle contract in section 4 |
| 7 / R7 | **Medium**; unsubstantiated AI value; M/L | Move template baseline, prompt/version manifests, initial evals and tracing into F1 in [02](02-phases-and-acceptance.md) / [03](03-evaluation-safety-privacy.md) | Smaller feature scope; frozen 40-case corpus, per-case comparison, human anchors, no fake-result claims about live quality |
| 8 / R8 | **Medium**; missing role evidence; M | Make genuine tool dispatch, async HTTP evidence, caching and judge limitations explicit in [00](00-charter-and-requirements.md) | A few targeted experiments instead of extra services; tool/fan-out traces and tests distinguish simulated transport, real behavior and unmet requirements |
| 9 / R9 | **Medium**; recurring cloud costs/weak recovery; L | Require priced topology, approved ceiling, schema rollback, restore and teardown proof before F4 apply in [02](02-phases-and-acceptance.md) / [04](04-decisions-risks-costs.md) | Cloud remains optional; applied resources, residual costs, measured recovery and budget-monitor limitations are documented |
| 10 / R10 | **Low**; maintainability opportunity; M | Revisit LangGraph, shared eval package, larger corpus and generated-output cache only after baseline evidence | Fewer framework artifacts initially; adopt only with a recorded problem, comparison and measurable improvement or learning objective |

These are recommended edits for reconciliation; the original planning documents were not modified.

Owner decisions required before F1:

- Ratify the narrow supported goal/equipment/population envelope and bounded prescription/catalog responsibility (R3).
- Choose request-scoped streaming with ephemeral candidates, or explicitly justify durable runs/checkpoints and their storage consent (R2/R6).
- Approve the exact approval identity, revision invalidation and idempotency retention rules (R1).
- Ratify local synthetic identity isolation and the later external authentication gate (R5).
- Set request budgets and retention policies; leave live-provider, judge, hosted tracing and cloud ceilings disabled/unapproved until numeric ceilings and destinations are selected (R2/R4/R9).
- Agree that mock/local-only work is a valid milestone outcome but does not fulfill real LLM/judge/AWS evidence; obtain the actual role posting if exact employer alignment is required (R7/R8).

Official documentation consulted on 2026-10-23 is linked at the point of use. The additional [FastAPI streaming response reference](https://fastapi.tiangolo.com/advanced/custom-response/) and [MDN SSE guide](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) were also inspected. These are evolving documents, not a dependency lock. At the authorized implementation milestone, select supported stable versions, check compatibility across Python/FastAPI/Pydantic/database drivers and any telemetry/checkpointer packages, and record the exact lock plus contract tests. No dependency version was installed or runtime compatibility verified during F0.
