# Proposed token-admission amendment and F3-03B safety gate

Current implementation note: offline F3-03B and documentation-only F3-03C are
owner-accepted. F3-03D hardens numerical discrepancy persistence, native stream
consistency, owned local-only HTTP/TLS and shutdown. Its conservative proposed
generation accounting bound is **$0.080002**, plus unknown counting costs; this
is a rounding refinement, not live ratification or spending permission. The
historical proposal body below is preserved. See
[F3-03D handoff](../implementation/f3-03d-handoff.md) and
[current checklist](19-f3-03c-pre-live-readiness.md).

**Current status:** the owner accepted F3-03A and ratified **amendments A–C for
offline implementation and testing only**, authorizing F3-03B. The body below is
the preserved F3-03A proposal; its prospective/unratified and not-yet-implemented
language describes that historical stage. Current normative contracts are
[14](14-f0-remaining-contract-clarifications.md) and
[provider safety](../../contracts/provider-safety.md). See the
[F3-03B handoff](../implementation/f3-03b-handoff.md) and
[F3-03C readiness checklist](19-f3-03c-pre-live-readiness.md).
No live requests, spending, active permits or later implementation are ratified.

Date: 2026-10-24. Status: **PROPOSED — NOT RATIFIED**. Prepared under F3-03A only.
This document does not change contracts 12–14, `provider-safety.md`, runtime
limits, spending permissions or live gates. No provider/counting request is
authorized. Owner acceptance of an offline work unit is not live authorization.

## 1. Recommendation and resolution boundary

Recommend a narrowly scoped **three generation attempts / three counting
attempts / six combined wire attempts** policy for a separately ratified,
count-aware experiment. Every generation must have its own fresh exact count
bound to the frozen generation payload. Keep the existing inference token,
tool, repair, retry, concurrency, validation and 30-second deadline limits.

The protocol conflict is specified precisely and demonstrated offline: initial
count + generation of a tool call + continuation count + final generation needs
four wire calls. It cannot fit the current three-total-call rule. The implemented
mock experiment therefore refuses the continuation before an unusable second
count. Six-call behavior is evaluated only by a pure reference model; no active
adapter or application can execute it under this unit.

This is a **conditional design resolution**, not proof of live readiness. Counting
price/maximum charge and endpoint-specific data retention remain unverified;
there is no durable count-operation ledger or live transport. The exact-count
promise also depends on provider behavior for the selected model and native
state. No local code can undo input tokens or charges already consumed if that
promise fails. Live entry remains disabled pending ratification, implementation
review and separate numerical/provider/privacy authorization.

## 2. Independent documentation review

Official pages were searched/opened on 2026-10-24. No SDK, API key or provider
endpoint was used. Some expanded language-neutral reference pages exceeded the
documentation fetch size; the compact Python reference and its schema panels
were used instead. API request permission does not follow from reading docs.

