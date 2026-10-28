"""Blank blinded review packets and scoring checks; no invented human judgments."""

import random
from statistics import mean

DIMENSIONS = ("preference_adherence", "perceived_usefulness", "plan_variety")
RUBRIC_VERSION = "synthetic-plan-human-rubric-v1"
REVIEW_SEED = 30401


def review_packet(report, cases, *, seed=REVIEW_SEED):
    """Seed controls presentation only, never provider sampling or case selection."""
    selected = [c for c in cases if c.fixture == "normal" and c.case_id.startswith("ME-D")][:10]
    selected += [c for c in cases if c.split == "comparison_candidate"]
    if len(selected) != 20:
        raise ValueError("The predeclared twenty-pair review population is incomplete")
    rng = random.Random(seed)
    rng.shuffle(selected)
    orientations = [False, True] * 10
    rng.shuffle(orientations)
    packet, key, forms = [], [], []
    for number, (case, flipped) in enumerate(zip(selected, orientations, strict=True), 1):
        variants = ["template", "replay"]
        if flipped:
            variants.reverse()
        pair_id = f"pair-{number:02}"
        items = {}
        for label, source in zip(("A", "B"), variants, strict=True):
            result = next(
                r for r in report["cases"] if (r["case_id"], r["source"]) == (case.case_id, source)
            )
            items[label] = {
                "plan": result["output"]["plan"] if result["quality_eligible"] else None,
                "scorable": result["quality_eligible"],
                "explanation": None,
            }
            forms.append(
                {
                    "pair_id": pair_id,
                    "label": label,
                    "reviewer_token": None,
                    "evidence_type": "human_pending_not_collected",
                    "ratings": dict.fromkeys(DIMENSIONS),
                    "explanation_clarity": None,
                }
            )
        packet.append(
            {"pair_id": pair_id, "preferences": case.profile.model_dump(), "variants": items}
        )
        key.append(
            {
                "pair_id": pair_id,
                "case_id": case.case_id,
                "split": case.split,
                "A": variants[0],
                "B": variants[1],
            }
        )
    return {
        "reviewer/packet.json": {
            "rubric": RUBRIC_VERSION,
            "pairs": packet,
            "stage": "offline_practice_not_real_model_comparison",
        },
        "reviewer/blank-scores.json": forms,
        "private/blinding-key.json": {"seed": seed, "mapping": key},
        "private/reviewer-registry.json": {"reviewers": [], "status": "not_recruited"},
    }


def validate_ratings(result, ratings):
    """One future import check; invalid/error results can never earn quality scores."""
    if not result["hard_passed"] or not result["quality_eligible"]:
        raise ValueError("Hard failures and non-plan outcomes are not quality-scorable")
    if not isinstance(ratings, dict) or set(ratings) != {*DIMENSIONS, "explanation_clarity"}:
        raise ValueError("Exact rubric dimensions required")
    if ratings["explanation_clarity"] is not None:
        raise ValueError("No explanation content exists; clarity must be N/A")
    if any(type(ratings[k]) is not int or not 1 <= ratings[k] <= 5 for k in DIMENSIONS):
        raise ValueError("Observed integer ratings 1..5 required; pending is not a score")
    return dict(ratings)


def agreement(human, judge):
    """Numeric checks for FUTURE calibration, also usable for two human reviewers.

    Caller must supply genuinely collected paired ratings. Unit tests use marked
    synthetic labels. Empty/missing data never becomes a perfect agreement.
    """
    if not human or len(human) != len(judge):
        raise ValueError("Nonempty matched ratings required")
    if any(type(v) is not int or not 1 <= v <= 5 for v in [*human, *judge]):
        raise ValueError("Integer ratings 1..5 required")
    deltas = [j - h for h, j in zip(human, judge, strict=True)]
    return {
        "n": len(deltas),
        "exact_fraction": mean(d == 0 for d in deltas),
        "within_one_fraction": mean(abs(d) <= 1 for d in deltas),
        "mean_absolute_error": mean(abs(d) for d in deltas),
        "signed_bias": mean(deltas),
        "disagreement_indices": [i for i, d in enumerate(deltas) if abs(d) > 1],
    }
