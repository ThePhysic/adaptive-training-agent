"""Aggregate test budgets never suppress failures or run later acceptance steps."""

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize("phase", ["routine", "integration"])
def test_expanded_suite_budget_preserves_failure_propagation(monkeypatch, tmp_path, phase):
    path = Path(__file__).resolve().parents[1] / "scripts/check.py"
    spec = importlib.util.spec_from_file_location("offline_check", path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(
        runner.sys, "argv", ["check.py", *(["--integration"] if phase == "integration" else [])]
    )
    monkeypatch.setattr(runner.shutil, "which", lambda name: "npm")
    calls = []

    def execute(command, **kwargs):
        calls.append((command, kwargs))
        tests = command[1:3] == ["-m", "pytest"]
        if tests:
            assert kwargs["timeout"] == (900 if "integration" in command else 2400)
        else:
            assert kwargs["timeout"] == 180
        fail = tests and (("integration" in command) == (phase == "integration"))
        return subprocess.CompletedProcess(command, 7 if fail else 0)

    monkeypatch.setattr(runner.subprocess, "run", execute)
    assert runner.main() == 7
    assert calls[-1][0][1:3] == ["-m", "pytest"]
    assert not any("scripts/evaluate_baseline.py" in command for command, _ in calls)
    report = json.loads((tmp_path / ".cache/f107/check-results.json").read_bytes())
    assert report["commands"][-1]["exit_code"] == 7
    assert all(item["exit_code"] == 0 for item in report["commands"][:-1])
