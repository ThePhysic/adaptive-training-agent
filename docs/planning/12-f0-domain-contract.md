# F0 contract A — Supported exercise-planning domain and duration semantics

**Status:** proposed owner sign-off, NOT clinical guidance, NOT a fitness safety certification. Normative for F1 after ratification. Supersedes any vaguer envelope text in 00/03/09. F1 must implement and test these rules rather than infer them.

## Supported envelope and matrix

Adults self-identifying as at least 18 years old, for **general wellness only**. Never solicit or interpret diagnoses, injuries, rehabilitation instructions, medications, pregnancy-specific advice, health measurements, or clinical history. Redirect requests needing such information to qualified professionals without writing a bespoke plan. No claims that passing the validator establishes physical safety, training effectiveness, or appropriateness for any individual's condition.

A profile has exactly one goal (`general_strength` or `general_conditioning`), one equipment selection (`bodyweight` or `dumbbells_and_bodyweight`), one experience band (`beginner` or `intermediate`), **2, 3, or 4** days/week, and one session duration preset (**20, 30, or 45 minutes**) applied to each day. The eight goal/equipment/experience combinations are supported **subject to having sufficient eligible catalog records**:

| Goal | Equipment selection | Experience | Exercise prescription | Template bounds |
|---|---|---|---|---|
| general_strength | bodyweight | beginner | repetitions | 2–3 sets, 6–12 reps/set, between-set rest 45/60/75/90 s |
| general_strength | bodyweight | intermediate | repetitions | 2–4 sets, 6–15 reps/set, between-set rest 30/45/60/75/90 s |
| general_strength | dumbbells_and_bodyweight | beginner | repetitions | 2–3 sets, 6–12 reps/set, between-set rest 45/60/75/90 s |
| general_strength | dumbbells_and_bodyweight | intermediate | repetitions | 2–4 sets, 6–15 reps/set, between-set rest 30/45/60/75/90 s |
| general_conditioning | bodyweight | beginner | timed | 2–3 sets, 30–75 work s/set, between-set rest 30/45/60/75/90 s |
| general_conditioning | bodyweight | intermediate | timed | 2–4 sets, 30–90 work s/set, between-set rest 30/45/60/75/90 s |
| general_conditioning | dumbbells_and_bodyweight | beginner | timed | 2–3 sets, 30–75 work s/set, between-set rest 30/45/60/75/90 s |
| general_conditioning | dumbbells_and_bodyweight | intermediate | timed | 2–4 sets, 30–90 work s/set, between-set rest 30/45/60/75/90 s |

These are **software-fixture bounds**, not universal exercise recommendations. No target heart rate, load percentages, maximal effort, guaranteed calorie burn, automatic progression, injury-specific adaptation, or claimed exercise-prescription safety. Store optional human-readable effort guidance only from reviewed catalog/template content; it is not a substitute for qualified safety review. A strength day's blocks use `repetitions`; a conditioning day's blocks use `timed`. Mixed-mode days are out of F1 scope. Each day contains **3–6 distinct exercise IDs**, from the versioned catalog, with no duplicate ID within a day; repetition across different days is permitted.

- `bodyweight` permits **only** exercises requiring `bodyweight`.
- `dumbbells_and_bodyweight` permits either `bodyweight` or `dumbbells` records. It **does not require** use of dumbbells.
- Catalog records define stable IDs, title, goal compatibility, mode, equipment requirement, supported experience, supported exclusion tags, provenance/licensing, and catalog revision. They are content, **never instructions to the agent**. Drafts reference only known catalog IDs and do not invent workouts/exercises.
- User exclusions are at most **12 catalog IDs and 8 known catalog tags**, deduplicated; an unsupported tag or an ambiguous free-text prohibition triggers a clarification or abstention, not an ignored constraint. Each generated day's IDs must avoid excluded IDs/tags.
- Requested days must be distinct and numbered 1..N. Every session is independently checked against the same preset. No requirement to maximize weekly variety; optional diversity is evaluated separately.
- If any supported input becomes infeasible due to exclusions, missing catalog coverage, or the time template, return `clarify` with explicit controllable choices or `abstain` if no compliant option exists. **Never** silently remove exclusions, change goal/equipment/experience/days/preset, fabricate an exercise, or output an invalid plan.

### Catalog coverage requirement before F1 acceptance

Curate ~20–40 original/licensed records (size is not a quota), ensuring each of the eight matrix rows has >=6 distinguishable eligible records across its supported mode/equipment/experience filters in the unexcluded seed catalog; at least one feasible plan per requested duration and row must be demonstrated by fixtures. If a row cannot satisfy this without inflating the catalog, explicitly mark that row unsupported in the matrix **before** freezing schemas; do not claim unconditional coverage. Exercise selection and proposed prescriptions require independent human review before any participant trial.

## Canonical typed prescription and units

