"""Atomic paired replay liabilities using the existing PostgreSQL project guard.

No live grant or provider billing lookup. A successful count remains charged at
its synthetic maximum until explicit typed reconciliation supplies known cost.
"""

from dataclasses import dataclass

from psycopg.types.json import Jsonb

from future_training.persistence.spending import (
    LedgerFault,
    SpendingLedger,
    digest,
    identifier,
    money,
)
from future_training.providers.accounting import (
    MODEL,
    RATE_VERSION,
    ActualUsage,
    cost_micro,
    reserve_micro,
)
from future_training.providers.observations import discrepancy, response_observation

COUNT_QUOTE = "synthetic-count-ceiling-v1"


@dataclass(frozen=True, repr=False)
class PairReservation:
    project: str
    grant: str
    session: str
    run: str
    pair: str
    ordinal: int
    input_ceiling: int
    output_cap: int
    count_ceiling_micro: int
    count_quote: str = COUNT_QUOTE

    def checked(self):
        for value in (self.project, self.grant, self.session, self.run, self.pair):
            identifier(value)
        identifier(self.pair + "-c"), identifier(self.pair + "-g")
        if type(self.ordinal) is not int or not 1 <= self.ordinal <= 3:
            raise ValueError("Invalid pair ordinal")
        if self.count_quote != COUNT_QUOTE or money(self.count_ceiling_micro) <= 0:
            raise ValueError("Synthetic count quote required")
        reserve_micro(self.input_ceiling, self.output_cap)
        if self.input_ceiling < 1:
            raise ValueError("Positive input ceiling required")
        return self

    def fingerprint(self):
        self.checked()
        return digest(
            [
                self.project,
                self.grant,
                self.session,
                self.run,
                self.pair,
                self.ordinal,
                self.input_ceiling,
                self.output_cap,
                self.count_ceiling_micro,
                self.count_quote,
                RATE_VERSION,
            ]
        )


