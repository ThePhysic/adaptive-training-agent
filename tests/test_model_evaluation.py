"""Offline software/evaluator tests. No genuine human or model quality labels."""

import asyncio
import copy
import json
import logging
from collections import Counter

import pytest
from pydantic import ValidationError
from test_observability import console  # noqa: F401 -- shared safe-sink fixture

from future_training.agent.protocol import ToolCall, canonical
from future_training.domain.catalog import load_catalog
from future_training.domain.validator import validate_plan
from future_training.errors import ServiceError
from future_training.evaluation import ROOT, load_scenarios
from future_training.experiments.model_eval_assets import (
    DIRECTORY,
    compatible_score_reference,
    generated_assets,
)
from future_training.experiments.model_evaluation import (
    SyntheticProfile,
    evaluate,
    load_suite,
    reproducible,
    run_case,
)
from future_training.experiments.model_review import (
    DIMENSIONS,
    agreement,
    review_packet,
    validate_ratings,
)
from future_training.experiments.model_scoring import Observation, check_call, score
from future_training.identity import Principal
from future_training.observability import LocalTracer, Span

CATALOG = load_catalog()
MANIFEST, CASES, OUTPUTS = load_suite()


@pytest.fixture(scope="module")
def report():
    return asyncio.run(evaluate(), loop_factory=asyncio.SelectorEventLoop)


@pytest.mark.parametrize("case_id", [c.case_id for c in CASES])
def test_each_case_across_all_offline_variants(report, case_id):
    case = next(c for c in CASES if c.case_id == case_id)
    rows = [r for r in report["cases"] if r["case_id"] == case_id]
    assert {r["source"] for r in rows} == {"template", "fake", "replay"}
    for row in rows:
        assert row["handling_passed"], row
        assert row["quality_scores"] is None
        assert row["actual"] == case.expected[row["source"]]
        assert row["external_cost_usd"] == 0 and row["financial_authority"] == "none"
        if row["actual"] == "plan":
            assert validate_plan(row["output"]["plan"], case.profile, CATALOG).valid
        if not row["hard_passed"]:
            assert row["failures"] and not row["quality_eligible"]
        if row["source"] != "template":
            assert row["counts"]["provider_requests"] <= 3
            assert row["counts"]["tool_dispatches"] <= 4


def test_exact_dispositions_and_deliberate_failures(report):
    assert report["summary"]["template"]["hard_passed"] == 50
    for source in ("fake", "replay"):
        summary = report["summary"][source]
        assert summary["handling_passed"] == 50 and summary["hard_passed"] == 44
        assert summary["outcomes"] == {"plan": 34, "clarify": 6, "abstain": 5, "error": 5}
        assert len(summary["failures"]) == 6
    assert all(s["quality_eligible"] == 34 for s in report["summary"].values())


def test_coverage_splits_exposure_and_exact_new_inputs():
    assert Counter(c.split for c in CASES) == {"development": 40, "comparison_candidate": 10}
    assert MANIFEST["genuinely_unseen_holdout"] == 0
    assert Counter(c.eligibility for c in CASES) == {
        "saved_profile_agent": 41,
        "controlled_provider_fixture": 9,
    }
    assert all(c.exposure == "developer_exposed_not_blind" for c in CASES)
    matrix = [c for c in CASES if c.case_id.startswith("ME-D")]
    assert (
        len(
            {
                (
                    c.profile.goal,
                    c.profile.equipment,
                    c.profile.experience,
                    c.profile.session_minutes,
                )
                for c in matrix
            }
        )
        == 24
    )
    assert {c.profile.days_per_week for c in matrix} == {2, 3, 4}
    candidates = [c for c in CASES if c.split == "comparison_candidate"]
    assert (
        len({(c.profile.goal, c.profile.equipment, c.profile.experience) for c in candidates}) == 8
    )
    assert any(c.profile.excluded_tags for c in candidates)
    assert all(c.profile.excluded_ids for c in candidates)
    old = load_scenarios(CATALOG)[1]
    for c in candidates:
        assert all(c.profile.model_dump() != _normalized(x.profile) for x in old)
        assert all(c.profile != x.profile for x in CASES if x.split == "development")


def _normalized(value):
    from future_training.schemas import ProfilePreferences

    try:
        return ProfilePreferences.model_validate(value).model_dump()
    except ValidationError:
        return None


def test_assets_scores_and_legacy_mapping_frozen(report):
    assert all(
        (DIRECTORY / name).read_text(encoding="utf-8") == content
        for name, content in generated_assets().items()
    )
    expected = compatible_score_reference()
    assert reproducible(report) == expected
    historical = json.loads((DIRECTORY / "offline-scores.json").read_text(encoding="utf-8"))
    assert expected["cases"] == historical["cases"]
    assert expected["summary"] == historical["summary"]
    eligibility = report["manifest"]["legacy_eligibility"]
    assert Counter(r["eligibility"] for r in eligibility) == {
        "agent_reachable": 28,
        "validator_only": 4,
        "profile_rejected": 4,
        "save_rejected": 2,
        "decline_flag_not_in_agent_api": 2,
    }
    assert report["manifest"]["live_enabled"] is False


