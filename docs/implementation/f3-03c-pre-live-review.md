# F3-03C pre-live preparation review

Review date: **2026-10-24**. Scope: documentation, source inspection and bounded
offline verification only. F3-03B is owner-accepted for its offline scope.
Amendments A–C remain ratified for **offline implementation/testing only**.

**Decision: ready for review of the preparation; NO-GO for any live request.**
Counting has no verified charge ceiling or endpoint-specific retention evidence
in the public sources reviewed. Live authority/transport is deliberately absent.
No positive spending permit is proposed for activation. Current generation,
counting, judge and hosted-export authorizations are each **USD 0**.

Only this report is added. No application code, tests, dependencies, migrations,
contracts, existing handoffs, evaluation artifacts or live gates are changed.
No provider/counting request, account probe, support message, spending, export,
provisioning, deployment, commit or push occurred. Reading public documentation
is distinct from invoking provider API endpoints.

## 1. Evidence and prerequisite classification

Read local ignored `AGENTS.md`, the planning README, approved F3 documents
[17](../planning/17-f3-experiment-and-spend-plan.md),
[18](../planning/18-proposed-token-admission-amendment.md),
[19](../planning/19-f3-03c-pre-live-readiness.md),
[provider safety](../../contracts/provider-safety.md) and handoffs
[F3-01](f3-01-handoff.md), [F3-02](f3-02-handoff.md),
[F3-03A](f3-03a-handoff.md), [F3-03B](f3-03b-handoff.md).
Inspected the actual Responses/counting adapter, Agent admission/budgets,
accounting/ledger, gates, configuration, migrations, versioned assets and tests.
Historical pending/proposal labels in earlier reports describe their stage;
the owner's current acceptance resolves F3-03B's offline review gate.

Classification: **R** = resolved to the stated evidence boundary;
**U** = unresolved, nonblocking for offline preparation;
**B** = blocks the first live request. Some U properties are the intended subject
of a later bounded compatibility probe; they need explicit risk acceptance,
rather than circularly requiring a successful live probe before that probe.

| Prerequisite | Class | Finding / disposition |
| --- | --- | --- |
| Offline A–C ratification and F3-03B acceptance | R | Explicitly accepted; this does not extend ratification to live execution |
| Count-aware 3-generation / 3-count / 6-combined protocol | R, offline | Existing implementation and fixtures exercise four/six-call sequences; original inference/time/tool/retry/repair/admission caps stand |
| Immutable payload binding and independent validation | R, offline | Exact projection, single-use request-memory tickets, checked tool results, authoritative validator and unpublished internal results |
| Paired accounting, SQL ordering and restart fences | R, offline | Accepted native PostgreSQL evidence; held counts and unknown generations remain liabilities; this review does not rerun or relabel native SQL evidence |
| Advertised model/protocol and generation rates | R, documentary | Current official sources support the proposed model/features and dated Standard rate assumptions; account access and actual behavior remain unverified |
| Count tariff and charge maximum `C` | **B / HIGH** | Public review does not establish either; invented fixture hold is unusable as live pricing |
| Counting retention and account-specific privacy controls | **B / HIGH** | Counting has no explicit row in the reviewed retention table; do not inherit generation storage controls |
| Owner's live scope, exact numeric grant, account/project and session | **B / HIGH** | None approved; credentials and accepted offline reports confer no authority |
| Live capability, price provenance and transport enforcement | **B / HIGH** | Current gate is unconditional, adapters require exact MockTransport and SQL projects are replay-only; deliberate protections, not defects to remove by a toggle |
| Durable evidence for usage/pricing discrepancies | **B / HIGH before activation** | Project freeze is durable, but discrepant numeric usage is not written in the mismatch branch; request metrics alone are insufficient after a crash; see section 3 |
| Actual schema compilation, native continuation and count equality | U | Publicly supported shapes, no live evidence; probe must stop on mismatch, never weaken parsing/validation to pass |
| Latency within 30 seconds and stream/state byte limits | U | Cannot infer from fake timings; timeout/oversize is a recorded probe failure, not permission to enlarge caps |
| Model choosing a catalog tool under `auto` | U | An experiment objective, not guaranteed behavior; skip/incorrect choice must remain a reported failure |
| Receipt automation/provider-enforced spend cutoff | U | Not required for one bounded probe if verified maxima remain held and owner accepts that policy; local ledger is not a hard invoice cap |
| Blinded quality evaluation, explanation field, judge, hosted telemetry | U, later scope | Not prerequisites for this minimal compatibility probe; remain unimplemented/unverified and separately gated |
| Real-user authentication/privacy release and deployment | U, excluded | No release gate changes; synthetic-only, one-process local architecture remains |

