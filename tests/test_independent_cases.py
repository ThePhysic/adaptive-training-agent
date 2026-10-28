"""Public/exposed controls only, fixed NONSECRET key, no final cases or curator."""

import ast
import copy
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import pytest

from experiments import independent_cases as e
from future_training.agent.protocol import canonical
from future_training.domain.baseline import plan_week
from future_training.domain.catalog import load_catalog
from future_training.experiments.model_eval_assets import compatible_score_reference
from future_training.experiments.model_evaluation import load_suite
from future_training.experiments.model_scoring import Observation, score


@pytest.fixture(scope="module")
def public_paths():
    # Tests reuse the validated PUBLIC path inventory, never private case paths.
    # File bytes are still rehashed on every freeze; production has no such cache.
    return e.sealed.public_sources()


@pytest.fixture
def package(monkeypatch, public_paths):
    monkeypatch.setattr(e.sealed, "public_sources", lambda: public_paths)
    f = e.freeze()
    source = {c.case_id: c for c in load_suite()[1]}
    cases, entries = [], []
    for ordinal, case_id in enumerate(e.IDS, 1):
        row = source[case_id]
        body = dict(
            version="independent-case-v1",
            case_id=f"fixture-{ordinal:02}",
            ordinal=ordinal,
            profile=row.profile.model_dump(mode="json"),
            request_text="",
            expected_outcome="plan",
            required_tools=row.required_tools,
            coverage=["matrix", "duration", "schedule"],
            checks="all_common_hard_checks_v1",
            catalog_sha256=load_catalog().fingerprint(),
            freeze_sha256=f["fingerprint"],
            selection_sha256=f["selection_sha256"],
            origin=dict(
                kind="developer_fixture",
                state="synthetic_fixture",
                public_fixture_id=case_id,
                attestation_ref=None,
                opening_ref=None,
            ),
        )
        raw = e.canonical_fixture(canonical(body))
        cases.append(raw)
        entries.append(
            dict(
                ordinal=ordinal,
                content_commitment=e.sealed.curator_token(
                    e.TEST_KEY, f["fingerprint"], raw, purpose="content"
                ),
                input_token=e.sealed.curator_token(
                    e.TEST_KEY,
                    f["fingerprint"],
                    e.sealed.input_fingerprint(body["profile"], "").encode(),
                    purpose="input",
                ),
            )
        )
    context = e.sealed.curator_token(
        e.TEST_KEY, f["fingerprint"], b"SYNTHETIC", purpose="key_context"
    )
    exposure = dict(
        version="private-exposure-index-v1",
        freeze_sha256=f["fingerprint"],
        public_exposure_index_sha256=f["public_exposure_index_sha256"],
        key_context=context,
        tokens=[
            e.sealed.curator_token(e.TEST_KEY, f["fingerprint"], d.encode(), purpose="input")
            for d in e.sealed.exposed_input_index()
        ],
    )
    m = dict(
        version="sealed-evaluation-v2",
        kind="synthetic_test",
        population="synthetic-e4-public-controls",
        case_count=10,
        split="held_out",
        exposure="synthetic_not_unseen",
        curator_attestation_ref="synthetic-not-an-attestation",
        owner_freeze_ref="synthetic-not-an-approval",
        freeze_sha256=f["fingerprint"],
        public_exposure_index_sha256=f["public_exposure_index_sha256"],
        content_root=e.sealed.digest(entries),
        key_context=context,
        entries=entries,
        coverage=list(e.sealed.COVERAGE),
        scorer=e.sealed.SCORER,
        rubric=e.sealed.RUBRIC_VERSION,
        provenance="curator_attestation_not_cryptographic_identity",
        validation="metadata_only_not_case_validation",
    )
    pins = e.sealed.ReviewedPins(
        kind="synthetic_test",
        manifest_sha256=e.sealed.digest(m),
        exposure_sha256=e.sealed.digest(exposure),
        content_root=m["content_root"],
        key_context=context,
        freeze_sha256=f["fingerprint"],
        curator_attestation_ref=m["curator_attestation_ref"],
        owner_freeze_ref=m["owner_freeze_ref"],
    )
    return tuple(cases), canonical(m), canonical(exposure), f, pins


