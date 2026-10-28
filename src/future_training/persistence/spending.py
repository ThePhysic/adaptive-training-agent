"""Native SQL offline spend ledger. No credential, network send or live grant authority.

Project row first serializes grants/sessions/attempts, even across repository
objects. Uncertain sent attempts retain the maximum reservation indefinitely.
Cancellation drains the owned bounded transaction before propagating.
"""

import asyncio
import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime

import psycopg
from psycopg.types.json import Jsonb
from pydantic import TypeAdapter

from future_training.agent.protocol import canonical
from future_training.persistence.profiles import connect_local
from future_training.providers.accounting import MODEL, RATE_VERSION, ActualUsage, cost_micro
from future_training.providers.accounting import reserve_micro as amount_for
from future_training.providers.observations import classification, discrepancy, numbers
from future_training.schemas import Identifier

_ID = TypeAdapter(Identifier)


class LedgerFault(Exception):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


def identifier(value):
    return _ID.validate_python(value)


def money(value):
    if type(value) is not int or not 0 <= value <= 10**9:
        raise ValueError("Invalid monetary limit")
    return value


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


@dataclass(frozen=True, repr=False)
class Reservation:
    project: str
    grant: str
    session: str
    run: str
    attempt: str
    number: int
    input_bound: int
    output_cap: int

    def checked(self):
        for value in (self.project, self.grant, self.session, self.run, self.attempt):
            identifier(value)
        if type(self.number) is not int or not 1 <= self.number <= 3:
            raise ValueError("Invalid attempt")
        amount_for(self.input_bound, self.output_cap)
        return self

    def fingerprint(self):
        self.checked()
        return digest(
            [
                self.project,
                self.grant,
                self.session,
                self.run,
                self.attempt,
                self.number,
                self.input_bound,
                self.output_cap,
                RATE_VERSION,
            ]
        )


