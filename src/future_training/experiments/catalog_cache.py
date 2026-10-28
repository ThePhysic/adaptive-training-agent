"""Bounded catalog-projection prototype, deliberately absent from application composition.

Only common catalog metadata is retained. Exclusions and every authoritative
validation are applied afresh; profiles, plans and validation decisions are not cached.
One cooperative event loop only: synchronous lookup/build/publish never suspends.
"""

import json
from collections import OrderedDict
from dataclasses import dataclass

from future_training.domain.catalog import Catalog
from future_training.schemas import ProfilePreferences

Key = tuple[str, str, str, str, str, str]


@dataclass(frozen=True)
class Entry:
    projection: Catalog
    logical_bytes: int


class ProjectionCache:
    def __init__(self, *, max_entries=8, max_bytes=65536):
        if (
            type(max_entries) is not int
            or not 1 <= max_entries <= 32
            or type(max_bytes) is not int
            or not 1 <= max_bytes <= 1048576
        ):
            raise ValueError("Invalid experimental cache bounds")
        self.max_entries, self.max_bytes = max_entries, max_bytes
        self._entries: OrderedDict[Key, Entry] = OrderedDict()
        self.bytes = self.hits = self.misses = self.evictions = self.bypasses = 0

    def get(self, key: Key) -> Catalog | None:
        entry = self._entries.get(key)
        if entry is None:
            self.misses += 1
            return None
        self.hits += 1
        self._entries.move_to_end(key)
        return entry.projection

    def put(self, key: Key, value: Catalog, logical_bytes: int):
        if type(logical_bytes) is not int or logical_bytes < 1:
            raise ValueError("Invalid logical byte cost")
        if logical_bytes > self.max_bytes:
            self.bypasses += 1
            return
        previous = self._entries.pop(key, None)
        if previous:
            self.bytes -= previous.logical_bytes
        while len(self._entries) >= self.max_entries or self.bytes + logical_bytes > self.max_bytes:
            _, removed = self._entries.popitem(last=False)
            self.bytes -= removed.logical_bytes
            self.evictions += 1
        self._entries[key] = Entry(value, logical_bytes)
        self.bytes += logical_bytes

    def clear(self):
        self._entries.clear()
        self.bytes = 0

    def stats(self):
        return {
            "entries": len(self._entries),
            "logical_bytes": self.bytes,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "bypasses": self.bypasses,
        }


class CachedCatalog:
    """Experimental Catalog-compatible view; all non-eligibility operations delegate."""

    def __init__(self, source: Catalog, cache: ProjectionCache):
        self._source, self._cache = source, cache
        self._fingerprint = source.fingerprint()  # Immutable source binding, outside hot path.

    @property
    def revision(self):
        return self._source.revision

    @property
    def ids(self):
        return self._source.ids

    @property
    def known_tags(self):
        return self._source.known_tags

    def get(self, exercise_id):
        return self._source.get(exercise_id)

    def records(self):
        return self._source.records()

    def fingerprint(self):
        return self._source.fingerprint()

    def unknown_exclusions(self, profile):
        return self._source.unknown_exclusions(profile)

    def eligible(self, profile: ProfilePreferences):
        profile = ProfilePreferences.model_validate(profile.model_dump(warnings=False))
        key = (
            "catalog-projection-v1",
            self.revision,
            self._fingerprint,
            profile.goal,
            profile.equipment,
            profile.experience,
        )
        projection = self._cache.get(key)
        if projection is None:
            # Only these three filters affect this common, unexcluded projection.
            # Dates/days/preset/exclusions/owner never enter retained values or keys.
            common = ProfilePreferences(
                adult=True,
                goal=profile.goal,
                equipment=profile.equipment,
                experience=profile.experience,
                days_per_week=2,
                session_minutes=20,
            )
            records = self._source.eligible(common)
            projection = Catalog(self.revision, records)
            logical_bytes = len(json.dumps(key, separators=(",", ":")).encode()) + sum(
                len(record.model_dump_json().encode()) for record in records
            )
            self._cache.put(key, projection, logical_bytes)
        # Original catalog code applies every exclusion afresh and returns copies.
        return projection.eligible(profile)
