"""F3-E6: fixed public control, synthetic receipt, native SQL, actual local probe.

No genuine key/case/opener, live execution, command line or application route.
The only supported collection slot is the existing compatibility profile.
"""

import asyncio
import hashlib
import hmac
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

from psycopg.types.json import Jsonb

from experiments import counted_probe as recorder
from experiments import independent_cases as cases
from future_training.agent.budget import Deadline, SystemClock
from future_training.agent.protocol import canonical
from future_training.approval import finish_owned
from future_training.domain.catalog import load_catalog
from future_training.experiments.model_scoring import Observation, ScoringFacts, score_facts

ROOT = Path(__file__).resolve().parents[1]
STUDY = "synthetic-e6-primary"
AUTH_KEY = bytes(reversed(range(32)))  # Public NONSECRET authentication simulation only.
SPEC = "docs/implementation/f3-e6-opening-and-collection-contract.md"
LIMIT = 262144
BINDING_FIELDS = (
    "study",
    "configuration",
    "selection",
    "root",
    "case_id",
    "ordinal",
    "variant",
    "content_commitment",
    "input_commitment",
    "financial_binding",
    "logical_execution",
)


def freeze():
    base = cases.freeze()
    public = cases.sealed.public_sources()
    files = dict(base["files"])
    for name in (SPEC, "tests/test_opening_collection.py"):
        files[name] = hashlib.sha256(public[name].read_bytes()).hexdigest()
    body = dict(
        version="evaluation-configuration-freeze-v3",
        status="candidate_not_owner_approved",
        files=dict(sorted(files.items())),
        selection_sha256=base["selection_sha256"],
        scorer=base["scorer"],
        scorer_interface=base["scorer_interface"],
        rubric=base["rubric"],
        historical_e4_candidate_sha256=hashlib.sha256(
            (ROOT / "docs/implementation/evidence/f3-e4-freeze-candidate.json").read_bytes()
        ).hexdigest(),
        live_enabled=False,
        monetary_authority=False,
    )
    return {**body, "fingerprint": cases.sealed.digest(body)}


def check_freeze(value):
    if type(value) is not dict or canonical(value) != canonical(freeze()):
        raise ValueError("simulation_source_changed")


@dataclass(frozen=True, repr=False)
class Preparation:
    original: tuple[bytes, ...]
    manifest: bytes
    pins: bytes
    configuration: bytes


def verified(preparation):
    """E2 shapes/E4 canonical controls, all ten commitments, v3 binding."""
    try:
        if (
            type(preparation) is not Preparation
            or type(preparation.original) is not tuple
            or len(preparation.original) != 10
        ):
            raise ValueError
        f = cases.json_object(preparation.configuration)
        check_freeze(f)
        m = cases.sealed.SealedManifest.model_validate_json(
            canonical(cases.json_object(preparation.manifest))
        )
        p = cases.sealed.ReviewedPins.model_validate_json(
            canonical(cases.json_object(preparation.pins))
        )
        fp = f["fingerprint"]
        context = cases.sealed.curator_token(
            cases.TEST_KEY, fp, b"SYNTHETIC", purpose="key_context"
        )
        if (
            m.kind != "synthetic_test"
            or p.kind != "synthetic_test"
            or m.freeze_sha256 != fp
            or p.freeze_sha256 != fp
            or m.key_context != context
            or p.key_context != context
            or m.content_root != p.content_root
            or cases.sealed.digest(m.model_dump()) != p.manifest_sha256
            or m.curator_attestation_ref != p.curator_attestation_ref
            or m.owner_freeze_ref != p.owner_freeze_ref
            or m.public_exposure_index_sha256
            != cases.sealed.digest(cases.sealed.exposed_input_index())
        ):
            raise ValueError
        inputs = []
        for ordinal, (raw, entry) in enumerate(
            zip(preparation.original, m.entries, strict=True), 1
        ):
            body = cases.canonical_fixture(raw)
            if body != raw:
                raise ValueError  # Committed representation is canonical; do not mutate on opening.
            c = cases.CaseContent.model_validate_json(body)
            token = cases.sealed.curator_token(
                cases.TEST_KEY,
                fp,
                cases.sealed.input_fingerprint(c.profile.model_dump(), c.request_text).encode(),
                purpose="input",
            )
            if (
                c.ordinal != ordinal
                or c.freeze_sha256 != fp
                or c.selection_sha256 != f["selection_sha256"]
                or token != entry.input_token
                or entry.content_commitment
                != cases.sealed.curator_token(cases.TEST_KEY, fp, raw, purpose="content")
            ):
                raise ValueError
            inputs.append(token)
        if len(set(inputs)) != 10:
            raise ValueError
        exposure = dict(
            version="private-exposure-index-v1",
            freeze_sha256=fp,
            public_exposure_index_sha256=m.public_exposure_index_sha256,
            key_context=context,
            tokens=[
                cases.sealed.curator_token(cases.TEST_KEY, fp, d.encode(), purpose="input")
                for d in cases.sealed.exposed_input_index()
            ],
        )
        if cases.sealed.digest(exposure) != p.exposure_sha256:
            raise ValueError
        return f, m
    except Exception:
        raise ValueError("synthetic_preparation_rejected") from None