def evidence(variant="template", repair=False, ordinal=1):
    case = next(c for c in load_suite()[1] if c.case_id == e.IDS[ordinal - 1])
    output = dict(
        outcome="plan", plan=plan_week(case.profile, load_catalog()).plan.model_dump(mode="json")
    )
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
    tools = []
    if variant != "template":
        counts.update(
            provider_requests=3 if repair else 2,
            count_requests=3 if repair else 2,
            wire_requests=6 if repair else 4,
            tool_dispatches=1,
            semantic_repairs=int(repair),
            input_tokens=2000,
            output_tokens=300,
        )
        if variant == "fake":
            counts.update(count_requests=0, wire_requests=counts["provider_requests"])
        tools = [
            dict(
                name="search_exercises",
                arguments_valid=True,
                authorized=True,
                result_valid=True,
                status="ok",
            )
        ]
    observed = Observation(
        source=variant,
        output_json=canonical(output).decode(),
        terminal_state="ready_unpublished",
        tools=tools,
        proposal_schema_valid=True,
        proposals_domain_valid=True,
        counts=counts,
        no_publication=True,
    )
    return dict(
        version="independent-fixture-evidence-v1",
        variant=variant,
        public_fixture_id=e.IDS[ordinal - 1],
        complete=True,
        observation=observed.model_dump(mode="json"),
        responses=[]
        if variant == "template"
        else ["tools", *(["proposal"] if repair else []), "proposal"],
        proposals=(
            [dict(response_ordinal=2, schema_valid=True, domain_valid=False)] if repair else []
        )
        + [
            dict(
                response_ordinal=0 if variant == "template" else 3 if repair else 2,
                schema_valid=True,
                domain_valid=True,
            )
        ],
        tool_attempts=[]
        if variant == "template"
        else [dict(name="search_exercises", arguments_json='{"limit":20}')],
        accounting_status="not_applicable_template" if variant == "template" else "synthetic_known",
        charged_micro=None if variant == "template" else 7,
        held_micro=None if variant == "template" else 13,
        uncertainty=[],
    )


def scored(package, data, ordinal=1):
    return e.score_fixture(*package, ordinal, canonical(data))


def test_new_freeze_covers_interfaces_study_and_added_experiments(
    package, monkeypatch, tmp_path, public_paths
):
    f = package[3]
    assert f == e.freeze() and f["version"] == "evaluation-configuration-freeze-v2"
    assert e.SPEC in f["files"] and "experiments/independent_cases.py" in f["files"]
    assert "data/evaluation/study-v1/selection.json" in f["files"]
    assert "data/evaluation/study-v1/legacy-compatibility.json" in f["files"]
    assert not f["live_enabled"] and not f["monetary_authority"]
    added = tmp_path / "synthetic.py"
    added.write_bytes(b"# SYNTHETIC extra dependency\n")
    monkeypatch.setattr(
        e.sealed, "public_sources", lambda: {**public_paths, "experiments/NEW_SYNTHETIC.py": added}
    )
    with pytest.raises(ValueError, match="independent_freeze_mismatch"):
        e.check_freeze(f)


def test_original_candidate_is_preserved_but_stale_for_changed_source(package):
    prior = e.ROOT / "docs/implementation/evidence/f3-e2-freeze-candidate.json"
    assert (
        hashlib.sha256(prior.read_bytes()).hexdigest()
        == "ecaeb2db0cb4a309b9b20d3a7c63f203e09351b49848ef9677cb379e49530dfa"
    )
    with pytest.raises(ValueError, match="configuration_freeze_mismatch"):
        e.sealed.check_freeze(json.loads(prior.read_bytes()))


def test_canonicalization_stability_and_no_opening(package):
    raw = package[0][0]
    value = json.loads(raw)
    value["coverage"].reverse()
    value["profile"].pop("excluded_ids")
    value["profile"].pop("excluded_tags")
    assert e.canonical_fixture(json.dumps(value, indent=3).encode()) == raw
    result = e.verify_fixture_population(*package)
    assert result["exposure"] == "public_controls_already_exposed"
    assert result["human_scores"] is None
    for opener in (e.open_independent, e.sealed.open_population):
        with pytest.raises(ValueError):
            opener(approved=True)


