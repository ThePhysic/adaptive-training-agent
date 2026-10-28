"""Versioned original metadata. Return copies so callers cannot mutate the catalog."""

import hashlib
import json
from pathlib import Path
from types import MappingProxyType

from pydantic import TypeAdapter

from future_training.schemas import CatalogRecord, Identifier, ProfilePreferences

CATALOG_PATH = Path(__file__).resolve().parents[3] / "data/catalog/v1.json"


class Catalog:
    def __init__(self, revision: str, records: list[CatalogRecord]):
        if len(records) > 40:
            raise ValueError("catalog exceeds bounded F1 scope")
        self._revision = TypeAdapter(Identifier).validate_python(revision)
        encoded: dict[str, bytes] = {}
        tags = set()
        for record in records:
            # Revalidate mutable transport models; never trust model_construct().
            record = CatalogRecord.model_validate(record.model_dump(warnings=False))
            if record.catalog_revision != revision or record.exercise_id in encoded:
                raise ValueError("catalog revision mismatch or duplicate ID")
            encoded[record.exercise_id] = record.model_dump_json().encode("utf-8")
            tags.update(record.exclusion_tags)
        self._records = MappingProxyType(encoded)
        self._known_tags = frozenset(tags)

    @property
    def revision(self) -> str:
        return self._revision

    @property
    def known_tags(self) -> frozenset[str]:
        return self._known_tags

    @property
    def ids(self) -> frozenset[str]:
        return frozenset(self._records)

    def get(self, exercise_id: str) -> CatalogRecord | None:
        raw = self._records.get(exercise_id)
        return CatalogRecord.model_validate_json(raw) if raw else None

    def records(self) -> list[CatalogRecord]:
        return [
            CatalogRecord.model_validate_json(self._records[key]) for key in sorted(self._records)
        ]

    def fingerprint(self) -> str:
        payload = {"revision": self.revision, "records": [r.model_dump() for r in self.records()]}
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    def unknown_exclusions(self, profile: ProfilePreferences) -> bool:
        return bool(
            set(profile.excluded_ids) - self.ids or set(profile.excluded_tags) - self.known_tags
        )

    def eligible(self, profile: ProfilePreferences) -> list[CatalogRecord]:
        allowed_equipment = {"bodyweight"}
        if profile.equipment == "dumbbells_and_bodyweight":
            allowed_equipment.add("dumbbells")
        records = [
            r
            for r in self.records()
            if (
                profile.goal in r.goals
                and profile.experience in r.experiences
                and r.equipment in allowed_equipment
                and r.exercise_id not in profile.excluded_ids
                and not set(r.exclusion_tags).intersection(profile.excluded_tags)
            )
        ]
        # Dumbbells are optional; prefer their records if offered and available.
        return sorted(records, key=lambda r: (r.equipment != "dumbbells", r.exercise_id))


def load_catalog(path: Path = CATALOG_PATH) -> Catalog:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if set(payload) != {"revision", "records"}:
        raise ValueError("invalid catalog envelope")
    return Catalog(
        payload["revision"], [CatalogRecord.model_validate(r) for r in payload["records"]]
    )
