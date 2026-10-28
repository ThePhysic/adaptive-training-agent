# F3-E7 — Provider account-readiness checklist

2026-10-27. **Preparation only.** No dashboard, support, public-documentation or API
request was made in E7. This is a future owner procedure, not an execution script
or permission to use an account. No API credentials are needed, requested or to be
displayed, copied or exported. All live allowances remain USD0.

## Evidence rules and safe owner preparation

Use four distinct evidence classes:

- **P — public documentation:** dated official page and applicable model/tier;
  establishes a documented promise, not account entitlement or measured behavior.
- **A — account dashboard:** dated owner observation for the exact selected
  organization/project; owner-attested unless independently reviewed later.
- **S — support/account terms:** dated written confirmation explicitly applicable
  to the selected account/endpoints; escalation alone is not an answer.
- **X — measured API behavior:** requires separate source, privacy, monetary and
  execution approval. No X check is authorized by this checklist.

Before future manual review, obtain the owner's approval for read-only website
access. Use the existing account in its normal trusted browser; navigate manually
to the [OpenAI API dashboard](https://platform.openai.com/), not ChatGPT subscription
billing or a third-party portal. No Codex/browser automation or developer-console
requests. If login or a privilege change is required, stop for the owner; do not
create keys, invite members, change permissions, add a payment method, purchase
credits, raise limits, opt in to sharing, change retention or run Playground.

Privately compare actual organization/project identifiers in the dashboard; keep
them out of shared notes/screenshots. Use opaque labels such as organization-A /
project-A only in the sanitized summary. Do not upload raw account pages, support
threads, invoices, request IDs, payment details or any API-key material. A useful
summary contains check ID, evidence class/date, matched/unmatched/unknown status,
applicable tier/settings and a redacted conclusion. Keep underlying noncredential
evidence under owner custody, outside Git, traces, public ZIPs and developer review.
No new private file or security setting is created by E7.

The settings labels below identify the required screen/field, not verified current
UI routes. If a section is absent or inaccessible, record **unknown**, request the
account owner's help or written support confirmation; do not substitute an API.

## Minimum read-only owner actions

Work in order. One session can collect multiple observations; no test purchase,
request, export, account edit or extra service is necessary.

| ID / question | Exact proposed owner action | Evidence and sufficient conclusion | Stop / what this cannot prove |
| --- | --- | --- | --- |
| A1 — identity/routing | In dashboard settings, select the intended organization. Read its General identity; open the intended existing project and its General identity. Compare exact private organization/project IDs and your role with the intended bindings | A: owner privately confirms both IDs, membership/visibility and intended project; sanitized `routing_matched` | Wrong/multiple ambiguous projects or missing access: stop. Display names alone and an available model in another project are insufficient. No API key inspection |
| A2 — model access | While still in that project, read Limits/model-permission information and the model catalogue/availability view, if offered, for exact `gpt-6.1-sol`. Record any access restriction and available documented revision | A+P, or S if dashboard does not show project-specific entitlement. Record `documented_access`, `restricted` or `unknown`; do not invent a snapshot | Do not open a paid generation session or click Run/Send. A global model catalogue or model-list response would not prove successful inference; actual schema/tool behavior is X |
| A3 — billing/credit | At organization Billing, read the current billing arrangement, usable credit balance/expiry and whether credits apply to API use in this project; inspect project budget visibility without editing it | A: privately record USD balance, expiry and exclusions as of a UTC timestamp; sanitized sufficient/insufficient/unknown for a future separately priced task | Do not add funds/card or enable auto-recharge. ChatGPT subscription/credit and AWS promotional credit do not establish API credit. Positive balance is not spend authorization; absent a count bound, sufficiency is still unknown |
| A4 — limits | Read organization Limits/usage tier and selected project Limits. Record model RPM/TPM and any other displayed request/concurrency/token restrictions, budget thresholds, monthly caps, alert/cutoff behavior and reset timezone | A+P/S: distinguish notifications/soft project budgets from a documented enforced cutoff. Record current competing usage and who controls it | Never call an alert a hard cap without evidence. Rate limits do not bound dollars. If exact limits or shared-project contention are unknown, no probe window is ready. No limit-increase request |
| A5 — applicable generation/cache price | Read the official model/pricing/cache references below; compare any account pricing/contract and selected Standard/default tier. Check currency, effective date, cache read/write TTL classes, minimums, tax/FX/surcharges and tier fallback behavior | P+A, S for account-specific differences. A dated applicable rate card, with explicit unsupported classes, is needed | No published or dashboard price is inferred for counting. Do not silently select another tier/model or use a discount to shrink conservative liability |
| A6 — counting billing | Inspect any existing written support response/account pricing terms for exact POST `/v1/responses/input_tokens`; if insufficient, prepare the question set below for a separately approved owner inquiry | S or explicit applicable P/account documentation: independently bounded maximum charge before sending, including errors and unknown outcomes | A token count18, no invoice line, support escalation, no published tariff or a successful count does not mean free. Unknown maximum keeps every live financial gate closed |
| A7 — data/retention | Read organization Data controls and applicable project overrides, including data sharing/training opt-ins, abuse monitoring, application-state retention, cache processing, processing location and any special terms. Compare the exact counting and Responses endpoint policies | A+P/S: owner records applicable defaults/overrides and policy date. Do not assume ZDR/MAM entitlement; verify any claimed exception independently | No toggles. `store:false` affects application storage behavior, not an abuse-monitoring opt-out. Unknown counting retention, unintended sharing/residency or broader terms than conditionally accepted: privacy approval remains blocked |
| A8 — request compatibility | Compare the exact existing public config/tool/output/count projection with current official model, Responses, counting, streaming, schema, reasoning and caching references; request S clarification for any contradiction | P/S: documented compatibility or an explicit unresolved item; retain requested/effective alias uncertainty. See fixed settings below | Actual compilation, automatic tool choice, encrypted continuation, count-to-usage equality, returned tier/usage and30s latency require X. Never use an API call as a read-only documentation check |
| A9 — reconciliation | Read Usage and Billing views for the same organization/project. Check available filters, reporting delay/timezone, token/cache/cost categories, count visibility and whether charges are project/operation-specific. Read available invoice/usage descriptions; no download/export needed | A+S: identify who can reconcile, evidence delay/granularity and how an unknown count charge could be authoritatively resolved | Dashboard silence/aggregate zero is not proof of a free or unsent operation. If per-attempt resolution is unavailable, retain conservative holds; do not build a billing API integration or use an admin API key |

## Counting-specific questions for a later owner support inquiry

Do not send a message in this milestone. Reuse the pending inquiry rather than
create duplicate cases. The owner can privately identify the account to support
through its authenticated channel; never send credentials or case contents.

1. For the exact project/model and `/v1/responses/input_tokens`, what billing
   units/rates/minimums apply, and what **maximum charge before sending** covers
   every permitted <=65,536-byte count, tools/schemas and encrypted continuation?
   Cover success, invalid input,429/5xx, interrupted response and cancellation.
   Does counting cause billable inference/cache writes? If free, explicitly
   confirm scope, exceptions and effective dates rather than infer zero.
2. Which training/data-sharing, abuse-monitoring, application/cache retention,
   deletion and processing-region rules apply to this endpoint and this account?
   Does it inherit Responses terms, with what exceptions? Counting does not send
   `store:false`; generation's setting cannot establish counting retention.
3. How are count charges/unknown outcomes exposed in usage/invoices, at what
   granularity and delay? Which evidence could reconcile one held liability?
   Which account limits actually stop spend rather than alert?

A reply must establish an applicable conservative bound and retention treatment;
it need not disclose an internal provider implementation. Missing/contradictory
answers remain unresolved. No paid count is permitted to discover its own tariff.

## Fixed proposed request and public-source assumptions

The F3-E7 owner supplied the following **provisional public facts**, consistent
with earlier repository assumptions: `gpt-6.1-sol`; Standard USD/million tokens
input2, cached input0.10, cache writes2.50, output10; Responses/tool/structured
output and low reasoning support; documented counting; abuse-monitoring retention
may include content. These were **not fetched or independently reverified in E7**.
The generic cache-write figure is not approval for all TTLs/tier classes. Existing
code admits only its reviewed30m class and rejects/unprices unsupported writes.

Official references for the owner's later public review (links copied from the
historical [F3-03C source review](f3-03c-pre-live-review.md), dated2026-10-24;
availability/currentness of these pages is unverified today):