@pytest.mark.parametrize(
    "fault",
    [
        "duplicate",
        "utf16",
        "bom",
        "bool",
        "unknown",
        "oversized",
        "nonfinite",
        "missing",
        "extra",
        "profile",
        "tool",
        "provenance",
        "opened",
        "coverage",
        "path",
    ],
)
def test_bad_case_is_rejected_without_content_leak(package, fault, capsys, caplog):
    data = json.loads(package[0][0])
    if fault == "bool":
        data["ordinal"] = True
    elif fault == "unknown":
        data["version"] = "PRIVATE_CANARY"
    elif fault == "missing":
        data.pop("profile")
    elif fault == "extra":
        data["notes"] = "PRIVATE_CANARY"
    elif fault == "profile":
        data["profile"]["session_minutes"] = 30
    elif fault == "tool":
        data["required_tools"] = ["approve_plan"]
    elif fault == "provenance":
        data["origin"]["kind"] = "independent_curator"
    elif fault == "opened":
        data["origin"]["state"] = "opened_separate_authorization"
    elif fault == "coverage":
        data["coverage"] = ["matrix", "matrix", "duration"]
    elif fault == "path":
        data["case_id"] = "../PRIVATE_CANARY"
    raw = canonical(data)
    if fault == "duplicate":
        raw = raw[:-1] + b',"ordinal":1}'
    elif fault == "utf16":
        raw = json.dumps(data).encode("utf-16")
    elif fault == "bom":
        raw = b"\xef\xbb\xbf" + raw
    elif fault == "oversized":
        raw = b" " * 8193
    elif fault == "nonfinite":
        raw = b'{"ordinal":NaN}'
    with pytest.raises(ValueError, match="^independent_fixture_rejected$") as err:
        e.canonical_fixture(raw)
    assert "PRIVATE_CANARY" not in str(err.value)
    assert not capsys.readouterr().out and not caplog.text


@pytest.mark.parametrize(
    "fault",
    [
        "input",
        "content",
        "ordinal",
        "root",
        "count",
        "context",
        "pins",
        "freeze",
        "selection",
        "duplicate_case",
        "changed_case",
        "index",
        "upgrade",
    ],
)
def test_commitment_substitution_tampering_and_provenance_fail(package, fault):
    cases, raw, xraw, f, pins = copy.deepcopy(package)
    m, x = json.loads(raw), json.loads(xraw)
    if fault in ("input", "content"):
        m["entries"][0]["input_token" if fault == "input" else "content_commitment"] = "0" * 64
        m["content_root"] = e.sealed.digest(m["entries"])
        pins = pins.model_copy(
            update={"manifest_sha256": e.sealed.digest(m), "content_root": m["content_root"]}
        )
    elif fault == "ordinal":
        m["entries"][0]["ordinal"] = 2
    elif fault == "root":
        m["content_root"] = "0" * 64
    elif fault == "count":
        cases = cases[:-1]
    elif fault == "context":
        m["key_context"] = "0" * 64
    elif fault == "pins":
        pins = pins.model_copy(update={"manifest_sha256": "0" * 64})
    elif fault == "freeze":
        f["files"][next(iter(f["files"]))] = "0" * 64
    elif fault in ("selection", "changed_case"):
        data = json.loads(cases[0])
        data["selection_sha256" if fault == "selection" else "freeze_sha256"] = "0" * 64
        cases = (canonical(data), *cases[1:])
    elif fault == "duplicate_case":
        cases = (cases[0], cases[0], *cases[2:])
    elif fault == "index":
        x["tokens"].reverse()
    elif fault == "upgrade":
        m["kind"] = "independently_curated"
    with pytest.raises(ValueError, match="^independent_fixture_verification_stopped$"):
        e.verify_fixture_population(cases, canonical(m), canonical(x), f, pins)


@pytest.mark.parametrize("variant", ["template", "fake", "replay"])
def test_same_common_scorer_no_false_legacy_case_label(package, variant):
    data = evidence(variant)
    result = scored(package, data)
    old = next(c for c in load_suite()[1] if c.case_id == e.IDS[0])
    expected = score(old, Observation.model_validate(data["observation"]), load_catalog())
    actual = result["score"]
    assert {k: v for k, v in actual.items() if k not in ("case_id", "split")} == {
        k: v for k, v in expected.items() if k not in ("case_id", "split")
    }
    assert (
        actual["hard_passed"]
        and actual["split"] == "synthetic_fixture"
        and actual["quality_scores"] is None
    )
    assert result["provenance"] == "synthetic_not_model_or_human_evidence"


def test_valid_terminal_does_not_erase_intermediate_hard_failure(package):
    result = scored(package, evidence("replay", repair=True))
    assert result["score"]["handling_passed"] and not result["score"]["hard_passed"]
    assert not result["score"]["quality_eligible"] and len(result["proposals"]) == 2
    assert not result["proposals"][0]["domain_valid"]