def test_future_live_observation_uses_identical_scorer_without_execution():
    # Unit observation only; never a live output or execution claim.
    case = CASES[0]
    tool = dict(
        name="search_exercises",
        arguments_valid=True,
        authorized=True,
        result_valid=True,
        status="ok",
    )
    counts = {
        **observation(case).counts,
        "provider_requests": 2,
        "count_requests": 2,
        "wire_requests": 4,
        "tool_dispatches": 1,
    }
    observed = observation(case, source="live", counts=counts, tools=[tool])
    result = score(case, observed, CATALOG)
    assert result["hard_passed"] and result["quality_scores"] is None


@pytest.mark.parametrize("mutation", ["checksum", "split", "legacy", "prior"])
def test_changed_evaluation_assets_fail_closed(tmp_path, monkeypatch, mutation):
    from future_training.experiments import model_evaluation

    manifest = copy.deepcopy(MANIFEST)
    if mutation == "split":
        manifest["splits"]["comparison_candidate"] = []
    elif mutation == "legacy":
        manifest["legacy_sha256"] = "0" * 64
    elif mutation == "prior":
        manifest["prior_fixture_sha256"].pop("plan.json")
    for name in ("scenarios.jsonl", "outputs.jsonl"):
        value = (DIRECTORY / name).read_text(encoding="utf-8")
        (tmp_path / name).write_text(
            value + (" " if mutation == "checksum" else ""), encoding="utf-8"
        )
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(model_evaluation, "DIRECTORY", tmp_path)
    with pytest.raises(ValueError):
        load_suite()


def observation(case, **changes):
    fields = dict(
        source="template",
        output_json=canonical(OUTPUTS[case.case_id]).decode(),
        terminal_state="ready_unpublished",
        counts=dict(
            provider_requests=0,
            count_requests=0,
            wire_requests=0,
            tool_dispatches=0,
            semantic_repairs=0,
            transport_retries=0,
            input_tokens=0,
            output_tokens=0,
        ),
    )
    fields.update(changes)
    return Observation(**fields)


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown_id",
        "duration",
        "constraint",
        "extra",
        "candidate",
        "EOF",
        "publish",
        "budget",
        "counts",
        "duplicate_json",
        "repaired_bad_proposal",
        "missing_tool",
    ],
)
def test_failures_cannot_receive_quality_scores(mutation):
    case = CASES[0]
    output = copy.deepcopy(OUTPUTS[case.case_id])
    changes = {}
    if mutation == "unknown_id":
        output["plan"]["days"][0]["blocks"][0]["exercise_id"] = "unknown_exercise"
    elif mutation == "duration":
        output["plan"]["days"][0]["planned_seconds"] += 1
    elif mutation == "constraint":
        output["plan"]["profile"]["session_minutes"] = 30
    elif mutation == "extra":
        output["explanation"] = "Unapproved field"
    elif mutation == "candidate":
        output["candidate"] = {"candidate_id": "not_approved"}
    elif mutation == "EOF":
        changes["terminal_state"] = "failed"
    elif mutation == "publish":
        changes["no_publication"] = False
    elif mutation == "budget":
        changes["counts"] = {**observation(case).counts, "input_tokens": 16001}
    elif mutation == "counts":
        changes["counts"] = {**observation(case).counts, "wire_requests": 1}
    elif mutation == "repaired_bad_proposal":
        changes["proposals_domain_valid"] = False
    elif mutation == "missing_tool":
        changes["source"] = "replay"
    raw = canonical(output).decode()
    if mutation == "duplicate_json":
        raw = raw[:-1] + ',"outcome":"plan"}'
    result = score(case, observation(case, output_json=raw, **changes), CATALOG)
    assert not result["hard_passed"] and not result["quality_eligible"]
    assert result["quality_scores"] is None
    with pytest.raises(ValueError, match="Hard failures"):
        validate_ratings(result, {**dict.fromkeys(DIMENSIONS, 5), "explanation_clarity": None})


@pytest.mark.parametrize(
    "name,args,valid,authorized",
    [
        ("search_exercises", '{"limit":20}', True, True),
        ("get_user_preferences", "{}", True, True),
        ("search_exercises", '{"limit":true}', False, True),
        ("search_exercises", '{"limit":21}', False, True),
        ("search_exercises", '{"equipment":"dumbbells"}', False, True),
        ("get_user_preferences", '{"owner_id":"other"}', False, False),
        ("approve_plan", "{}", False, False),
        ("search_exercises", '{"url":"https://example.invalid"}', False, False),
        ("search_exercises", '{"tag":"not_a_known_tag"}', False, True),
    ],
)
def test_tool_argument_and_capability_scoring(name, args, valid, authorized):
    call = ToolCall(call_id="fixture", name=name, arguments_json=args)
    _, actual_valid, actual_authorized = check_call(call, CASES[0].profile, CATALOG)
    assert (actual_valid, actual_authorized) == (valid, authorized)


