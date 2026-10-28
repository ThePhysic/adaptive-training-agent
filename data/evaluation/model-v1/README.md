# Offline model evaluation v1

New synthetic assets, separate from immutable [F1 v1](../v1/manifest.json).
`scenarios.jsonl` freezes 50 inputs, per-variant expected outcomes and read-tool
requirements before scoring. `outputs.jsonl` contains authored, template-derived
structured fixtures, including one deliberately invalid plan. These are **not
provider captures**. Native framing reuses existing F3-02 protocol fixtures.

Forty development cases comprise 24 matrix/preset cases and 16 controls. Ten
additional distinct feasible comparison inputs are **developer-exposed candidates**,
not a sealed/unseen holdout. Exposure and exclusions are explicit in the manifest.
Forty-one rows are model-input tasks; nine are controlled provider-response/fault
fixtures, excluded from any future live-input denominator.
Human/judge scores have not been collected. Explanation clarity is N/A.

`offline-scores.json` records all 150 deterministic per-case dispositions, hard
failures, output snapshots and provenance. Expected handling is separate from
hard correctness; deliberately invalid fixtures cannot receive quality ratings.
The template is not subjected to provider fault injection. Cross-variant quality
comparison is restricted to the 34 matched normal plan cases.

The accepted F3-04A `offline-scores.json` is preserved unchanged. Current source
provenance after F3-04B's provider changes remains in `offline-scores-f3-04b.json`.
F3-04C adds `offline-scores-f3-04c.json`; F3-05A's current reference is described below. Tests
require its entire case/summary content to equal the historical reference.
Inputs, expected outcomes, scorer and human review design are unchanged.

F3-05A preserves every earlier snapshot and adds current-source
`offline-scores-f3-05a.json`. All150 case/summary results still match. Optional
tracing adds separate case links; the Langfuse projection reuses these hard
verdicts and preserves null human/judge/quality scores. See
[specification21](../../../docs/planning/21-f3-langfuse-offline-integration.md).

F4-01 preserves those snapshots and adds `offline-scores-f4-01.json` as the
current-source reference after the thin-runtime import correction. All 150
case/summary outcomes remain equal; no inputs, expectations, split/exposure labels,
scorer or human/judge results change.

```powershell
.venv/Scripts/python.exe scripts/prepare_model_evaluation.py --check
.venv/Scripts/python.exe scripts/evaluate_models.py --check
# New local timestamped evidence and blank practice packets (no tracked writes):
.venv/Scripts/python.exe scripts/evaluate_models.py
```

Detailed artifacts stay under ignored `.cache/f3-04a/<UTC-run>/`. Only
`reviewer/` is intended for a future internal reviewer; `private/` holds the
variant key and an empty reviewer registry. The offline packets compare template
with authored replay and are **practice**, not actual-model/human evidence.
The explicit `--record-offline` option regenerates this new suite's synthetic
regression artifact after a reviewed change. It never modifies frozen F1 data.
Neither script has a live executor, credentials option, financial authority,
database write or hosted destination. See [protocol 20](../../../docs/planning/20-f3-model-evaluation-protocol.md).
