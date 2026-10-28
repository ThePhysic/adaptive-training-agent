"""Offline, instance-local evidence rehearsal. No CLI, factory, grant or live mode.

Kept outside src: the accepted evaluation manifest fingerprints every src file.
Only an already constructed synthetic SingleProbe is observed, once. The original
implementation owns execution, retries, transport, validation and cleanup.
"""

import asyncio
import hashlib
import os
from dataclasses import asdict
from pathlib import Path

import httpx

from future_training.agent.orchestration import RunResult
from future_training.agent.protocol import (
    RESPONSE_ADAPTER,
    FinalResponse,
    ModelInput,
    ToolCallsResponse,
    canonical,
    parse_json,
)
from future_training.agent.tools import ReadTools, ToolResult
from future_training.domain.catalog import load_catalog
from future_training.experiments.model_evaluation import load_suite, manifest
from future_training.experiments.model_scoring import (
    Observation,
    ToolEvidence,
    check_call,
    proposal_checks,
    score,
)
from future_training.persistence.authority import AuthorityLedger
from future_training.providers.accounting import ActualUsage
from future_training.providers.authority import approved_preferences
from future_training.providers.http import LocalTLS
from future_training.providers.probe import FixedProfile, ProbeSession, ResponsesProbe, SingleProbe
from future_training.schemas import SavedProfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = "counted-probe-evidence-v1"
LIMIT = 131072


def offline(probe):
    """Source/type/transport/accounting checks, never an activation workaround."""
    if type(probe) is not SingleProbe or type(probe.provider) is not ResponsesProbe:
        raise ValueError("fixed_offline_probe_required")
    p = probe.provider
    if (
        p.kind != "replay"
        or p.evidence_source != "authority_fixture"
        or type(p.ledger) is not AuthorityLedger
        or p.ledger.execution != "simulation"
        or p.spec != p.ledger.spec
        or p.spec.count_bound.kind != "synthetic_fixture"
        or type(p.transport) not in (httpx.MockTransport, LocalTLS)
    ):
        raise ValueError("fixed_offline_probe_required")


async def accounting(probe):
    """Bounded read-only consistent SQL snapshot; never reconcile/unfreeze/settle.

    ProbeConnection routes trusted table identifiers to the separate probe namespace.
    Private selectors/IDs stay in parameters and are never returned in artifacts.
    """
    offline(probe)
    ledger, s = probe.provider.ledger, probe.provider.spec
    async with asyncio.timeout(5), await ledger.connect() as c:
        await c.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        await c.execute("SET LOCAL statement_timeout='3000ms'")
        header = await (
            await c.execute(
                "SELECT a.state,p.mode,p.disabled,p.frozen,a.run_id FROM probe_authorities a "
                "JOIN spend_projects p USING(project_id) WHERE a.project_id=%s "
                "AND a.account_id=%s AND a.authority_id=%s AND a.fingerprint=%s",
                (s.project, s.account, s.authority_id, s.fingerprint()),
            )
        ).fetchone()
        if (
            header is None
            or header[0] not in ("simulation", "revoked")
            or header[1] != "simulation"
        ):
            raise ValueError("simulation_accounting_required")
        rows = await (
            await c.execute(
                "SELECT b.ordinal,o.kind,o.state,o.reserved_micro,o.actual_micro,"
                "o.counted_input,o.wire_ordinal,o.usage FROM spend_operations o "
                "JOIN spend_pairs b USING(pair_id) WHERE b.project_id=%s AND b.run_id=%s "
                "ORDER BY b.ordinal,o.kind LIMIT 7",
                (s.project, header[4]),
            )
        ).fetchall()
        discrepancies = await (
            await c.execute(
                "SELECT reason,numbers FROM spend_observations WHERE project_id=%s LIMIT 7",
                (s.project,),
            )
        ).fetchall()
    return accounting_rows(
        rows,
        discrepancies,
        pending=s.project in ledger._uncertain,
        frozen=header[3],
        disabled=header[2],
    )


