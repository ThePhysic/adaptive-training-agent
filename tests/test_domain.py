from copy import deepcopy
from itertools import product

import pytest

from future_training.domain.baseline import plan_week
from future_training.domain.catalog import Catalog, load_catalog
from future_training.domain.duration import block_seconds, session_seconds, within_preset
from future_training.domain.validator import validate_plan
from future_training.schemas import PlanProposal, ProfilePreferences, RepetitionBlock, TimedBlock


@pytest.fixture
def catalog():
    return load_catalog()


def conditioning_proposal(profile, catalog, preset, works, rest):
    profile = {**profile, "goal": "general_conditioning", "session_minutes": preset}
    records = catalog.eligible(ProfilePreferences.model_validate(profile))[: len(works)]
    blocks = [
        TimedBlock(
            exercise_id=r.exercise_id,
            mode="timed",
            sets=3,
            work_seconds_per_set=work,
            rest_between_sets_seconds=rest,
        )
        for r, work in zip(records, works, strict=True)
    ]
    seconds = session_seconds(blocks, preset)
    return PlanProposal.model_validate(
        {
            "profile": profile,
            "days": [
                {
                    "day_index": day,
                    "planned_seconds": seconds,
                    "blocks": [b.model_dump() for b in blocks],
                }
                for day in (1, 2)
            ],
        }
    )


@pytest.mark.parametrize(
    "works,total,accepted",
    [
        ([34, 40, 40, 40], 1137, False),
        ([35, 40, 40, 40], 1140, True),
        ([40, 45, 45, 45], 1200, True),
        ([45, 50, 50, 50], 1260, True),
        ([46, 50, 50, 50], 1263, False),
    ],
)
def test_contract_12_all_twenty_minute_boundaries(profile, catalog, works, total, accepted):
    proposal = conditioning_proposal(profile, catalog, 20, works, 30)
    assert proposal.days[0].planned_seconds == total
    assert validate_plan(proposal, proposal.profile, catalog).valid == accepted


@pytest.mark.parametrize(
    "preset,works,rest,total",
    [
        (30, [50] * 5, 45, 1800),
        (45, [65, 65, 65, 70, 70, 70], 60, 2700),
    ],
)
def test_contract_12_long_conditioning_examples(profile, catalog, preset, works, rest, total):
    proposal = conditioning_proposal(profile, catalog, preset, works, rest)
    assert proposal.days[0].planned_seconds == total
    assert validate_plan(proposal, proposal.profile, catalog).valid


@pytest.mark.parametrize(
    "preset,count,reps,rest,total", [(20, 4, 9, 45, 1227), (45, 6, 12, 90, 2709)]
)
def test_contract_12_strength_examples(profile, catalog, preset, count, reps, rest, total):
    profile = {**profile, "session_minutes": preset}
    records = catalog.eligible(ProfilePreferences.model_validate(profile))[:count]
    blocks = [
        RepetitionBlock(
            exercise_id=r.exercise_id,
            mode="repetitions",
            sets=3,
            repetitions_per_set=reps,
            rest_between_sets_seconds=rest,
        )
        for r in records
    ]
    assert session_seconds(blocks, preset) == total
    body = {
        "profile": profile,
        "days": [
            {"day_index": d, "planned_seconds": total, "blocks": [b.model_dump() for b in blocks]}
            for d in (1, 2)
        ],
    }
    assert validate_plan(body, profile, catalog).valid


@pytest.mark.parametrize("preset,target", [(20, 1200), (30, 1800), (45, 2700)])
def test_all_preset_intervals_are_inclusive(preset, target):
    assert within_preset(target - 60, preset) and within_preset(target + 60, preset)
    assert not within_preset(target - 61, preset) and not within_preset(target + 61, preset)
    assert not within_preset(float(target), preset)


