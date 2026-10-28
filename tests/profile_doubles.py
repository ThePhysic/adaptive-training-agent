"""Explicit test-only profile backend; PostgreSQL correctness is integration-tested."""

from future_training.errors import ServiceError
from future_training.identity import owner_id
from future_training.schemas import SavedProfile


class MemoryProfiles:
    def __init__(self):
        self.rows = {}

    async def get(self, principal):
        owner = owner_id(principal)
        if owner not in self.rows:
            raise ServiceError(404, "not_found")
        return SavedProfile.model_validate_json(self.rows[owner])

    async def save(self, principal, request):
        owner = owner_id(principal)
        old = self.rows.get(owner)
        revision = SavedProfile.model_validate_json(old).revision if old else 0
        if revision != request.expected_revision:
            raise ServiceError(409, "stale_profile")
        result = SavedProfile(revision=revision + 1, preferences=request.preferences)
        self.rows[owner] = result.model_dump_json()
        return result