def test_blinding_randomization_and_blank_forms(report):
    packet = review_packet(report, CASES)
    assert packet == review_packet(report, CASES)
    assert packet != review_packet(report, CASES, seed=30402)
    key = packet["private/blinding-key.json"]["mapping"]
    assert Counter(r["A"] for r in key) == {"template": 10, "replay": 10}
    assert Counter(r["split"] for r in key) == {"development": 10, "comparison_candidate": 10}
    public = json.dumps(packet["reviewer/packet.json"])
    for hidden in ("ME-D", "ME-C", "template", "replay", "reviewer_token", "model_id"):
        assert hidden not in public
    forms = packet["reviewer/blank-scores.json"]
    assert len(forms) == 40
    assert all(r["reviewer_token"] is None and r["explanation_clarity"] is None for r in forms)
    assert all(set(r["ratings"].values()) == {None} for r in forms)
    assert packet["private/reviewer-registry.json"]["reviewers"] == []


def test_clarity_not_assigned_without_content(report):
    result = report["cases"][0]
    good = {**dict.fromkeys(DIMENSIONS, 3), "explanation_clarity": None}
    assert validate_ratings(result, good) == good
    for bad in (
        {**good, "explanation_clarity": 5},
        {**good, "plan_variety": True},
        {**good, "perceived_usefulness": None},
    ):
        with pytest.raises(ValueError):
            validate_ratings(result, bad)


def test_future_agreement_arithmetic_only_synthetic_labels():
    result = agreement([1, 3, 5, 2], [1, 4, 3, 2])
    assert result == dict(
        n=4,
        exact_fraction=0.5,
        within_one_fraction=0.75,
        mean_absolute_error=0.75,
        signed_bias=-0.25,
        disagreement_indices=[2],
    )
    for human, judge in (([], []), ([3], []), ([True], [1]), ([0], [3])):
        with pytest.raises(ValueError):
            agreement(human, judge)


async def test_live_execution_cannot_be_selected_and_principal_is_not_model_input():
    with pytest.raises(ValueError, match="Offline execution only"):
        await run_case(CASES[0], OUTPUTS[CASES[0].case_id], "live", CATALOG)
    with pytest.raises(ServiceError) as error:
        await SyntheticProfile(CASES[0].profile).get(Principal.B)
    assert error.value.status == 404


@pytest.mark.parametrize("outcome", ["error", "abstain"])
async def test_unexpected_baseline_failure_is_not_rewritten_as_clarification(monkeypatch, outcome):
    from future_training.domain.baseline import PlanningResult
    from future_training.experiments import model_evaluation

    monkeypatch.setattr(
        model_evaluation,
        "plan_week",
        lambda *a, **kw: PlanningResult(outcome, "controlled_failure"),
    )
    case = CASES[0].model_copy(update={"expected": {"template": outcome}})
    result = await run_case(case, OUTPUTS[case.case_id], "template", CATALOG)
    assert result["actual"] == outcome and result["handling_passed"]
    assert result["quality_scores"] is None and not result["quality_eligible"]


@pytest.mark.parametrize("source", ["fake", "replay"])
async def test_evaluation_canaries_absent_from_both_configured_sinks(monkeypatch, request, source):
    sink = request.getfixturevalue("console")
    canaries = ("sk-evaluation-synthetic-canary", "fake.person@example.invalid", "555-010-4567")
    monkeypatch.setenv("OPENAI_API_KEY", canaries[0])
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", canaries[0])
    tracer = LocalTracer()
    for canary in canaries:
        case = next(c for c in CASES if c.case_id == "ME-text-preference")
        case = case.model_copy(update={"request_text": canary})
        with Span("agent.session", tracer=tracer, prompt=canary, billing_id=canary):
            result = await run_case(case, OUTPUTS[case.case_id], source, CATALOG)
        assert result["actual"] == "clarify"
        logging.getLogger("httpx").error(
            canary, exc_info=(RuntimeError, RuntimeError(canary), None)
        )
        assert canary not in json.dumps(result)
    sinks = sink.getvalue() + json.dumps(tracer.snapshot())
    assert tracer.snapshot() and sink.getvalue()
    for value in (*canaries, "exercise_id", "preferences_text", "encrypted_content"):
        assert value not in sinks


def test_no_production_dependency_or_frozen_asset_changes():
    import subprocess

    paths = [
        "src/future_training/evaluation.py",
        "src/future_training/domain",
        "data/evaluation/v1",
        "data/evaluation/results",
        "migrations",
        "uv.lock",
        "contracts/openapi.json",
        "contracts/approval-safety.md",
        "contracts/completion-feedback.md",
        "web/src",
    ]
    assert subprocess.run(["git", "diff", "--quiet", "--", *paths], cwd=ROOT).returncode == 0
