# Synthetic baseline corpus v1

`v1/scenarios.jsonl` contains exactly 40 hand-authored structured scenarios:
24 development, 16 held out. `v1/manifest.json` freezes IDs, split membership,
normalized UTF-8 dataset SHA-256 and canonical catalog fingerprint. No real user
data, model-generated labels, model calls or API faults are represented as real
observations. The split is fixed and inspectable, not a claim that developers
have never read the held-out cases.

There are 24 positive row/preset scenarios: all eight goal/equipment/experience
combinations at 20/30/45 minutes. Each row contributes two development presets
and one rotating held-out preset. Weekly lengths cover 2/3/4 sessions. Sixteen
negative scenarios add eight cases per split. These cover unknown exclusions,
exhausted/fewer-than-three records, impossible duration, missing/unsupported
preferences, uninterpreted injection/medical text, declined changes and supplied
invalid proposals. The nine hand-calculated duration examples and detailed
schema/constraint mutations are additional unit tests, not extra corpus cases.

Cases declare expected outcome/code and, for invalid supplied plans, exact issue
code sets. Expected outcomes are independent of a particular template workout.
The four `validate` cases contain manually specified plans from contract-12
arithmetic, rather than corrupting whichever output the template currently emits.
They are rejection checks, not failed generation requests. The evaluator does not
pretend to exercise model tools, identity isolation or provider faults; those
remain later work units.

## Run and inspect

From the repository root, with the accepted F1-01 environment installed:

```powershell
.venv/Scripts/python.exe scripts/evaluate_baseline.py
.venv/Scripts/python.exe scripts/evaluate_baseline.py --check
```

The first command writes `results/baseline-v1.json`; `--check` verifies without
writing. A stale artifact, unexpected outcome, hard-check failure or inadequate
matrix coverage exits nonzero. Reports include every case, complete synthetic
plans, clarification choices, rejection locations/codes, split denominators,
eight-row coverage, catalog/data/source/dependency fingerprints and rule/scorer
versions. No live clock, timing samples, random seed or Git working-tree metadata
changes report bytes. UTF-8 line endings are normalized for hash portability.

The 40-case pass count measures expected software outcomes. A valid negative
rejection counts as expected behavior, not as a generated plan. Separately inspect
all generated plans through the independent validator. No subjective quality,
human/judge agreement, clinical safety, fitness effectiveness or live LLM metric
is established. Do not increase the success denominator with separate coverage
or API tests. Do not tune on held-out results and still claim untouched holdout.

To evolve the corpus or catalog, create a reviewed versioned revision and update
the manifest intentionally. Do not change expected outcomes to make a regression
green. Runtime source changes make the recorded artifact stale until an explicit
rerun; frozen expected outcomes still decide whether that rerun passes.