def accounting_rows(rows, discrepancies, *, pending, frozen, disabled):
    """Shared bounded numerical projection of native fixture SQL, no writes."""
    if len(rows) > 6 or len(discrepancies) > 6:
        raise ValueError("accounting_evidence_bounds")
    operations = []
    for ordinal, kind, state, reserved, actual, counted, wire, usage in rows:
        if (
            kind not in ("count", "generation")
            or state not in ("reserved", "sent", "responded_held", "settled", "not_sent")
            or type(ordinal) is not int
            or not 1 <= ordinal <= 3
        ):
            raise ValueError("accounting_evidence_invalid")
        if (
            type(reserved) is not int
            or reserved < 0
            or (state == "settled") != (actual is not None)
        ):
            raise ValueError("accounting_evidence_invalid")
        operations.append(
            dict(
                pair=ordinal,
                kind=kind,
                state=state,
                reserved_micro=reserved,
                actual_micro=actual,
                counted_input=counted,
                wire_ordinal=wire,
                usage=ActualUsage.model_validate(usage).model_dump() if usage else None,
            )
        )
    held = sum(o["reserved_micro"] for o in operations if o["state"] not in ("settled", "not_sent"))
    charged = sum(o["actual_micro"] for o in operations if o["state"] == "settled")
    # Only database-enforced finite numerical observations cross this boundary.
    from future_training.providers.observations import FIELDS

    reasons = {
        "model",
        "tier",
        "cache_ttl",
        "usage_input",
        "usage_output",
        "cache_details",
        "usage_missing",
        "usage_invalid",
        "count_price",
    }
    if any(
        reason not in reasons
        or not isinstance(nums, dict)
        or set(nums) - FIELDS
        or any(type(v) is not int or not 0 <= v <= 10**9 for v in nums.values())
        for reason, nums in discrepancies
    ):
        raise ValueError("accounting_evidence_invalid")
    return dict(
        status="observed_simulation_sql",
        operations=operations,
        claimed_counts=sum(
            o["kind"] == "count" and o["wire_ordinal"] is not None for o in operations
        ),
        claimed_generations=sum(
            o["kind"] == "generation" and o["wire_ordinal"] is not None for o in operations
        ),
        known_charged_micro=charged,
        held_micro=None if pending else held,
        liability_micro=None if pending else charged + held,
        committed_liability_micro=charged + held,
        actual_total_micro=None if pending or held else charged,
        frozen=frozen,
        disabled=disabled,
        reconciliation_pending=pending,
        discrepancies=[dict(reason=r, numbers=n) for r, n in discrepancies],
    )