## 2. Current official documentation verification

All links in this section were searched and actually opened on **2026-10-24**
using official OpenAI documentation. No SDK, credential or API request was used.
These sources establish documented interfaces, not account eligibility or measured
provider correctness. Recheck within 24 hours of a later approved session.

| Source | Verified fact and practical implication |
| --- | --- |
| [GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol) | Responses tool calling, streaming and structured output are advertised; `low` reasoning is supported. Use the exact `gpt-6.1-sol` identifier; no dated immutable snapshot was established. Do not substitute another model. |
| [Standard pricing](https://developers.openai.com/api/docs/pricing?latest-pricing-expanded=true) | USD/million: ordinary input **2**, cached read **0.10**, 30m write **2.50**, 12h write **5**, output **10**. The existing approved subset excludes 12h writes, alternate tiers and regional surcharges. No counting tariff was found on this page. |
| [Function calling](https://developers.openai.com/api/docs/guides/function-calling) | Native function calls carry name, JSON arguments and `call_id`; local results use `function_call_output` with the same ID. Strict function schemas do not authorize a tool or establish ownership. |
| [Structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs) | Object root, required fields, closed objects and nullable optional representation support the existing projection. Documented limits include 5,000 properties and ten nesting levels. Actual compilation/refusal/incomplete behavior still needs a probe. |
| [Streaming](https://developers.openai.com/api/docs/guides/streaming-responses) | Responses streaming is SSE with typed lifecycle/content events. Provider completion is distinct from application validation or candidate publication. No argument delta may dispatch a tool. |
| [Count reference](https://developers.openai.com/api/reference/python/resources/responses/subresources/input_tokens/methods/count) | Parameters: `conversation,input,instructions,model,parallel_tool_calls,personality,previous_response_id,reasoning,text,tool_choice,tools,truncation`. Reply: integer `input_tokens` and `object=response.input_tokens`; no cost/model/hash receipt. `truncation` is listed but deprecated, with `disabled` default. |
| [Counting guide](https://developers.openai.com/api/docs/guides/token-counting) | Counting includes request formatting, tools and model-specific input handling; plain-text tokenization cannot replace it for this workflow. Output usage includes nonvisible generated tokens. Count/generation equivalence remains a provider promise to measure. |
| [Reasoning](https://developers.openai.com/api/docs/guides/reasoning) | Stateless `store=false` output carries encrypted reasoning by default. Preserve ordered native history; do not decode, summarize, persist or log it. This does not prove the selected model's actual continuation shape. |
| [Responses create reference](https://developers.openai.com/api/reference/python/resources/responses/methods/create) | `service_tier=default` requests Standard; check the actual returned tier. Usage exposes input/output/detail/total fields; examples include explicit zero cache writes without TTL partitions. Storage defaults require explicit `store=false`. |
| [Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching) | `ttl=30m` is a **minimum lifetime**, not a deletion deadline. Cache writes replace ordinary input pricing for that partition, rather than adding a second input charge. Cached KV tensors can have a maximum 24-hour retention period. |
| [Data controls](https://developers.openai.com/api/docs/guides/your-data) | The Responses row describes no training use and 30-day abuse-monitoring retention, subject to documented exceptions/account controls. Generation storage and cache retention are separate. No explicit `/v1/responses/input_tokens` entry was found. Counting's policy is therefore unresolved here. |
| [Official spending-controller example](https://developers.openai.com/cookbook/articles/per_run_spending_controller_responses_api) | Supports verified rates, matching supported input fields, conservative accounting and zero implicit retries. Its example count step does **not** establish a count tariff or replace this project's paired pre-count reservation. |

The count schema also describes broader inputs and defaults not used here. Generic
reasoning wording in that reference is not model/account-specific confirmation.
The narrow existing subset remains preferable to guessing compatibility.

### Counting policy: confirmation still required

Targeted official-domain searches covered `responses/input_tokens`, counting
pricing/free/charges and retention, in addition to the count reference/guide,
pricing page, data-controls table and spending example. No verifiable endpoint
tariff, maximum charge or endpoint-specific retention policy was established.
This is a bounded search finding, not a claim that no private agreement exists.

The owner must obtain dated provider-support or account-specific documentation
answering the following; **no support message was sent in this task**:

1. For this account/project/model and exact endpoint, what are the billing units,
   rates, minimums and maximum charge for a <=65,536-byte supported text/schema/
   encrypted-continuation request? Does counting itself invoke inference or warm
   a billable cache? Cover successful counts, invalid requests, 429/5xx, transport
   interruption, cancellation and unknown outcomes. Establish an upper bound
   independent of the not-yet-returned count.
2. If counting is claimed free, confirm explicitly that the claim covers this
   endpoint/account/model, all approved inputs/statuses and effective dates.
   Lack of a published price or a usage field is not confirmation.
3. What training use, abuse/application-state retention, cache side effects,
   subprocessors/processing regions, deletion and ZDR/MAM eligibility apply
   specifically to counting? Does it inherit any Responses policy, and exactly
   which exceptions apply? `store=false` is not a listed counting parameter.
4. How is counting shown in account usage/cost evidence, including delayed or
   aggregate billing? What evidence permits resolving one unknown charge, and
   what controls actually enforce limits rather than merely alerting?
5. Confirm counting support for this model's completed encrypted items, schemas,
   reasoning defaults and omitted generation-only options. Identify any alias/
   tokenizer changes or effective-model identifier behavior relevant to equality.

Retain private account/support evidence outside Git and ordinary telemetry;
tracked review artifacts should contain a dated redacted conclusion, not billing
IDs, credentials or private correspondence. If evidence remains insufficient,
keep **all live allowances at zero**; do not send a paid/possibly-paid count to
discover its price.

## 3. Source audit: what must change before execution

No source change is necessary to finish this review. The following are scoped
follow-up requirements before live activation, not work implemented here.

| Location | Finding | Minimum disposition and acceptance evidence |
| --- | --- | --- |
| [gates.py](../../src/future_training/providers/gates.py), [config.py](../../src/future_training/config.py), [orchestration.py](../../src/future_training/agent/orchestration.py) | The gate always denies; settings are fake-only; Agent allows only fake or the exact replay class. `LivePermit` covers one generation endpoint and lacks the full price/assets/two-endpoint capability. | A separately reviewed experiment-only live boundary must bind both endpoints, account/project, rates/count quote, asset versions, numeric limits, expiry and shutdown state. Preserve application fake defaults and truthful `live` evidence labels; never label network traffic fake/replay or simply remove class guards. |
| [005](../../migrations/005_spending.sql), [006](../../migrations/006_counted_spending.sql), [007](../../migrations/007_counted_rate_version.sql), [counted_spending.py](../../src/future_training/persistence/counted_spending.py) | SQL mode and count quote are explicitly replay/synthetic-only. Current setup APIs and default settlement evidence do not grant real spending authority. | Design the smallest explicit live authority/rate binding using a reviewed **additive** migration if needed; preserve existing rows/history and reject synthetic grants in any live sender. Never rewrite migrations or turn fixture amounts into tariffs. No new service required. |
| `CountedSpendingLedger.settle_generation` | On mismatch the transaction durably freezes the project, leaving `sent` and its maximum hold. It does **not** persist the discrepant numeric usage; current metrics retain it only for the request/local diagnostics. | Before live use, durably retain validated numeric observations plus a bounded discrepancy reason atomically with freeze, without treating them as a priced settlement or releasing the hold. Test crash/restart, duplicate observation, unknown model/tier and overrun. Freeze already prevents new work; this is an evidence/reconciliation gap, not an offline approval defect. |
| `CountedSpendingLedger.settle_count` | Only trusted synthetic held-count settlement exists; caller-supplied synthetic evidence is not a provider receipt. Unknown sent counts cannot automatically reconcile. | Keep real count settlement disabled for a first probe; with a verified `C`, retaining every count maximum is sufficient. Later real settlement needs separately reviewed evidence authority, duplicate policy and over-quote freeze/observation handling. Never use the synthetic zero/known-cost path for live billing. |
| [responses.py](../../src/future_training/providers/responses.py), `read_stream`, `_normalize` | Deliberately narrow event/item sets reject summaries, unknown reasoning content and mixed commentary/tool calls. `output_item.done` is shape-checked, but its completed item is discarded; continuation relies on the terminal output array. | Add documentation-shaped offline fixtures for completed encrypted items, phase and event/terminal consistency. Require bounded preservation/verification of completed native state before continuation; mismatches stop. Do not silently drop commentary/reasoning state or assume the terminal copy is equivalent without evidence. Public count input-item documentation specifically describes completed `output_item.done` reasoning; exact live behavior remains a probe observation. |
| [accounting.py](../../src/future_training/providers/accounting.py), [counting.py](../../src/future_training/providers/counting.py) | Missing/nonzero cache-write detail without TTL partition fails closed; generation input must exactly equal its count, even downward. Model/tier checks are literal. | Preserve rejection. Test published nonzero write shapes and safe unpriced retention; obtain sufficient detail or explicitly reviewed reasoning from fixed TTL before exact settlement. Do not infer missing writes are zero. Do not accept an unexpected returned snapshot ID through an unreviewed alias fallback. |
| Mock-only HTTP clients | `trust_env=false`, redirects off and bounded bodies are present, but mocks do not prove TLS, DNS, connection pooling, compression, socket cancellation or actual request cardinality. | Future live transport needs explicit TLS verification, exact destinations, `retries=0`, one owned client lifecycle and independent opt-in. First test it against local controlled TLS/socket fixtures under a separately authorized implementation scope. Keep routine external egress denied. |
| Existing PostgreSQL runtime | Accepted tests prove logical ordering/process restart; not arbitrary host/disk power failure or a hostile local user. | Before monetary use inspect persistent-volume and `fsync`/`synchronous_commit` settings and acknowledge local trust-auth risk. Do not promise more durability/security than demonstrated; no new infrastructure is required for this review. |

The reported literal generation-rate version is still consistent with the public
Standard prices reviewed today. The missing real price/permit authority must not
be addressed by weakening existing SQL checks. Existing domain validation,
ownership, terminalization, approval and completion transactions need no redesign.

### Exact equivalence and privacy boundaries

Keep the existing nine common fields identical in both bodies, including full
instructions, strict tool/output schemas, ordered history, checked call outputs,
reasoning settings and explicit `truncation=disabled`. Bind the entire generation
body before counting, including output/stream/store/cache/tier fields not sent
to counting. No additional read or context refresh may mutate a counted attempt.
Every continuation/repair/retry requires a new count and paired reservation.

These are client-side consistency guarantees. They cannot prove alias stability,
server tokenization, model/schema acceptance, native-state replay, actual cache
partitions or latency. Do not “fix” a downward count mismatch by silently accepting
it. Preserve actual observations, freeze/stop and retain liability.

Generation `store=false` does not disable abuse monitoring or eliminate encrypted
cache-state retention. The owner must separately accept the documented generation
and cache behavior, including the distinction between 30m minimum and 24-hour
maximum cache retention, and resolve counting's policy. No US-only processing or
ZDR account status is assumed. Native state remains request-memory-only locally.

## 4. Financial recalculation

The public generation rates match the current implementation. With `I` inference
input and `O` inference output, the approved 30m-only worst raw charge is:

```text
USD_raw <= (2.50*I + 10*O) / 1,000,000
I_total <= 16000; O_total <= 4000; raw logical maximum = $0.080000
```

**Rounding refinement (local arithmetic, not a provider price change):** the
ledger rounds each generation settlement upward to whole microdollars. Across
three attempts, the sum can exceed the raw $0.08 formula. Executing the existing
`cost_micro` with all input assigned to 30m writes gives:

| Attempt | Input | Output | Rounded microdollars |
| --- | --- | --- | --- |
| 1 | 5,333 | 1,333 | 26,663 |
| 2 | 5,333 | 1,333 | 26,663 |
| 3 | 5,334 | 1,334 | 26,675 |
| Total | **16,000** | **4,000** | **80,001** |

A simple conservative three-attempt accounting bound is **80,002 microdollars
($0.080002)**: each rounding adds less than one microdollar, so the integer total
is below 80,003. This bound need not be tight. Existing financial ceilings already
reject reservations that do not fit; no inference limit or monetary authorization
is amended here. Future permit arithmetic should cover this rounding margin.

Let **`Cµ`** be a provider-verified, upward-rounded maximum count charge in integer
microdollars, covering failures and uncertainty. It is **unknown**. Conditional
local accounting ceilings, excluding unapproved surcharges/tax/FX, are:

| Population | Conservative accounting ceiling |
| --- | --- |
| One compatibility logical request, up to three pairs | `(80002 + 3*Cµ)` microdollars |
| Ten smoke requests, separately authorized later | `(800020 + 30*Cµ)` microdollars |
| 68 historical proposed requests, separately authorized later | `(5440136 + 204*Cµ)` microdollars |

These are calculations, **not permits**. No positive numeric total can be verified
while `Cµ` is unknown. Earlier $1/$6 and conditional $1.25/$8 proposals are not
activated or carried into a new stage. The fixture's $0.001 is not evidence for
`Cµ`. A confirmed zero tariff would also require a reviewed compatibility change
because the current synthetic quote contract intentionally requires positivity.

| Authorization category | Exact current limit |
| --- | --- |
| Live generation, counting, compatibility grant | **$0.000000 each** |
| Live project lifetime, UTC day, operator session | **$0.000000 each** |
| Judge, hosted telemetry, cloud | **$0.000000 each** |
| Live outbound requests | **0** |

If `Cµ` later becomes verified, a narrowly bounded owner proposal can use the same
exact `(80002+3*Cµ)` limit for grant, dedicated probe project, UTC day and one
operator session, with **one logical request total**, no top-up or rollover reset.
The owner must approve the verified count maximum and resulting four concrete
limit values, not a symbolic formula. A grant expiring within two hours and the
30-second request deadline are distinct. Any all-in tax/FX or account surcharge exposure
needs explicit treatment
before that approval. Local ceilings are not a synchronous provider invoice cap.

## 5. Minimum later compatibility experiment — specified, not executed

This is a first compatibility probe, **not** the ten-case smoke or F3 quality
acceptance. After all B gates and separate authorization, use one frozen synthetic
case with the existing Agent/read dispatcher/validator and `catalog-v1`:

- Adult synthetic preferences from the existing valid development fixture,
  normalized explicitly as follows; profile revision **1**, generation request
  **`{"profile_revision":1,"preferences_text":""}`**, no previous plan:

  ```json
  {
    "adult": true,
    "goal": "general_strength",
    "equipment": "bodyweight",
    "experience": "beginner",
    "days_per_week": 2,
    "session_minutes": 20,
    "excluded_ids": [],
    "excluded_tags": []
  }
  ```

  Freeze this JSON and existing assets before execution. All workout semantics
  remain those of the ratified domain contract; no new workout rules are proposed.
- No free-form preference text: current Agent intentionally clarifies nonempty
  text. No real person/history, owner identifiers, credentials or health notes in
  provider input. Use one authorized synthetic principal and captured profile revision.
- Existing versioned prompt/tools/output/config; model `gpt-6.1-sol`, reasoning
  low, `service_tier=default`, implicit 30m cache, `store=false`, background off,
  stream true, `tool_choice=auto`, parallel calls false and truncation disabled.
- Harness calls existing request-scoped internal orchestration and returns an
  **unpublished** result. It grants no candidate publication, approval, completion
  or business-plan write authority and does not enable live application routes.

**Only permitted provider destinations**, POST over verified HTTPS port 443:

```text
https://api.openai.com/v1/responses/input_tokens
https://api.openai.com/v1/responses
```

No model-list/auth probe, response retrieval/cancel/delete, conversation, file,
cache-prewarm, hosted tool, judge, telemetry, alternate host/region/path or URL
from provider/tool content. Provider docs browsing is outside this proposed run.

| Step | Operation and required evidence |
| --- | --- |
| 0, local only | Confirm exact permit/assets/rates, no pending reconciliation, all ceilings and original deadline/admission; atomically reserve count maximum plus worst paired generation; commit one-shot count claim |
| 1 | Count the exact frozen initial supported body; validate reply and retain the count charge maximum; acknowledge count and reduce only the paired generation hold |
| 2 | Commit generation claim, recheck gate/deadline and send original bytes. Expect an actual model-selected `search_exercises` call; validate complete call/name/arguments/native ID and actual usage, including `input_tokens=N` |
| 3, local only | Dispatch the owned read exactly once, revalidate result/size/catalog/profile and append it with the original native call ID; preserve completed native state |
| 4 | Freeze the complete continuation, reserve its pair and count it independently, retaining count liability |
| 5 | Claim/send continuation and validate structured output, usage, exact durations/prescriptions/exclusions and all captured constraints; return an unpublished outcome |

Expected happy path: **two counts + two generations = four requests**. The full
probe maximum is **one logical request, three counts, three generations, six
combined requests**, including any permitted third tool-continuation/repair/known
retry. At most four local reads, one semantic repair and one shared retry; all
inference across attempts stays 16,000 input / 4,000 output, with at most 2,000
output per attempt and one original 30-second deadline. Existing admission remains
one/principal and two/global; run this probe serially, with no second logical run.

If the model first reads preferences, a further catalog read/final response may
use the remaining pair if all limits permit. A skipped catalog call is a tool-
selection evidence failure even if a valid plan appears. Do not force a tool or
silently perform a script-selected read and call it model-selected behavior.
No automatic retry for count failure or uncertain transport; only the existing
single owner may retry a classified generation failure with known usage.

**Stop immediately** on failed funding/claim/permit checks, unknown count cost
policy, count mismatch, stale payload/native/profile/catalog, unexpected model/
tier/cache category, malformed/oversized stream, missing usage, duplicate/unmatched
call, write attempt, privacy leak, exhausted budget, cancellation/deadline or
emergency disable. Existing safe validation failures may use the one semantic
repair only within the same limits. Unknown costs stay held; failure does not
authorize another logical request, model fallback, wider caps or a top-up.

A successful probe requires genuine `auto` catalog selection, one checked local
dispatch/result continuation, complete supported output, independent validity,
count/usage equality for every generation and correctly retained/settled accounting.
Record every failure and unknown too. Clarification, abstention, cancellation and
other live smoke cases remain for a separately approved stage; do not claim this
single case establishes those live behaviors or useful personalization.

## 6. Required live transport safeguards and offline proofs

These are requirements for a later reviewed implementation, not implemented here:

1. Default-deny explicit experiment opt-in plus independently owner-approved,
   unexpired durable capability bound to model, two endpoints, account/project,
   price/count evidence, asset versions and exact numerical ceilings. Credentials
   alone must fail. Preserve fake-only normal startup and truthful source labels.
2. Exact HTTPS host/path/method/port allowlist; certificate and hostname verification
   on; no redirects, inherited proxies, arbitrary base URL, user-selected URL,
   implicit retries, automatic polling/reconnection or startup API calls. Bound
   decoded bytes as well as frames; compressed responses cannot bypass limits.
3. One owned async client with bounded connection/pool/read/write operations inside
   the original deadline; no reuse of a closed real transport across the current
   per-operation mock-client contexts. No SDK is required merely to add HTTP.
4. Commit paired reservation before count, durable claim before each send, and
   fail closed on any unknown database outcome. Recheck permit/shutdown/deadline
   immediately before transport after the claim. Preserve request-local tickets,
   original counter/token ownership and no generation replay after restart.
5. Emergency stop durably disables future claims, then cancels and awaits owned
   work and clears native/ticket state. An already claimed/in-flight request can
   still charge. Closing a socket is not proof of provider cancellation/refund;
   do not add an unapproved cancel endpoint. Restart never resumes a generation.
6. No HTTP/provider debug or automatic body instrumentation. Local console/ring
   only: allowlisted stages, opaque correlations, counts/durations/versions;
   no prompts, plans, credentials, native state, raw exceptions, payload hashes
   or private billing IDs. Credential headers must never be forwarded to another
   destination. No hosted sink is part of this experiment.

Additional offline acceptance cases before activation: wrong host/path/port and
redirect target; proxy/CA environment injection; untrusted/expired certificate;
connect/TLS/read interruption and compressed oversize; shutdown between reservation,
claim and send; cancellation after count acceptance; terminal without timely EOF;
completed native-item/terminal mismatch and preserved phase; supported nonzero
cache-write shapes; durable discrepant usage across restart; per-attempt monetary
rounding; and credential/permit/quote/asset mismatches. Use local transports,
barriers/fake clocks and isolated PostgreSQL schemas; no real provider is needed.
Re-run the existing full CI-equivalent/privacy/contracts/frozen-baseline suite
after those separately authorized changes. Retain the accepted F1/F2 architecture.

## 7. Concrete authorization record required before any live request

Every item below is pending except accepted offline F3-03B. This report neither
creates a permit nor asks to activate one while count policy is unknown.

- [x] Owner accepts F3-03B for offline scope; accepted limits/evidence preserved.
- [ ] Owner accepts this preparation report and identifies a separately authorized
  implementation scope for the required offline prerequisites/live boundary.
- [ ] Provider/account-specific evidence establishes counting tariff, all-status
  maximum `Cµ`, retention/data-use/region policy and selected model access.
- [ ] Review/accept the concrete implementation and new offline proofs, including
  durable observations and financial rounding; extend A–C explicitly to **this
  one live experiment**, without raising inference/time/tool/admission limits.
- [ ] Approve exact provider/account/project, alias risk and returned-model policy,
  Standard rates/version, count quote/evidence and generation/cache/privacy terms.
- [ ] Enter verified `Cµ=____` microdollars and exact grant/project/day/session USD
  limits `____/____/____/____` (currently all zero), one logical request total,
  <=3 generation + <=3 count + <=6 combined calls, start/end and expiry <=2 hours,
  no automatic top-up/new session/day resetting the project budget. Confirm any
  operator-session and grant identifiers privately; do not put secrets in Git.
- [ ] Approve the two exact destinations and frozen synthetic input/assets;
  accept generation abuse/cache retention and **separately confirmed counting
  retention**. Approve minimal local evidence retention; no external-user data.
- [ ] Name the emergency operator and demonstrate disable/cancel/drain/restart
  behavior offline, with persistent uncertainty and key revocation instructions.
- [ ] Verify dedicated-account/project use and provider-side controls without
  unbudgeted API probes. Record their limitations; billing alerts are not assumed
  synchronous enforcement. Unknown costs reduce available allowances indefinitely.
- [ ] Owner explicitly authorizes execution **after** the above review, with the
  stated stop conditions and one first-result disposition. Silence, a credential,
  offline acceptance or completion of this report is not authorization.
- [ ] After the future probe, stop and review evidence before any ten-case smoke,
  F3-04 evaluation, judge, export, cloud work or additional logical run.

Future evidence must label source `live` and retain requested/effective versions,
asset/catalog/validator/price versions, case disposition, exact operation counts,
per-generation count versus actual numeric usage/cache/reasoning partitions,
known/reserved/unknown costs and DB states, fixed failure reasons, stage durations
and deadline outcome. Keep private receipt IDs only in reviewed ignored billing
evidence; never raw native reasoning or ordinary-log content. No provider hash
echo or frozen model weights are implied by local artifact fingerprints.

## 8. Checks performed and stopping point

This review changes only this Markdown file, so no build/migration/full regression
rerun was necessary. Executed bounded offline corroboration:

```powershell
.venv/Scripts/python.exe -m pytest -q tests/test_responses.py tests/test_token_admission.py tests/test_counted_responses.py --basetemp=.cache/pytest-f303c-review
.venv/Scripts/python.exe scripts/evaluate_baseline.py --check
git diff --check
git check-ignore AGENTS.md
```

Observed: **162/162 tests passed**, 5.11 s; **24/24 development + 16/16 legacy
held-out baseline cases passed**, zero failures. The targeted set uses synthetic
HTTP and protocol/reference tests; it is not native SQL or live-provider proof.
The separate arithmetic stdin check called existing `ActualUsage/cost_micro` on
the three synthetic partitions above and returned `[26663,26663,26675]`, total
80,001 microdollars. No business data or ledger state was written.

Historical F3-03B evidence remains 766 routine / 174 native-HTTP-browser / 85
frontend / 47 isolated-graph tests; these are **accepted prior results**, not
new runs in this review. No database/browser service was started. Existing
migrations, contracts, limits, immutable records and frozen evidence are unchanged.
Documentation checks verify UTF-8, balanced fences, whitespace, local links and
the single-file change boundary; ignored local test outputs are not deliverables.
All **18 local links** resolve. A separate read-only stdin check validates the
exact proposed profile/request with the existing schemas and confirms a feasible
baseline plan. `AGENTS.md` remains ignored and untracked.

**Stop after this review.** Pricing/retention confirmation, follow-up implementation
review, numerical authorization and a separate execution instruction remain
required before even the first counting request. No F3-04 work has begun.