`DayPlan` stores `day_index`, ordered `blocks[]`, and calculated `planned_seconds`. Each block stores `exercise_id`, `mode`, `sets`, `rest_between_sets_seconds`, and **exactly one** of `repetitions_per_set` (repetition mode) or `work_seconds_per_set` (timed mode). Values are integers; forbid extra fields and boolean-as-integer coercion. Set counts, repetitions, timed seconds, and rest choices must satisfy the matrix row above. The initial validator uses a **4-second-per-repetition estimation constant**, which is only a scheduling heuristic, not a prescribed tempo or guarantee of completion time. The estimated time of one block:

```
rep block:    sets * repetitions_per_set * 4
            + (sets - 1) * rest_between_sets_seconds

timed block:  sets * work_seconds_per_set
            + (sets - 1) * rest_between_sets_seconds
```

Between **different** exercise blocks use **45 seconds transition**; no transition after the last exercise. No additional intra-set rest is counted. Warm-up and cooldown are fixed planning buckets, not medically individualized exercise instructions:

| Requested preset | Warm-up | Cooldown | Target seconds | Accepted inclusive interval |
|---|---:|---:|---:|---:|
| 20 min | 180 s | 120 s | 1,200 s | [1,140, 1,260] s |
| 30 min | 240 s | 180 s | 1,800 s | [1,740, 1,860] s |
| 45 min | 300 s | 240 s | 2,700 s | [2,640, 2,760] s |

`planned_seconds = warmup_seconds + cooldown_seconds + sum(block work + block rest) + 45 * (number_of_blocks - 1)`. Reject invalid arithmetic, unsupported units and any plan outside the inclusive **±60 second** interval. Store the exact integer seconds; the UI may show rounded minutes but acceptance never uses UI rounding. Show both preset and estimated planned minutes to the user, explicitly as an estimate rather than actual exercise duration. The complete weekly plan is valid only if **every** day meets its interval and other constraints. No silently inserted filler exercise or empty-time block to hit the target.

## Hand-calculated duration boundary fixtures

**20-minute conditioning beginner**, 4 distinct bodyweight timed exercises, 3 sets each, 30 seconds rest between sets. Warm-up + cooldown = 180+120=300; transitions = 3×45=135; between-set rest = 4×(3−1)×30=240; fixed total = **675 s**. Variable work = `3 × sum(work_seconds_per_set for 4 blocks)`.

| Work seconds per set for four different exercises | Work sum | Total calculation | Expected |
|---|---:|---|---|
| [34,40,40,40] | 154 | 675 + 3×154 = **1137** | Reject: 3 s below lower limit |
| [35,40,40,40] | 155 | 675 + 3×155 = **1140** | Accept: lower boundary |
| [40,45,45,45] | 175 | 675 + 3×175 = **1200** | Accept: exact target |
| [45,50,50,50] | 195 | 675 + 3×195 = **1260** | Accept: upper boundary |
| [46,50,50,50] | 196 | 675 + 3×196 = **1263** | Reject: 3 s above upper limit |

**30-minute conditioning beginner:** 5 distinct eligible timed exercises, 3 sets×50 work seconds, 45 seconds between-set rest. `240+180 + 4×45 + 5×(3×50 + 2×45) = 420+180+1200 = **1800 s**`, valid.

**45-minute conditioning beginner:** 6 distinct eligible timed exercises, 3 sets each, between-set rest 60 s; work seconds `[65,65,65,70,70,70]`. `300+240 + 5×45 + (3×405 + 6×2×60) = 540+225+1215+720 = **2700 s**`, valid.

**Strength sanity cases:** 20-min beginner with 4 distinct eligible exercises, 3 sets×9 reps, 45 s rest gives `300 + 3×45 + 4×(3×9×4 + 2×45) = **1227 s**` (accept). 45-min beginner with 6 eligible exercises, 3 sets×12 reps, 90 s rest gives `540 + 5×45 + 6×(3×12×4 + 2×90) = **2709 s**` (accept).

**Infeasible exclusion case:** Profile `general_conditioning/bodyweight/beginner/2 days/20 min` excludes every compatible seed-catalog timed bodyweight exercise by ID. There are zero legal blocks, so the expected outcome is **clarify** (offer to remove specific exclusions or change supported constraints), not a plan. If the user declines, **abstain**. An invalid/missing exclusion tag must *not* be silently ignored. Also test fewer than three eligible distinct exercises and impossible duration under the remaining catalog.

## Ratification notes

Owner must explicitly accept/revise: eight-row matrix, bounds, duration algorithm and ±60 s inclusive tolerance, coverage rule, exclusion caps and infeasible-result policy. F1-01 schemas must derive from this contract; F1-02 implements hand-calculated boundary fixtures and feasibility checks. Before any real-user pilot, qualified content review and the separately approved access/consent safeguards remain necessary.
