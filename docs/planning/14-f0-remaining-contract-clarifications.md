# F0 contract C — Typed stream outcomes, budgets and evidence boundaries

**Status:** proposed owner sign-off. Closes C3/C4 and makes C5 normative via `13`. No new infrastructure or frameworks.

## Terminal SSE outcome

A versioned stream envelope contains `schema_version`, `request_id`, monotonic `sequence`, `event_type`, typed `payload`. Allowed events: `status`, at most one `draft`, `error`, and exactly one terminal `done` **if transport permits**; metadata-only heartbeats are optional. Only a **validated** plan is emitted in `draft`. `done.payload` is a discriminated union with `outcome` of `plan | clarify | abstain | error`:

- `plan`: requires one prior validated `draft` **preview**, a live owned immutable candidate ID/revision/hash conveyed **only in `done.payload`**, and no prior `error`. The earlier `draft` does not expose an approval-addressable candidate ID/token.
- `clarify`: no draft/approvable candidate; bounded missing/conflicting fields and plain-language supported choices.
- `abstain`: no draft/approvable candidate; sanitized general reason and supported next step (e.g. professional advice for out-of-scope medical request).
- `error`: requires sanitized typed `error` event when headers are already sent; no draft remains approvable; bounded code/retryability, no raw provider/user data.

Authorization/validation errors before stream headers use ordinary typed HTTP error responses. After headers, terminal error and `done(outcome=error)` are emitted when transport permits. For a broken connection, `done` may be absent; **unexpected EOF without validated terminal done is incomplete even if a draft was received**. Client clears/disables approval on incomplete EOF or client abort, with no automatic reconnection/replay. The server publishes an approval-eligible candidate only at successful terminalization, immediately before yielding `done(plan)`. A stream that fails before terminalization must not publish an approvable candidate. If `done` was emitted by the server but not actually received by the browser, the server cannot guarantee receipt; its now-orphaned candidate expires normally and the UI cannot approve without the opaque identity delivered only in `done`. This is an explicit transport limitation, not a guarantee of client receipt. `done` indicates response completion **not** approval. Tests cover four outcomes plus EOF before `draft`, between `draft` and `done`, after `done`, malformed framing, chunk boundaries and cancellation.

## Budget scope and retry semantics

**Owner-ratified F3-03B offline exception (amendments A–C of document 18):**
the explicit count-aware mocked Responses pathway permits at most **three
generation attempts, three counting attempts and six combined outbound claims**.
Each generation needs a fresh count of its immutable payload. The 16,000 input /
4,000 output limits apply cumulatively to inference, including unknown attempts;
count results are admission measures, not additional inference usage. Deadline,
four reads, one shared retry, one repair and concurrency caps below are unchanged.
`BudgetLimits.provider_attempts` remains three. Failed/cancelled/uncertain claims
consume their kind and combined counters; no hidden retry or replay is permitted.
This exception authorizes no external request or money. Fake and legacy uncounted
replay semantics remain unchanged. Financial ordering and implementation details:
[provider safety](../../contracts/provider-safety.md). Historical F1 examples below
continue describing generation attempts; the original total-three rule applies
to pathways without this explicitly ratified counting exception.

- **No automatic generation retry** means no replay of the whole generation request after SSE disconnect and no browser auto-reconnect. User-triggered new generation/revision is a new bounded request and **does not** resurrect the incomplete request.
- For **each** request-scoped generation or explicit revision: one **30-second** wall-clock deadline; **≤4 read-tool dispatches**; **≤3 outbound model-provider requests in total** (each initial call, tool-result continuation, structured repair and transport retry counts as one); **≤1 semantic repair**; **≤1 transport retry**; cumulative **≤16,000 input** and **≤4,000 output** tokens across successes, failed, cancelled and uncertain attempts; **≤1 concurrent generation per synthetic principal** and **≤2 globally**, enforced even by fakes.
- The maximum 3 attempts is a hard global cap, **not** three per step. Example: initial call → model-selected catalog tool → continuation → repair = **3 provider attempts**; no fourth transport retry. Example: initial failed transport → retry → continuation = **3 attempts**; no fourth repair. Tool dispatches and provider attempts are different counters, both enforced. Uncounted SDK retries are forbidden: disable them or account for every attempt under the one retry owner.
- Explicit revision starts a fresh **per-request** attempt/tool/token/deadline budget; the **single successful revision per candidate lineage** is independently enforced by contract `13`. The short revision reservation prevents unlimited concurrent revisions. New candidate IDs do not reset lineage revision count.
- Credentials, environment variables, or SDK installation alone **never** enable provider/live mode. F1 provider is fake-only with denied external egress; a later live adapter needs separate named provider, destination/privacy review, **numeric dollar ceiling** and durable concurrency-safe reservations including unknown usage before the first call. Judge, tracing export, AWS and participants each remain separately gated.
- F1 metrics describe fake/local behavior only; F3 live data, human ratings and judge results require actual authorized experiments. A mock tool envelope cannot prove model-selected tool choices, real token charges or useful personalization.

## Contract/evidence tests

Use fake time and barriers: continuation+repair+retry attempt exhaustion; tool cap vs provider cap; cancellation cleanup; fake concurrency limits; same user starting repeated requests; a failing revision followed by retry vs successful revision cap; credentials injected with live mode disabled; actual egress blocked in tests; all four terminal outcomes; `draft` followed by lost `done`; and approved plan readback only after explicit approval. No new run manager, SSE replay server or permanent external API is introduced to satisfy these tests.
