import json
from pathlib import Path

import pytest

from future_training.domain.catalog import load_catalog
from future_training.domain.validator import validate_plan
from future_training.evaluation import RESULTS, evaluate, load_scenarios

MANIFEST, SCENARIOS = load_scenarios(load_catalog())


@pytest.fixture(scope="module")
def report():
    return evaluate()


@pytest.mark.parametrize("case_id", [s.case_id for s in SCENARIOS])
def test_each_frozen_case_expected_outcome_and_checks(report, case_id):
    case = next(c for c in report["cases"] if c["case_id"] == case_id)
    assert case["passed"], case
    if case["task"] == "plan" and case["outcome"] == "plan":
        expected = next(s.profile for s in SCENARIOS if s.case_id == case_id)
        assert validate_plan(case["plan"], expected, load_catalog()).valid


def test_fixed_corpus_and_split_membership(report):
    assert len(SCENARIOS) == 40
    assert report["summary"]["development"]["total"] == 24
    assert report["summary"]["held_out"]["total"] == 16
    dev = set(MANIFEST["splits"]["development"])
    held = set(MANIFEST["splits"]["held_out"])
    assert len(dev | held) == 40 and not dev.intersection(held)
    assert report["failed_cases"] == []
    assert sum(c["outcome"] == "plan" for c in report["cases"]) == 24
    assert sum(c["outcome"] == "clarify" for c in report["cases"]) == 10
    assert sum(c["outcome"] == "abstain" for c in report["cases"]) == 2
    assert sum(c["outcome"] == "error" for c in report["cases"]) == 4


def test_catalog_coverage_all_rows_and_presets(report):
    assert len(report["catalog_coverage"]) == 8
    assert sum(len(row["presets"]) for row in report["catalog_coverage"]) == 24
    assert all(row["eligible_records"] >= 6 for row in report["catalog_coverage"])
    assert all(p["valid"] for row in report["catalog_coverage"] for p in row["presets"])


def test_reproducible_report_and_recorded_artifact(report):
    assert report == evaluate()
    assert json.loads(RESULTS.read_text(encoding="utf-8")) == report
    assert report["provider"] == "none" and report["external_cost_usd"] == 0


def test_frozen_data_change_is_detected(monkeypatch):
    from future_training import evaluation

    original = evaluation.DATASET.read_text(encoding="utf-8")

    class ChangedDataset:
        def read_text(self, *, encoding):
            assert encoding == "utf-8"
            return original.replace("dev-unknown-id", "dev-changed-id")

    monkeypatch.setattr(evaluation, "DATASET", ChangedDataset())
    with pytest.raises(ValueError, match="dataset checksum mismatch"):
        evaluation.load_scenarios(load_catalog())


def test_frozen_manifest_rejects_a_changed_catalog():
    from future_training.domain.catalog import Catalog

    catalog = load_catalog()
    altered = catalog.records()
    altered[0].title = "Changed metadata needs a new version and manifest"
    with pytest.raises(ValueError, match="catalog differs"):
        load_scenarios(Catalog(catalog.revision, altered))


def test_evaluation_does_not_import_business_workflows():
    # Dependency direction: this unit has no provider, database or HTTP imports.
    for path in Path("src/future_training/domain").glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "import psycopg" not in source and "from fastapi" not in source
