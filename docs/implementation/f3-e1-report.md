# F3-E1 — Offline counted-probe evidence rehearsal

2026-10-27. **Offline implementation complete; stop for independent review.**
No real AWS/provider/authentication request, hosted export, monetary authority,
candidate/approval write, infrastructure change, installation, commit or push.
Both independent live denials and the original uncertain IAM attempt are unchanged.

`experiments/counted_probe.py` connects the actual fixed `SingleProbe` to the
existing `Observation` and `score()` contracts. It observes only owned session
instances and calls the original probe once. Normalized responses supply proposal
checks and tool intent; the Agent's subsequent continuation context supplies the
actually dispatched/checked tool results. Missing evidence blocks hard pass.
The Agent's repair context preserves semantic rejection beyond JSON/schema checks.

Accounting is a bounded, repeatable-read **READ ONLY** query of the existing
simulation authority namespace. It never issues authority, claims, settles,
reconciles or clears a fence. Successful counts retain their unknown-charge holds.
Unresolved commit fences make totals unknown; committed row observations remain
distinct from unresolved totals. No provider invoice is inferred.

The adapter lives outside `src`, whose files are all fingerprinted by the accepted
150-case evaluation. No production source, provider hook API, evaluator, schema,
dependency, transport, migration or historical snapshot was changed. The existing
common scorer remains the only scorer. There is no CLI or live activation path.

| Native PostgreSQL + controlled MockTransport example | Observed result |
| --- | --- |
| [Successful tool/continuation](evidence/f3-e1-success.json) | 2 counts/2 generations/4 combined; common hard and handling pass; 5,540 known synthetic microdollars +2,000 held; actual total unknown |
| [Repair hard failure](evidence/f3-e1-repair-failure.json) | 3/3/6; intermediate domain failure/Agent rejection retained despite final valid plan; handling passes, hard/quality eligibility fail; 8,310 known +3,000 held |
| [Cancellation/incomplete](evidence/f3-e1-cancelled-incomplete.json) | No invented terminal Observation or score; SQL records one count claim and no generation claim; 1,000 retained hold, actual total unknown |

The repair example has complete evidence of a hard failure; it is not a passing
model trial. Cancellation has incomplete evidence. All examples are
`replay`/`authority_fixture`, one fixed developer-exposed case, zero actual model,
human or hosted evidence. Scores remain null for quality; no fitness claims.
Public JSON files are metadata-only projections. Full bounded synthetic packets
remain under ignored `.cache/f3-e1/evidence/`, labelled for 14-day local retention
and explicit owner review/deletion, never automatic cleanup or telemetry export.

Fresh validation: **341 existing routine provider/scorer/privacy/transport tests**;
**152 native SQL tests** (50 new at that revision +102 existing); final expanded
new suite **51/51**. Nonduplicated selected denominator **494**. Mock and actual
loopback TLS positive/repair cases have matching non-timing verdicts. Frozen
baseline 40/40, 150 expected software dispositions, contract drift, syntax, lint
and format checks pass. These are selected tests, not a fresh full application,
frontend or installed-browser run.

See the [structured handoff](f3-e1-handoff.md) for exact commands, adversarial
findings, design limits and archive verification. Live compatibility, counting
pricing/retention, owner approvals, real-model quality/human scoring, hosted
integration and other milestones remain blocked or separately gated.