- [Model](https://developers.openai.com/api/docs/models/gpt-6.1-sol),
  [pricing](https://developers.openai.com/api/docs/pricing),
  [caching](https://developers.openai.com/api/docs/guides/prompt-caching).
- [Responses](https://developers.openai.com/api/reference/python/resources/responses/methods/create),
  [tools](https://developers.openai.com/api/docs/guides/function-calling),
  [structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs),
  [streaming](https://developers.openai.com/api/docs/guides/streaming-responses),
  [reasoning](https://developers.openai.com/api/docs/guides/reasoning).
- [Counting guide](https://developers.openai.com/api/docs/guides/token-counting),
  [count reference](https://developers.openai.com/api/reference/python/resources/responses/subresources/input_tokens/methods/count),
  [data controls](https://developers.openai.com/api/docs/guides/your-data).

Recheck against [config](../../data/experiments/f3-02/v1/config.json) and
[provider safety](../../contracts/provider-safety.md): default/Standard, low
reasoning, auto tool choice, serial calls, strict tool/output schemas, streaming,
store/background false, implicit30m cache; temperature/seed absent. Fresh count
for each generation/continuation/repair, exact count-to-generation input binding,
bounded encrypted native items, no conversation/previous_response_id references or
hosted tools. Only search_exercises/get_user_preferences may read; no writes.
Documented broader API fields are not permission to use them.

Future permitted data destinations would be exactly HTTPS/443 POST
`https://api.openai.com:443/v1/responses/input_tokens` and
`https://api.openai.com:443/v1/responses`; neither is authorized now. Synthetic
preferences, prompt/schema, catalog read results and bounded native continuation
can reveal evaluation inputs. No genuine curator/commitment/reviewer metadata or
account identifiers belong in model payloads; authentication/routing remain
private control-plane data. Ordinary telemetry stays metadata-only/local; no
Langfuse export, AWS destination, playground or external evaluation service.

## Readiness matrix

V = verified **repository fact only**; C = conditional preference/documentary
assumption; U = unresolved. No row is verified live account/model/billing evidence.

| Item | Status / evidence now | What remains before progression |
| --- | --- | --- |
| D8/D9,20-pair priority | C: owner preference recorded, selection unchanged | Final scope approval; no full69-task acceptance claim |
| D7, standard synthetic retention | C: owner preference, account conditions unresolved | A7 and counting-specific S evidence, then final privacy approval |
| Model/prices/features | C: supplied public assumptions and dated repository references | A2/A5/A8, exact account/model/tier/version compatibility |
| Organization/project, billing/credit/limits | U: no E7 account access or attestation | A1/A3/A4/A9; credit is not authority |
| Count maximum/retention/reconciliation | U, blocking any live call | A6/A7/A9 and applicable written terms; escalation/count18 are insufficient |
| Admission/accounting/isolation | V offline: E6 tested fixed public-control path; both hard denials remain | Source release and per-case authority decisions; no arbitrary independent-case execution |
| Actual provider schema/stream/usage/tool behavior | U; only synthetic fixtures established | Separately authorized single compatibility logical request after all earlier gates |
| Final freeze/genuine custody/opening | U, denied | Independent human and separate source/freeze/creation/registration/opening approvals |
| Study/human judgments | U, not performed | Separate execution limits and real reviewer allocation/collection; no fake quality evidence |

## Financial and authorization stop conditions

Retain30s,16,000 input/4,000 output total,2,000 output/attempt,3 counts/3
generations/6 combined,4 read dispatches, existing retry/repair/concurrency caps.
No compatibility hypothesis permits increasing limits. Count/usage mismatch,
unexpected model/tier/cache class, unknown liability, timeout or SQL uncertainty
retains holds and stops; no automatic request replay or top-up.

At the **unverified-for-live** recorded rates only, let Cµ be an independently
verified maximum count charge in integer microdollars. Conditional planning bound
per logical request remains `80,002 + 3*Cµ`;20 model tasks would be
`1,600,040 + 60*Cµ`, or with a separate smoke `1,680,042 + 63*Cµ`.
Templates require no provider request. These are not approved limits, quotations
or invoice caps; current ceilings are0. Unknown Cµ makes a positive proposal
unready. If rates/terms differ, return for review before arithmetic/authority
changes. Taxes/FX/surcharges and competing usage need explicit treatment later.
The existing CountBound requires a positive integer ceiling: even an explicit
provider confirmation of zero tariff would require review of a conservative
positive reservation or separately amended representation. Do not inject a zero
quote or reinterpret simulation authority as money.

**Recommended next authorization:** owner-only manual read-only review A1–A9's
dashboard/document portions, returning a redacted dated checklist. Support contact
requires its own owner decision; API portions remain deferred, not bundled. Stop
on a required edit/payment/key/API test, missing privilege, unresolved identity or
conflicting terms. Review the evidence before proposing source changes, numerical
money or a single compatibility probe. No freeze, curator appointment or genuine
study permission follows from completing the checklist.
