"""Offline matched evaluation through the actual typed Agent; no live factory.

Only authored fixtures cross MockTransport. No candidate store, DB write, grant,
provider credential, automatic replay or alternative business rules are present.
"""

import copy
import hashlib
import platform
import subprocess
import time
from collections import Counter
from dataclasses import asdict

import httpx

from future_training.agent.fake import FakeModel, response_bytes
from future_training.agent.orchestration import Agent
from future_training.agent.protocol import (
    RESPONSE_ADAPTER,
    FailureKind,
    FinalResponse,
    ProviderFailure,
    ToolCall,
    ToolCallsResponse,
    canonical,
    parse_json,
)
from future_training.agent.tools import ReadTools
from future_training.domain.baseline import TEMPLATE_VERSION, plan_week
from future_training.domain.catalog import load_catalog
from future_training.domain.duration import DURATION_VERSION
from future_training.domain.validator import VALIDATOR_VERSION
from future_training.errors import ServiceError
from future_training.evaluation import ROOT, load_scenarios, text_sha256
from future_training.experiments.model_eval_assets import DIRECTORY, VERSION
from future_training.experiments.model_review import REVIEW_SEED, RUBRIC_VERSION
from future_training.experiments.model_scoring import (
    SCORER,
    Case,
    Observation,
    ToolEvidence,
    check_call,
    proposal_checks,
    score,
)
from future_training.identity import Principal
from future_training.providers.accounting import RATE_VERSION
from future_training.providers.artifacts import assets as provider_assets
from future_training.providers.responses import ASSETS, ResponsesReplay
from future_training.schemas import GenerateRequest, SavedProfile