class CountedSpendingLedger(SpendingLedger):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tickets = {}

    def invalidate(self, pair):
        self._tickets.pop(pair.pair, None)

    async def observe_generation(self, pair, response):
        pair.checked()
        reason, observed = response_observation(response)

        async def write(c, project):
            row = await self._op(c, pair, "generation")
            if row[0] != "sent":
                raise LedgerFault("attempt_not_sent")
            await self._freeze(
                c,
                pair.project,
                "mixed",
                pair.pair + "-g",
                reason,
                observed,
                response.get("model"),
                response.get("service_tier"),
            )

        await self._owned(pair.project, write)

    async def _pair(self, connection, pair):
        found = await (
            await connection.execute(
                "SELECT fingerprint,rate_version FROM spend_pairs "
                "WHERE pair_id=%s AND project_id=%s",
                (pair.pair, pair.project),
            )
        ).fetchone()
        if found is None or found != (pair.fingerprint(), RATE_VERSION):
            raise LedgerFault("pair_conflict")

    async def _op(self, connection, pair, kind):
        await self._pair(connection, pair)
        row = await (
            await connection.execute(
                "SELECT state,reserved_micro,actual_micro,input_bound,output_cap,counted_input,"
                "settlement_hash,wire_ordinal FROM spend_operations WHERE pair_id=%s AND kind=%s",
                (pair.pair, kind),
            )
        ).fetchone()
        if row is None:
            raise LedgerFault("pair_conflict")
        return row

    async def reserve_pair(self, pair: PairReservation):
        pair.checked()

        async def write(c, project):
            if await (
                await c.execute("SELECT 1 FROM spend_attempts WHERE run_id=%s LIMIT 1", (pair.run,))
            ).fetchone():
                raise LedgerFault("run_protocol_conflict")
            existing = await (
                await c.execute(
                    "SELECT fingerprint FROM spend_pairs WHERE pair_id=%s",
                    (pair.pair,),
                )
            ).fetchone()
            if existing:
                if existing[0] != pair.fingerprint():
                    raise LedgerFault("pair_conflict")
                return
            previous = await (
                await c.execute(
                    "SELECT kind,state,input_bound,output_cap,usage FROM spend_operations "
                    "WHERE run_id=%s",
                    (pair.run,),
                )
            ).fetchall()
            generations = [r for r in previous if r[0] == "generation"]
            if any(r[1] != "settled" for r in generations):
                raise LedgerFault("run_reconciliation_pending")
            if any(r[1] not in ("responded_held", "settled") for r in previous if r[0] == "count"):
                raise LedgerFault("run_reconciliation_pending")
            if pair.ordinal != len(generations) + 1:
                raise LedgerFault("attempt_order")
            if (
                sum(r[4]["input_tokens"] for r in generations) + pair.input_ceiling > 16000
                or sum(r[4]["output_tokens"] for r in generations) + pair.output_cap > 4000
            ):
                raise LedgerFault("token_exhausted")
            generation = reserve_micro(pair.input_ceiling, pair.output_cap)
            day = self.time().date()
            await self._limits(c, pair, project, generation + pair.count_ceiling_micro, day)
            await c.execute(
                "INSERT INTO spend_pairs(pair_id,project_id,grant_id,session_id,run_id,ordinal,"
                "input_ceiling,output_cap,count_ceiling_micro,count_quote,"
                "rate_version,fingerprint) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    pair.pair,
                    pair.project,
                    pair.grant,
                    pair.session,
                    pair.run,
                    pair.ordinal,
                    pair.input_ceiling,
                    pair.output_cap,
                    pair.count_ceiling_micro,
                    pair.count_quote,
                    RATE_VERSION,
                    pair.fingerprint(),
                ),
            )
            for kind, amount, inp, out in [
                ("count", pair.count_ceiling_micro, 0, 0),
                ("generation", generation, pair.input_ceiling, pair.output_cap),
            ]:
                await c.execute(
                    "INSERT INTO spend_operations(operation_id,pair_id,project_id,grant_id,"
                    "session_id,"
                    "run_id,ordinal,kind,day,state,reserved_micro,input_bound,output_cap) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'reserved',%s,%s,%s)",
                    (
                        pair.pair + ("-c" if kind == "count" else "-g"),
                        pair.pair,
                        pair.project,
                        pair.grant,
                        pair.session,
                        pair.run,
                        pair.ordinal,
                        kind,
                        day,
                        amount,
                        inp,
                        out,
                    ),
                )

        await self._owned(pair.project, write)

    async def claim(self, pair, kind):
        pair.checked()
        if kind not in ("count", "generation"):
            raise ValueError("Invalid operation")
        if kind == "generation" and self._tickets.pop(pair.pair, None) is None:
            raise LedgerFault("count_ticket_missing")

        async def write(c, project):
            row = await self._op(c, pair, kind)
            if row[0] != "reserved":
                raise LedgerFault("attempt_already_claimed")
            if kind == "generation":
                count = await self._op(c, pair, "count")
                if count[0] not in ("responded_held", "settled") or count[5] is None:
                    raise LedgerFault("count_result_missing")
            # Prevent later operations from skipping an unresolved earlier pair.
            if await (
                await c.execute(
                    "SELECT 1 FROM spend_operations WHERE run_id=%s AND ordinal<%s "
                    "AND ((kind='generation' AND state<>'settled') OR "
                    "(kind='count' AND state NOT IN ('responded_held','settled'))) LIMIT 1",
                    (pair.run, pair.ordinal),
                )
            ).fetchone():
                raise LedgerFault("run_reconciliation_pending")
            counts = await (
                await c.execute(
                    "SELECT count(*),count(*) FILTER (WHERE kind=%s) FROM spend_operations "
                    "WHERE run_id=%s AND wire_ordinal IS NOT NULL",
                    (kind, pair.run),
                )
            ).fetchone()
            if counts[0] >= 6 or counts[1] >= 3:
                raise LedgerFault("wire_exhausted")
            operation = pair.pair + ("-c" if kind == "count" else "-g")
            today = self.time().date()
            await self._limits(c, pair, project, row[1], today, exclude_operation=operation)
            await c.execute(
                "UPDATE spend_operations SET state='sent',day=%s,wire_ordinal=%s "
                "WHERE operation_id=%s",
                (today, counts[0] + 1, operation),
            )
            return counts[0] + 1

        return await self._owned(pair.project, write)

    async def accept_count(self, pair, counted_input):
        pair.checked()
        if type(counted_input) is not int or not 1 <= counted_input <= pair.input_ceiling:
            raise LedgerFault("count_invalid_or_exceeded")

        async def write(c, project):
            count = await self._op(c, pair, "count")
            generation = await self._op(c, pair, "generation")
            if count[0] in ("responded_held", "settled"):
                if count[5] != counted_input:
                    raise LedgerFault("count_result_conflict")
                return False
            if count[0] != "sent" or generation[0] != "reserved":
                raise LedgerFault("count_result_conflict")
            # The count is acknowledged but its cost is STILL fully held.
            await c.execute(
                "UPDATE spend_operations SET state='responded_held',counted_input=%s "
                "WHERE pair_id=%s AND kind='count'",
                (counted_input, pair.pair),
            )
            await c.execute(
                "UPDATE spend_operations SET input_bound=%s,reserved_micro=%s "
                "WHERE pair_id=%s AND kind='generation'",
                (counted_input, reserve_micro(counted_input, pair.output_cap), pair.pair),
            )
            return True

        created = await self._owned(pair.project, write)
        if created:
            self._tickets[pair.pair] = counted_input

    async def settle_generation(self, pair, usage: ActualUsage, *, model=MODEL, tier="default"):
        pair.checked()
        usage = ActualUsage.model_validate(usage.model_dump())
        fingerprint = digest([usage.model_dump(), model, tier])

        async def write(c, project):
            row = await self._op(c, pair, "generation")
            if row[0] == "settled":
                if row[6] != fingerprint:
                    raise LedgerFault("settlement_conflict")
                return row[2]
            if row[0] != "sent":
                raise LedgerFault("attempt_not_sent")
            reason = discrepancy(usage, model, tier, row[3], row[4], exact=True)
            if reason:
                await self._freeze(
                    c,
                    pair.project,
                    "mixed",
                    pair.pair + "-g",
                    reason,
                    usage.model_dump(),
                    model,
                    tier,
                )
                return None
            if await self._has_observation(c, pair.project, "mixed", pair.pair + "-g"):
                return None
            cost = cost_micro(usage)
            await c.execute(
                "UPDATE spend_operations SET state='settled',actual_micro=%s,usage=%s,"
                "settlement_hash=%s WHERE pair_id=%s AND kind='generation'",
                (cost, Jsonb(usage.model_dump()), fingerprint, pair.pair),
            )
            return cost

        result = await self._owned(pair.project, write)
        if result is None:
            raise LedgerFault("pricing_or_usage_discrepancy")
        return result

    async def settle_count(self, pair, actual_micro, *, evidence="synthetic-count-charge-v1"):
        pair.checked()
        money(actual_micro)
        if evidence != "synthetic-count-charge-v1":
            raise ValueError("Known synthetic evidence within quote required")
        fingerprint = digest([actual_micro, evidence])

        async def write(c, project):
            row = await self._op(c, pair, "count")
            if row[0] == "settled":
                if actual_micro > pair.count_ceiling_micro:
                    raise ValueError("Known synthetic evidence within quote required")
                if row[6] != fingerprint:
                    raise LedgerFault("settlement_conflict")
                return row[2]
            if row[0] != "responded_held":
                raise LedgerFault("count_charge_unknown")
            if actual_micro > pair.count_ceiling_micro:
                await self._freeze(
                    c,
                    pair.project,
                    "mixed",
                    pair.pair + "-c",
                    "count_price",
                    {"charge_micro": actual_micro},
                    MODEL,
                    "default",
                )
                return None
            if await self._has_observation(c, pair.project, "mixed", pair.pair + "-c"):
                raise LedgerFault("pricing_or_usage_discrepancy")
            await c.execute(
                "UPDATE spend_operations SET state='settled',actual_micro=%s,settlement_hash=%s "
                "WHERE pair_id=%s AND kind='count'",
                (actual_micro, fingerprint, pair.pair),
            )
            return actual_micro

        result = await self._owned(pair.project, write)
        if result is None:
            raise ValueError("Count pricing discrepancy")
        return result

    async def abandon_pair(self, pair):
        """Release only durable proof of NO send claim; sent/held costs survive."""
        pair.checked()
        self.invalidate(pair)

        async def write(c, project):
            await self._pair(c, pair)
            await c.execute(
                "UPDATE spend_operations SET state='not_sent' "
                "WHERE pair_id=%s AND state='reserved'",
                (pair.pair,),
            )

        await self._owned(pair.project, write)

    async def reconcile_mixed(self, project):
        async def read(c, row):
            return await (
                await c.execute(
                    "SELECT pair_id,kind,state,reserved_micro,actual_micro,counted_input,"
                    "wire_ordinal "
                    "FROM spend_operations WHERE project_id=%s ORDER BY pair_id,kind",
                    (project,),
                )
            ).fetchall()

        rows = await self._owned(project, read, reconcile=True)
        self._uncertain.discard(project)
        return rows
