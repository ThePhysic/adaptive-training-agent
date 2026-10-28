"""Versioned synthetic baseline evaluation; deterministic, local, no providers."""

import hashlib
import json
from collections import Counter
from dataclasses import asdict
from itertools import product
from pathlib import Path
from typing import Literal

from pydantic import Field

from future_training.domain.baseline import TEMPLATE_VERSION, plan_week
from future_training.domain.catalog import Catalog, load_catalog
from future_training.domain.duration import DURATION_VERSION
from future_training.domain.validator import VALIDATOR_VERSION, validate_plan
from future_training.schemas import Contract, Identifier, ProfilePreferences

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "data/evaluation/v1/scenarios.jsonl"
MANIFEST = ROOT / "data/evaluation/v1/manifest.json"
RESULTS = ROOT / "data/evaluation/results/baseline-v1.json"
SCORER_VERSION = "hard-outcome-scorer-v1"


class Scenario(Contract):
    case_id: Identifier
    split: Literal["development", "held_out"]
    task: Literal["plan", "validate"]
    description: str
    profile: dict
    proposal: dict | None = None
    request_text: str = Field(default="", max_length=2048)
    choices_declined: bool = False
    expected_outcome: Literal["plan", "clarify", "abstain", "error"]
    expected_code: str
    expected_issues: list[str] = Field(default_factory=list)


def text_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def _source_hash() -> str:
    paths = [
        ROOT / "src/future_training/schemas.py",
        ROOT / "src/future_training/evaluation.py",
        *sorted((ROOT / "src/future_training/domain").glob("*.py")),
    ]
    sources = {p.relative_to(ROOT).as_posix(): text_sha256(p) for p in paths}
    return hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()


def load_scenarios(catalog: Catalog) -> tuple[dict, list[Scenario]]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest["dataset_sha256"] != text_sha256(DATASET):
        raise ValueError("dataset checksum mismatch; do not silently change a frozen corpus")
    if (
        manifest["catalog_revision"] != catalog.revision
        or manifest["catalog_sha256"] != catalog.fingerprint()
    ):
        raise ValueError("catalog differs from the frozen dataset manifest")
    cases = [
        Scenario.model_validate_json(line)
        for line in DATASET.read_text(encoding="utf-8").splitlines()
    ]
    ids = [case.case_id for case in cases]
    splits = {
        name: sorted(c.case_id for c in cases if c.split == name)
        for name in ("development", "held_out")
    }
    if len(ids) != 40 or len(set(ids)) != 40 or splits != manifest["splits"]:
        raise ValueError("invalid frozen scenario IDs or split membership")
    if [len(splits[s]) for s in ("development", "held_out")] != [24, 16]:
        raise ValueError("expected 24 development and 16 held-out cases")
    if any((c.task == "validate") != (c.proposal is not None) for c in cases):
        raise ValueError("validation scenarios require a supplied proposal")
    return manifest, cases


def catalog_coverage(catalog: Catalog) -> list[dict]:
    rows = []
    for goal, equipment, experience in product(
        ("general_strength", "general_conditioning"),
        ("bodyweight", "dumbbells_and_bodyweight"),
        ("beginner", "intermediate"),
    ):
        profile = ProfilePreferences(
            adult=True,
            goal=goal,
            equipment=equipment,
            experience=experience,
            days_per_week=2,
            session_minutes=20,
        )
        durations = []
        for minutes in (20, 30, 45):
            request = {**profile.model_dump(), "session_minutes": minutes}
            result = plan_week(request, catalog)
            durations.append(
                {
                    "preset_minutes": minutes,
                    "outcome": result.outcome,
                    "valid": result.plan is not None
                    and validate_plan(result.plan, request, catalog).valid,
                    "planned_seconds": result.plan.days[0].planned_seconds if result.plan else None,
                }
            )
        rows.append(
            {
                "goal": goal,
                "equipment": equipment,
                "experience": experience,
                "eligible_records": len(catalog.eligible(profile)),
                "presets": durations,
            }
        )
    return rows


def evaluate() -> dict:
    catalog = load_catalog()
    manifest, scenarios = load_scenarios(catalog)
    cases = []
    for scenario in scenarios:
        if scenario.task == "plan":
            result = plan_week(
                scenario.profile,
                catalog,
                request_text=scenario.request_text,
                choices_declined=scenario.choices_declined,
            )
            outcome, code, plan = result.outcome, result.code, result.plan
            issues = (
                validate_plan(plan, scenario.profile, catalog).issues if plan is not None else ()
            )
            choices = list(result.choices)
        else:
            issues = validate_plan(scenario.proposal, scenario.profile, catalog).issues
            outcome, code, plan = (
                ("error", "invalid_plan", None) if issues else ("plan", "validated", None)
            )
            choices = []
        actual_issues = sorted({i.code for i in issues})
        passed = (
            outcome == scenario.expected_outcome
            and code == scenario.expected_code
            and actual_issues == sorted(scenario.expected_issues)
            and (scenario.task != "plan" or outcome != "plan" or plan is not None)
        )
        cases.append(
            {
                "case_id": scenario.case_id,
                "split": scenario.split,
                "task": scenario.task,
                "expected_outcome": scenario.expected_outcome,
                "expected_code": scenario.expected_code,
                "outcome": outcome,
                "code": code,
                "passed": passed,
                "issues": [asdict(i) for i in issues],
                "choices": choices,
                "plan": plan.model_dump() if plan is not None else None,
            }
        )
    summary = {}
    for split in ("development", "held_out"):
        selected = [c for c in cases if c["split"] == split]
        summary[split] = {
            "passed": sum(c["passed"] for c in selected),
            "total": len(selected),
            "outcomes": dict(sorted(Counter(c["outcome"] for c in selected).items())),
        }
    return {
        "dataset_version": manifest["dataset_version"],
        "dataset_sha256": manifest["dataset_sha256"],
        "catalog_revision": catalog.revision,
        "catalog_sha256": catalog.fingerprint(),
        "template_version": TEMPLATE_VERSION,
        "validator_version": VALIDATOR_VERSION,
        "duration_version": DURATION_VERSION,
        "scorer_version": SCORER_VERSION,
        "source_sha256": _source_hash(),
        "dependency_lock_sha256": text_sha256(ROOT / "uv.lock"),
        "run_type": "deterministic_template",
        "provider": "none",
        "external_cost_usd": 0,
        "summary": summary,
        "failed_cases": [c["case_id"] for c in cases if not c["passed"]],
        "catalog_coverage": catalog_coverage(catalog),
        "cases": cases,
        "limitations": [
            "Synthetic constraint/outcome checks only; not model quality or fitness safety.",
            "Held-out is a fixed split label, not a claim of unseen developer data.",
            "Malformed tool calls, auth and provider faults remain later-unit tests.",
        ],
    }