class Observations:
    """Pure, bounded observation logic. No execution or authorization capability."""

    def __init__(self, profile):
        self.catalog = load_catalog()
        self.profile = SavedProfile.model_validate_json(profile.model_dump_json())
        self.calls, self.results = {}, {}
        self.attempts, self.call_indices = [], {}
        self.repairs = 0
        self.tools, self.proposals, self.responses = [], [], []
        self.sessions, self.reasons = [], set()

    def _context(self, payload):
        if type(payload) is not bytes or len(payload) > 65536:
            raise ValueError("observation_input_bounds")
        context = ModelInput.model_validate_json(payload)
        if context.profile != self.profile or context.request_text or context.previous_plan:
            self.reasons.add("context_mismatch")
        repairs = sum(m.role == "repair" for m in context.messages)
        if repairs > self.repairs:
            if repairs != self.repairs + 1 or not self.proposals:
                self.reasons.add("repair_observation_missing")
            else:
                self.proposals[-1]["agent_rejected"] = True
            self.repairs = repairs
        for message in context.messages:
            if message.role != "tool":
                continue
            result = ToolResult.model_validate_json(message.data_json)
            encoded = canonical(result.model_dump())
            if result.call_id in self.results:
                if self.results[result.call_id] != encoded:
                    self.reasons.add("tool_result_changed")
                continue
            if result.call_id not in self.calls or len(self.tools) >= 4:
                self.reasons.add("tool_observation_missing")
                continue
            call = self.calls[result.call_id]
            name, valid, authorized = check_call(call, self.profile.preferences, self.catalog)
            checked = True
            try:
                ReadTools(FixedProfile(), self.catalog).checked_bytes(self.profile, call, result)
            except Exception:
                checked = False
            self.results[result.call_id] = encoded
            self.attempts[self.call_indices[result.call_id]].update(
                result_observed=True, result_valid=checked, status=result.status
            )
            self.tools.append(
                ToolEvidence(
                    name=name,
                    arguments_valid=valid,
                    authorized=authorized,
                    result_valid=checked,
                    status=result.status,
                )
            )

    def _response(self, raw):
        if type(raw) is not bytes or len(raw) > 16384:
            raise ValueError("observation_response_bounds")
        response = RESPONSE_ADAPTER.validate_json(raw)
        if len(self.responses) >= 3:
            self.reasons.add("observation_overflow")
            return
        self.responses.append(response.kind)
        if isinstance(response, ToolCallsResponse):
            for call in response.calls:
                if call.call_id in self.calls or len(self.calls) >= 12:
                    self.reasons.add("duplicate_or_excess_calls")
                else:
                    self.calls[call.call_id] = call
                    name, valid, authorized = check_call(
                        call, self.profile.preferences, self.catalog
                    )
                    self.call_indices[call.call_id] = len(self.attempts)
                    self.attempts.append(
                        dict(
                            name=name,
                            arguments_valid=valid,
                            authorized=authorized,
                            result_observed=False,
                            result_valid=None,
                            status=None,
                        )
                    )
        elif isinstance(response, FinalResponse):
            try:
                value = parse_json(response.output_json)
                schema, domain = proposal_checks(value, self.profile.preferences, self.catalog)
            except Exception:
                schema = domain = False
            self.proposals.append(
                dict(schema_valid=schema, domain_valid=domain, agent_rejected=False)
            )

    def finish(self, result, financial, *, evidence_source, no_publication):
        if financial["status"] != "unknown":
            if financial["reconciliation_pending"]:
                self.reasons.add("accounting_uncertain")
            if financial["frozen"] or financial["discrepancies"]:
                self.reasons.add("accounting_discrepancy")
            if financial["disabled"]:
                self.reasons.add("shutdown_observed")
        observed, scored = None, None
        if type(result) is not RunResult or result.evidence_source != evidence_source:
            self.reasons.add("terminal_missing")
        else:
            counts = {
                k: v
                for k, v in asdict(result.metrics).items()
                if k not in ("uncertain_attempts", "finish_reasons", "token_kind")
            }
            counts.update(count_requests=result.count_requests, wire_requests=result.wire_requests)
            if len(self.responses) != counts["provider_requests"]:
                self.reasons.add("response_observation_missing")
            if len(self.tools) != counts["tool_dispatches"] or set(self.calls) != set(self.results):
                self.reasons.add("tool_observation_missing")
            if financial["status"] != "unknown" and (
                financial["claimed_counts"] != result.count_requests
                or financial["claimed_generations"] != result.metrics.provider_requests
            ):
                self.reasons.add("accounting_counter_mismatch")
            if result.metrics.uncertain_attempts:
                self.reasons.add("provider_usage_uncertain")
            if self.repairs != result.metrics.semantic_repairs:
                self.reasons.add("repair_observation_missing")
            if not self.responses:
                self.reasons.add("response_observation_missing")
            complete = not self.reasons and bool(self.responses)
            # Explicit false flags block hard pass when any evidence is missing.
            observed = Observation(
                source="replay",
                output_json=result.canonical_bytes.decode(),
                terminal_state=result.states[-1].value,
                tools=self.tools,
                proposal_schema_valid=complete and all(p["schema_valid"] for p in self.proposals),
                proposals_domain_valid=complete
                and all(p["domain_valid"] and not p["agent_rejected"] for p in self.proposals),
                counts=counts,
                no_publication=no_publication,
            )
            case = next(
                c
                for c in load_suite()[1]
                if c.fixture == "normal"
                and c.profile == self.profile.preferences
                and not c.request_text
            )
            scored = score(case, observed, self.catalog)
        return observed, scored


