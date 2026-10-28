# F3-E2 — Blank human-review materials

2026-10-27. No actual case packet, reviewer, participation or score exists.
[Blank form](templates/f3-e2-human-review-blank.json) is sealed-human-form-v1;
assignments/judgments are null/pending. Reuse existing synthetic-plan-human-rubric-v1,
DIMENSIONS, validate_ratings and agreement arithmetic, not a new quality scorer.

## Future operator procedure

- After separately authorized opening and frozen first results, preselect20 pairs
  (ten development/ten independent). Aim for two internal reviewers on at least10
  shared pairs; disclose owner-only bias. Actual reviewers require owner approval.
- Operator privately retains case/split/model/variant/reviewer linkage. Reviewers
  receive randomized opaque A/B pairs, supported preferences/permitted final outputs
  and rubric only. Balance orientation; a presentation seed is not a model seed,
  genuine blindness proof or random sample of users. Do not unblind until ratings freeze.
- Declare every reviewer/pair/variant slot before collection. Missing, pending,
  abstained and hard-failure/ineligible slots remain in the full denominator.
  Never derive the denominator from returned forms or silently discard negatives.
- Hard failures, incomplete evidence and non-plan outputs remain ineligible/null.
  A repaired final plan cannot erase F3-E1 intermediate failure. Future import must
  verify complete common-scored eligibility then reuse validate_ratings; a form's
  claimed status or a high mean cannot authorize quality eligibility.
- Reviewer tokens and collection references are assigned privately later. No default
  identity, invented timestamp, fake attestation or silence counts as a judgment.
  Approval/completion records are not independent usefulness ratings.

## Existing ordinal1–5 anchors

| Dimension | 1 | 3 | 5 |
| --- | --- | --- | --- |
| Preference adherence | Supported preferences poorly reflected | Checked preferences met, limited tailoring | Coherent choices reflecting supported preferences |
| Perceived usefulness | Hard to use as a schedule | Usable, understandable structure | Especially easy to follow within scope |
| Plan variety | Needless repetition despite alternatives | Reasonable catalog diversity | Purposeful constraint-respecting variety |

Scores2/4 are intermediate. Explanation clarity is always **N/A/null**: current
outputs have no explanation. No invented rationale, clinical safety/effectiveness
or physical exercise inference. Repetition is domain-valid, not a new hard failure.

## Missingness, disagreement and provenance

Use categorical abstention reasons (unjudgeable, insufficient_information,
conflict_of_interest), not unrestricted health narrative. Keep raw independent
ratings privately, preserve disagreements and negative scores; later adjudication
is an additional record, not replacement. Report planned/returned/eligible/rated
per-dimension denominators, missing/pending/abstained/ineligible and reviewer overlap.
Missing is neither zero nor a pass. Means/medians/wins/ties/losses, if later reported,
use genuine applicable scores and retain full task/hard-failure denominators.

`review_status_counts` counts supplied statuses against a predeclared slot schedule,
not verified judgments or quality. `rated_attested` is explicitly reported/unverified
until later evidence/provenance/eligibility checks. This helper assigns no rating.
Reuse existing agreement arithmetic only with genuine matched human labels; tests
are synthetic arithmetic, not human agreement. No judge requests/calibration now.

Real forms, hidden labels and registries stay outside developer/Git workspaces.
Reserved private paths are archive-denied defense in depth. Owner must approve
retention/deletion/backups before collection. No packet/content opener, rating
importer, actual scoring collection or network upload is implemented here.