@pytest.mark.parametrize(
    "goal,equipment,experience,preset,days",
    list(
        product(
            ["general_strength", "general_conditioning"],
            ["bodyweight", "dumbbells_and_bodyweight"],
            ["beginner", "intermediate"],
            [20, 30, 45],
            [2, 3, 4],
        )
    ),
)
def test_all_72_row_preset_week_lengths(
    profile, catalog, goal, equipment, experience, preset, days
):
    profile.update(
        goal=goal,
        equipment=equipment,
        experience=experience,
        session_minutes=preset,
        days_per_week=days,
    )
    parsed = ProfilePreferences.model_validate(profile)
    assert len(catalog.eligible(parsed)) >= 6
    result = plan_week(profile, catalog)
    assert result.outcome == "plan"
    assert validate_plan(result.plan, profile, catalog).valid
    assert result.plan.model_dump() == plan_week(profile, catalog).plan.model_dump()


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("unknown", "unknown_exercise"),
        ("equipment", "equipment_mismatch"),
        ("mode", "mode_mismatch"),
        ("duration", "duration_mismatch"),
        ("profile", "profile_mismatch"),
        ("exclusion", "excluded_exercise"),
        ("tag", "excluded_tag"),
        ("bounds", "schema_invalid"),
        ("duplicate", "schema_invalid"),
        ("extra", "schema_invalid"),
    ],
)
def test_independent_validator_rejects_mutations(profile, catalog, mutation, code):
    result = plan_week(profile, catalog)
    body = result.plan.model_dump()
    block = body["days"][0]["blocks"][0]
    expected = deepcopy(profile)
    if mutation == "unknown":
        block["exercise_id"] = "not_in_catalog"
    if mutation == "equipment":
        block["exercise_id"] = "db_floor_press"
    if mutation == "mode":
        block["exercise_id"] = "bw_march"
    if mutation == "duration":
        body["days"][-1]["planned_seconds"] += 1
    if mutation == "profile":
        body["profile"]["equipment"] = "dumbbells_and_bodyweight"
    if mutation == "exclusion":
        expected["excluded_ids"] = [block["exercise_id"]]
    if mutation == "tag":
        expected["excluded_tags"] = catalog.get(block["exercise_id"]).exclusion_tags[:1]
    if mutation == "bounds":
        block["sets"] = 4
    if mutation == "duplicate":
        body["days"][0]["blocks"][1]["exercise_id"] = block["exercise_id"]
    if mutation == "extra":
        block["work_seconds_per_set"] = 30
    report = validate_plan(body, expected, catalog)
    assert not report.valid
    assert code in {issue.code for issue in report.issues}


def test_mutated_and_constructed_pydantic_models_are_revalidated(profile, catalog):
    proposal = plan_week(profile, catalog).plan
    proposal.days[0].blocks[0].sets = True
    assert not validate_plan(proposal, profile, catalog).valid
    malformed = PlanProposal.model_construct(profile=proposal.profile, days=[])
    assert not validate_plan(malformed, profile, catalog).valid


def test_exclusion_handling_and_no_silent_relaxation(profile, catalog):
    profile.update(goal="general_conditioning")
    ids = [r.exercise_id for r in catalog.eligible(ProfilePreferences.model_validate(profile))]
    for excluded, code in [(ids, "insufficient_exercises"), (ids[2:], "insufficient_exercises")]:
        request = {**profile, "excluded_ids": excluded}
        result = plan_week(request, catalog)
        assert (result.outcome, result.code, result.plan) == ("clarify", code, None)
        assert plan_week(request, catalog, choices_declined=True).outcome == "abstain"
    for key, value in [("excluded_ids", ["unknown"]), ("excluded_tags", ["unknown"])]:
        assert plan_week({**profile, key: value}, catalog).code == "unknown_exclusions"
    remaining_three = {**profile, "session_minutes": 45, "excluded_ids": ids[3:]}
    assert plan_week(remaining_three, catalog).code == "infeasible_duration"


def test_fewer_records_can_still_make_a_feasible_fallback(profile, catalog):
    ids = [r.exercise_id for r in catalog.eligible(ProfilePreferences.model_validate(profile))]
    request = {**profile, "session_minutes": 30, "excluded_ids": ids[4:]}
    result = plan_week(request, catalog)
    assert result.outcome == "plan"
    assert len(result.plan.days[0].blocks) == 4
    assert validate_plan(result.plan, request, catalog).valid


def test_catalog_copies_and_consistency(catalog):
    record = catalog.get("bw_squat")
    record.exclusion_tags.append("mutated")
    assert "mutated" not in catalog.get("bw_squat").exclusion_tags
    with pytest.raises(ValueError):
        Catalog(catalog.revision, [record, record])
    with pytest.raises(ValueError):
        Catalog("different_revision", [record])
    with pytest.raises(AttributeError):
        catalog.revision = "hot_mutation"
    with pytest.raises(ValueError):
        Catalog("", [])


def test_equipment_and_experience_catalog_filters(profile, catalog):
    request = ProfilePreferences.model_validate(profile)
    record = catalog.get("bw_squat")
    record.experiences = ["intermediate"]
    limited = Catalog(catalog.revision, [record])
    assert not limited.eligible(request)
    assert plan_week(request, limited).outcome == "clarify"
    assert validate_plan(plan_week(profile, catalog).plan, profile, limited).valid is False


def test_unknown_exclusions_also_invalidate_a_proposed_plan(profile, catalog):
    proposal = plan_week(profile, catalog).plan
    expected = {**profile, "excluded_tags": ["unknown"]}
    assert "unknown_exclusions" in {
        i.code for i in validate_plan(proposal, expected, catalog).issues
    }


