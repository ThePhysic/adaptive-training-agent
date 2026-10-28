"""Synthetic opaque metadata only: no final held-out inputs or real attestors.

Commitment test bytes are non-case sentinels. Public v1 inputs are read only to
verify normalization/overlap. No independent sealed population is created here.
"""

import copy
import importlib.util
import json
import subprocess
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import pytest

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@pytest.fixture
def e():
    return module("sealed_evaluation", "experiments/sealed_evaluation.py")


@pytest.fixture
def synthetic(e):
    f = e.freeze()
    key = bytes(range(32))  # Explicitly predictable SYNTHETIC TEST KEY, not curator secret.
    context = e.curator_token(key, f["fingerprint"], b"SYNTHETIC", purpose="key_context")
    entries = [
        dict(
            ordinal=i,
            content_commitment=e.curator_token(
                key, f["fingerprint"], f"SYNTHETIC-NONCASE-{i}".encode(), purpose="content"
            ),
            input_token=e.curator_token(
                key, f["fingerprint"], f"SYNTHETIC-INPUT-SENTINEL-{i}".encode(), purpose="input"
            ),
        )
        for i in range(1, 11)
    ]
    x = dict(
        version="private-exposure-index-v1",
        freeze_sha256=f["fingerprint"],
        public_exposure_index_sha256=f["public_exposure_index_sha256"],
        key_context=context,
        tokens=[
            e.curator_token(key, f["fingerprint"], d.encode(), purpose="input")
            for d in e.exposed_input_index()
        ],
    )
    m = dict(
        version=e.VERSION,
        kind="synthetic_test",
        population="synthetic-metadata-not-final",
        case_count=10,
        split="held_out",
        exposure="synthetic_not_unseen",
        curator_attestation_ref="synthetic-not-a-curator-approval",
        owner_freeze_ref="synthetic-not-owner-approval",
        freeze_sha256=f["fingerprint"],
        public_exposure_index_sha256=f["public_exposure_index_sha256"],
        key_context=context,
        content_root=e.digest(entries),
        entries=entries,
        coverage=list(e.COVERAGE),
        scorer=e.SCORER,
        rubric=e.RUBRIC_VERSION,
        provenance="curator_attestation_not_cryptographic_identity",
        validation="metadata_only_not_case_validation",
    )
    pins = e.ReviewedPins(
        kind="synthetic_test",
        manifest_sha256=e.digest(m),
        exposure_sha256=e.digest(x),
        content_root=m["content_root"],
        key_context=context,
        freeze_sha256=f["fingerprint"],
        curator_attestation_ref=m["curator_attestation_ref"],
        owner_freeze_ref=m["owner_freeze_ref"],
    )
    return f, m, x, pins


@pytest.fixture
def registry():
    path = ROOT / ".cache/f3-e2" / ("synthetic-registry-" + uuid4().hex)
    path.mkdir(parents=True, mode=0o700)
    return path


def validate(e, data):
    f, m, x, pins = data
    return e.validate_manifest(e.canonical(m), e.canonical(x), f, pins)


def test_freeze_is_reproducible_candidate_not_ratification(e):
    first, second = e.freeze(), e.freeze()
    assert e.canonical(first) == e.canonical(second)
    assert e.check_freeze(first) == first
    assert first["status"] == "candidate_not_owner_approved"
    assert not first["live_enabled"] and not first["monetary_authority"]
    assert first["selection"]["sealed_count"] == 10
    assert "experiments/counted_probe.py" in first["files"]
    assert "src/future_training/experiments/model_scoring.py" in first["files"]
    assert all(".cache/" not in n and "AGENTS.md" not in n for n in first["files"])


@pytest.mark.parametrize(
    "fault",
    [
        "source",
        "added_source",
        "selection",
        "fingerprint",
        "scorer",
        "rubric",
        "bool_type",
        "number_type",
    ],
)
def test_configuration_mutation_never_silently_rebinds(e, monkeypatch, fault):
    f = e.freeze()
    if fault in ("source", "added_source"):
        original = e.freeze_inputs

        def changed():
            values = original()
            values[
                next(iter(values))
                if fault == "source"
                else "src/future_training/SYNTHETIC_added.py"
            ] = "0" * 64
            return values

        monkeypatch.setattr(e, "freeze_inputs", changed)
    elif fault == "selection":
        f["selection"]["first_results_only"] = False
    elif fault == "bool_type":
        f["live_enabled"] = 0
    elif fault == "number_type":
        f["selection"]["sealed_count"] = 10.0
    else:
        f[fault] = "PRIVATE_CANARY"
    with pytest.raises(ValueError, match="configuration_freeze_mismatch"):
        e.check_freeze(f)