class Rehearsal(Observations):
    """One exact owned fixed probe. Original execution/type gates remain intact."""

    def __init__(self, probe):
        offline(probe)
        if (
            probe.used
            or "run" in probe.__dict__
            or any(
                key in probe.provider.__dict__
                for key in ("for_request", "create_http", "make_pair")
            )
        ):
            raise ValueError("fresh_owned_probe_required")
        self.probe, self.used = probe, False
        self._packet = None
        self._persist_attempted = False
        super().__init__(SavedProfile(revision=1, preferences=approved_preferences()))

    def _session(self, original):
        offline(self.probe)
        session = original()
        if type(session) is not ProbeSession or self.sessions:
            raise ValueError("single_owned_session_required")
        self.sessions.append(session)
        admit, complete = session.admit, session.complete

        async def observed_admit(payload, *args):
            offline(self.probe)
            self._context(payload)
            return await admit(payload, *args)

        async def observed_complete(request):
            offline(self.probe)
            raw = await complete(request)
            self._response(raw)
            return raw  # Exact original bytes; no model output substitution.

        session.admit, session.complete = observed_admit, observed_complete
        return session

    async def run(self):
        if self.used:
            raise ValueError("rehearsal_already_used")
        self.used = True
        offline(self.probe)
        provider = self.probe.provider
        if self.probe.used or "for_request" in provider.__dict__:
            raise ValueError("fresh_owned_probe_required")
        result, failure = None, None
        original = provider.for_request
        provider.for_request = lambda: self._session(original)
        try:
            result = await self.probe.run()
        except BaseException as exc:
            failure = exc
            self.reasons.add(
                "cancelled" if isinstance(exc, asyncio.CancelledError) else "execution_incomplete"
            )
        finally:
            provider.__dict__.pop("for_request", None)
            for session in self.sessions:
                session.__dict__.pop("admit", None)
                session.__dict__.pop("complete", None)
                if not session.closed or session.history or session.pending:
                    self.reasons.add("cleanup_uncertain")
        try:
            financial = await accounting(self.probe)
        except BaseException as exc:
            financial = dict(
                status="unknown",
                operations=None,
                known_charged_micro=None,
                held_micro=None,
                liability_micro=None,
                actual_total_micro=None,
            )
            self.reasons.add("accounting_unknown")
            if isinstance(exc, asyncio.CancelledError):
                failure = exc
                self.reasons.add("cancelled")
        try:
            self._finish(result, financial)
        finally:
            self.calls.clear()
            self.results.clear()
            self.call_indices.clear()
            self.sessions.clear()
        if isinstance(failure, asyncio.CancelledError):
            raise failure
        return self.packet()

    def _finish(self, result, financial):
        try:
            offline(self.probe)
        except ValueError:
            self.reasons.add("provenance_invalid")
        observed, scored = self.finish(
            result,
            financial,
            evidence_source="authority_fixture",
            no_publication=type(self.probe) is SingleProbe,
        )
        current = manifest()
        selected = next(
            c
            for c in load_suite()[1]
            if c.fixture == "normal"
            and c.profile == self.profile.preferences
            and not c.request_text
        )
        current.update(
            version="counted-probe-rehearsal-manifest-v1",
            selection="one_fixed_compatibility_profile_not_50_case_execution",
            case_ids=[selected.case_id],
            eligibility=[r for r in current["eligibility"] if r["case_id"] == selected.case_id],
            measurement="one_counted_fixture_latency_not_collected_not_real_model_timing",
        )
        current["counted_probe_adapter"] = dict(
            version=VERSION,
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            protocol="3-count-3-generation-6-combined",
            pricing="synthetic_fixture_only",
            transport="mock_transport"
            if type(self.probe.provider.transport) is httpx.MockTransport
            else "loopback_tls",
            fixture_source_sha256={
                name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                for name in (
                    "tests/test_counted_probe_evidence.py",
                    "tests/authority_doubles.py",
                    "tests/test_token_admission.py",
                    "tests/responses_doubles.py",
                    "tests/local_tls_doubles.py",
                    "tests/approval_db_doubles.py",
                )
            },
        )
        packet = dict(
            version=VERSION,
            source="replay",
            provenance="authority_fixture",
            financial_authority="simulation_not_money",
            model_quality="unverified",
            human_scores="not_collected",
            hosted_export=False,
            evidence_complete=not self.reasons and bool(self.responses),
            reasons=sorted(self.reasons),
            responses=self.responses,
            proposals=self.proposals,
            tool_attempts=self.attempts,
            observation=observed.model_dump() if observed else None,
            scored=scored,
            accounting=financial,
            reported_usage=[u.model_dump() for u in result.provider_usage]
            if type(result) is RunResult
            else None,
            uncertain_attempts=result.metrics.uncertain_attempts
            if type(result) is RunResult
            else None,
            manifest=current,
        )
        validate_packet(packet)
        encoded = canonical(packet)
        if len(encoded) > LIMIT:
            raise ValueError("evidence_packet_too_large")
        self._packet = encoded

    def packet(self):
        if self._packet is None:
            raise ValueError("evidence_not_finished")
        return parse_json(self._packet)

    def persist(self, path):
        """Exclusive bounded local synthetic artifact. Failure never reruns a probe."""
        if self._persist_attempted:
            raise ValueError("persistence_already_attempted")
        self._persist_attempted = True
        body = canonical(self.packet()) + b"\n"
        path = Path(path).absolute()
        if not path.resolve().is_relative_to((ROOT / ".cache/f3-e1").resolve()):
            raise ValueError("local_synthetic_artifact_required")
        if any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)):
            raise ValueError("artifact_link_rejected")
        with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())