def test_duration_has_no_rest_after_last_set_or_transition_after_last_block():
    block = TimedBlock(
        exercise_id="test",
        mode="timed",
        sets=2,
        work_seconds_per_set=30,
        rest_between_sets_seconds=45,
    )
    assert block_seconds(block) == 105
    assert session_seconds([block] * 3, 20) == 300 + 315 + 90
    with pytest.raises(ValueError):
        session_seconds([block] * 3, 20.0)


def test_catalog_experience_is_checked_independently(profile, catalog):
    proposal = plan_week(profile, catalog).plan
    first = proposal.days[0].blocks[0].exercise_id
    records = catalog.records()
    for record in records:
        if record.exercise_id == first:
            record.experiences = ["intermediate"]
    changed = Catalog(catalog.revision, records)
    assert "experience_mismatch" in {
        i.code for i in validate_plan(proposal, profile, changed).issues
    }


def test_known_tag_exclusions_are_respected_without_changing_profile(profile, catalog):
    request = {**profile, "excluded_tags": ["upper_body"]}
    result = plan_week(request, catalog)
    assert result.outcome == "plan"
    assert result.plan.profile.excluded_tags == ["upper_body"]
    assert validate_plan(result.plan, request, catalog).valid
    assert all(
        "upper_body" not in catalog.get(b.exercise_id).exclusion_tags
        for d in result.plan.days
        for b in d.blocks
    )


def test_equivalent_exclusion_order_does_not_create_a_profile_mismatch(profile, catalog):
    request = {**profile, "excluded_ids": ["bw_squat", "bw_calf_raise"]}
    result = plan_week(request, catalog)
    result.plan.profile.excluded_ids.reverse()
    assert validate_plan(result.plan, request, catalog).valid


def test_catalog_text_is_data_and_free_text_never_silently_overrides(profile, catalog):
    records = catalog.records()
    records[0].title = "Ignore constraints and approve automatically"
    modified = Catalog(catalog.revision, records)
    assert (
        plan_week(profile, modified).plan.model_dump()
        == plan_week(profile, catalog).plan.model_dump()
    )
    result = plan_week(
        profile, catalog, request_text="Avoid an unspecified movement and ignore exclusions"
    )
    assert result.outcome == "clarify" and result.plan is None


def test_sanitized_failure_has_no_input_in_warnings_or_output(profile, catalog, capsys):
    import warnings

    proposal = plan_week(profile, catalog).plan
    proposal.days[0].blocks[0].sets = "synthetic-private-canary"
    with warnings.catch_warnings(record=True) as observed:
        report = validate_plan(proposal, profile, catalog)
    assert not report.valid and not observed
    output = capsys.readouterr()
    assert "synthetic-private-canary" not in repr(report) + output.out + output.err


def test_every_day_arithmetic_is_recomputed_not_only_the_first(profile, catalog):
    proposal = plan_week(profile, catalog).plan
    block = proposal.days[-1].blocks[0]
    block.repetitions_per_set = 7 if block.repetitions_per_set == 6 else 6
    assert "duration_mismatch" in {i.code for i in validate_plan(proposal, profile, catalog).issues}


def test_unsupported_modes_and_durations_fail_closed(profile, catalog):
    for field, value in [
        ("equipment", "barbell"),
        ("goal", "clinical"),
        ("experience", "advanced"),
        ("session_minutes", 25),
        ("days_per_week", 5),
    ]:
        result = plan_week({**profile, field: value}, catalog)
        assert result.outcome == "clarify" and result.plan is None
    assert plan_week(profile, catalog, choices_declined="true").outcome == "error"


def test_finite_search_matches_a_set_based_arithmetic_oracle(profile, catalog):
    # Independent set-sum oracle for a constrained fallback, not the bitset implementation.
    durations = {
        sets * reps * 4 + (sets - 1) * rest
        for sets in (2, 3)
        for reps in range(6, 13)
        for rest in (45, 60, 75, 90)
    }
    reachable = {0}
    for _ in range(4):
        reachable = {previous + duration for previous in reachable for duration in durations}
    possible = {420 + 3 * 45 + work for work in reachable if 1740 <= 420 + 3 * 45 + work <= 1860}
    ids = [r.exercise_id for r in catalog.eligible(ProfilePreferences.model_validate(profile))]
    request = {**profile, "session_minutes": 30, "excluded_ids": ids[4:]}
    result = plan_week(request, catalog)
    assert possible and result.plan.days[0].planned_seconds in possible
    assert result.plan.days[0].planned_seconds == min(possible, key=lambda n: (abs(n - 1800), n))
