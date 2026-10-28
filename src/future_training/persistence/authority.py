"""Separate probe tables, reusing the accepted counted SQL transaction algorithm.

Prepared proposals and synthetic simulations confer NO monetary authority. Actual
activation still hits both source-review barriers. Replay tables are untouched.
"""

import re
from dataclasses import dataclass

import psycopg
from psycopg.types.json import Jsonb

from future_training.agent.protocol import canonical
from future_training.persistence.counted_spending import CountedSpendingLedger, PairReservation
from future_training.persistence.profiles import connect_local
from future_training.persistence.spending import LedgerFault, identifier, money
from future_training.providers.accounting import reserve_micro
from future_training.providers.authority import AuthoritySpec
from future_training.providers.counting import COUNT_ENDPOINT
from future_training.providers.gates import ENDPOINT

_TABLES = re.compile(r"\bspend_(projects|grants|sessions|attempts|pairs|operations|observations)\b")


class ProbeConnection:
    """Fixed identifier routing of trusted existing SQL, never of values/parameters."""

    def __init__(self, connection):
        self.connection = connection

    async def execute(self, query, params=None):
        return await self.connection.execute(_TABLES.sub(r"probe_spend_\1", query), params)

    async def commit(self):
        await self.connection.commit()

    async def close(self):
        await self.connection.close()

    async def __aenter__(self):
        await self.connection.__aenter__()
        return self

    async def __aexit__(self, *args):
        return await self.connection.__aexit__(*args)


@dataclass(frozen=True, repr=False)
class AuthorityPair(PairReservation):
    count_quote: str = "provider-count-bound-v1"

    def checked(self):
        for v in (self.project, self.grant, self.session, self.run, self.pair):
            identifier(v)
        identifier(self.pair + "-c"), identifier(self.pair + "-g")
        if type(self.ordinal) is not int or not 1 <= self.ordinal <= 3:
            raise ValueError("Invalid pair ordinal")
        if self.count_quote != "provider-count-bound-v1" or money(self.count_ceiling_micro) <= 0:
            raise ValueError("Verified positive counting ceiling required")
        reserve_micro(self.input_ceiling, self.output_cap)
        if self.input_ceiling < 1:
            raise ValueError("Positive input ceiling required")
        return self


@dataclass(frozen=True, repr=False)
class SendClaim:
    pair_id: str
    kind: str
    body: bytes
    nonce: object

    def __repr__(self):
        return "<SendClaim redacted>"


