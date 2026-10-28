"""Atomic owner-scoped profile Save, not an approval/idempotency transaction."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Protocol

import psycopg
from psycopg.types.json import Jsonb
from pydantic import ValidationError

from future_training.domain.catalog import Catalog
from future_training.errors import ServiceError
from future_training.identity import Principal, owner_id
from future_training.observability import traced
from future_training.schemas import ProfileSaveRequest, SavedProfile

LOCAL_DSN = (
    "host=127.0.0.1 hostaddr=127.0.0.1 port=55432 dbname=training_dev "
    "user=training_dev connect_timeout=3 "
    "options='-c statement_timeout=5000 -c lock_timeout=2000 "
    "-c idle_in_transaction_session_timeout=5000'"
)


async def connect_local():
    return await psycopg.AsyncConnection.connect(LOCAL_DSN)


class ProfileAccess(Protocol):
    async def get(self, principal: Principal) -> SavedProfile: ...
    async def save(self, principal: Principal, request: ProfileSaveRequest) -> SavedProfile: ...


class PostgresProfiles:
    def __init__(self, catalog: Catalog, *, connect: Callable[[], Awaitable] = connect_local):
        self._catalog = catalog
        self._connect = connect
        self._slots = asyncio.Semaphore(4)

    @traced("profile.read")
    async def get(self, principal: Principal) -> SavedProfile:
        owner = owner_id(principal)
        try:
            async with asyncio.timeout(10), self._slots, await self._connect() as connection:
                cursor = await connection.execute(
                    "SELECT revision, preferences FROM profiles WHERE owner_id = %s", (owner,)
                )
                row = await cursor.fetchone()
                if row is None:
                    raise ServiceError(404, "not_found")
                return SavedProfile(revision=row[0], preferences=row[1])
        except (
            psycopg.Error,
            TimeoutError,
            ValidationError,
        ):
            raise ServiceError(503, "internal_error", retryable=True) from None

    @traced("profile.save")
    async def save(self, principal: Principal, request: ProfileSaveRequest) -> SavedProfile:
        owner = owner_id(principal)
        try:
            request = ProfileSaveRequest.model_validate(request.model_dump(warnings=False))
        except (
            ValidationError,
            AttributeError,
        ):
            raise ServiceError(422, "invalid_request") from None
        if request.expected_revision >= 2**63 - 1 or self._catalog.unknown_exclusions(
            request.preferences
        ):
            raise ServiceError(422, "invalid_request")
        try:
            async with asyncio.timeout(10), self._slots, await self._connect() as connection:
                if request.expected_revision == 0:
                    cursor = await connection.execute(
                        "INSERT INTO profiles (owner_id, revision, preferences) VALUES (%s, 1, %s) "
                        "ON CONFLICT (owner_id) DO NOTHING RETURNING revision, preferences",
                        (owner, Jsonb(request.preferences.model_dump())),
                    )
                else:
                    cursor = await connection.execute(
                        "UPDATE profiles SET revision = revision + 1, preferences = %s "
                        "WHERE owner_id = %s AND revision = %s RETURNING revision, preferences",
                        (Jsonb(request.preferences.model_dump()), owner, request.expected_revision),
                    )
                row = await cursor.fetchone()
                if row is None:
                    raise ServiceError(409, "stale_profile")
                return SavedProfile(revision=row[0], preferences=row[1])
        except (
            psycopg.Error,
            TimeoutError,
            ValidationError,
        ):
            # Context manager commits before returning; failed commit cannot report success.
            raise ServiceError(503, "internal_error", retryable=True) from None