class Receipt(cases.Private):
    version: Literal["synthetic-opening-receipt-v1"]
    mode: Literal["synthetic_not_human_authorization"]
    operation: Literal["simulate_counted_probe_once"]
    study: Literal["synthetic-e6-primary"]
    configuration: cases.Digest
    selection: cases.Digest
    root: cases.Digest
    case_id: Literal["fixture-01"]
    ordinal: Literal[1]
    variant: Literal["replay"]
    content_commitment: cases.Digest
    input_commitment: cases.Digest
    financial_binding: cases.Digest
    logical_execution: cases.Digest
    starts_at: datetime
    expires_at: datetime


def binding(preparation, probe):
    recorder.offline(probe)
    f, m = verified(preparation)
    c = cases.CaseContent.model_validate_json(preparation.original[0])
    if c.profile != recorder.approved_preferences():
        raise ValueError("fixed_probe_case_required")
    value = dict(
        study=STUDY,
        configuration=f["fingerprint"],
        selection=f["selection_sha256"],
        root=m.content_root,
        case_id="fixture-01",
        ordinal=1,
        variant="replay",
        content_commitment=m.entries[0].content_commitment,
        input_commitment=m.entries[0].input_token,
        financial_binding=probe.provider.spec.fingerprint(),
    )
    return {**value, "logical_execution": cases.sealed.digest(value)}


class SyntheticAuthority:
    """Explicit fixture trust anchor; not a human identity or genuine signing key.

    HMAC plus issued digest pin, separate from the untrusted receipt. Restart
    requires the trusted fixture issuer/pins; refs supplied by a caller prove nothing.
    """

    def __init__(self, *, now):
        self.now = now
        self._issued = set()

    def issue(self, preparation, probe):
        now = self.now()
        body = Receipt(
            version="synthetic-opening-receipt-v1",
            mode="synthetic_not_human_authorization",
            operation="simulate_counted_probe_once",
            **binding(preparation, probe),
            starts_at=now,
            expires_at=now + timedelta(minutes=30),
        ).model_dump(mode="json")
        tag = hmac.new(AUTH_KEY, canonical(body), hashlib.sha256).hexdigest()
        raw = canonical(dict(body=body, tag=tag))
        self._issued.add(hashlib.sha256(raw).hexdigest())
        return raw

    def authenticate(self, raw, preparation, probe):
        try:
            if type(self) is not SyntheticAuthority:
                raise ValueError
            value = cases.json_object(raw)
            if set(value) != {"body", "tag"} or type(value["tag"]) is not str:
                raise ValueError
            r = Receipt.model_validate_json(canonical(value["body"]))
            if not hmac.compare_digest(
                value["tag"],
                hmac.new(
                    AUTH_KEY, canonical(r.model_dump(mode="json")), hashlib.sha256
                ).hexdigest(),
            ):
                raise ValueError
            if hashlib.sha256(raw).hexdigest() not in self._issued:
                raise ValueError
            if (
                any(getattr(r, k) != v for k, v in binding(preparation, probe).items())
                or type(value["body"]["ordinal"]) is not int
                or r.starts_at.utcoffset() != timedelta(0)
                or r.expires_at.utcoffset() != timedelta(0)
                or not timedelta(0) < r.expires_at - r.starts_at <= timedelta(minutes=30)
                or not r.starts_at <= self.now() < r.expires_at
            ):
                raise ValueError
            return r
        except Exception:
            raise ValueError("synthetic_opening_not_authorized") from None


