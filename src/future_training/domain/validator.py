"""Independent trust boundary shared by the template and future model adapter.

Only declared general-wellness constraints are checked; no auth or safety verdict.
The expected profile must come from the application, never from proposed model text.
"""

from dataclasses import dataclass

from pydantic import ValidationError

from future_training.domain.catalog import Catalog
from future_training.domain.duration import session_seconds, within_preset
from future_training.schemas import PlanProposal, ProfilePreferences

VALIDATOR_VERSION = "validator-v1"


@dataclass(frozen=True)
class Issue:
    code: str
    day_index: int | None = None
    block_index: int | None = None


@dataclass(frozen=True)
class ValidationReport:
    issues: tuple[Issue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues


def parse_profile(raw: object) -> ProfilePreferences:
    if isinstance(raw, ProfilePreferences):
        raw = raw.model_dump(warnings=False)
    return ProfilePreferences.model_validate(raw)


def _constraints(profile: ProfilePreferences) -> dict:
    result = profile.model_dump()
    result["excluded_ids"] = sorted(result["excluded_ids"])
    result["excluded_tags"] = sorted(result["excluded_tags"])
    return result


def validate_plan(raw: object, expected_profile: object, catalog: Catalog) -> ValidationReport:
    try:
        expected = parse_profile(expected_profile)
    except ValidationError:
        return ValidationReport((Issue("unsupported_profile"),))
    try:
        if isinstance(raw, PlanProposal):
            raw = raw.model_dump(warnings=False)
        proposal = PlanProposal.model_validate(raw)
    except ValidationError:
        # Never expose Pydantic error inputs/exception strings or arbitrary user text.
        return ValidationReport((Issue("schema_invalid"),))
    issues = []
    if _constraints(proposal.profile) != _constraints(expected):
        issues.append(Issue("profile_mismatch"))
    if catalog.unknown_exclusions(expected):
        issues.append(Issue("unknown_exclusions"))
    allowed_equipment = {"bodyweight"}
    if expected.equipment == "dumbbells_and_bodyweight":
        allowed_equipment.add("dumbbells")
    for day in proposal.days:
        for index, block in enumerate(day.blocks):
            record = catalog.get(block.exercise_id)
            if record is None:
                issues.append(Issue("unknown_exercise", day.day_index, index))
                continue
            checks = (
                (record.equipment in allowed_equipment, "equipment_mismatch"),
                (expected.goal in record.goals, "goal_mismatch"),
                (expected.experience in record.experiences, "experience_mismatch"),
                (record.mode == block.mode, "mode_mismatch"),
                (block.exercise_id not in expected.excluded_ids, "excluded_exercise"),
                (
                    not set(record.exclusion_tags).intersection(expected.excluded_tags),
                    "excluded_tag",
                ),
            )
            issues.extend(Issue(code, day.day_index, index) for valid, code in checks if not valid)
        actual = session_seconds(day.blocks, expected.session_minutes)
        if actual != day.planned_seconds:
            issues.append(Issue("duration_mismatch", day.day_index))
        if not within_preset(actual, expected.session_minutes):
            issues.append(Issue("duration_out_of_bounds", day.day_index))
    return ValidationReport(tuple(issues))
