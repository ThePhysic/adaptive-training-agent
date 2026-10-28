"""Public examples only. No curator participation, crypto custody or new cases."""

import json
from pathlib import Path

import pytest

from scripts import curator_public_rehearsal as r


def test_public_rehearsal_reuses_canonicalizer_and_domain():
    value = r.run()
    assert value["result"] == "passed" and value["genuine_authority"] is False
    assert value["tamper_detected"] and value["public_overlap_detected"]
    assert value["encryption"].startswith("not_exercised")


def test_public_exposure_export_matches_existing_helper():
    assert r.exposure() == r.cases.sealed.exposed_input_index()


@pytest.mark.parametrize("kind", ["extra", "source", "duplicates", "scope", "shape"])
def test_tampered_public_export_rejected(monkeypatch, kind):
    value = json.loads((r.ROOT / r.INDEX).read_bytes())
    if kind == "extra":
        value["private_input"] = "PRIVATE_CANARY"
    elif kind == "source":
        value["source_files"][".aws/credentials"] = "0" * 64
    elif kind == "duplicates":
        value["inputs"].append(value["inputs"][0])
    elif kind == "scope":
        value["scope"] = "genuine_independent"
    else:
        value["source_files"] = None
    monkeypatch.setattr(r.cases, "json_object", lambda *a: value)
    monkeypatch.setattr(r.sys, "argv", ["practice"])
    assert r.main() == 1


@pytest.mark.parametrize("args", [["private.json"], ["--key", "PRIVATE_CANARY"], ["--open"]])
def test_no_private_input_or_opening_interface(monkeypatch, capsys, args):
    monkeypatch.setattr(r.sys, "argv", ["practice", *args])
    monkeypatch.setattr(r, "run", lambda: pytest.fail("unexpected execution"))
    assert r.main() == 1
    assert json.loads(capsys.readouterr().out) == {
        "version": "curator-public-rehearsal-v1",
        "result": "stopped",
    }


def test_failure_never_prints_exception_or_input(monkeypatch, capsys):
    monkeypatch.setattr(r.sys, "argv", ["practice"])

    def fail():
        raise OSError("PRIVATE_CANARY")

    monkeypatch.setattr(r, "run", fail)
    assert r.main() == 1
    assert "PRIVATE_CANARY" not in capsys.readouterr().out


def test_public_runner_has_no_path_scanning_or_key_generation():
    text = Path(r.__file__).read_text()
    assert "secrets." not in text and "os.environ" not in text
    assert "open_population(" not in text and "open_independent(" not in text