@dataclass(frozen=True, repr=False)
class OpenedSimulation:
    preparation: Preparation
    receipt: bytes
    original: bytes


def open_simulation(preparation, receipt, authority, probe):
    if type(authority) is not SyntheticAuthority:
        raise ValueError("synthetic_opening_not_authorized")
    authority.authenticate(receipt, preparation, probe)
    return OpenedSimulation(preparation, receipt, preparation.original[0])


class _Recorder(recorder.Rehearsal):
    def __init__(self, probe, deadline):
        super().__init__(probe)
        self.study_deadline = deadline

    def _context(self, payload):
        self.study_deadline.check()
        # The same Agent/session deadline is shortened to include first-claim
        # work. No new budget or longer deadline for count/continuation/repair.
        for session in self.sessions:
            session.deadline.started = min(session.deadline.started, self.study_deadline.started)
            session.deadline.expires = min(session.deadline.expires, self.study_deadline.expires)
        super()._context(payload)


DDL = """CREATE TABLE IF NOT EXISTS experiment_e6_first (
 slot integer PRIMARY KEY CHECK(slot=1),
 binding jsonb NOT NULL CHECK(octet_length(binding::text)<8192),
 receipt_sha text NOT NULL CHECK(length(receipt_sha)=64),
 disposition text NOT NULL CHECK(disposition IN ('claimed_unknown','recorded')),
 evidence jsonb CHECK(evidence IS NULL OR octet_length(evidence::text)<262144),
 CHECK((disposition='recorded')=(evidence IS NOT NULL)))"""