| Source | Verified fact / review implication |
| --- | --- |
| [Counting guide](https://developers.openai.com/api/docs/guides/token-counting) | The documented exact endpoint accounts for provider formatting and tools, unlike local text estimates. Its result is a token count, not generation usage or a cost receipt. |
| [Python count reference](https://developers.openai.com/api/reference/python/resources/responses/subresources/input_tokens/methods/count) | Count request fields are `conversation`, `input`, `instructions`, `model`, `parallel_tool_calls`, `personality`, `previous_response_id`, `reasoning`, `text`, `tool_choice`, `tools`, `truncation`. Response fields are `object="response.input_tokens"` and integer `input_tokens`. |
| [Reasoning schema panel](https://developers.openai.com/api/reference/python/__sdk_schema?declaration=%28resource%29+responses.input_tokens+%3E+%28method%29+count+%3E+%28params%29+default+%3E+%28param%29+reasoning+%3E+%28schema%29&selected=%28resource%29+responses.input_tokens+%3E+%28method%29+count) | Reasoning options include context/effort/mode/summary settings. Preserve exactly the supported subset being used; do not translate opaque state into readable text. Generic older-model wording is not account-specific proof for Sol. |
| [Text schema panel](https://developers.openai.com/api/reference/python/__sdk_schema?declaration=%28resource%29+responses.input_tokens+%3E+%28method%29+count+%3E+%28params%29+default+%3E+%28param%29+text+%3E+%28schema%29&selected=%28resource%29+responses.input_tokens+%3E+%28method%29+count) | Count supports the `text.format` structured JSON schema and verbosity. Counting only user text would omit required schema context. |
| [Generation reference](https://developers.openai.com/api/reference/python/resources/responses/methods/create) | Generation has additional output/transport/storage/cache/tier options. They cannot all be submitted blindly to the count endpoint. Official usage examples can explicitly report zero cache writes without a per-TTL breakdown. |
| [Reasoning guide](https://developers.openai.com/api/docs/guides/reasoning) | Stateless continuation can carry encrypted reasoning plus ordered native output items. Preserve completed state, including assistant phase where present; no reasoning summaries, decoding or durable chat is needed. |
| [Structured-output rules](https://developers.openai.com/api/docs/guides/structured-outputs) | Root object, required/closed properties and the supported schema subset remain necessary. Current documented limits include ten nesting levels and 5,000 properties; local grammar compatibility is not server acceptance evidence. |
| [Pricing](https://developers.openai.com/api/docs/pricing), [data controls](https://developers.openai.com/api/docs/guides/your-data) | This review did not establish an endpoint-specific counting tariff/charge bound or retention guarantee. Absence of a price row is not evidence of free service. Generation `store=false` cannot simply be added to an endpoint that does not list it. |

The count reference accepts the Responses input-item family, including native
continuation types; the guide supports tool schemas and the schema panel supports
output formatting. Whether Sol's actual encrypted items are accepted and counted
consistently still needs a separately authorized provider compatibility probe.
No snapshot/deterministic-tokenization SLA, payload-hash echo or server-side
binding receipt was established. A count result does not identify the effective
model version, so client correlation cannot by itself eliminate alias drift.

## 3. Payload equivalence contract (proposed)

Scope only synthetic text, the two existing local read tools, the strict plan /
clarify / abstain envelope, and bounded manual continuation. No hosted tool,
file/image input, URL fetch, provider conversation, previous-response reference,
remote prompt template, server compaction or automatic truncation.

| Field group | Count body | Generation body / required invariant |
| --- | --- | --- |
| `model`, `instructions`, `input` | Exact frozen values | Same model and all roles/text/native items; no new context read or reconstruction after counting |
| `tools`, `tool_choice`, `parallel_tool_calls` | Exact definitions, `auto`, false | Same strict schemas/names/descriptions, nulls/default representation and tool-selection settings |
| `reasoning`, `text` | Exact supported configuration and output schema | Same effort/context/verbosity/format if specified; omitted versus explicit values stay distinct |
| `truncation` | Explicit `disabled` | Same; normalization occurs once before either body is frozen |
| `max_output_tokens` | Not sent: not listed by count reference | Bound generation-only value, at most `min(2000, remaining output)`; changing it invalidates the frozen attempt |
| `stream`, `store`, `background` | Not sent | Fixed true/false/false; cannot infer counting retention from generation storage control |
| `service_tier`, `prompt_cache_options` | Not sent | Default/Standard and approved implicit 30m settings remain fixed; omission from counting relies on documented input-count semantics, still check actual usage |
| Conversation/reference/personality and all other fields | Rejected by this narrow experiment even when broader API supports them | A new field requires a new projection/compatibility review; never silently omit an input-affecting option |

Serialize the full generation body once into bounded canonical UTF-8 bytes.
Derive the count body from those same parsed values, preserving all string values,
array/item order, schema property order and explicit null/omitted distinctions.
After freezing, send the original generation bytes unchanged. Even a harmless
re-serialization is rejected; do not rebuild a request from mutable context after
a count. Keep the binding private/request-local; it is not a user/candidate ID,
telemetry attribute, stored prompt hash or authorization token.

For a tool continuation, preserve completed ordered reasoning/function/message
items, their IDs/status/phase and opaque `encrypted_content` bytes-as-text. Append
the checked local function result with the original native `call_id`; keep the
existing native/local correlation and ownership validation. No partial stream
reasoning item, summary, decryption, normalization, dropped item or caller-selected
identity is permitted. A changed result/profile/config/history requires a fresh
count, or cancellation/new explicit request; no silent constraint refresh.

A successful count creates a single-use, attempt-bound, request-memory admission
ticket. It cannot authorize a different payload, retry, semantic repair or
continuation. If a count result/settlement arrives after cancellation or deadline,
retain its accounting but discard the ticket. Restart discards all tickets/native
state; it cannot resume or regenerate a paid request. Matching local digest
proves client consistency, not provider tokenization, billing or authorization.

## 4. Exact counter and budget semantics (proposed amendment A)

Proposed replacement for the provider-call clause of contract 14, **not applied**:

> For one explicitly authorized count-aware generation/revision request, allow
> at most three generation wire attempts, three input-counting wire attempts,
> and six combined wire attempts. Every initial call, continuation, repair,
> retry, failed/cancelled/uncertain dispatch consumes its operation counter and
> the shared total before the transport await. One retry owner and at most one
> transport retry across both kinds remain. No hidden SDK/proxy retries, extra
> preflight calls or whole-request replay. Local pre-send failures may be charged
> conservatively as attempts; no counter is reset after an uncertain send.

Before counting, require capacity for both a count and its generation, remaining
token/output allowance, deadline, admission and paired dollar reservation.
Avoid a paid count that cannot possibly authorize a generation. A count failure
still consumes a count/total slot; a retry, if separately safe/permitted, consumes
another count/total slot and the shared retry. Never allocate one retry per
endpoint. Failure/ambiguity may stop earlier than the maximum.

| Sequence | Counting / generation / total | Proposed disposition |
| --- | --- | --- |
| Count → initial model → tool → count → continuation | 2 / 2 / 4 | Fits proposal; cannot fit current total three |
| Above → repair → count → repaired generation | 3 / 3 / 6 | Fits if all token/time/tool/dollar bounds remain; no fourth count or generation |
| Count failure → shared retry → count → initial model → tool → count → continuation | 3 / 2 / 5 | Fits; remaining single slot cannot buy another required pair |
| Count → ambiguous generation failure | 1 / 1 / 2 | Stop/hold; no automatic resend or whole-request replay |
| Any second retry, second repair, fifth read or seventh wire call | Irrespective of other spare counters | Reject |

The existing `BudgetLimits.provider_attempts=3` inference bound stays three.
Do **not** change it to six. Add a separate count/combined wire supervisor only
after ratification; keep fake/F1/F2 semantics and original evaluation provenance.
The current mock experiment hard-caps its actual backend requests at three.

## 5. Token, deadline and failure semantics (proposed amendment B)

Clarify that **16,000 cumulative input and 4,000 cumulative output** refer to
generation inference, including known and reserved unknown generation attempts.
A count's numerical result measures its paired inference input; it is not itself
another generation usage report. This distinction needs explicit ratification;
it is not a claim that counting is free of processing, privacy or cost.
Record count-operation measures and wire bytes separately. At most six 65,536-byte
bodies increases the potential disclosure volume relative to three; approve both
endpoint paths explicitly. Do not treat a count error as zero tokens/cost.

For each generation reserve count `N` against remaining inference input and the
bounded output allowance before send. Require `1 <= N <= remaining input` for
this nonempty schema-bearing workflow; require a strict integer result, correct
object tag, bounded JSON and no ambiguous duplicate keys. Never estimate after
count unavailability or silently fall back to local byte ratios/template output.
Count/HTTP/model metadata mismatch halts. No candidate is published by the
experiment, and existing final validation/publication/approval rules remain.

| Fault | Fail-closed requirement |
| --- | --- |
| Count 4xx/429/5xx, redirect, wrong MIME, missing/malformed/oversized result or connection loss | No generation; classify and hold any sent count liability. No count retry in the current prototype. |
| Count > remaining inference input; output exhausted; pair cannot fit wire/dollars/deadline | No generation; avoid even counting if insufficiency is already known. |
| Changed payload/schema/tool result/native state/settings | Invalidate ticket. Fresh count only within all remaining counters; otherwise stop. |
| Cancellation, deadline, emergency disable or grant/session expiry | No subsequent count/generation; cancel and await child transport, retain uncertain cost, discard ticket; no automatic replay. |
| Reported generation input differs from count, even downward | Record actual usage unchanged, freeze affected live spending/permit and halt. Lower usage is also an equivalence discrepancy, not silent success. |
| Actual input/output overruns reservation | Preserve actual overage; no clamping/refund or further calls. Client limits cannot undo server-consumed tokens/charges. |
| Model/tier/cache-price mismatch or missing usage | Stop, retain unresolved reservation and require authoritative reconciliation. |

One original **30-second** deadline covers context, counts, generation, local
reads, backoff/repair and terminalization. Counts do not get a fresh deadline or
admission slot. Existing one/principal and two/global admission lasts through
cleanup. SQL finalization may drain its existing bounded critical section, but
cannot authorize another provider call after deadline. No background recovery,
queue or durable generation state is needed.

Pre-send prevention of over-limit inference is conditional on the documented
counter being correct for the unchanged request. A deliberately wrong fixture
reporting 16,001 after a 16,000 count is retained as an overrun and fails; this is
not claimed to satisfy a retrospective 16,000 hard guarantee. Real compatibility
probes must measure count-versus-reported-input equality before broader runs.

## 6. Durable counting costs (proposed amendment C)

**Current ledger is insufficient for counting.** Migration 005 has generation
attempt ordinals 1–3, positive output caps, a generation rate version and only
generation usage settlement. Do not disguise counts as generation attempts,
invent a zero-output plan usage, decrement model tokens twice or reuse a model
idempotency key. No count-ledger migration or implementation is made in F3-03A.

Smallest future extension: retain PostgreSQL as sole authority and the existing
project-first lock order. Add an operation kind, unique opaque wire/pair identities,
separate per-kind ordinals, combined ordinal and count-rate evidence/version.
Use additive schema changes with checks/unique constraints, never rewrite 005.
Persist only bounded numeric accounting and opaque operation links; native
state/payload/tickets remain in request memory. Include count rows in all
project/grant/session/day liabilities, even after cancellation/restart.

Before the first count, atomically reserve **both** a verified maximum count
charge and the worst remaining paired generation allowance. Counting needs a
documented tariff/maximum charge independent of the as-yet-unknown `N`, or another
proved bound. Unknown price is a blocker, not a zero default. A documented zero
rate can be used only with dated endpoint/account evidence and explicit owner
approval; it does not remove network/attempt/privacy controls.

On known count success, preserve a private request-local binding and reduce the
generation dollar hold to its actual counted-input/output quote under the same
lock. A count result is **not** an invoice receipt. If actual count cost is not
known, retain the verified maximum in a distinct `responded_held`-type state.
Only an acknowledged, validated count with a pre-proved charge ceiling may let
its paired generation proceed while that hold remains. Unknown count transport,
unknown reservation COMMIT or missing count response blocks the run instead.
This distinction is a required amendment to F3-02's generation-only uncertainty
ordering, not an unannounced exception to it.

State/cost updates are exactly once per operation. Uncertain COMMIT requires
authoritative database ordering before another dispatch; crashes discard tickets
but retain holds. Same-operation retries recheck committed binding under the
project lock. Count success cannot reset generation attempts. Reconciliation
must not infer no charge from a count number, absent receipt, dashboard silence,
cancellation or elapsed time. Retain unknown holds indefinitely without adequate
evidence; do not introduce automatic refunds or another recovery service.

Recheck disabled/expiry/rate card at both send claims. At UTC midnight rebase only
the not-yet-sent generation hold against the new day's capacity; retain already
sent count liability on its actual dispatch day and in project/grant totals.
Expired sessions/new sessions cannot erase prior unknowns. No raw provider IDs
belong in ordinary traces; private receipt handling needs its own reviewed scope.

Required future native tests: concurrent mixed-kind reservations/ceilings,
paired rollback, same/different identities, lost claim/settlement acknowledgements,
in-flight COMMIT, cancellation between count/reduce/claim, successful count with
held cost, unknown count charge, restart without reusable tickets, midnight and
shutdown between the pair, actual usage mismatch and new-day/session liabilities.
F3-03A's in-memory synthetic holds prove none of those new SQL guarantees.

### Conditional numerical sensitivity — not spending authorization

Generation's dated worst case remains **$0.08 per logical request**, conditional
on the approved rates and token caps. Let `C` be a **verified** per-count maximum:

```text
logical request <= $0.08 + 3*C
ten-case smoke <= $0.80 + 30*C
68-request interactive population <= $5.44 + 204*C
```

If `C=$0.01` were verified (it is **not**), these become $0.11, $1.10 and $7.48.
The original proposed $1 smoke/$6 lifetime figures would then be insufficient.
A conditional owner-review option is **$1.25 smoke, $6.50 later evaluation,
$8 project lifetime, $2/day, $2/operator session**, with maximum ten/58 logical
requests unchanged, and no automatic transfer/top-up. These are sensitivity
numbers, not an asserted counting price, active permit or hard invoice guarantee.
If no verified `C` exists, approve **$0 live** and do not send even one count.
The prototype instead uses an explicitly invented positive **$0.001** hold/count
to demonstrate conservative handling; it is not provider pricing evidence.

## 7. Compatibility findings and remaining assumptions

- The strict schema projection remains local: root result envelope, required
  closed properties, enum/disjoint-union mapping and existing independent domain
  validation. Numeric/string/array keywords used by this project are documented
  for supported non-fine-tuned structured output. Server acceptance, schema
  compilation latency and exact model configuration are not established by mocks.
  A read-only audit measured 32 declared output object properties and a
  conservative seven-container maximum depth after reference expansion, within
  the documented size/depth limits; it did not call the provider schema compiler.
- F3-03A fixes explicit-zero cache writes with omitted TTL detail: mathematically
  both nonnegative write partitions are zero. Nonzero/missing/invalid write totals
  without adequate detail still fail closed. It does not infer free inference.
- F3-03A adds explicit JSON request content type to the existing mock adapter;
  the count prototype also pins JSON versus SSE response negotiation. Both send
  JSON bodies, while count accepts JSON and generation accepts event-stream.
  This offline protocol correction enables no real transport or new permission.
- Counting's reply has no model/tier/usage/binding receipt. Exact field copying
  cannot prove alias stability, correct server interpretation or real encrypted
  item acceptance. Pin a provider-supported identifier if available and record
  requested/effective versions; do not invent a dated snapshot.
- F3-02 deliberately rejects nonempty reasoning summaries, unsupported items,
  mixed commentary text/tool calls and malformed usage. Those stricter fail-closed
  choices may reject legitimate real responses. Before live use, review whether
  the selected model emits them; any extension needs bounded native-item fixtures,
  privacy review and authoritative validation, not silent dropping of state.
- No API-key credential or accepted offline report proves provider access, token
  rate/charge behavior, retention, latency, real tool choice or clinical quality.
  A future smoke failure is evidence to record, not permission to widen limits.
- The prototype intentionally supports a narrower subset: fixed low reasoning,
  at most 24 input items and a 1 KiB count reply. Those are experimental resource
  bounds, not newly ratified application limits or proof of all SDK input types.
  A future live integration must review full supported continuation coverage and
  bounds before activation; current production behavior is unchanged.

## 8. F3-03B pre-live authorization checklist

All entries below are **pending**. Ratifying this proposal alone does not authorize
implementation of F3-03B or a provider request. All live gates remain disabled.

- [ ] **Ratification:** owner explicitly approves amendments A–C and the exact
  contract-14/provider-safety wording; generation three, count three, total six,
  inference 16,000/4,000, one retry/repair, four reads and 30 seconds are recorded.
- [ ] **Separate implementation scope:** owner authorizes the needed offline
  count-ledger/transport integration and review before any live activation.
  Mixed-kind native fault tests and all existing regressions pass; current
  replay-only SQL mode cannot be bypassed by a key/config toggle.
- [ ] **Provider access:** owner verifies the dedicated project/account can use
  the chosen model and counting endpoint via reviewed account evidence. Do not
  add uncounted `models.list`, auth probes or SDK startup calls. No access check
  is run in F3-03A.
- [ ] **Pricing:** dated official/provider evidence establishes count tariff,
  a valid maximum `C`, generation/cache/tier prices, taxes/region treatment and
  uncertainty rules. Recalculate per-run/stage/project caps; unknown price blocks.
- [ ] **Explicit numerical spending:** owner separately approves exact USD smoke,
  later stage, lifetime, UTC daily and operator-session ceilings and count maxima.
  Conditional option above is $1.25 / $6.50 / $8 / $2 / $2 only if its assumptions
  are proved. No grants or permits have been created from those figures.
- [ ] **Privacy/data destinations:** synthetic-only corpus, versioned prompt/schema
  and bounded native state; approve both exact global endpoint paths:
  `https://api.openai.com/v1/responses/input_tokens` and
  `https://api.openai.com/v1/responses`. Verify endpoint-specific retention and
  absence/presence of count application state; no automatic `store=false`
  inheritance or US-only/ZDR claim. No real health histories or notes.
- [ ] **Transport restrictions:** one reviewed HTTP client, exact HTTPS host/paths,
  no redirects/proxies/SDK retries, no hosted tools, file URLs, alternate models,
  server conversations, background generation or automatic reconnect/replay.
  Routine tests still deny external egress and ignore real credentials.
- [ ] **Initial compatibility probe:** separately approve its exact case/call count
  and costs. Test count payload/server acceptance, exact usage equality, native
  encrypted continuation, strict output and typed failure within existing caps;
  stop on any mismatch. Do not claim these are verified before the approved probe.
- [ ] **Controlled evidence population:** frozen assets/manifests, explicit source
  labels, ten smoke case dispositions, development-only iteration and disclosed
  legacy held-out reuse. No real-model evidence is inferred from this experiment.
- [ ] **Emergency shutdown:** default-off permit with fixed project/model/endpoints,
  rate/asset versions and maximum two-hour session; recheck before every operation.
  Test persistent disable between count and generation, cancel/drain active work,
  retain pending liabilities, and document operator key revocation. Stop cannot
  undo accepted work or guarantee no later invoice.
- [ ] **Observability isolation:** all configured sinks pass canaries; bounded
  opaque correlation, counters and versions only. No prompt/workout/native state,
  credential, raw exception, private receipt ID or payload hash enters logs/spans.
  Hosted Langfuse/export/judge budgets remain independently disabled at $0.
- [ ] **Final owner go-ahead:** explicit F3-03B authorization plus spending/privacy
  permission after the preceding evidence is reviewable. Silence, a credential,
  an installed client or elapsed time is not approval.

## Owner decision record (unfilled)

| Decision | Current status |
| --- | --- |
| Ratify A: separate 3/3/6 wire policy | Pending; enforced application total remains three |
| Ratify B: inference/count accounting and binding semantics | Pending |
| Ratify C: durable counting reservations/held-success ordering | Pending; no count-ledger migration |
| Count tariff/maximum and endpoint retention evidence | Not established |
| Exact model/project, numeric grants and session dates | Not approved |
| Authorize further offline integration or F3-03B | Not authorized by F3-03A |
