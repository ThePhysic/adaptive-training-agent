"""Ratified E9: ten fixed public controls, replay-only, no CLI or genuine opener."""

import asyncio
import hashlib
import hmac
import re
from datetime import timedelta

import httpx
from psycopg.types.json import Jsonb

from experiments import counted_probe as shared
from experiments import independent_cases as cases
from experiments import opening_collection as fixed
from future_training.agent.budget import Deadline, SystemClock
from future_training.agent.orchestration import Agent
from future_training.agent.protocol import canonical
from future_training.approval import finish_owned
from future_training.domain.catalog import load_catalog
from future_training.experiments.model_evaluation import SyntheticProfile, load_suite
from future_training.experiments.model_scoring import Observation, score
from future_training.identity import Principal
from future_training.persistence.counted_spending import CountedSpendingLedger
from future_training.providers.counted import CountedResponseSession
from future_training.providers.http import LocalTLS
from future_training.providers.responses import ResponsesReplay
from future_training.schemas import GenerateRequest, SavedProfile

ROOT = fixed.ROOT
STUDY = "synthetic-e9-ten-public-replay-v1"
SCOPE = ("e9-public", "e9-grant", "e9-session")
KEY = bytes([9] * 32)  # Public NONSECRET issuer simulation, never genuine authority.
SPEC = "docs/implementation/f3-e9-replay-collection-contract.md"
LIMIT = 131072
STATUSES = ("not_started", "interrupted", "indeterminate", "failed", "completed")