@pytest.mark.parametrize(
    "fault",
    [
        "missing_proposal",
        "missing_response",
        "missing_tool",
        "unknown_accounting",
        "missing_liability",
        "missing_terminal",
        "cleanup",
        "cancelled",
        "incomplete",
        "missing_flag",
        "false_publication",
        "budget",
        "invalid_argument",
        "write_tool",
        "owner_tool",
        "missing_counts",
        "live",
        "wrong_case",
    ],
)
def test_evidence_failure_cannot_pass_quality(package, fault):
    data = evidence("replay", repair=True)
    if fault == "missing_proposal":
        data["proposals"].pop(0)
    elif fault == "missing_response":
        data["responses"].pop(0)
    elif fault == "missing_tool":
        data["tool_attempts"] = []
    elif fault == "unknown_accounting":
        data.update(accounting_status="synthetic_unknown", charged_micro=None, held_micro=None)
    elif fault == "missing_liability":
        data["held_micro"] = None
    elif fault == "missing_terminal":
        data["observation"] = None
    elif fault in ("cleanup", "cancelled"):
        data["uncertainty"] = [fault]
    elif fault == "incomplete":
        data["complete"] = False
    elif fault == "missing_flag":
        data["observation"].pop("no_publication")
    elif fault == "false_publication":
        data["observation"]["no_publication"] = False
    elif fault == "budget":
        data["observation"]["counts"]["wire_requests"] = 7
    elif fault == "missing_counts":
        data["observation"]["counts"].pop("input_tokens")
    elif fault == "invalid_argument":
        data["tool_attempts"][0]["arguments_json"] = '{"limit":true}'
    elif fault == "write_tool":
        data["tool_attempts"][0]["name"] = "approve_plan"
    elif fault == "owner_tool":
        data["tool_attempts"][0]["arguments_json"] = '{"owner_id":"PRIVATE_CANARY"}'
    elif fault == "live":
        data["observation"]["source"] = "live"
    elif fault == "wrong_case":
        data["public_fixture_id"] = e.IDS[1]
    try:
        result = scored(package, data)
    except ValueError as err:
        assert str(err) == "independent_fixture_scoring_stopped"
    else:
        assert result["score"] is None or not result["score"]["quality_eligible"]
        if fault == "unknown_accounting":
            assert (
                result["accounting"]["held_micro"]
                is result["accounting"]["actual_total_micro"]
                is None
            )


@pytest.mark.parametrize("fault", ["ids", "denominator", "float", "extra", "variant", "status"])
def test_study_selection_rejects_tamper(package, monkeypatch, fault):
    old = Path.read_bytes
    data = e.study()
    if fault == "ids":
        data["development_ids"][0] = "ME-C01"
    elif fault == "denominator":
        data["hard_denominator"] = 39
    elif fault == "float":
        data["hard_denominator"] = 40.0
    elif fault == "extra":
        data["unknown"] = "PRIVATE_CANARY"
    elif fault == "variant":
        data["comparison_variants"] = ["template", "fake"]
    elif fault == "status":
        data["status"] = "owner_approved"
    monkeypatch.setattr(
        Path,
        "read_bytes",
        lambda p: canonical(data) if p == e.DIRECTORY / "selection.json" else old(p),
    )
    with pytest.raises(ValueError, match="study_selection_rejected"):
        e.study()


@pytest.mark.parametrize("fault", ["historical_hash", "manifest", "source", "new_source"])
def test_legacy_compatibility_is_exact_not_ignore_source_drift(package, monkeypatch, fault):
    old = Path.read_bytes
    path = e.DIRECTORY / "legacy-compatibility.json"
    data = json.loads(path.read_bytes())
    if fault == "historical_hash":
        data["historical_sha256"] = "0" * 64
    elif fault == "manifest":
        data["current_manifest"]["live_enabled"] = True
    elif fault == "source":
        data["current_manifest"]["source_sha256"] = "0" * 64
    else:
        data["current_manifest"]["source_files"]["src/SYNTHETIC.py"] = "0" * 64
    monkeypatch.setattr(Path, "read_bytes", lambda p: canonical(data) if p == path else old(p))
    with pytest.raises(ValueError, match="legacy_compatibility_rejected"):
        compatible_score_reference()


