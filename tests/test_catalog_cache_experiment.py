import asyncio
import gc
import json
import weakref

import pytest

from future_training.agent.protocol import ToolCall
from future_training.agent.tools import ReadTools
from future_training.api import create_app
from future_training.domain.baseline import plan_week
from future_training.domain.catalog import Catalog, load_catalog
from future_training.domain.validator import validate_plan
from future_training.experiments.catalog_cache import CachedCatalog, ProjectionCache
from future_training.experiments.catalog_performance import distribution, timed, workload
from future_training.identity import Principal
from future_training.schemas import SavedProfile


@pytest.fixture
def source():
    return load_catalog()


@pytest.mark.parametrize("row", range(8))
def test_all_supported_rows_presets_days_and_exclusions_are_equivalent(source, row):
    cache = ProjectionCache()
    view = CachedCatalog(source, cache)
    cases = workload(source)[row * 27 : (row + 1) * 27]
    assert len(cases) == 27
    for case in cases:
        assert view.eligible(case.profile) == source.eligible(case.profile)
        actual = plan_week(case.profile, view)
        expected = plan_week(case.profile, source)
        assert actual == expected
        assert validate_plan(actual.plan, case.profile, view) == validate_plan(
            expected.plan, case.profile, source
        )
    assert cache.stats()["entries"] == 1  # No profile/day/duration/exclusion entries.
    assert cache.misses == 1


def test_copy_isolation_and_no_profile_or_plan_retention(source):
    cache = ProjectionCache()
    view = CachedCatalog(source, cache)
    profile = workload(source)[0].profile.model_copy(deep=True)
    reference = weakref.ref(profile)
    values = view.eligible(profile)
    values[0].title = "synthetic mutation"
    values[0].exclusion_tags.append("synthetic")
    assert view.eligible(profile) == source.eligible(profile)
    del profile
    gc.collect()
    assert reference() is None
    assert all(isinstance(entry.projection, Catalog) for entry in cache._entries.values())
    assert all(len(key) == 6 for key in cache._entries)


@pytest.mark.parametrize("new_version", [False, True])
def test_catalog_changes_cannot_hit_old_projection_even_if_label_reused(source, new_version):
    cache = ProjectionCache(max_entries=32)
    profile = workload(source)[0].profile
    before = CachedCatalog(source, cache).eligible(profile)
    records = source.records()
    selected = next(record for record in records if record.exercise_id == before[0].exercise_id)
    selected.experiences = ["intermediate"]
    revision = "catalog-v2" if new_version else source.revision
    for record in records:
        record.catalog_revision = revision
    changed = Catalog(revision, records)
    after = CachedCatalog(changed, cache).eligible(profile)
    assert after == changed.eligible(profile) and before != after
    assert cache.misses == 2 and cache.hits == 0
    assert cache.stats()["entries"] == 2  # Old immutable version remains bounded, not reused.
    cache.clear()
    assert cache.stats()["entries"] == cache.bytes == 0


def test_lru_touch_entry_limit_and_byte_limit(source):
    profiles = [workload(source)[index].profile for index in (0, 27, 54)]
    cache = ProjectionCache(max_entries=2)
    view = CachedCatalog(source, cache)
    for position in (0, 1, 0, 2):
        assert view.eligible(profiles[position]) == source.eligible(profiles[position])
    assert cache.stats()["entries"] == 2 and cache.evictions == 1 and cache.hits == 1
    view.eligible(profiles[1])
    assert cache.misses == 4 and cache.evictions == 2

    costs = []
    for profile in profiles[:2]:
        probe = ProjectionCache()
        CachedCatalog(source, probe).eligible(profile)
        costs.append(probe.bytes)
    limit = max(costs) + min(costs) // 2
    bounded = ProjectionCache(max_entries=32, max_bytes=limit)
    view = CachedCatalog(source, bounded)
    for profile in profiles[:2]:
        assert view.eligible(profile) == source.eligible(profile)
    assert bounded.evictions == 1 and bounded.stats()["entries"] == 1
    assert bounded.bytes <= limit