def test_normalized_public_input_identity_ignores_exclusion_order(e):
    rows = [
        json.loads(line)
        for line in (ROOT / "data/evaluation/v1/scenarios.jsonl").read_text().splitlines()
    ]
    old = next(r for r in rows if len(r["profile"].get("excluded_ids", [])) > 1)
    profile = copy.deepcopy(old["profile"])
    profile["excluded_ids"].reverse()
    assert e.input_fingerprint(profile, old.get("request_text", "")) == e.input_fingerprint(
        old["profile"], old.get("request_text", "")
    )


def test_ready_synthetic_manifest_is_not_an_independent_population(e, synthetic):
    m = validate(e, synthetic)
    assert m.kind == "synthetic_test" and m.exposure == "synthetic_not_unseen"
    assert str(m) == repr(m) == "<private_evaluation_metadata>"
    assert m.validation == "metadata_only_not_case_validation"


@pytest.mark.parametrize(
    "fault",
    [
        "version",
        "scorer",
        "rubric",
        "missing_attestation",
        "missing_owner",
        "provenance",
        "exposure",
        "kind_upgrade",
        "case_count",
        "duplicate_input",
        "duplicate_content",
        "ordinal",
        "root",
        "commitment_replacement",
        "context",
        "extra_content",
        "coverage",
        "freeze",
        "exposure_index",
        "exposure_count",
        "index_context",
        "index_duplicate",
    ],
)
def test_malformed_or_tampered_metadata_is_finite_and_private(e, synthetic, fault, capsys, caplog):
    f, m, x, pins = synthetic
    if fault in ("version", "scorer", "rubric", "provenance", "exposure"):
        m[fault] = "PRIVATE_CANARY"
    elif fault == "missing_attestation":
        m["curator_attestation_ref"] = None
    elif fault == "missing_owner":
        m["owner_freeze_ref"] = None
    elif fault == "kind_upgrade":
        m["kind"] = "independently_curated"
    elif fault == "case_count":
        m["case_count"] = 9
    elif fault in ("duplicate_input", "duplicate_content"):
        k = "input_token" if fault == "duplicate_input" else "content_commitment"
        m["entries"][1][k] = m["entries"][0][k]
        m["content_root"] = e.digest(m["entries"])
    elif fault == "ordinal":
        m["entries"][0]["ordinal"] = 2
    elif fault == "root":
        m["content_root"] = "0" * 64
    elif fault == "commitment_replacement":
        m["entries"][0]["content_commitment"] = "0" * 64
        m["content_root"] = e.digest(m["entries"])  # Owner pins stay original.
    elif fault == "context":
        m["key_context"] = "0" * 64
    elif fault == "extra_content":
        m["case_content"] = "PRIVATE_CANARY_DO_NOT_DISCLOSE"
    elif fault == "coverage":
        m["coverage"][0] = "PRIVATE_CANARY"
    elif fault == "freeze":
        m["freeze_sha256"] = "0" * 64
    elif fault == "exposure_index":
        x["public_exposure_index_sha256"] = "0" * 64
    elif fault == "exposure_count":
        x["tokens"].pop()
    elif fault == "index_context":
        x["key_context"] = "0" * 64
    else:
        x["tokens"][1] = x["tokens"][0]
    with pytest.raises(ValueError, match="^sealed_metadata_rejected$") as error:
        validate(e, (f, m, x, pins))
    assert "PRIVATE_CANARY" not in str(error.value)
    assert not capsys.readouterr().out and not caplog.text


def test_overlap_rejected_even_with_coherent_synthetic_pins(e, synthetic):
    f, m, x, pins = synthetic
    m["entries"][0]["input_token"] = x["tokens"][0]
    m["content_root"] = e.digest(m["entries"])
    # Synthetic permission fixture only. Real pins must be independently approved.
    pins = pins.model_copy(
        update={"content_root": m["content_root"], "manifest_sha256": e.digest(m)}
    )
    with pytest.raises(ValueError, match="sealed_metadata_rejected"):
        validate(e, (f, m, x, pins))