def test_exclusive_first_result_cannot_replace_failure(package, monkeypatch):
    directory = e.ROOT / ".cache/f3-e4" / ("synthetic-results-" + uuid4().hex)
    directory.mkdir()
    failed = scored(package, evidence("replay", True))
    e.retain_first(directory, 1, "replay", failed)
    with pytest.raises(ValueError, match="record_retained"):
        e.retain_first(directory, 1, "replay", scored(package, evidence("replay")))
    barrier = Barrier(2)
    second = scored(package, evidence("replay", True, ordinal=2), ordinal=2)

    def write(_):
        barrier.wait()
        try:
            e.retain_first(directory, 2, "replay", second)
            return "stored"
        except ValueError:
            return "stopped"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(write, range(2))) == ["stopped", "stored"]
    fsync = e.sealed.os.fsync
    third = scored(package, evidence("replay", True, ordinal=3), ordinal=3)
    monkeypatch.setattr(
        e.sealed.os, "fsync", lambda _: (_ for _ in ()).throw(OSError("PRIVATE_CANARY"))
    )
    with pytest.raises(ValueError):
        e.retain_first(directory, 3, "replay", third)
    monkeypatch.setattr(e.sealed.os, "fsync", fsync)
    with pytest.raises(ValueError, match="record_retained"):
        e.retain_first(directory, 3, "replay", third)


@pytest.mark.parametrize(
    "fault", ["identity", "variant", "provenance", "fingerprint", "extension", "ordinal_type"]
)
def test_retention_does_not_mislabel_a_first_result(package, fault):
    directory = e.ROOT / ".cache/f3-e4" / ("synthetic-retention-" + uuid4().hex)
    directory.mkdir()
    result = scored(package, evidence("replay", True))
    if fault == "identity":
        result["case_id"] = "fixture-02"
    elif fault == "variant":
        result["variant"] = "fake"
    elif fault == "provenance":
        result["provenance"] = "live"
    elif fault == "fingerprint":
        result["freeze_sha256"] = "PRIVATE_CANARY"
    elif fault == "extension":
        result["human_judgment"] = "PRIVATE_CANARY"
    with pytest.raises(ValueError, match="synthetic_retention_rejected"):
        e.retain_first(directory, "1" if fault == "ordinal_type" else 1, "replay", result)
    assert not list(directory.iterdir())


def test_direct_facts_label_cannot_authorize_genuine_opening(package):
    from future_training.experiments.model_scoring import ScoringFacts, score_facts

    case = next(c for c in load_suite()[1] if c.case_id == e.IDS[0])
    facts = ScoringFacts(
        case_id="synthetic",
        split="independent_opened",
        profile=case.profile,
        request_text="",
        expected={"template": "plan"},
        required_tools=case.required_tools,
        fixture="normal",
    )
    with pytest.raises(ValueError, match="independent_opening_not_authorized"):
        score_facts(facts, Observation.model_validate(evidence()["observation"]), load_catalog())


def test_hard_rule_ast_is_identical_to_accepted_pre_e4_body():
    path = e.ROOT / "src/future_training/experiments/model_scoring.py"
    f = next(
        n
        for n in ast.parse(path.read_bytes()).body
        if isinstance(n, ast.FunctionDef) and n.name == "_score"
    )
    body = ast.dump(ast.Module(body=f.body, type_ignores=[]), include_attributes=False)
    assert (
        hashlib.sha256(body.encode()).hexdigest()
        == "0e0cc2ad111b41cc780c90cace86a88844a938ad16276ef942db372cc55bfbd9"
    )


@pytest.mark.parametrize("flag", ["proposal_schema_valid", "proposals_domain_valid"])
def test_missing_proposal_aggregate_is_never_default_true(package, flag):
    data = evidence("replay")
    data["observation"].pop(flag)
    with pytest.raises(ValueError, match="independent_fixture_scoring_stopped"):
        scored(package, data)


@pytest.mark.parametrize("fault", ["owner", "unknown", "invalid_args"])
def test_truthfully_recorded_denied_tool_request_is_a_hard_failure(package, fault):
    from future_training.agent.protocol import ToolCall
    from future_training.experiments.model_scoring import check_call

    data = evidence("replay")
    attempt = data["tool_attempts"][0]
    if fault == "owner":
        attempt["arguments_json"] = '{"owner_id":"PRIVATE_CANARY"}'
    elif fault == "unknown":
        attempt["name"] = "approve_plan"
    else:
        attempt["arguments_json"] = '{"limit":true}'
    case = next(c for c in load_suite()[1] if c.case_id == e.IDS[0])
    name, valid, allowed = check_call(
        ToolCall(call_id="synthetic", **attempt), case.profile, load_catalog()
    )
    data["observation"]["tools"][0].update(name=name, arguments_valid=valid, authorized=allowed)
    result = scored(package, data)
    assert result["score"]["handling_passed"] and not result["score"]["hard_passed"]
    assert not result["score"]["quality_eligible"]
