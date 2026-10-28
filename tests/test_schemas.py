import json
from copy import deepcopy
from itertools import product
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from future_training.schemas import (
    ApprovalRequest,
    BudgetLimits,
    CandidateLimits,
    CandidateMetadata,
    CatalogRecord,
    DoneEvent,
    DraftEvent,
    PlanProposal,
    ProfilePreferences,
    RepetitionBlock,
    TimedBlock,
)


@pytest.mark.parametrize(
    "goal,equipment,experience",
    list(
        product(
            ["general_strength", "general_conditioning"],
            ["bodyweight", "dumbbells_and_bodyweight"],
            ["beginner", "intermediate"],
        )
    ),
)
def test_all_eight_profile_matrix_rows(profile, goal, equipment, experience):
    profile.update(goal=goal, equipment=equipment, experience=experience)
    assert ProfilePreferences.model_validate(profile).goal == goal


@pytest.mark.parametrize(
    "key,value",
    [
        ("adult", False),
        ("adult", 1),
        ("adult", "true"),
        ("goal", "rehabilitation"),
        ("equipment", "barbell"),
        ("experience", "advanced"),
        ("days_per_week", "2"),
        ("days_per_week", 2.0),
        ("days_per_week", 1),
        ("session_minutes", 25),
        ("session_minutes", 20.0),
        ("owner_id", "other"),
        ("excluded_ids", [f"id-{n}" for n in range(13)]),
        ("excluded_tags", [f"tag-{n}" for n in range(9)]),
    ],
)
def test_profile_negative_contract(profile, key, value):
    profile[key] = value
    with pytest.raises(ValidationError):
        ProfilePreferences.model_validate(profile)


def test_exclusions_deduplicate_before_cap(profile):
    profile["excluded_ids"] = ["exercise-1"] * 13
    assert ProfilePreferences.model_validate(profile).excluded_ids == ["exercise-1"]


@pytest.mark.parametrize(
    "model,body",
    [
        (RepetitionBlock, {"mode": "repetitions", "sets": 2, "repetitions_per_set": 6}),
        (TimedBlock, {"mode": "timed", "sets": 2, "work_seconds_per_set": 30}),
    ],
)
@pytest.mark.parametrize("value", [True, "2", 2.0, 1, 5])
def test_numeric_coercion_and_sets_rejected(model, body, value):
    body.update(exercise_id="fixture", sets=value, rest_between_sets_seconds=45)
    with pytest.raises(ValidationError):
        model.model_validate(body)


@pytest.mark.parametrize(
    "change",
    [
        {"sets": 4},
        {"repetitions_per_set": 13},
        {"rest_between_sets_seconds": 30},
        {"rest_between_sets_seconds": 44},
        {"work_seconds_per_set": 30},
    ],
)
def test_beginner_strength_and_exactly_one_prescription(proposal, change):
    proposal["days"][0]["blocks"][0].update(change)
    with pytest.raises(ValidationError):
        PlanProposal.model_validate(proposal)


@pytest.mark.parametrize(
    "work,experience,valid",
    [
        (75, "beginner", True),
        (76, "beginner", False),
        (90, "intermediate", True),
        (91, "intermediate", False),
    ],
)
def test_timed_experience_bounds(proposal, work, experience, valid):
    proposal["profile"].update(goal="general_conditioning", experience=experience)
    for day in proposal["days"]:
        for block in day["blocks"]:
            block.update(mode="timed", work_seconds_per_set=work)
            del block["repetitions_per_set"]
    if valid:
        PlanProposal.model_validate(proposal)
    else:
        with pytest.raises(ValidationError):
            PlanProposal.model_validate(proposal)


def test_duplicate_ids_and_missing_days(proposal):
    altered = deepcopy(proposal)
    altered["days"][0]["blocks"][1]["exercise_id"] = "exercise-0"
    with pytest.raises(ValidationError):
        PlanProposal.model_validate(altered)
    proposal["days"][1]["day_index"] = 1
    with pytest.raises(ValidationError):
        PlanProposal.model_validate(proposal)


def test_provenance_seed_is_structural_only():
    content = Path("data/catalog-provenance-seed.json").read_text(encoding="utf-8")
    record = CatalogRecord.model_validate_json(content)
    assert record.catalog_revision == "schema-fixture-v1"
    assert record.provenance.origin == "original"


def test_approval_rejects_user_identity_and_client_plan():
    body = {
        "candidate_id": "c1",
        "revision": 1,
        "content_hash": "a" * 64,
        "idempotency_key": "request-1",
    }
    ApprovalRequest.model_validate(body)
    for key in ("owner_id", "plan"):
        with pytest.raises(ValidationError):
            ApprovalRequest.model_validate({**body, key: "untrusted"})
    with pytest.raises(ValidationError):
        ApprovalRequest.model_validate({**body, "revision": True})


@pytest.mark.parametrize("model", [BudgetLimits, CandidateLimits])
def test_ratified_limits_cannot_be_coerced_or_increased(model):
    defaults = model().model_dump()
    key = next(iter(defaults))
    for wrong in (True, str(defaults[key]), defaults[key] + 1):
        with pytest.raises(ValidationError):
            model.model_validate({key: wrong})


@pytest.mark.parametrize(
    "payload",
    [
        {
            "outcome": "plan",
            "candidate": {"candidate_id": "c1", "revision": 1, "content_hash": "a" * 64},
        },
        {"outcome": "clarify", "fields": ["excluded_ids"], "choices": ["Change exclusions"]},
        {"outcome": "abstain", "reason": "infeasible", "next_step": "change_supported_preferences"},
        {"outcome": "error", "error": {"code": "provider_failure", "retryable": False}},
    ],
)
def test_four_terminal_payloads(payload):
    body = {"event_type": "done", "request_id": "r1", "sequence": 1, "payload": payload}
    assert DoneEvent.model_validate_json(json.dumps(body)).payload.outcome == payload["outcome"]


def test_draft_preview_cannot_leak_approval_identity(proposal):
    body = {"event_type": "draft", "request_id": "r1", "sequence": 1, "payload": proposal}
    DraftEvent.model_validate(body)
    body["payload"]["candidate_id"] = "must-not-leak"
    with pytest.raises(ValidationError):
        DraftEvent.model_validate(body)


def test_schema_parsing_does_not_pretend_to_validate_duration_or_catalog(proposal):
    # Explicit scope test: F1-02 must independently reject this later.
    proposal["days"][0]["planned_seconds"] = 1
    assert PlanProposal.model_validate(proposal).days[0].planned_seconds == 1


def test_unknown_terminal_outcome():
    with pytest.raises(ValidationError):
        TypeAdapter(DoneEvent).validate_python(
            {
                "event_type": "done",
                "request_id": "r1",
                "sequence": 0,
                "payload": {"outcome": "approved"},
            }
        )


def test_internal_candidate_metadata_carries_separate_commit_state():
    body = {
        "lineage_id": "lineage-a",
        "owner_id": "synthetic-owner",
        "candidate": {"candidate_id": "candidate-a", "revision": 1, "content_hash": "a" * 64},
        "versions": {"profile_revision": 1, "catalog_revision": "v1", "validator_revision": "v1"},
        "expires_at_monotonic": 1800.0,
        "status": "ready",
        "commit_state": "unresolved",
    }
    assert CandidateMetadata.model_validate(body).commit_state == "unresolved"
    with pytest.raises(ValidationError):
        CandidateMetadata.model_validate({**body, "successful_revisions": True})
    with pytest.raises(ValidationError):
        CandidateMetadata.model_validate({**body, "successful_revisions": 2})