@pytest.mark.parametrize(
    "raw",
    [b"{PRIVATE_CANARY", b"\xff", b"[]", b'{"version":1,"version":2}', b'{"x":NaN}', b" " * 32769],
    ids=["invalid", "utf8", "array", "duplicate", "nonfinite", "oversized"],
)
def test_invalid_json_is_not_echoed(e, raw):
    with pytest.raises(ValueError, match="^sealed_metadata_rejected$"):
        e.metadata_json(raw)


def test_registration_is_exclusive_and_verified_without_content(e, synthetic, registry):
    f, m, x, pins = synthetic
    raw, exposed = e.canonical(m), e.canonical(x)
    result = e.register_metadata(raw, exposed, f, pins, directory=registry)
    assert result["state"] == "registered_unopened" and result["kind"] == "synthetic_test"
    assert e.verify_registration(raw, exposed, f, pins, directory=registry)["case_count"] == 10
    with pytest.raises(ValueError, match="record_retained"):
        e.register_metadata(raw, exposed, f, pins, directory=registry)
    with pytest.raises(ValueError, match="separate_content_opening"):
        e.open_population("DO_NOT_READ_CASE_CONTENT", approved=True)


def test_concurrent_registration_has_one_writer(e, synthetic, registry):
    f, m, x, pins = synthetic
    barrier = Barrier(2)

    def register(_):
        barrier.wait()
        try:
            e.register_metadata(e.canonical(m), e.canonical(x), f, pins, directory=registry)
            return "registered"
        except ValueError:
            return "stopped"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(register, range(2))) == ["registered", "stopped"]


@pytest.mark.parametrize("partial", [False, True])
def test_invalidation_is_irreversible_via_supported_api(e, synthetic, registry, partial):
    f, m, x, pins = synthetic
    e.register_metadata(e.canonical(m), e.canonical(x), f, pins, directory=registry)
    e.invalidate_population(m["population"], directory=registry, reason="accidental_exposure")
    if partial:
        (registry / (m["population"] + ".invalidated.json")).write_bytes(b"{")
    with pytest.raises(ValueError, match="population_invalidated"):
        e.verify_registration(e.canonical(m), e.canonical(x), f, pins, directory=registry)
    with pytest.raises(ValueError, match="population_invalidated"):
        e.register_metadata(e.canonical(m), e.canonical(x), f, pins, directory=registry)


def test_partial_registration_blocks_replacement(e, synthetic, registry, monkeypatch):
    f, m, x, pins = synthetic
    original = e.os.fsync
    monkeypatch.setattr(e.os, "fsync", lambda _: (_ for _ in ()).throw(OSError("PRIVATE_CANARY")))
    with pytest.raises(ValueError, match="record_retained"):
        e.register_metadata(e.canonical(m), e.canonical(x), f, pins, directory=registry)
    monkeypatch.setattr(e.os, "fsync", original)
    path = registry / (m["population"] + ".json")
    path.write_bytes(b"{")  # Explicit synthetic interruption, never a real record.
    with pytest.raises(ValueError):
        e.verify_registration(e.canonical(m), e.canonical(x), f, pins, directory=registry)
    with pytest.raises(ValueError, match="record_retained"):
        e.register_metadata(e.canonical(m), e.canonical(x), f, pins, directory=registry)


def test_blank_human_materials_do_not_create_judgments(e):
    stored = json.loads((ROOT / e.TEMPLATE).read_text())
    assert stored == e.blank_review()
    assert stored["reviewer_token"] is None and set(stored["ratings"].values()) == {None}
    missing = e.review_status_counts(("slot-1", "slot-2", "slot-3"), {})
    assert missing["planned"] == 3 and missing["counts"]["missing"] == 3
    mixed = e.review_status_counts(
        ("slot-1", "slot-2", "slot-3"), {"slot-1": "abstained", "slot-2": "ineligible"}
    )
    assert mixed["planned"] == 3 and mixed["counts"]["missing"] == 1
    assert mixed["verified_judgments"] == 0 and mixed["quality_scores"] is None
    with pytest.raises(ValueError):
        e.review_status_counts(("slot-1",), {"slot-2": "rated_attested"})