class SpendingLedger:
    def __init__(self, *, connect=connect_local, now=lambda: datetime.now(UTC)):
        self.connect, self.now = connect, now
        self._uncertain = set()

    async def _has_observation(self, c, project, source, operation):
        return (
            await (
                await c.execute(
                    "SELECT 1 FROM spend_observations WHERE project_id=%s "
                    "AND source=%s AND operation_id=%s",
                    (project, source, operation),
                )
            ).fetchone()
            is not None
        )

    async def _freeze(self, c, project, source, operation, reason, observed, model, tier):
        # The project lock is already held. No raw model/tier or exception survives.
        bounded = numbers(observed)
        mc, tc = classification(model, MODEL), classification(tier, "default")
        fingerprint = digest([reason, bounded, mc, tc])
        await c.execute("UPDATE spend_projects SET frozen=true WHERE project_id=%s", (project,))
        await c.execute(
            "INSERT INTO spend_observations(project_id,source,operation_id,reason,model_class,"
            "tier_class,numbers,fingerprint) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) "
            "ON CONFLICT DO NOTHING",
            (project, source, operation, reason, mc, tc, Jsonb(bounded), fingerprint),
        )
        row = await (
            await c.execute(
                "SELECT fingerprint FROM spend_observations "
                "WHERE project_id=%s AND source=%s AND operation_id=%s",
                (project, source, operation),
            )
        ).fetchone()
        if row[0] != fingerprint:
            raise LedgerFault("observation_conflict")

    async def observe_generation(self, request, response):
        from future_training.providers.observations import response_observation

        request.checked()
        reason, observed = response_observation(response)

        async def write(c, project):
            row = await self._attempt(c, request)
            if row[1] != "sent":
                raise LedgerFault("attempt_not_sent")
            await self._freeze(
                c,
                request.project,
                "legacy",
                request.attempt,
                reason,
                observed,
                response.get("model"),
                response.get("service_tier"),
            )

        await self._owned(request.project, write)

    def time(self):
        value = self.now()
        if value.tzinfo is None:
            raise ValueError("Aware clock required")
        return value.astimezone(UTC)

    async def _lock_project(self, connection, project):
        return await (
            await connection.execute(
                "SELECT limit_micro,day_limit_micro,disabled,frozen FROM spend_projects "
                "WHERE project_id=%s FOR UPDATE",
                (project,),
            )
        ).fetchone()

    async def _owned(self, project, body, *, reconcile=False):
        identifier(project)
        if project in self._uncertain and not reconcile:
            raise LedgerFault("reconciliation_pending")

        async def operation():
            connection = None
            try:
                connection = await self.connect()
                await connection.execute("SET LOCAL statement_timeout='3000ms'")
                await connection.execute("SET LOCAL lock_timeout='1500ms'")
                row = await self._lock_project(connection, project)
                if row is None:
                    raise LedgerFault("project_missing")
                result = await body(connection, row)
                await connection.commit()
                return result
            except psycopg.Error:
                # This includes uncertain COMMIT. Callers must not send after it.
                self._uncertain.add(project)
                raise LedgerFault("reconciliation_pending") from None
            finally:
                if connection is not None:
                    await connection.close()

        async def transaction():
            try:
                async with asyncio.timeout(5):
                    return await operation()
            except TimeoutError:
                self._uncertain.add(project)
                raise LedgerFault("reconciliation_pending") from None

        task = asyncio.create_task(transaction())
        cancelled = False
        while not task.done():
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                cancelled = True
            except Exception:
                if not cancelled:
                    raise
        if cancelled:
            # Observe any failure, keeping its fence, but cancellation wins.
            if not task.cancelled():
                task.exception()
            raise asyncio.CancelledError
        return task.result()

    async def create_replay_project(self, project, limit_micro, day_limit_micro):
        """Explicit local fixture setup, never a live permit; migration inserts nothing."""
        identifier(project)
        money(limit_micro), money(day_limit_micro)
        try:
            async with await self.connect() as connection:
                await connection.execute(
                    "INSERT INTO spend_projects(project_id,limit_micro,day_limit_micro) "
                    "VALUES (%s,%s,%s)",
                    (project, limit_micro, day_limit_micro),
                )
        except psycopg.Error:
            raise LedgerFault("project_setup_failed") from None

    async def grant(self, project, grant, limit_micro, expires_at):
        identifier(grant), money(limit_micro)
        if expires_at.tzinfo is None or expires_at <= self.time():
            raise ValueError("Invalid grant expiry")

        async def write(connection, row):
            await connection.execute(
                "INSERT INTO spend_grants VALUES (%s,%s,%s,%s)",
                (grant, project, limit_micro, expires_at),
            )

        await self._owned(project, write)

    async def session(self, project, grant, session, limit_micro, expires_at):
        identifier(grant), identifier(session), money(limit_micro)
        if expires_at.tzinfo is None or expires_at <= self.time():
            raise ValueError("Invalid session expiry")

        async def write(connection, row):
            found = await (
                await connection.execute(
                    "SELECT expires_at FROM spend_grants WHERE grant_id=%s AND project_id=%s",
                    (grant, project),
                )
            ).fetchone()
            if found is None or expires_at > found[0]:
                raise LedgerFault("invalid_session")
            await connection.execute(
                "INSERT INTO spend_sessions VALUES (%s,%s,%s,%s)",
                (session, grant, limit_micro, expires_at),
            )

        await self._owned(project, write)

    async def _limits(
        self, connection, request, project, proposed, day, *, exclude=None, exclude_operation=None
    ):
        if project[2] or project[3]:
            raise LedgerFault("spending_disabled")
        limits = await (
            await connection.execute(
                "SELECT g.limit_micro,g.expires_at,s.limit_micro,s.expires_at "
                "FROM spend_grants g JOIN spend_sessions s ON s.grant_id=g.grant_id "
                "WHERE g.project_id=%s AND g.grant_id=%s AND s.session_id=%s",
                (request.project, request.grant, request.session),
            )
        ).fetchone()
        if limits is None or min(limits[1], limits[3]) <= self.time():
            raise LedgerFault("permit_expired_or_missing")
        rows = await (
            await connection.execute(
                "SELECT grant_id,session_id,day,CASE WHEN state='settled' THEN actual_micro "
                "WHEN state='not_sent' THEN 0 ELSE reserved_micro END FROM spend_attempts "
                "WHERE project_id=%s AND (%s::text IS NULL OR attempt_id<>%s) "
                "UNION ALL SELECT grant_id,session_id,day,CASE WHEN state='settled' "
                "THEN actual_micro WHEN state='not_sent' THEN 0 ELSE reserved_micro END "
                "FROM spend_operations WHERE project_id=%s "
                "AND (%s::text IS NULL OR operation_id<>%s)",
                (
                    request.project,
                    exclude,
                    exclude,
                    request.project,
                    exclude_operation,
                    exclude_operation,
                ),
            )
        ).fetchall()
        used = [
            sum(r[3] for r in rows),
            sum(r[3] for r in rows if r[2] == day),
            sum(r[3] for r in rows if r[0] == request.grant),
            sum(r[3] for r in rows if r[1] == request.session),
        ]
        for consumption, ceiling in zip(
            used, [project[0], project[1], limits[0], limits[2]], strict=True
        ):
            if consumption + proposed > ceiling:
                raise LedgerFault("spend_exhausted")

    async def reserve(self, request: Reservation):
        request.checked()

        async def write(connection, project):
            if await (
                await connection.execute(
                    "SELECT 1 FROM spend_pairs WHERE run_id=%s LIMIT 1", (request.run,)
                )
            ).fetchone():
                raise LedgerFault("run_protocol_conflict")
            existing = await (
                await connection.execute(
                    "SELECT fingerprint,state FROM spend_attempts WHERE attempt_id=%s",
                    (request.attempt,),
                )
            ).fetchone()
            if existing:
                if existing[0] != request.fingerprint():
                    raise LedgerFault("attempt_conflict")
                return existing[1]
            rows = await (
                await connection.execute(
                    "SELECT attempt_number,state,input_bound,output_cap,usage FROM spend_attempts "
                    "WHERE run_id=%s",
                    (request.run,),
                )
            ).fetchall()
            if any(row[1] in ("reserved", "sent") for row in rows):
                raise LedgerFault("run_reconciliation_pending")
            if request.number != len(rows) + 1:
                raise LedgerFault("attempt_order")
            used_input = sum(r[4]["input_tokens"] if r[1] == "settled" else r[2] for r in rows)
            used_output = sum(r[4]["output_tokens"] if r[1] == "settled" else r[3] for r in rows)
            if used_input + request.input_bound > 16000 or used_output + request.output_cap > 4000:
                raise LedgerFault("token_exhausted")
            amount = amount_for(request.input_bound, request.output_cap)
            today = self.time().date()
            await self._limits(connection, request, project, amount, today)
            await connection.execute(
                "INSERT INTO spend_attempts(attempt_id,project_id,grant_id,session_id,run_id,"
                "attempt_number,day,fingerprint,input_bound,output_cap,reserved_micro,state,"
                "rate_version) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'reserved',%s)",
                (
                    request.attempt,
                    request.project,
                    request.grant,
                    request.session,
                    request.run,
                    request.number,
                    today,
                    request.fingerprint(),
                    request.input_bound,
                    request.output_cap,
                    amount,
                    RATE_VERSION,
                ),
            )
            return "reserved"

        return await self._owned(request.project, write)

    async def _attempt(self, connection, request):
        row = await (
            await connection.execute(
                "SELECT fingerprint,state,reserved_micro,settlement_hash,actual_micro "
                "FROM spend_attempts WHERE attempt_id=%s AND project_id=%s",
                (request.attempt, request.project),
            )
        ).fetchone()
        if row is None or row[0] != request.fingerprint():
            raise LedgerFault("attempt_conflict")
        return row

    async def mark_sent(self, request):
        """One-shot durable claim before send. Lost acknowledgement forbids resend."""
        request.checked()

        async def write(connection, project):
            row = await self._attempt(connection, request)
            if row[1] != "reserved":
                raise LedgerFault("attempt_already_claimed")
            today = self.time().date()
            await self._limits(connection, request, project, row[2], today, exclude=request.attempt)
            await connection.execute(
                "UPDATE spend_attempts SET state='sent',day=%s WHERE attempt_id=%s",
                (today, request.attempt),
            )

        await self._owned(request.project, write)

    async def settle(self, request, usage: ActualUsage, *, model=MODEL, tier="default"):
        request.checked()
        usage = ActualUsage.model_validate(usage.model_dump())
        settlement = digest([usage.model_dump(), model, tier])
        reason = discrepancy(usage, model, tier, request.input_bound, request.output_cap)

        async def write(connection, project):
            row = await self._attempt(connection, request)
            if row[1] == "settled":
                if row[3] != settlement:
                    raise LedgerFault("settlement_conflict")
                return row[4]
            if row[1] != "sent":
                raise LedgerFault("attempt_not_sent")
            if reason:
                await self._freeze(
                    connection,
                    request.project,
                    "legacy",
                    request.attempt,
                    reason,
                    usage.model_dump(),
                    model,
                    tier,
                )
                return None  # Unknown pricing: retain sent reservation, do not invent cost.
            if await self._has_observation(connection, request.project, "legacy", request.attempt):
                return None
            cost = cost_micro(usage)
            await connection.execute(
                "UPDATE spend_attempts SET state='settled',actual_micro=%s,usage=%s,"
                "settlement_hash=%s WHERE attempt_id=%s",
                (cost, Jsonb(usage.model_dump()), settlement, request.attempt),
            )
            return cost

        result = await self._owned(request.project, write)
        if result is None:
            raise LedgerFault("pricing_or_usage_discrepancy")
        return result

    async def release_unsent(self, request):
        request.checked()

        async def write(connection, project):
            row = await self._attempt(connection, request)
            if row[1] not in ("reserved", "not_sent"):
                raise LedgerFault("cannot_release_sent")
            await connection.execute(
                "UPDATE spend_attempts SET state='not_sent' WHERE attempt_id=%s",
                (request.attempt,),
            )

        await self._owned(request.project, write)

    async def reconcile(self, project):
        """Acquire authoritative ordering, inspect unresolved rows; NEVER infer free usage."""

        async def read(connection, row):
            return await (
                await connection.execute(
                    "SELECT attempt_id,state,reserved_micro,actual_micro FROM spend_attempts "
                    "WHERE project_id=%s ORDER BY attempt_id",
                    (project,),
                )
            ).fetchall()

        result = await self._owned(project, read, reconcile=True)
        self._uncertain.discard(project)
        return result

    async def stop(self, project):
        async def write(connection, row):
            await connection.execute(
                "UPDATE spend_projects SET disabled=true WHERE project_id=%s",
                (project,),
            )

        await self._owned(project, write, reconcile=True)