class AuthorityLedger(CountedSpendingLedger):
    @classmethod
    async def load(cls, project, account, *, connect=connect_local, **kwargs):
        """Ordered private metadata read; stale assets may reconcile but not send."""
        identifier(project), identifier(account)
        try:
            async with await connect() as c:
                await c.execute("SET LOCAL statement_timeout='3000ms'")
                await c.execute("SET LOCAL lock_timeout='1500ms'")
                await c.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended(%s,10403))", (project,)
                )
                row = await (
                    await c.execute(
                        "SELECT specification FROM probe_authorities "
                        "WHERE project_id=%s AND account_id=%s",
                        (project, account),
                    )
                ).fetchone()
                if row is None:
                    raise LedgerFault("authority_missing")
                specification = AuthoritySpec.model_validate_json(canonical(row[0]))
            return cls(specification, connect=connect, **kwargs)
        except psycopg.Error:
            raise LedgerFault("reconciliation_pending") from None

    def __init__(self, specification: AuthoritySpec, *, execution="simulation", **kwargs):
        self.spec = AuthoritySpec.model_validate_json(specification.model_dump_json())
        if execution not in ("simulation", "live"):
            raise ValueError("Explicit probe execution kind required")
        self.execution = execution
        self._acknowledged = {}
        self._send_claims = {}
        super().__init__(**kwargs)
        original = self.connect

        async def connect():
            return ProbeConnection(await original())

        self.connect = connect

    def __repr__(self):
        return "<AuthorityLedger bound-redacted>"

    async def _lock_project(self, connection, project):
        if project != self.spec.project:
            raise LedgerFault("authority_mismatch")
        # Shared by issuance, reserve, claim, revoke and reconciliation. The
        # advisory lock precedes every row lock; no reversed issuer lock order.
        await connection.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s,10403))", (project,)
        )
        await connection.execute(
            "INSERT INTO spend_projects(project_id,limit_micro,day_limit_micro) VALUES (%s,0,0) "
            "ON CONFLICT DO NOTHING",
            (project,),
        )
        return await super()._lock_project(connection, project)

    async def _authority(self, c):
        row = await (
            await c.execute(
                "SELECT state,specification,fingerprint,run_id FROM probe_authorities "
                "WHERE project_id=%s FOR UPDATE",
                (self.spec.project,),
            )
        ).fetchone()
        if (
            row is None
            or row[2] != self.spec.fingerprint()
            or (AuthoritySpec.model_validate_json(canonical(row[1])) != self.spec)
        ):
            raise LedgerFault("authority_mismatch")
        return row

    async def _owned(self, project, body, *, reconcile=False):
        async def protected(c, row):
            existing = await (
                await c.execute(
                    "SELECT fingerprint,specification FROM probe_authorities "
                    "WHERE project_id=%s FOR UPDATE",
                    (project,),
                )
            ).fetchone()
            if existing is not None:
                if existing[0] != self.spec.fingerprint() or (
                    AuthoritySpec.model_validate_json(canonical(existing[1])) != self.spec
                ):
                    raise LedgerFault("authority_conflict")
            return await body(c, row)

        return await super()._owned(project, protected, reconcile=reconcile)

    async def prepare(self):
        self.spec.checked(positive=True)
        return await self._issue("prepared")

    async def simulate(self):
        """Nonmonetary fixtures only, with synthetic evidence and local transport."""
        self.spec.checked(positive=True)
        if self.spec.count_bound.kind != "synthetic_fixture":
            raise LedgerFault("fixture_authority_required")
        return await self._issue("simulation")

    async def activate(self, gate):
        """Fully specified but unreachable positive issuance until separate review."""
        self.spec.checked(positive=True, network=True)
        from future_training.providers.gates import LiveGate
        from future_training.providers.sender import require_live_financial_authority

        LiveGate.check(gate)
        require_live_financial_authority()
        return await self._issue("active")

    async def _issue(self, state):
        if state == "active":
            from future_training.providers.sender import require_live_financial_authority

            require_live_financial_authority()
        self.spec.checked(positive=state != "prepared", network=state == "active")
        s = self.spec

        async def write(c, project):
            if s.expires_at <= self.time():
                raise LedgerFault("authority_expired")
            existing = await (
                await c.execute(
                    "SELECT fingerprint,state FROM probe_authorities "
                    "WHERE project_id=%s FOR UPDATE",
                    (s.project,),
                )
            ).fetchone()
            if existing:
                if existing == (s.fingerprint(), state):
                    return state
                if existing != (s.fingerprint(), "prepared") or state not in (
                    "simulation",
                    "active",
                ):
                    raise LedgerFault("authority_conflict")
            if existing:
                await c.execute(
                    "UPDATE probe_authorities SET state=%s WHERE project_id=%s", (state, s.project)
                )
            else:
                await c.execute(
                    "INSERT INTO probe_authorities(project_id,account_id,authority_id,state,"
                    "specification,fingerprint) VALUES (%s,%s,%s,%s,%s,%s)",
                    (
                        s.project,
                        s.account,
                        s.authority_id,
                        state,
                        Jsonb(s.model_dump(mode="json")),
                        s.fingerprint(),
                    ),
                )
            if state != "prepared":
                await c.execute(
                    "UPDATE spend_projects SET limit_micro=%s,day_limit_micro=%s,"
                    "mode=%s WHERE project_id=%s",
                    (
                        s.project_limit_micro,
                        s.day_limit_micro,
                        "live" if state == "active" else "simulation",
                        s.project,
                    ),
                )
                await c.execute(
                    "INSERT INTO spend_grants VALUES (%s,%s,%s,%s)",
                    (s.grant, s.project, s.grant_limit_micro, s.expires_at),
                )
                await c.execute(
                    "INSERT INTO spend_sessions VALUES (%s,%s,%s,%s)",
                    (s.session, s.grant, s.session_limit_micro, s.expires_at),
                )
            return state

        return await self._owned(s.project, write)

    async def _limits(self, c, request, project, proposed, day, **kwargs):
        s = self.spec.checked(positive=True, network=self.execution == "live")
        row = await self._authority(c)
        if row[0] != ("active" if self.execution == "live" else "simulation"):
            raise LedgerFault("authority_inactive")
        if self.execution == "live":
            from future_training.providers.sender import require_live_financial_authority

            require_live_financial_authority()
        if not s.starts_at <= self.time() < s.expires_at:
            raise LedgerFault("authority_expired")
        if (request.project, request.grant, request.session) != (s.project, s.grant, s.session):
            raise LedgerFault("authority_mismatch")
        bound = await (
            await c.execute(
                "SELECT g.limit_micro,s.limit_micro,g.expires_at,s.expires_at,p.mode "
                "FROM spend_grants g JOIN spend_sessions s ON s.grant_id=g.grant_id "
                "JOIN spend_projects p ON p.project_id=g.project_id "
                "WHERE p.project_id=%s AND g.grant_id=%s AND s.session_id=%s",
                (s.project, s.grant, s.session),
            )
        ).fetchone()
        if project[:2] != (s.project_limit_micro, s.day_limit_micro) or bound != (
            s.grant_limit_micro,
            s.session_limit_micro,
            s.expires_at,
            s.expires_at,
            "live" if self.execution == "live" else "simulation",
        ):
            raise LedgerFault("authority_mismatch")
        if row[3] is not None and row[3] != request.run:
            raise LedgerFault("single_request_already_claimed")
        await super()._limits(c, request, project, proposed, day, **kwargs)
        await c.execute(
            "UPDATE probe_authorities SET run_id=%s WHERE project_id=%s", (request.run, s.project)
        )

    async def reserve_pair(self, pair):
        if type(pair) is not AuthorityPair or pair.count_ceiling_micro != (
            self.spec.count_bound.ceiling_micro
        ):
            raise LedgerFault("authority_mismatch")
        return await super().reserve_pair(pair)

    async def claim(self, pair, kind):
        if type(pair) is not AuthorityPair:
            raise LedgerFault("authority_mismatch")
        wire = await super().claim(pair, kind)
        self._acknowledged[(pair.pair, kind)] = (pair.fingerprint(), wire)
        return wire

    def authorize_send(self, pair, kind, body):
        self.spec.checked(positive=True, network=self.execution == "live")
        if self.spec.project in self._uncertain:
            raise LedgerFault("reconciliation_pending")
        if not self.spec.starts_at <= self.time() < self.spec.expires_at:
            raise LedgerFault("authority_expired")
        if type(pair) is not AuthorityPair or kind not in ("count", "generation"):
            raise LedgerFault("send_claim_mismatch")
        acknowledged = self._acknowledged.pop((pair.pair, kind), None)
        if acknowledged is None or acknowledged[0] != pair.fingerprint():
            raise LedgerFault("send_claim_missing")
        if type(body) is not bytes or len(body) > 65536:
            raise LedgerFault("send_claim_mismatch")
        proof = SendClaim(pair.pair, kind, body, object())
        self._send_claims[proof.nonce] = proof
        return proof

    def consume_send(self, proof, method, url, body):
        stored = self._send_claims.pop(proof.nonce, None) if type(proof) is SendClaim else None
        if (
            type(proof) is not SendClaim
            or stored is not proof
            or method != "POST"
            or url != (COUNT_ENDPOINT if proof.kind == "count" else ENDPOINT)
            or body != proof.body
        ):
            raise LedgerFault("send_claim_mismatch")

    def discard_send(self, proof):
        self._send_claims.pop(proof.nonce, None)

    def invalidate(self, pair):
        super().invalidate(pair)
        self._acknowledged = {k: v for k, v in self._acknowledged.items() if k[0] != pair.pair}
        self._send_claims = {k: v for k, v in self._send_claims.items() if v.pair_id != pair.pair}

    async def revoke(self):
        async def write(c, row):
            await self._authority(c)
            await c.execute(
                "UPDATE probe_authorities SET state='revoked' WHERE project_id=%s",
                (self.spec.project,),
            )
            await c.execute(
                "UPDATE spend_projects SET disabled=true WHERE project_id=%s", (self.spec.project,)
            )

        try:
            await self._owned(self.spec.project, write, reconcile=True)
        finally:
            self._acknowledged.clear()
            self._send_claims.clear()
            self._tickets.clear()

    async def stop(self, project):
        if project != self.spec.project:
            raise LedgerFault("authority_mismatch")
        await self.revoke()

    async def settle_count(self, *args, **kwargs):
        raise LedgerFault("count_charge_unknown")

    async def create_replay_project(self, *args, **kwargs):
        raise LedgerFault("separate_authority_required")

    async def grant(self, *args, **kwargs):
        raise LedgerFault("separate_authority_required")

    async def session(self, *args, **kwargs):
        raise LedgerFault("separate_authority_required")

    async def reserve(self, *args, **kwargs):
        raise LedgerFault("counted_authority_required")

    async def mark_sent(self, *args, **kwargs):
        raise LedgerFault("counted_authority_required")

    async def settle(self, *args, **kwargs):
        raise LedgerFault("counted_authority_required")