def test_registered_metadata_cannot_be_replaced_or_rebound(e, synthetic, registry, monkeypatch):
    f, m, x, pins = synthetic
    e.register_metadata(e.canonical(m), e.canonical(x), f, pins, directory=registry)
    m["population"] = "synthetic-renamed-not-a-new-approval"
    with pytest.raises(ValueError, match="sealed_metadata_rejected"):
        validate(e, (f, m, x, pins))
    m["population"] = "synthetic-metadata-not-final"
    original = e.freeze_inputs
    monkeypatch.setattr(e, "freeze_inputs", lambda: {**original(), "SYNTHETIC_DRIFT": "0" * 64})
    with pytest.raises(ValueError, match="sealed_metadata_rejected"):
        e.verify_registration(e.canonical(m), e.canonical(x), f, pins, directory=registry)
    assert (registry / (m["population"] + ".json")).is_file()


def test_registry_rejects_external_directory_and_oversized_record(e, synthetic, registry):
    f, m, x, pins = synthetic
    with pytest.raises(ValueError, match="private_registry_required"):
        e.register_metadata(e.canonical(m), e.canonical(x), f, pins, directory=ROOT / "docs")
    e.register_metadata(e.canonical(m), e.canonical(x), f, pins, directory=registry)
    (registry / (m["population"] + ".json")).write_bytes(b"SYNTHETIC" * 5000)
    with pytest.raises(ValueError, match="registration_verification_stopped"):
        e.verify_registration(e.canonical(m), e.canonical(x), f, pins, directory=registry)


def test_saved_numeric_type_tampering_is_not_python_equality(e, synthetic, registry):
    f, m, x, pins = synthetic
    e.register_metadata(e.canonical(m), e.canonical(x), f, pins, directory=registry)
    path = registry / (m["population"] + ".json")
    saved = json.loads(path.read_bytes())
    saved["manifest"]["entries"][0]["ordinal"] = 1.0
    path.write_bytes(e.canonical(saved))  # SYNTHETIC tamper, not a real registration.
    with pytest.raises(ValueError, match="registration_verification_stopped"):
        e.verify_registration(e.canonical(m), e.canonical(x), f, pins, directory=registry)


def test_old_case_labels_and_hard_rating_gate_remain(e):
    from future_training.experiments.model_evaluation import load_suite
    from future_training.experiments.model_review import DIMENSIONS, validate_ratings

    _, cases, _ = load_suite()
    assert len(cases) == 50 and sum(c.split == "comparison_candidate" for c in cases) == 10
    assert all(c.exposure == "developer_exposed_not_blind" for c in cases)
    ratings = {
        **dict.fromkeys(DIMENSIONS, 3),
        "explanation_clarity": None,
    }  # SYNTHETIC unit values.
    with pytest.raises(ValueError):
        validate_ratings({"hard_passed": False, "quality_eligible": False}, ratings)
    counted = module("counted_probe", "experiments/counted_probe.py")
    with pytest.raises(ValueError, match="invalid_synthetic_evidence"):
        counted.validate_packet({"source": "live", "evidence_complete": False})


@pytest.mark.parametrize(
    "component", ["sealed-cases", "private-evaluation", "reviewer-materials", "blinding-keys"]
)
def test_review_archive_filters_private_names_before_reading(e, tmp_path, monkeypatch, component):
    review = module("review_source", "scripts/review_source.py")
    public = tmp_path / "public.py"
    public.write_text("# SYNTHETIC public source\n")
    secret = tmp_path / component / "PRIVATE_CANARY.jsonl"
    secret.parent.mkdir()
    secret.write_bytes(b"SYNTHETIC_DO_NOT_READ_NOT_REAL_CASES")
    listing = ("public.py\0" + component + "/PRIVATE_CANARY.jsonl\0").encode()
    monkeypatch.setattr(
        review.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess([], 0, stdout=listing)
    )
    original = Path.read_bytes

    def guarded(path):
        assert path != secret, "private content must not be read for classification"
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", guarded)
    snap = review.inspect(tmp_path)
    assert set(snap["files"]) == {"public.py"}
    archive = tmp_path / "review.zip"
    review.create_archive(archive, snap, tmp_path)
    with zipfile.ZipFile(archive) as zipped:
        assert all("PRIVATE_CANARY" not in n for n in zipped.namelist())