def validate_packet(packet):
    """Finite rejection only; no untrusted validation details reach ordinary logs."""
    try:
        if type(packet) is not dict:
            raise ValueError
        return _validate_packet(packet)
    except Exception:
        raise ValueError("invalid_synthetic_evidence") from None


def _validate_packet(packet):
    """Consistency only, NOT authentication or proof of genuine execution."""
    if (
        packet.get("version"),
        packet.get("source"),
        packet.get("provenance"),
        packet.get("financial_authority"),
        packet.get("model_quality"),
        packet.get("human_scores"),
        packet.get("hosted_export"),
    ) != (
        VERSION,
        "replay",
        "authority_fixture",
        "simulation_not_money",
        "unverified",
        "not_collected",
        False,
    ):
        raise ValueError("synthetic_provenance_required")
    if len(canonical(packet)) > LIMIT or set(packet) != {
        "version",
        "source",
        "provenance",
        "financial_authority",
        "model_quality",
        "human_scores",
        "hosted_export",
        "evidence_complete",
        "reasons",
        "responses",
        "proposals",
        "observation",
        "scored",
        "accounting",
        "manifest",
        "reported_usage",
        "uncertain_attempts",
        "tool_attempts",
    }:
        raise ValueError("evidence_packet_shape")
    m = packet["manifest"]
    if (
        m["live_enabled"] is not False
        or m["generation_allowance_usd"] != 0
        or m["count_allowance_usd"] != 0
        or m["human_scores"] != "not_collected"
        or m["judge_scores"] != "not_run"
        or len(m["case_ids"]) != 1
        or m["selection"] != "one_fixed_compatibility_profile_not_50_case_execution"
        or m["counted_probe_adapter"]["pricing"] != "synthetic_fixture_only"
        or m["counted_probe_adapter"]["transport"] not in ("mock_transport", "loopback_tls")
    ):
        raise ValueError("synthetic_provenance_required")
    return validate_observations(
        packet, next(c for c in load_suite()[1] if c.case_id == packet["manifest"]["case_ids"][0])
    )


