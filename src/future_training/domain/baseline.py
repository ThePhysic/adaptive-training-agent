"""Finite deterministic feasibility planner; no model, clinical or optimization claim."""

from dataclasses import dataclass
from functools import lru_cache

from pydantic import ValidationError

from future_training.domain.catalog import Catalog
from future_training.domain.duration import (
    TOLERANCE_SECONDS,
    TRANSITION_SECONDS,
    block_seconds,
    preset_timing,
    session_seconds,
)
from future_training.domain.validator import parse_profile, validate_plan
from future_training.schemas import DayPlan, PlanProposal, RepetitionBlock, TimedBlock

TEMPLATE_VERSION = "template-v1"


@dataclass(frozen=True)
class PlanningResult:
    outcome: str
    code: str
    plan: PlanProposal | None = None
    choices: tuple[str, ...] = ()


@dataclass(frozen=True)
class Prescription:
    sets: int
    work: int
    rest: int
    seconds: int


def _block(goal: str, exercise_id: str, sets: int, work: int, rest: int):
    common = {"exercise_id": exercise_id, "sets": sets, "rest_between_sets_seconds": rest}
    if goal == "general_strength":
        return RepetitionBlock(mode="repetitions", repetitions_per_set=work, **common)
    return TimedBlock(mode="timed", work_seconds_per_set=work, **common)


@lru_cache(maxsize=4)
def _options(goal: str, experience: str) -> tuple[Prescription, ...]:
    beginner = experience == "beginner"
    strength = goal == "general_strength"
    sets = sorted(range(2, 4 if beginner else 5), key=lambda n: (abs(n - 3), n))
    work = (
        range(6, (12 if beginner else 15) + 1)
        if strength
        else range(30, (75 if beginner else 90) + 1)
    )
    rests = (45, 60, 75, 90) if strength and beginner else (30, 45, 60, 75, 90)
    # Keep one canonical prescription per duration; selection does not depend on exercise text.
    unique = {}
    for count in sets:
        for rest in rests:
            for amount in work:
                seconds = block_seconds(_block(goal, "arithmetic-only", count, amount, rest))
                unique.setdefault(seconds, Prescription(count, amount, rest, seconds))
    return tuple(unique.values())


def _schedule(goal: str, experience: str, preset: int, available: int):
    warmup, cooldown, target = preset_timing(preset)
    maximum_count = min(6, available)
    if maximum_count < 3:
        return None
    options = _options(goal, experience)
    limit = target + TOLERANCE_SECONDS - warmup - cooldown
    mask = (1 << (limit + 1)) - 1
    reachable = [1]
    for _ in range(maximum_count):
        bits = 0
        for option in options:
            bits |= reachable[-1] << option.seconds
        reachable.append(bits & mask)
    preferred = {20: 4, 30: 5, 45: 6}[preset]
    for count in sorted(range(3, maximum_count + 1), key=lambda n: (abs(n - preferred), n)):
        fixed = warmup + cooldown + TRANSITION_SECONDS * (count - 1)
        totals = sorted(
            range(target - TOLERANCE_SECONDS, target + TOLERANCE_SECONDS + 1),
            key=lambda n: (abs(n - target), n),
        )
        for total in totals:
            remaining = total - fixed
            if remaining < 0 or not (reachable[count] >> remaining) & 1:
                continue
            selected = []
            for position in range(count, 0, -1):
                option = next(
                    o
                    for o in options
                    if remaining >= o.seconds
                    and (reachable[position - 1] >> (remaining - o.seconds)) & 1
                )
                selected.append(option)
                remaining -= option.seconds
            return tuple(selected)
    return None


def plan_week(
    profile_input: object,
    catalog: Catalog,
    *,
    choices_declined: bool = False,
    request_text: str = "",
) -> PlanningResult:
    """Structured preferences only. Uninterpreted free text never silently changes constraints."""
    if (
        type(choices_declined) is not bool
        or not isinstance(request_text, str)
        or len(request_text) > 2048
    ):
        return PlanningResult("error", "invalid_request")
    if request_text:
        if choices_declined:
            return PlanningResult(
                "abstain",
                "unsupported_free_text",
                choices=(
                    "Clinical, injury or rehabilitation requests require "
                    "qualified professional advice.",
                ),
            )
        return PlanningResult(
            "clarify",
            "uninterpreted_request",
            choices=(
                "Select supported structured preferences and exclusions explicitly.",
                "Clinical, injury or rehabilitation requests require "
                "qualified professional advice.",
            ),
        )
    try:
        profile = parse_profile(profile_input)
    except ValidationError:
        return PlanningResult(
            "abstain" if choices_declined else "clarify",
            "unsupported_profile",
            choices=("Provide an adult general-wellness profile within the supported matrix.",),
        )
    if catalog.unknown_exclusions(profile):
        return PlanningResult(
            "abstain" if choices_declined else "clarify",
            "unknown_exclusions",
            choices=("Select only known catalog IDs and exclusion tags.",),
        )
    eligible = catalog.eligible(profile)
    schedule = _schedule(profile.goal, profile.experience, profile.session_minutes, len(eligible))
    if schedule is None:
        code = "insufficient_exercises" if len(eligible) < 3 else "infeasible_duration"
        if choices_declined:
            return PlanningResult("abstain", code)
        return PlanningResult(
            "clarify",
            code,
            choices=(
                "Explicitly revise exclusions or choose another supported "
                "duration/equipment option.",
            ),
        )
    days = []
    for day_index in range(1, profile.days_per_week + 1):
        blocks = [
            _block(
                profile.goal,
                eligible[((day_index - 1) * len(schedule) + i) % len(eligible)].exercise_id,
                option.sets,
                option.work,
                option.rest,
            )
            for i, option in enumerate(schedule)
        ]
        days.append(
            DayPlan(
                day_index=day_index,
                blocks=blocks,
                planned_seconds=session_seconds(blocks, profile.session_minutes),
            )
        )
    proposal = PlanProposal(profile=profile, days=days)
    if not validate_plan(proposal, profile, catalog).valid:
        # Do not return a convincing fallback if implementation and validator disagree.
        return PlanningResult("error", "baseline_validation_failed")
    return PlanningResult("plan", "validated", proposal)