class Collection:
    """One fixed simulation slot, PostgreSQL sole first-result authority.

    No directory/study/run selector. Table only allowed in existing disposable
    integration schemas. No migration/application-owned persistent state.
    """

    def __init__(self, probe, authority):
        recorder.offline(probe)
        if type(authority) is not SyntheticAuthority:
            raise ValueError("synthetic_authority_required")
        self.probe, self.authority, self.used = probe, authority, False

    async def _connection(self):
        c = await self.probe.provider.ledger.connect()
        try:
            name = (await (await c.execute("SELECT current_schema()")).fetchone())[0]
            if not re.fullmatch(r"f103_test_[a-f0-9]{32}", name or ""):
                raise ValueError("disposable_test_schema_required")
            if hasattr(self, "schema") and self.schema != name:
                raise ValueError("simulation_database_changed")
            self.schema = name
            await c.execute("SET LOCAL statement_timeout='3000ms'")
            await c.execute("SET LOCAL lock_timeout='1500ms'")
            return c
        except BaseException:
            await c.close()
            raise

    async def initialize(self):
        async with asyncio.timeout(5):
            c = await self._connection()
            try:
                await c.execute(DDL)
                await c.commit()
            finally:
                await c.close()

    async def _claim(self, b, receipt):
        async with asyncio.timeout(5):
            c = await self._connection()
            try:
                owned = await (
                    await c.execute(
                        "SELECT state,run_id,fingerprint FROM probe_authorities "
                        "WHERE project_id=%s",
                        (self.probe.provider.spec.project,),
                    )
                ).fetchone()
                if owned != ("simulation", None, self.probe.provider.spec.fingerprint()):
                    raise ValueError("fresh_simulation_scope_required")
                await c.execute(
                    "INSERT INTO experiment_e6_first VALUES (1,%s,%s,'claimed_unknown',NULL)",
                    (Jsonb(b), hashlib.sha256(receipt).hexdigest()),
                )
                await c.commit()
            finally:
                await c.close()

    async def _finish(self, b, receipt, result):
        validate_result(result)
        if (
            canonical(result["binding"]) != canonical(b)
            or result["receipt_sha256"] != hashlib.sha256(receipt).hexdigest()
        ):
            raise ValueError("first_result_mismatch")
        if len(canonical(result)) > LIMIT:
            raise ValueError("synthetic_evidence_bounds")
        async with asyncio.timeout(5):
            c = await self._connection()
            try:
                row = await (
                    await c.execute(
                        "UPDATE experiment_e6_first SET disposition='recorded',evidence=%s "
                        "WHERE slot=1 AND binding=%s AND receipt_sha=%s "
                        "AND disposition='claimed_unknown' RETURNING slot",
                        (Jsonb(result), Jsonb(b), hashlib.sha256(receipt).hexdigest()),
                    )
                ).fetchone()
                if row != (1,):
                    raise ValueError("first_result_mismatch")
                await c.commit()
            finally:
                await c.close()

    async def readback(self):
        async with asyncio.timeout(5):
            c = await self._connection()
            try:
                row = await (
                    await c.execute(
                        "SELECT disposition,evidence,binding,receipt_sha "
                        "FROM experiment_e6_first WHERE slot=1"
                    )
                ).fetchone()
            finally:
                await c.close()
        if row is None:
            return dict(disposition="no_committed_claim", outcome_uncertain=True)
        if row[2].get("financial_binding") != self.probe.provider.spec.fingerprint():
            raise ValueError("first_result_binding_mismatch")
        if row[0] == "claimed_unknown":
            return dict(disposition="claimed_unknown", outcome_uncertain=True, accounting=None)
        validate_result(row[1])
        if canonical(row[1]["binding"]) != canonical(row[2]) or row[1]["receipt_sha256"] != row[3]:
            raise ValueError("first_result_binding_mismatch")
        return dict(disposition="recorded", result=row[1])

    def _fence(self, b):
        directory = ROOT / ".cache/f3-e6/attempt-fences"
        if any(p.is_symlink() or p.is_junction() for p in (directory, *directory.parents)):
            raise ValueError("attempt_fence_path_rejected")
        directory.mkdir(parents=True, exist_ok=True)
        # Schema-derived, never receipt/run/config/project/directory-derived.
        # A partial fence also blocks a new handle after an uncertain SQL COMMIT.
        cases.sealed.write_exclusive(
            directory / (self.schema + ".json"), dict(mode="synthetic_attempt_fence", binding=b)
        )

    async def run(self, opened):
        if self.used:
            raise ValueError("collection_already_attempted")
        self.used = True
        if (
            type(opened) is not OpenedSimulation
            or opened.original != opened.preparation.original[0]
        ):
            raise ValueError("opened_simulation_required")
        deadline = Deadline(self.probe.clock if self.probe.clock is not None else SystemClock())
        r = None
        try:
            async with deadline.scope():
                self.authority.authenticate(opened.receipt, opened.preparation, self.probe)
                b = binding(opened.preparation, self.probe)
                r = _Recorder(self.probe, deadline)
                # Resolve/check the only permitted test DB namespace before the
                # durable append-only fence. No selectable output directory.
                c = await self._connection()
                await c.close()
                self._fence(b)
                await finish_owned(self._claim(b, opened.receipt))
                self.authority.authenticate(opened.receipt, opened.preparation, self.probe)
                deadline.check()
                try:
                    packet = await r.run()
                except asyncio.CancelledError:
                    packet = r.packet()
                    result = collected(opened, packet, self.authority, self.probe)
                    await finish_owned(self._finish(b, opened.receipt, result))
                    raise
                result = collected(opened, packet, self.authority, self.probe)
                await finish_owned(self._finish(b, opened.receipt, result))
                return result
        except asyncio.CancelledError:
            raise
        except Exception:
            # Claim/result COMMIT uncertainty must not be called a clean failure.
            raise ValueError("collection_stopped_outcome_uncertain") from None