def validate_observations(packet, case):
    """Consistency only. Caller must validate its own fixed provenance envelope."""
    responses, proposals, reasons = packet["responses"], packet["proposals"], packet["reasons"]
    allowed_reasons = {
        "context_mismatch",
        "tool_result_changed",
        "tool_observation_missing",
        "observation_overflow",
        "duplicate_or_excess_calls",
        "cancelled",
        "execution_incomplete",
        "cleanup_uncertain",
        "accounting_unknown",
        "provenance_invalid",
        "terminal_missing",
        "response_observation_missing",
        "accounting_counter_mismatch",
        "provider_usage_uncertain",
        "repair_observation_missing",
        "accounting_uncertain",
        "accounting_discrepancy",
        "shutdown_observed",
    }
    if (
        type(responses) is not list
        or len(responses) > 3
        or any(r not in ("final", "tool_calls", "refusal", "truncated") for r in responses)
        or type(proposals) is not list
        or len(proposals) != responses.count("final")
        or any(
            type(p) is not dict
            or set(p) != {"schema_valid", "domain_valid", "agent_rejected"}
            or any(type(v) is not bool for v in p.values())
            for p in proposals
        )
        or type(reasons) is not list
        or len(reasons) > len(allowed_reasons)
        or any(type(r) is not str or r not in allowed_reasons for r in reasons)
        or type(packet["evidence_complete"]) is not bool
        or packet["evidence_complete"] != (not reasons and bool(responses))
    ):
        raise ValueError("evidence_observations_inconsistent")
    if packet["reported_usage"] is not None:
        if type(packet["reported_usage"]) is not list or len(packet["reported_usage"]) > 3:
            raise ValueError("usage_evidence_invalid")
        for usage in packet["reported_usage"]:
            ActualUsage.model_validate(usage)
    attempts = packet["tool_attempts"]
    if (
        type(attempts) is not list
        or len(attempts) > 12
        or any(
            type(a) is not dict
            or set(a)
            != {
                "name",
                "arguments_valid",
                "authorized",
                "result_observed",
                "result_valid",
                "status",
            }
            or a["name"] not in ("search_exercises", "get_user_preferences", "unknown")
            or any(
                type(a[k]) is not bool for k in ("arguments_valid", "authorized", "result_observed")
            )
            or (
                a["result_observed"]
                and (type(a["result_valid"]) is not bool or a["status"] not in ("ok", "error"))
            )
            or (
                not a["result_observed"]
                and (a["result_valid"] is not None or a["status"] is not None)
            )
            for a in attempts
        )
    ):
        raise ValueError("tool_evidence_invalid")
    f = packet["accounting"]
    if f["status"] == "unknown":
        if packet["evidence_complete"] or any(
            f[k] is not None
            for k in (
                "operations",
                "known_charged_micro",
                "held_micro",
                "liability_micro",
                "actual_total_micro",
            )
        ):
            raise ValueError("unknown_accounting_is_not_zero")
    elif f["status"] == "observed_simulation_sql":
        operations = f["operations"]
        if type(operations) is not list or len(operations) > 6:
            raise ValueError("accounting_evidence_invalid")
        for o in operations:
            if set(o) != {
                "pair",
                "kind",
                "state",
                "reserved_micro",
                "actual_micro",
                "counted_input",
                "wire_ordinal",
                "usage",
            }:
                raise ValueError("accounting_evidence_invalid")
            if type(o["reserved_micro"]) is not int or not 0 <= o["reserved_micro"] <= 10**9:
                raise ValueError("accounting_evidence_invalid")
            if (
                o["kind"] not in ("count", "generation")
                or o["state"] not in ("reserved", "sent", "responded_held", "settled", "not_sent")
                or type(o["pair"]) is not int
                or not 1 <= o["pair"] <= 3
            ):
                raise ValueError("accounting_evidence_invalid")
            if o["state"] in ("reserved", "not_sent") and o["wire_ordinal"] is not None:
                raise ValueError("accounting_evidence_invalid")
            if o["kind"] == "count" and o["actual_micro"] is not None:
                raise ValueError("count_charge_remains_unknown")
            if o["usage"] is not None:
                ActualUsage.model_validate(o["usage"])
            if (o["state"] == "settled") != (o["actual_micro"] is not None):
                raise ValueError("accounting_evidence_invalid")
            if o["actual_micro"] is not None and (
                type(o["actual_micro"]) is not int or o["actual_micro"] < 0
            ):
                raise ValueError("accounting_evidence_invalid")
        held = sum(
            o["reserved_micro"] for o in operations if o["state"] not in ("settled", "not_sent")
        )
        charged = sum(o["actual_micro"] for o in operations if o["state"] == "settled")
        pending = f["reconciliation_pending"]
        if (
            f["held_micro"],
            f["known_charged_micro"],
            f["liability_micro"],
            f["actual_total_micro"],
        ) != (
            None if pending else held,
            charged,
            None if pending else held + charged,
            None if pending or held else charged,
        ):
            raise ValueError("accounting_evidence_invalid")
        if f["committed_liability_micro"] != held + charged:
            raise ValueError("accounting_evidence_invalid")
    else:
        raise ValueError("accounting_evidence_invalid")
    if packet["observation"] is not None:
        observation = Observation.model_validate(packet["observation"])
        if observation.source != "replay":
            raise ValueError("synthetic_provenance_required")
        complete = packet["evidence_complete"]
        if (
            observation.proposal_schema_valid
            != (complete and all(p["schema_valid"] for p in proposals))
            or observation.proposals_domain_valid
            != (complete and all(p["domain_valid"] and not p["agent_rejected"] for p in proposals))
            or complete
            and (
                len(responses) != observation.counts["provider_requests"]
                or len(observation.tools) != observation.counts["tool_dispatches"]
                or packet["accounting"]["status"] != "observed_simulation_sql"
                or packet["accounting"]["claimed_counts"] != observation.counts["count_requests"]
                or packet["accounting"]["claimed_generations"]
                != observation.counts["provider_requests"]
                or len(attempts) != len(observation.tools)
                or any(not a["result_observed"] for a in attempts)
            )
        ):
            raise ValueError("evidence_observations_inconsistent")
        catalog = load_catalog()
        if score(case, observation, catalog) != packet["scored"]:
            raise ValueError("evidence_score_mismatch")
        if not packet["evidence_complete"] and packet["scored"]["hard_passed"]:
            raise ValueError("incomplete_cannot_pass")
    return packet