def test_oversized_entry_bypasses_without_unbounded_retention(source):
    cache = ProjectionCache(max_bytes=1)
    view = CachedCatalog(source, cache)
    profile = workload(source)[0].profile
    assert view.eligible(profile) == view.eligible(profile) == source.eligible(profile)
    assert cache.bypasses == cache.misses == 2
    assert cache.stats()["entries"] == cache.bytes == 0


async def test_two_cooperative_clients_share_only_common_catalog_data(source):
    cache = ProjectionCache()
    view = CachedCatalog(source, cache)
    cases = workload(source)
    barrier = asyncio.Barrier(2)

    async def client(profile):
        await barrier.wait()
        for _ in range(100):
            await asyncio.sleep(0)
            assert view.eligible(profile) == source.eligible(profile)
            assert cache.bytes <= cache.max_bytes

    await asyncio.gather(client(cases[0].profile), client(cases[1].profile))
    assert cache.misses == 1 and cache.hits == 199 and cache.stats()["entries"] == 1


def test_validation_outcomes_are_not_cached(source):
    cache = ProjectionCache()
    view = CachedCatalog(source, cache)
    profile = workload(source)[0].profile
    plan = plan_week(profile, source).plan
    view.eligible(profile)
    assert validate_plan(plan, profile, view).valid
    before = cache.stats()
    plan.days[0].planned_seconds += 1
    assert not validate_plan(plan, profile, view).valid
    assert validate_plan(plan, profile, view) == validate_plan(plan, profile, source)
    assert cache.stats() == before
    assert view.records() == source.records() and view.fingerprint() == source.fingerprint()


@pytest.mark.parametrize(
    "settings",
    [{"max_entries": 0}, {"max_entries": True}, {"max_bytes": 0}, {"max_bytes": 1048577}],
)
def test_invalid_cache_bounds_rejected(settings):
    with pytest.raises(ValueError):
        ProjectionCache(**settings)


def test_percentile_definition_is_nearest_rank_without_discarding_outliers():
    values = list(range(1, 101))
    assert distribution(values) == {
        "count": 100,
        "p50_ns": 50,
        "p95_ns": 95,
        "p99_ns": 99,
        "min_ns": 1,
        "max_ns": 100,
    }


async def test_measurements_keep_failures_in_denominator_and_sanitize_errors():
    async def operation(index):
        if index == 1:
            raise ValueError("synthetic-private-canary")
        return "ok"

    result = await timed(operation, 4, 2)
    assert result["samples"] == 4 and result["failure_count"] == 1
    assert result["failure_indices"] == [1]
    assert result["outcomes"] == {"ok": 3, "failed": 1}
    assert len(result["raw_elapsed_ns"]) == len(result["raw_service_ns"]) == 4
    assert "synthetic-private-canary" not in str(result)


def test_prototype_is_not_installed_in_application_composition():
    app = create_app()
    assert type(app.state.agent.catalog) is Catalog


@pytest.mark.parametrize(
    "arguments",
    [{"limit": 1}, {"equipment": "dumbbells"}, {"tag": "floor"}, {"goal": "general_conditioning"}],
)
async def test_tool_filters_and_conflicts_remain_outside_projection_cache(source, arguments):
    profile = SavedProfile(revision=1, preferences=workload(source)[81].profile)
    if "tag" in arguments:
        arguments = {**arguments, "tag": source.eligible(profile.preferences)[0].exclusion_tags[0]}
    call = ToolCall(
        call_id="filter-check", name="search_exercises", arguments_json=json.dumps(arguments)
    )
    view = CachedCatalog(source, ProjectionCache())
    baseline, prototype = ReadTools(None, source), ReadTools(None, view)
    expected = await baseline.dispatch(Principal.A, profile, call)
    actual = await prototype.dispatch(Principal.A, profile, call)
    assert actual == expected
    assert actual.status == ("error" if "goal" in arguments else "ok")
    assert baseline.checked_bytes(profile, call, actual) == prototype.checked_bytes(
        profile, call, actual
    )
