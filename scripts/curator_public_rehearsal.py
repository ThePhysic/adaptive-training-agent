"""Fixed public E8 practice only. No case/key/path input, opening or execution."""

import hashlib
import hmac
import importlib.metadata
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

from experiments import independent_cases as cases  # noqa: E402
from future_training.agent.protocol import canonical  # noqa: E402
from future_training.domain.baseline import plan_week  # noqa: E402
from future_training.domain.catalog import load_catalog  # noqa: E402
from future_training.domain.validator import validate_plan  # noqa: E402

INDEX = "docs/implementation/curator/f3-e8-public-exposure.json"
INDEX_SOURCES = {
    "data/evaluation/v1/scenarios.jsonl",
    "data/evaluation/model-v1/scenarios.jsonl",
    "src/future_training/schemas.py",
    "src/future_training/agent/protocol.py",
    "experiments/sealed_evaluation.py",
}
CONTEXT = "0" * 64  # Synthetic context, NOT an approved configuration freeze.


def public_case():
    source = next(c for c in cases.load_suite()[1] if c.case_id == cases.IDS[0])
    return dict(
        version="independent-case-v1",
        case_id="fixture-01",
        ordinal=1,
        profile=source.profile.model_dump(mode="json"),
        request_text="",
        expected_outcome="plan",
        required_tools=source.required_tools,
        coverage=["matrix", "duration", "schedule"],
        checks="all_common_hard_checks_v1",
        catalog_sha256=load_catalog().fingerprint(),
        freeze_sha256=CONTEXT,
        selection_sha256=cases.sealed.digest(cases.study()),
        origin=dict(
            kind="developer_fixture",
            state="synthetic_fixture",
            public_fixture_id=source.case_id,
            attestation_ref=None,
            opening_ref=None,
        ),
    )


def exposure():
    value = cases.json_object((ROOT / INDEX).read_bytes())
    if (
        set(value) != {"version", "scope", "source_files", "inputs"}
        or value["version"] != "public-exposure-practice-v1"
        or value["scope"] != "already_public_not_complete_private_exposure_history"
        or set(value["source_files"]) != INDEX_SOURCES
        or value["inputs"] != sorted(set(value["inputs"]))
        or len(value["inputs"]) != 47
    ):
        raise ValueError("public_index_invalid")
    for name, expected in value["source_files"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError("public_index_changed")
    return value["inputs"]


def run():
    if sys.version_info[:2] != (3, 14):
        raise ValueError("python_version")
    versions = {n: importlib.metadata.version(n) for n in ("pydantic", "httpx", "psycopg")}
    if versions != {"pydantic": "2.14.1", "httpx": "0.28.1", "psycopg": "3.3.6"}:
        raise ValueError("dependency_version")
    value = public_case()
    raw = cases.canonical_fixture(canonical(value))
    reordered = json.dumps(value, indent=2).encode()
    assert cases.canonical_fixture(reordered) == raw
    invalid = {**value, "profile": {**value["profile"], "adult": False}}
    try:
        cases.canonical_fixture(canonical(invalid))
    except ValueError:
        pass
    else:
        raise ValueError("invalid_control_accepted")
    parsed = cases.CaseContent.model_validate_json(raw)
    catalog = load_catalog()
    proposal = plan_week(parsed.profile, catalog)
    assert proposal.plan is not None and validate_plan(proposal.plan, parsed.profile, catalog).valid
    token = cases.sealed.curator_token(cases.TEST_KEY, CONTEXT, raw, purpose="content")
    assert hmac.compare_digest(
        token, cases.sealed.curator_token(cases.TEST_KEY, CONTEXT, raw, purpose="content")
    )
    assert not hmac.compare_digest(
        token, cases.sealed.curator_token(cases.TEST_KEY, CONTEXT, raw + b" ", purpose="content")
    )
    identity = cases.sealed.input_fingerprint(parsed.profile.model_dump(), "")
    assert identity in exposure()  # Known public overlap is required, never an unseen claim.
    assert identity == cases.sealed.input_fingerprint(parsed.profile.model_dump(), "")
    return dict(
        version="curator-public-rehearsal-v1",
        evidence="developer_public_practice_not_curator_attestation",
        result="passed",
        python=".".join(map(str, sys.version_info[:3])),
        dependencies=versions,
        valid_control=True,
        invalid_control_rejected=True,
        canonicalization_stable=True,
        domain_valid=True,
        nonsecret_commitment_repeatable=True,
        tamper_detected=True,
        public_overlap_detected=True,
        encryption="not_exercised_requires_separate_human_rehearsal",
        backup="not_exercised_requires_separate_human_rehearsal",
        genuine_authority=False,
    )


def main():
    try:
        if sys.argv[1:] or not __debug__:
            raise ValueError("fixed_public_practice_only")
        print(json.dumps(run(), sort_keys=True))
        return 0
    except Exception:
        print('{"version":"curator-public-rehearsal-v1","result":"stopped"}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