def collected(opened, packet, authority, probe):
    """Actual E1 normalized evidence, never guessed raw tool arguments/results."""
    recorder.validate_packet(packet)
    guards = []
    try:
        verified(opened.preparation)
    except ValueError:
        guards.append("source_or_preparation_changed")
    try:
        authority.authenticate(opened.receipt, opened.preparation, probe)
    except ValueError:
        guards.append("opening_authorization_expired_or_changed")
    c = cases.CaseContent.model_validate_json(opened.original)
    expected = c.origin.public_fixture_id
    if packet["manifest"]["case_ids"] != [expected]:
        raise ValueError("observed_case_mismatch")
    scored = None
    if packet["evidence_complete"] and packet["observation"] is not None and not guards:
        observed = Observation.model_validate(packet["observation"])
        facts = ScoringFacts(
            case_id=c.case_id,
            split="synthetic_fixture",
            profile=c.profile,
            request_text=c.request_text,
            expected={"replay": c.expected_outcome},
            required_tools=list(c.required_tools),
            fixture="normal",
        )
        scored = score_facts(facts, observed, load_catalog())
    receipt = Receipt.model_validate_json(canonical(cases.json_object(opened.receipt)["body"]))
    result = dict(
        version="synthetic-opening-collection-v1",
        study=STUDY,
        provenance="actual_local_simulation_not_real_model_or_human_evidence",
        financial_authority="simulation_not_money",
        opening="synthetic_authenticated_not_human_approved",
        original_bytes_unchanged=True,
        evidence_complete=packet["evidence_complete"] and not guards,
        outcome_uncertain=not packet["evidence_complete"] or bool(guards),
        guards=guards,
        binding={k: getattr(receipt, k) for k in BINDING_FIELDS},
        receipt_sha256=hashlib.sha256(opened.receipt).hexdigest(),
        common_score=scored,
        packet=packet,
    )
    validate_result(result)
    return result


def validate_result(value):
    try:
        if (
            type(value) is not dict
            or len(canonical(value)) > LIMIT
            or set(value)
            != {
                "version",
                "study",
                "provenance",
                "financial_authority",
                "opening",
                "original_bytes_unchanged",
                "evidence_complete",
                "outcome_uncertain",
                "guards",
                "common_score",
                "packet",
                "binding",
                "receipt_sha256",
            }
            or value["version"] != "synthetic-opening-collection-v1"
            or value["study"] != STUDY
            or value["provenance"] != "actual_local_simulation_not_real_model_or_human_evidence"
            or value["financial_authority"] != "simulation_not_money"
            or value["opening"] != "synthetic_authenticated_not_human_approved"
            or value["original_bytes_unchanged"] is not True
            or type(value["guards"]) is not list
            or len(set(value["guards"])) != len(value["guards"])
            or set(value["guards"])
            - {"source_or_preparation_changed", "opening_authorization_expired_or_changed"}
        ):
            raise ValueError
        b = value["binding"]
        if (
            type(b) is not dict
            or set(b) != set(BINDING_FIELDS)
            or (b["study"], b["case_id"], b["ordinal"], b["variant"])
            != (STUDY, "fixture-01", 1, "replay")
            or type(b["ordinal"]) is not int
            or b["logical_execution"]
            != cases.sealed.digest({k: v for k, v in b.items() if k != "logical_execution"})
            or any(
                type(v) is not str or not re.fullmatch(r"[a-f0-9]{64}", v)
                for v in [
                    value["receipt_sha256"],
                    *[
                        b[k]
                        for k in (
                            "configuration",
                            "selection",
                            "root",
                            "content_commitment",
                            "input_commitment",
                            "financial_binding",
                        )
                    ],
                ]
            )
        ):
            raise ValueError
        p = recorder.validate_packet(value["packet"])
        complete = p["evidence_complete"] and not value["guards"]
        actual = None
        if p["observation"] is not None:
            source = next(c for c in recorder.load_suite()[1] if c.case_id == cases.IDS[0])
            actual = score_facts(
                ScoringFacts(
                    case_id="fixture-01",
                    split="synthetic_fixture",
                    profile=source.profile,
                    request_text=source.request_text,
                    expected={"replay": "plan"},
                    required_tools=source.required_tools,
                    fixture="normal",
                ),
                Observation.model_validate(p["observation"]),
                load_catalog(),
            )
            if canonical(p["scored"]) != canonical(
                {**actual, "case_id": source.case_id, "split": source.split}
            ):
                raise ValueError
        expected = actual if complete else None
        if (
            type(value["evidence_complete"]) is not bool
            or type(value["outcome_uncertain"]) is not bool
            or value["evidence_complete"] != complete
            or value["outcome_uncertain"] != (not complete)
            or p["manifest"]["case_ids"] != [cases.IDS[0]]
            or canonical(value["common_score"]) != canonical(expected)
        ):
            raise ValueError
    except Exception:
        raise ValueError("stored_simulation_evidence_invalid") from None


def open_genuine(*args, **kwargs):
    raise ValueError("genuine_opening_denied")
