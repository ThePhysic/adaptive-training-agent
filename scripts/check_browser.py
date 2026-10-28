"""Mandatory isolated installed-Chrome gate; no download, optional skip or retry."""

import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def valid_report(path):
    suites = ET.parse(path).getroot().iter("testsuite")
    totals = {key: 0 for key in ("tests", "errors", "failures", "skipped")}
    for suite in suites:
        for key in totals:
            totals[key] += int(suite.get(key, "0"))
    return totals == {"tests": 1, "errors": 0, "failures": 0, "skipped": 0}


def main():
    if len(sys.argv) != 1 or not Path(os.environ.get("FATA_BROWSER_EXECUTABLE", "")).is_file():
        print(json.dumps({"failure": "required_browser_not_installed"}))
        return 1
    report = ROOT / ".cache/f107/browser.xml"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.unlink(missing_ok=True)
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_browser_ui.py",
                "-q",
                "-s",
                "-m",
                "integration",
                "--basetemp=.cache/pytest-f107-browser",
                "--junitxml=" + str(report),
            ],
            cwd=ROOT,
            env={**os.environ, "FATA_BROWSER_EVIDENCE_STAGE": "f4-03b-r5a-startup"},
            timeout=150,
            check=False,
        )
        if result.returncode or not valid_report(report):
            return 1
    except (
        subprocess.TimeoutExpired,
        OSError,
        ET.ParseError,
        ValueError,
    ):
        print(json.dumps({"failure": "required_browser_check_failed"}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