def freeze():
    base = fixed.freeze()
    files = dict(base["files"])
    for name in (
        SPEC,
        "tests/test_synthetic_collection.py",
        "docs/implementation/f3-e9-synthetic-binding-proposal.md",
    ):
        files[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    body = dict(
        version="evaluation-configuration-freeze-v4",
        status="candidate_not_owner_approved",
        files=dict(sorted(files.items())),
        selection_sha256=base["selection_sha256"],
        historical_e6_sha256=hashlib.sha256(
            (ROOT / "docs/implementation/evidence/f3-e6-freeze-candidate.json").read_bytes()
        ).hexdigest(),
        scorer=base["scorer"],
        rubric=base["rubric"],
        live_enabled=False,
        monetary_authority=False,
    )
    return {**body, "fingerprint": cases.sealed.digest(body)}


def population(configuration):
    source = {c.case_id: c for c in load_suite()[1]}
    result = []
    for ordinal, name in enumerate(cases.IDS, 1):
        c = source[name]
        raw = canonical(
            dict(
                version="independent-case-v1",
                case_id=f"fixture-{ordinal:02}",
                ordinal=ordinal,
                profile=c.profile.model_dump(mode="json"),
                request_text="",
                expected_outcome="plan",
                required_tools=c.required_tools,
                coverage=["matrix", "duration", "schedule"],
                checks="all_common_hard_checks_v1",
                catalog_sha256=load_catalog().fingerprint(),
                freeze_sha256=configuration["fingerprint"],
                selection_sha256=configuration["selection_sha256"],
                origin=dict(
                    kind="developer_fixture",
                    state="synthetic_fixture",
                    public_fixture_id=name,
                    attestation_ref=None,
                    opening_ref=None,
                ),
            )
        )
        result.append(cases.canonical_fixture(raw))
    return tuple(result)


def ordinal_checked(ordinal):
    if type(ordinal) is not int or not 1 <= ordinal <= 10:
        raise ValueError("public_ordinal_required")


class Issuer:
    """Bounded synthetic issued-digest pins; not independent human authentication."""

    def __init__(self, *, now):
        self.now, self.issued = now, set()

    def issue(self, binding):
        if len(self.issued) >= 40:
            raise ValueError("synthetic_receipt_limit")
        now = self.now()
        body = dict(
            version="synthetic-ten-receipt-v1",
            operation="counted-replay-once",
            binding=binding,
            starts=now.isoformat(),
            expires=(now + timedelta(minutes=30)).isoformat(),
        )
        raw = canonical(
            dict(body=body, tag=hmac.new(KEY, canonical(body), hashlib.sha256).hexdigest())
        )
        self.issued.add(hashlib.sha256(raw).hexdigest())
        return raw

    def check(self, raw, binding):
        from datetime import datetime

        try:
            v = cases.json_object(raw, 8192)
            b = v["body"]
            if (
                set(v) != {"body", "tag"}
                or set(b) != {"version", "operation", "binding", "starts", "expires"}
                or b["version"] != "synthetic-ten-receipt-v1"
                or b["operation"] != "counted-replay-once"
                or canonical(b["binding"]) != canonical(binding)
                or not hmac.compare_digest(
                    v["tag"], hmac.new(KEY, canonical(b), hashlib.sha256).hexdigest()
                )
                or hashlib.sha256(raw).hexdigest() not in self.issued
            ):
                raise ValueError
            start, end = datetime.fromisoformat(b["starts"]), datetime.fromisoformat(b["expires"])
            if (
                start.utcoffset() != timedelta(0)
                or end.utcoffset() != timedelta(0)
                or not timedelta(0) < end - start <= timedelta(minutes=30)
                or not start <= self.now() < end
            ):
                raise ValueError
        except Exception:
            raise ValueError("synthetic_receipt_rejected") from None


DDL = """CREATE TABLE IF NOT EXISTS experiment_e9_schedule (
 slot integer PRIMARY KEY CHECK(slot=1), header jsonb NOT NULL);
 CREATE TABLE IF NOT EXISTS experiment_e9_results (
 ordinal integer PRIMARY KEY CHECK(ordinal BETWEEN 1 AND 10),
 binding jsonb NOT NULL, receipt_sha text NOT NULL CHECK(length(receipt_sha)=64),
 result jsonb CHECK(result IS NULL OR octet_length(result::text)<131072))"""


def unknown_accounting():
    return dict(
        status="unknown",
        operations=None,
        known_charged_micro=None,
        held_micro=None,
        liability_micro=None,
        actual_total_micro=None,
    )


class Collection:
    def __init__(self, ledger, issuer, *, clock=None):
        if type(ledger) is not CountedSpendingLedger or type(issuer) is not Issuer:
            raise ValueError("exact_synthetic_replay_scope_required")
        self.ledger, self.issuer, self.clock = ledger, issuer, clock or SystemClock()
        self.configuration = freeze()
        self.originals = population(self.configuration)
        self.header = dict(
            study=STUDY,
            configuration=self.configuration["fingerprint"],
            selection=self.configuration["selection_sha256"],
            scope=list(SCOPE),
            root=cases.sealed.digest([hashlib.sha256(c).hexdigest() for c in self.originals]),
        )
        self.used = set()
        self._write_tokens = {}

    def check_source(self):
        if canonical(freeze()) != canonical(self.configuration):
            raise ValueError("synthetic_configuration_changed")
        expected = dict(
            study=STUDY,
            configuration=self.configuration["fingerprint"],
            selection=self.configuration["selection_sha256"],
            scope=list(SCOPE),
            root=cases.sealed.digest([hashlib.sha256(c).hexdigest() for c in self.originals]),
        )
        if canonical(self.header) != canonical(expected):
            raise ValueError("synthetic_schedule_changed")

    def binding(self, ordinal):
        ordinal_checked(ordinal)
        raw = self.originals[ordinal - 1]
        c = cases.CaseContent.model_validate_json(cases.canonical_fixture(raw))
        if (
            c.ordinal != ordinal
            or c.origin.public_fixture_id != cases.IDS[ordinal - 1]
            or c.freeze_sha256 != self.header["configuration"]
            or c.selection_sha256 != self.header["selection"]
        ):
            raise ValueError("public_case_binding_mismatch")
        return dict(
            **self.header,
            ordinal=ordinal,
            case_id=c.case_id,
            public_id=c.origin.public_fixture_id,
            variant="replay",
            run=f"e9-case-{ordinal:02}",
            content=cases.sealed.curator_token(
                cases.TEST_KEY, self.header["configuration"], raw, purpose="content"
            ),
            input=cases.sealed.input_fingerprint(c.profile.model_dump(), ""),
        )

    def receipt(self, ordinal):
        self.check_source()
        return self.issuer.issue(self.binding(ordinal))

    async def connection(self, *, readonly=False):
        c = await self.ledger.connect()
        try:
            if readonly:
                await c.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            name = (await (await c.execute("SELECT current_schema()")).fetchone())[0]
            if not re.fullmatch(r"f103_test_[a-f0-9]{32}", name or ""):
                raise ValueError("disposable_schema_required")
            if hasattr(self, "schema") and self.schema != name:
                raise ValueError("synthetic_database_changed")
            self.schema = name
            await c.execute("SET LOCAL statement_timeout='3000ms'")
            await c.execute("SET LOCAL lock_timeout='1500ms'")
            mode = await (
                await c.execute("SELECT mode FROM spend_projects WHERE project_id=%s", (SCOPE[0],))
            ).fetchone()
            if mode != ("replay",):
                raise ValueError("replay_project_required")
            return c
        except BaseException:
            await c.close()
            raise

    def fence_path(self, ordinal=None):
        directory = ROOT / ".cache/f3-e9-implementation/fences" / self.schema
        if any(p.is_symlink() or p.is_junction() for p in (directory, *directory.parents)):
            raise ValueError("synthetic_fence_path_rejected")
        directory.mkdir(parents=True, exist_ok=True)
        return directory / ("schedule.json" if ordinal is None else f"case-{ordinal:02}.json")

    async def initialize(self):
        self.check_source()
        async with asyncio.timeout(5):
            c = await self.connection()
            try:
                path = self.fence_path()
                if path.exists():
                    if path.stat().st_size > 8192 or canonical(
                        cases.json_object(path.read_bytes())
                    ) != canonical(self.header):
                        raise ValueError("synthetic_schedule_conflict")
                else:
                    cases.sealed.write_exclusive(path, self.header)
                await c.execute(DDL)
                await c.execute(
                    "INSERT INTO experiment_e9_schedule VALUES(1,%s) ON CONFLICT DO NOTHING",
                    (Jsonb(self.header),),
                )
                await self.check_header(c)
                await c.commit()
            finally:
                await c.close()

    async def check_header(self, c):
        row = await (
            await c.execute("SELECT header FROM experiment_e9_schedule WHERE slot=1")
        ).fetchone()
        if row is None or canonical(row[0]) != canonical(self.header):
            raise ValueError("synthetic_schedule_conflict")

    async def rows(self):
        self.check_source()
        async with asyncio.timeout(5):
            c = await self.connection(readonly=True)
            try:
                await self.check_header(c)
                return await (
                    await c.execute(
                        "SELECT ordinal,binding,receipt_sha,result FROM experiment_e9_results "
                        "ORDER BY ordinal LIMIT 11"
                    )
                ).fetchall()
            finally:
                await c.close()

    async def claim(self, b, receipt):
        async with asyncio.timeout(5):
            c = await self.connection()
            try:
                await self.check_header(c)
                prior = await (
                    await c.execute(
                        "SELECT count(*) FROM spend_pairs WHERE project_id=%s AND run_id=%s",
                        (SCOPE[0], b["run"]),
                    )
                ).fetchone()
                if prior != (0,):
                    raise ValueError("financial_run_not_fresh")
                await c.execute(
                    "INSERT INTO experiment_e9_results VALUES(%s,%s,%s,NULL)",
                    (b["ordinal"], Jsonb(b), hashlib.sha256(receipt).hexdigest()),
                )
                await c.commit()
            finally:
                await c.close()

    async def _finish(self, b, receipt, result, token):
        if token is None or self._write_tokens.pop(b["ordinal"], None) is not token:
            raise ValueError("owned_execution_required")
        self.validate_result(result, b)
        if result["receipt_sha"] != hashlib.sha256(receipt).hexdigest():
            raise ValueError("result_receipt_conflict")
        async with asyncio.timeout(5):
            c = await self.connection()
            try:
                row = await (
                    await c.execute(
                        "UPDATE experiment_e9_results SET result=%s WHERE ordinal=%s "
                        "AND binding=%s AND receipt_sha=%s AND result IS NULL RETURNING ordinal",
                        (Jsonb(result), b["ordinal"], Jsonb(b), result["receipt_sha"]),
                    )
                ).fetchone()
                if row != (b["ordinal"],):
                    raise ValueError("first_result_conflict")
                await c.commit()
            finally:
                await c.close()

    async def accounting(self, b):
        async with asyncio.timeout(5):
            c = await self.connection(readonly=True)
            try:
                h = await (
                    await c.execute(
                        "SELECT frozen,disabled FROM spend_projects WHERE project_id=%s",
                        (SCOPE[0],),
                    )
                ).fetchone()
                rows = await (
                    await c.execute(
                        "SELECT b.ordinal,o.kind,o.state,o.reserved_micro,o.actual_micro,"
                        "o.counted_input,o.wire_ordinal,o.usage FROM spend_operations o "
                        "JOIN spend_pairs b USING(pair_id) WHERE b.project_id=%s AND b.run_id=%s "
                        "ORDER BY b.ordinal,o.kind LIMIT 7",
                        (SCOPE[0], b["run"]),
                    )
                ).fetchall()
                discrepancies = await (
                    await c.execute(
                        "SELECT reason,numbers FROM spend_observations WHERE project_id=%s LIMIT 7",
                        (SCOPE[0],),
                    )
                ).fetchall()
            finally:
                await c.close()
        return shared.accounting_rows(
            rows,
            discrepancies,
            pending=SCOPE[0] in self.ledger._uncertain,
            frozen=h[0],
            disabled=h[1],
        )

    async def run(self, ordinal, receipt, transport):
        deadline = Deadline(self.clock)
        ordinal_checked(ordinal)
        if type(transport) not in (httpx.MockTransport, LocalTLS):
            raise ValueError("fixed_local_transport_required")
        self.check_source()
        b = self.binding(ordinal)
        self.issuer.check(receipt, b)
        existing = next((r for r in await self.rows() if r[0] == ordinal), None)
        if existing:
            if (
                canonical(existing[1]) != canonical(b)
                or existing[2] != hashlib.sha256(receipt).hexdigest()
            ):
                raise ValueError("first_result_conflict")
            if existing[3] is None:
                raise ValueError("first_result_pending")
            self.validate_result(existing[3], b)
            return existing[3]  # Duplicate readback, never execution.
        if ordinal in self.used:
            raise ValueError("first_result_pending")
        self.used.add(ordinal)
        try:
            async with deadline.scope():
                deadline.check()
                cases.sealed.write_exclusive(self.fence_path(ordinal), b)
                await finish_owned(self.claim(b, receipt))
                self.issuer.check(receipt, b)
                self.check_source()
                deadline.check()
                token = object()
                self._write_tokens[ordinal] = token
                return await self._execute(b, receipt, transport, deadline, token)
        except asyncio.CancelledError:
            raise
        except Exception:
            raise ValueError("synthetic_collection_outcome_uncertain") from None
        finally:
            self._write_tokens.pop(ordinal, None)

    async def _execute(self, b, receipt, transport, deadline, token):
        if token is None or self._write_tokens.get(b["ordinal"]) is not token:
            raise ValueError("owned_execution_required")
        case = next(c for c in load_suite()[1] if c.case_id == b["public_id"])
        profiles = SyntheticProfile(case.profile)
        observed = shared.Observations(SavedProfile(revision=1, preferences=case.profile))
        provider = ResponsesReplay(
            transport, ledger=self.ledger, scope=SCOPE, counted=True, count_ceiling_micro=1000
        )
        original = provider.for_request

        def session():
            s = original()
            if type(s) is not CountedResponseSession or observed.sessions:
                raise ValueError("single_counted_replay_session_required")
            s.run_id = b["run"]  # Fixed claimed identity before any reservation/send.
            observed.sessions.append(s)
            admit, complete, close = s.admit, s.complete, s.aclose

            async def admission(payload, *args):
                deadline.check()
                s.deadline.started = min(s.deadline.started, deadline.started)
                s.deadline.expires = min(s.deadline.expires, deadline.expires)
                observed._context(payload)
                return await admit(payload, *args)

            async def completion(request):
                raw = await complete(request)
                observed._response(raw)
                return raw

            async def closing():
                try:
                    await close()
                except BaseException:
                    observed.reasons.add("cleanup_uncertain")
                    raise

            s.admit, s.complete, s.aclose = admission, completion, closing
            return s

        provider.for_request = session
        result, failure = None, None
        try:
            result = await Agent(
                profiles, load_catalog(), provider=provider, clock=self.clock
            ).generate(Principal.A, GenerateRequest(profile_revision=1))
        except BaseException as exc:
            failure = exc
            observed.reasons.add(
                "cancelled" if isinstance(exc, asyncio.CancelledError) else "execution_incomplete"
            )
        finally:
            provider.__dict__.pop("for_request", None)
            for s in observed.sessions:
                s.__dict__.pop("admit", None)
                s.__dict__.pop("complete", None)
                s.__dict__.pop("aclose", None)
                if not s.closed or s.history or s.pending:
                    observed.reasons.add("cleanup_uncertain")

        async def collect():
            try:
                financial = await self.accounting(b)
            except Exception:
                financial = unknown_accounting()
                observed.reasons.add("accounting_unknown")
            try:
                self.check_source()
                self.issuer.check(receipt, b)
            except ValueError:
                observed.reasons.add("provenance_invalid")
            o, scored = observed.finish(
                result, financial, evidence_source="replay", no_publication=True
            )
            value = dict(
                version="synthetic-ten-result-v1",
                provenance="actual_local_counted_replay_not_model_or_human",
                financial_authority="replay_not_money",
                binding=b,
                receipt_sha=hashlib.sha256(receipt).hexdigest(),
                evidence_complete=not observed.reasons and bool(observed.responses),
                reasons=sorted(observed.reasons),
                responses=observed.responses,
                proposals=observed.proposals,
                tool_attempts=observed.attempts,
                observation=o.model_dump() if o else None,
                scored=scored,
                accounting=financial,
                reported_usage=[u.model_dump() for u in result.provider_usage] if result else None,
                uncertain_attempts=result.metrics.uncertain_attempts if result else None,
            )
            value["disposition"] = disposition(value)
            await self._finish(b, receipt, value, token)
            return value

        try:
            value = await finish_owned(collect())
        finally:
            observed.calls.clear()
            observed.results.clear()
            observed.call_indices.clear()
            observed.sessions.clear()
        if isinstance(failure, asyncio.CancelledError):
            raise failure
        return value

    def validate_result(self, value, binding):
        try:
            if (
                type(value) is not dict
                or len(canonical(value)) > LIMIT
                or set(value)
                != {
                    "version",
                    "provenance",
                    "financial_authority",
                    "binding",
                    "receipt_sha",
                    "evidence_complete",
                    "reasons",
                    "responses",
                    "proposals",
                    "tool_attempts",
                    "observation",
                    "scored",
                    "accounting",
                    "reported_usage",
                    "uncertain_attempts",
                    "disposition",
                }
                or value["version"] != "synthetic-ten-result-v1"
                or value["provenance"] != "actual_local_counted_replay_not_model_or_human"
                or value["financial_authority"] != "replay_not_money"
                or canonical(value["binding"]) != canonical(binding)
                or not re.fullmatch(r"[a-f0-9]{64}", value["receipt_sha"])
            ):
                raise ValueError
            case = next(c for c in load_suite()[1] if c.case_id == binding["public_id"])
            financial = value["accounting"]
            if financial["status"] == "unknown":
                if canonical(financial) != canonical(unknown_accounting()):
                    raise ValueError
            else:
                if any(
                    type(financial[k]) is not bool
                    for k in ("frozen", "disabled", "reconciliation_pending")
                ):
                    raise ValueError
                operations = financial["operations"]
                rows = [
                    tuple(
                        o[k]
                        for k in (
                            "pair",
                            "kind",
                            "state",
                            "reserved_micro",
                            "actual_micro",
                            "counted_input",
                            "wire_ordinal",
                            "usage",
                        )
                    )
                    for o in operations
                ]
                if len({(o["pair"], o["kind"]) for o in operations}) != len(operations):
                    raise ValueError
                expected_financial = shared.accounting_rows(
                    rows,
                    [(o["reason"], o["numbers"]) for o in financial["discrepancies"]],
                    pending=financial["reconciliation_pending"],
                    frozen=financial["frozen"],
                    disabled=financial["disabled"],
                )
                if canonical(financial) != canonical(expected_financial):
                    raise ValueError
            shared.validate_observations(value, case)
            if value["observation"] is not None:
                if set(value["observation"]) != set(Observation.model_fields):
                    raise ValueError
                expected = score(
                    case, Observation.model_validate(value["observation"]), load_catalog()
                )
                if canonical(expected) != canonical(value["scored"]):
                    raise ValueError
            elif value["scored"] is not None or value["evidence_complete"]:
                raise ValueError
            if value["disposition"] != disposition(value):
                raise ValueError
        except Exception:
            raise ValueError("synthetic_result_invalid") from None

    async def summary(self):
        rows = await self.rows()
        if len(rows) > 10:
            raise ValueError("synthetic_schedule_overflow")
        rows = {r[0]: r for r in rows}
        slots, charge, held, unknown, observed, scored, passed = [], 0, 0, 0, 0, 0, 0
        counts = {k: 0 for k in STATUSES}
        observed_counts = dict(count_requests=0, provider_requests=0, wire_requests=0)
        for i in range(1, 11):
            row = rows.get(i)
            status, value = "not_started", None
            if row:
                if canonical(row[1]) != canonical(self.binding(i)):
                    raise ValueError("synthetic_binding_conflict")
                value = row[3]
                if value is not None:
                    try:
                        self.validate_result(value, row[1])
                        if value["receipt_sha"] != row[2]:
                            raise ValueError("synthetic_receipt_conflict")
                    except ValueError:
                        value = None
                if value is not None:
                    status = value["disposition"]
                    observed += value["observation"] is not None
                    scored += value["scored"] is not None
                    passed += bool(value["scored"] and value["scored"]["hard_passed"])
                    f = value["accounting"]
                    charge += f["known_charged_micro"] or 0
                    held += f["held_micro"] or 0
                    unknown += f["held_micro"] is None
                    if value["observation"]:
                        for k in observed_counts:
                            observed_counts[k] += value["observation"]["counts"][k]
                else:
                    status = "indeterminate"
                    unknown += 1
            elif self.fence_path(i).exists():
                status = "indeterminate"
                unknown += 1
            counts[status] += 1
            slots.append(
                dict(
                    ordinal=i,
                    case_id=f"fixture-{i:02}",
                    disposition=status,
                    scored=value is not None and value["scored"] is not None,
                    hard_passed=value["scored"]["hard_passed"]
                    if value and value["scored"]
                    else None,
                )
            )
        return dict(
            version="synthetic-ten-summary-v1",
            provenance="local_replay_not_independent_or_model_quality",
            configuration=self.header["configuration"],
            selection=self.header["selection"],
            scheduled=10,
            observed=observed,
            scored=scored,
            hard_passed=passed,
            slots=slots,
            dispositions=counts,
            observed_counts_subtotal=observed_counts,
            known_charged_subtotal_micro=charge,
            known_held_subtotal_micro=held,
            unknown_liability_slots=unknown,
            actual_total_micro=None,
            quality_scores=None,
        )


def disposition(value):
    if "cancelled" in value["reasons"]:
        return "interrupted"
    if not value["evidence_complete"]:
        return "indeterminate"
    if not value["scored"]["hard_passed"]:
        return "failed"
    return "completed"


def open_genuine(*args, **kwargs):
    raise ValueError("genuine_collection_denied")