def load_suite():
    manifest = parse_json((DIRECTORY / "manifest.json").read_bytes())
    catalog = load_catalog()
    if manifest["version"] != VERSION or manifest["catalog_sha256"] != catalog.fingerprint():
        raise ValueError("Evaluation catalog/version mismatch")
    if manifest["legacy_sha256"] != load_scenarios(catalog)[0]["dataset_sha256"]:
        raise ValueError("Frozen legacy reference mismatch")
    for name, digest in manifest["sha256"].items():
        if (
            name not in ("scenarios.jsonl", "outputs.jsonl")
            or text_sha256(DIRECTORY / name) != digest
        ):
            raise ValueError("Evaluation data checksum mismatch")
    if set(manifest["sha256"]) != {"scenarios.jsonl", "outputs.jsonl"}:
        raise ValueError("Missing evaluation assets")
    if set(manifest["prior_fixture_sha256"]) != {
        "plan.json",
        "tool.json",
        "refusal.json",
        "incomplete.json",
    }:
        raise ValueError("Missing prior fixture hashes")
    for name, digest in manifest["prior_fixture_sha256"].items():
        if name not in ("plan.json", "tool.json", "refusal.json", "incomplete.json") or (
            text_sha256(ASSETS / "fixtures" / name) != digest
        ):
            raise ValueError("Prior fixture mismatch")
    rows = [
        Case.model_validate_json(line)
        for line in (DIRECTORY / "scenarios.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    outputs = [
        parse_json(line)
        for line in (DIRECTORY / "outputs.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    if len(rows) != 50 or len({r.case_id for r in rows}) != 50:
        raise ValueError("Expected exactly fifty unique cases")
    if {k: len(v) for k, v in manifest["splits"].items()} != {
        "development": 40,
        "comparison_candidate": 10,
    }:
        raise ValueError("Expected 40/10 fixed split")
    if len(outputs) != 50 or {r.case_id for r in rows} != {o["case_id"] for o in outputs}:
        raise ValueError("Case/output mapping mismatch")
    if {s: [r.case_id for r in rows if r.split == s] for s in manifest["splits"]} != (
        manifest["splits"]
    ):
        raise ValueError("Split mismatch")
    if any(catalog.unknown_exclusions(r.profile) for r in rows):
        raise ValueError("A case cannot pass profile Save")
    return manifest, rows, {o["case_id"]: o["output"] for o in outputs}


class SyntheticProfile:
    """Read-only evaluation fixture, explicitly not PostgreSQL persistence proof."""

    def __init__(self, profile):
        self._saved = SavedProfile(revision=1, preferences=profile).model_dump_json()

    async def get(self, principal):
        if principal is not Principal.A:
            raise ServiceError(404, "not_found")
        return SavedProfile.model_validate_json(self._saved)


class Recorder:
    def __init__(self, profile, catalog):
        self.profile, self.catalog = profile, catalog
        self.schema = self.domain = True
        self.seen = set()
        self.tools = []

    def output(self, value):
        schema, domain = proposal_checks(value, self.profile, self.catalog)
        self.schema &= schema
        self.domain &= domain

    def calls(self, calls):
        ids = [c.call_id for c in calls]
        if len(set(ids)) != len(ids) or self.seen.intersection(ids):
            self.schema = False
        self.seen.update(ids)


class RecordedTools(ReadTools):
    def __init__(self, profiles, catalog, recorder):
        super().__init__(profiles, catalog)
        self.recorder = recorder

    async def dispatch(self, principal, profile, call):
        name, valid, authorized = check_call(call, profile.preferences, self.catalog)
        result = await super().dispatch(principal, profile, call)
        self.checked_bytes(profile, call, result)
        self.recorder.tools.append(
            ToolEvidence(
                name=name,
                arguments_valid=valid,
                authorized=authorized,
                result_valid=True,
                status=result.status,
            )
        )
        return result


def _call(mode, *, native=False):
    name, args = "search_exercises", {"limit": 20}
    if native:
        args.update(goal=None, experience=None, equipment=None, tag=None)
    if mode == "unknown_tool":
        name = "approve_plan"
    elif mode == "invalid_arguments":
        args["limit"] = 21
    elif mode == "owner_argument":
        name, args = "get_user_preferences", {"owner_id": "other_synthetic_owner"}
    return name, canonical(args).decode()


class ObservedFake:
    kind = "fake"

    def __init__(self, case, output, catalog, recorder):
        self.case, self.output, self.catalog = case, output, catalog
        self.recorder, self.base = recorder, FakeModel(catalog)

    async def complete(self, request):
        mode = self.case.fixture
        if mode == "normal" and self.case.case_id == "ME-C10" and request.attempt == 1:
            call = ToolCall(
                call_id="evaluation-profile", name="get_user_preferences", arguments_json="{}"
            )
            raw = response_bytes(request, kind="tool_calls", calls=[call.model_dump()])
        elif mode == "normal":
            raw = await self.base.complete(request)
        elif mode == "transport":
            raise ProviderFailure(FailureKind.FATAL)
        elif mode == "refusal":
            raw = response_bytes(request, kind="refusal", reason="policy")
        elif request.attempt == 1 or mode == "duplicate_call":
            name, arguments = _call(mode)
            call = ToolCall(call_id="evaluation-call", name=name, arguments_json=arguments)
            raw = response_bytes(request, kind="tool_calls", calls=[call.model_dump()])
        elif mode in ("unknown_tool", "invalid_arguments", "owner_argument"):
            raw = response_bytes(request, kind="refusal", reason="unspecified")
        elif mode == "incomplete":
            raw = response_bytes(request, kind="truncated")
        else:
            raw = response_bytes(
                request,
                kind="final",
                output_json=(
                    "{not-json" if mode == "malformed" else canonical(self.output).decode()
                ),
            )
        response = RESPONSE_ADAPTER.validate_json(raw)
        if isinstance(response, ToolCallsResponse):
            self.recorder.calls(response.calls)
        if isinstance(response, FinalResponse):
            try:
                value = parse_json(response.output_json)
            except ValueError:
                self.recorder.schema = self.recorder.domain = False
            else:
                self.recorder.output(value)
        return raw


class FixtureTransport:
    """Recorded authored protocol fixtures. Never a provider capture or live call."""

    def __init__(self, case, output, recorder):
        self.case, self.output, self.recorder = case, output, recorder
        self.attempts = 0

    async def __call__(self, request):
        if (str(request.url), request.method) != (
            "https://api.openai.com/v1/responses",
            "POST",
        ) or "authorization" in request.headers:
            raise ValueError("Only credential-free mocked Responses are supported")
        self.attempts += 1
        mode = self.case.fixture
        if mode == "transport":
            raise httpx.ConnectError("Synthetic interruption")
        name = (
            "refusal"
            if mode == "refusal"
            or (
                self.attempts > 1
                and mode in ("unknown_tool", "invalid_arguments", "owner_argument")
            )
            else "tool"
            if self.attempts == 1 or mode == "duplicate_call"
            else ("incomplete" if mode == "incomplete" else "plan")
        )
        native = parse_json((ASSETS / "fixtures" / f"{name}.json").read_bytes())
        if name == "tool":
            tool = native["output"][-1]
            tool["name"], tool["arguments"] = _call(mode, native=True)
            if self.case.case_id == "ME-C10":
                tool["name"], tool["arguments"] = "get_user_preferences", "{}"
            self.recorder.calls(
                [
                    ToolCall(
                        call_id="evaluation-call",
                        name=tool["name"],
                        arguments_json=tool["arguments"],
                    )
                ]
            )
        if name == "plan":
            native["output"][0]["content"][0]["text"] = (
                "{not-json" if mode == "malformed" else canonical({"result": self.output}).decode()
            )
            if mode == "malformed":
                self.recorder.schema = self.recorder.domain = False
            else:
                self.recorder.output(self.output)
        # Fresh fixture copies only; existing stream consistency validation runs.
        events = [
            {"type": "response.output_item.done", "output_index": i, "item": item}
            for i, item in enumerate(native.get("output", []))
        ] + [{"type": "response." + native["status"], "response": native}]
        body = b"".join(
            b"event: "
            + e["type"].encode()
            + b"\ndata: "
            + canonical({**e, "sequence_number": i})
            + b"\n\n"
            for i, e in enumerate(events)
        )
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=body)


async def run_case(case, fixture_output, source, catalog):
    if source not in ("template", "fake", "replay"):
        raise ValueError("Offline execution only; live and judge execution are absent")
    recorder = Recorder(case.profile, catalog)
    started = time.perf_counter()
    usage = None
    uncertain = 0
    finish_reasons = []
    if source == "template":
        result = plan_week(case.profile, catalog, request_text=case.request_text)
        # Use this run's baseline result, never the expected label or replay output.
        if result.plan:
            output = {"outcome": "plan", "plan": result.plan.model_dump()}
        elif result.outcome == "clarify":
            output = dict(
                outcome="clarify",
                fields=["preferences_text"]
                if case.request_text
                else ["excluded_ids", "session_minutes"],
                choices=list(result.choices),
            )
        elif result.outcome == "abstain":
            output = dict(
                outcome="abstain", reason="infeasible", next_step="change_supported_preferences"
            )
        elif result.outcome == "error":
            output = dict(outcome="error", error={"code": "internal_error", "retryable": False})
        else:
            raise ValueError("Unexpected template outcome; never substitute a plan")
        counts = dict.fromkeys(
            (
                "provider_requests",
                "count_requests",
                "wire_requests",
                "tool_dispatches",
                "semantic_repairs",
                "transport_retries",
                "input_tokens",
                "output_tokens",
            ),
            0,
        )
        state = "failed" if result.outcome == "error" else "ready_unpublished"
        versions = {
            "prompt": "not_applicable",
            "tools": "not_applicable",
            "output": "plan-output-v1",
            "model": "none",
        }
        token_kind = "not_applicable"
    else:
        profiles = SyntheticProfile(case.profile)
        provider = (
            ObservedFake(case, fixture_output, catalog, recorder)
            if source == "fake"
            else (
                ResponsesReplay(
                    httpx.MockTransport(FixtureTransport(case, fixture_output, recorder))
                )
            )
        )
        agent = Agent(profiles, catalog, provider=provider)
        agent.tools = RecordedTools(profiles, catalog, recorder)
        result = await agent.generate(
            Principal.A, GenerateRequest(profile_revision=1, preferences_text=case.request_text)
        )
        output = result.output().model_dump()
        state = result.states[-1].value
        counts = {
            k: v
            for k, v in asdict(result.metrics).items()
            if k not in ("uncertain_attempts", "finish_reasons", "token_kind")
        }
        counts.update(
            count_requests=result.count_requests,
            wire_requests=result.wire_requests
            if source == "replay"
            else counts["provider_requests"],
        )
        usage = [u.model_dump() for u in result.provider_usage] if source == "replay" else None
        versions = dict(
            prompt=result.prompt_version,
            tools=result.tool_version,
            output=result.output_version,
            model=result.model_id,
        )
        token_kind = result.metrics.token_kind
        uncertain = result.metrics.uncertain_attempts
        finish_reasons = list(result.metrics.finish_reasons)
    observed = Observation(
        source=source,
        output_json=canonical(output).decode(),
        terminal_state=state,
        tools=recorder.tools,
        proposal_schema_valid=recorder.schema,
        proposals_domain_valid=recorder.domain,
        counts=counts,
    )
    scored = score(case, observed, catalog)
    scored.update(
        versions=versions,
        token_kind=token_kind,
        usage=usage,
        usage_status="invented_fixture"
        if source == "replay"
        else ("simulated_not_actual" if source == "fake" else "not_applicable"),
        external_cost_usd=0,
        financial_authority="none",
        uncertain_attempts=uncertain,
        finish_reasons=finish_reasons,
        elapsed_ms=round((time.perf_counter() - started) * 1000, 3),
        provenance="deterministic_template"
        if source == "template"
        else (
            "fake_baseline_roundtrip"
            if source == "fake" and case.fixture == "normal"
            else "authored_scripted_fake"
            if source == "fake"
            else "authored_template_derived_native_replay_not_provider_capture"
        ),
    )
    return scored


def manifest():
    frozen, cases, _ = load_suite()
    paths = sorted((ROOT / "src/future_training").rglob("*.py")) + [
        ROOT / "scripts/evaluate_models.py",
        ROOT / "scripts/prepare_model_evaluation.py",
    ]
    sources = {p.relative_to(ROOT).as_posix(): text_sha256(p) for p in paths}
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    dirty = bool(
        subprocess.run(
            ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, check=True
        ).stdout
    )
    return {
        "version": "offline-evaluation-run-v1",
        "dataset": frozen,
        "scorer": SCORER,
        "rubric_version": RUBRIC_VERSION,
        "review_order_seed": REVIEW_SEED,
        "rate_version": RATE_VERSION,
        "pricing_status": "historical_assumptions_not_live_authorization_count_tariff_unknown",
        "validator": VALIDATOR_VERSION,
        "duration": DURATION_VERSION,
        "template": TEMPLATE_VERSION,
        "code_revision": revision,
        "dirty": dirty,
        "source_sha256": hashlib.sha256(canonical(sources)).hexdigest(),
        "source_files": sources,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "dependency_lock_sha256": text_sha256(ROOT / "uv.lock"),
        "provider_asset_sha256": {
            n: hashlib.sha256(v.encode()).hexdigest() for n, v in provider_assets().items()
        },
        "provider_configuration": parse_json((ASSETS / "config.json").read_bytes()),
        "live_enabled": False,
        "generation_allowance_usd": 0,
        "count_allowance_usd": 0,
        "human_scores": "not_collected",
        "judge_scores": "not_run",
        "case_ids": [c.case_id for c in cases],
        "eligibility": [
            {
                "case_id": c.case_id,
                "eligibility": c.eligibility,
                "fixture": c.fixture,
                "exposure": c.exposure,
            }
            for c in cases
        ],
        "legacy_eligibility": parse_json(provider_assets()["manifest.json"])["cases"],
        "measurement": "single_offline_observation_per_case_not_provider_latency",
        "selection": "all_50_preregistered_cases_no_best_of_N",
    }


async def evaluate(*, tracer=None):
    _, cases, outputs = load_suite()
    catalog = load_catalog()
    from future_training.observability import Span

    results, links = [], []
    for s in ("template", "fake", "replay"):
        for c in cases:
            if tracer is None:
                row = await run_case(c, copy.deepcopy(outputs[c.case_id]), s, catalog)
            else:
                with Span("evaluation.case", tracer=tracer, evidence_source=s) as root:
                    row = await run_case(c, copy.deepcopy(outputs[c.case_id]), s, catalog)
                    root.set(outcome=row["actual"], **row["counts"])
                links.append({"source": s, "case_id": c.case_id, "trace_id": root.trace_id})
            results.append(row)
    summary = {}
    for source in ("template", "fake", "replay"):
        selected = [r for r in results if r["source"] == source]
        summary[source] = {
            "total": len(selected),
            "handling_passed": sum(r["handling_passed"] for r in selected),
            "hard_passed": sum(r["hard_passed"] for r in selected),
            "quality_eligible": sum(r["quality_eligible"] for r in selected),
            "outcomes": dict(sorted(Counter(r["actual"] for r in selected).items())),
            "failures": [
                {"case_id": r["case_id"], "checks": r["failures"]}
                for r in selected
                if not r["hard_passed"]
            ],
        }
    report = {"manifest": manifest(), "summary": summary, "cases": results}
    if tracer is not None:
        report["trace_links"] = links
    return report


def reproducible(report):
    """Wall clocks and working-tree status are evidence, not deterministic scores."""
    value = copy.deepcopy(report)
    value["manifest"].pop("dirty")
    value["manifest"].pop("platform")
    value["manifest"].pop("python")
    value["manifest"].pop("code_revision")
    for row in value["cases"]:
        row.pop("elapsed_ms")
    return value
