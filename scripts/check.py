"""One offline check sequence for local development and CI; never installs anything."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def command_timeout(command):
    # F5-D1 measured the expanded Windows routine suite above 20 minutes and
    # native integration at 412s. Bound aggregate phases independently from the
    # unchanged individual request/browser/SQL deadlines. Ordinary checks stay 180s.
    if command[1:3] == ["-m", "pytest"]:
        return 900 if "integration" in command else 2400
    return 180


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--integration", action="store_true")
    parser.add_argument("--browser", action="store_true")
    parser.add_argument("--evidence", action="store_true")
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 14):
        parser.error("Use the supported Python 3.14 environment")
    if args.browser and (
        not args.integration or not Path(os.environ.get("FATA_BROWSER_EXECUTABLE", "")).is_file()
    ):
        parser.error("--browser requires --integration and an installed FATA_BROWSER_EXECUTABLE")
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    ruff = str(Path(sys.executable).parent / ("ruff.exe" if os.name == "nt" else "ruff"))
    if npm is None:
        parser.error("Install the supported Node/npm environment first")
    cache = ROOT / ".cache/f107"
    cache.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    if not args.browser:
        env.pop("FATA_BROWSER_EXECUTABLE", None)
    if args.evidence:
        env["FATA_WRITE_EVIDENCE"] = "1"
    else:
        env.pop("FATA_WRITE_EVIDENCE", None)
    commands = [
        [sys.executable, "--version"],
        ["node", "--version"],
        [npm, "--version"],
        [ruff, "--version"],
        [npm, "--prefix", "web", "ls", "--depth=0"],
        [ruff, "check", "src", "scripts", "tests", "--no-cache"],
        [ruff, "format", "--check", "src", "scripts", "tests", "--no-cache"],
        [sys.executable, "scripts/export_contracts.py", "--check"],
        [sys.executable, "scripts/prepare_responses.py", "--check"],
        [sys.executable, "scripts/measure_token_admission.py", "--check"],
        [sys.executable, "scripts/prepare_model_evaluation.py", "--check"],
        [sys.executable, "scripts/evaluate_models.py", "--check"],
        *[
            [npm, "--prefix", "web", "run", task]
            for task in ("check", "format:check", "check:generated", "test", "build")
        ],
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--basetemp=.cache/pytest-f107-unit",
            "--junitxml=.cache/f107/unit.xml",
        ],
    ]
    if args.integration:
        commands.append([sys.executable, "scripts/smoke_local.py"])
        commands.append(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-s",
                "-m",
                "integration",
                "--basetemp=.cache/pytest-f107-integration",
                "--junitxml=.cache/f107/integration.xml",
            ]
        )
    commands.append([sys.executable, "scripts/evaluate_baseline.py", "--check"])
    commands.append([sys.executable, "scripts/measure_async_reads.py"])
    report = {"integration": args.integration, "browser_required": args.browser, "commands": []}
    for command in commands:
        print(json.dumps({"command": command}), flush=True)
        started = time.perf_counter()
        result = subprocess.run(
            command, cwd=ROOT, env=env, timeout=command_timeout(command), check=False
        )
        report["commands"].append(
            {
                "command": command,
                "exit_code": result.returncode,
                "seconds": round(time.perf_counter() - started, 3),
            }
        )
        (cache / "check-results.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
        if result.returncode:
            return result.returncode
    report["tests"] = {}
    for name in ("unit", "integration") if args.integration else ("unit",):
        suite = ET.parse(cache / f"{name}.xml").getroot()
        totals = {
            key: sum(int(node.get(key, "0")) for node in suite.iter("testsuite"))
            for key in ("tests", "failures", "errors", "skipped")
        }
        report["tests"][name] = totals
        if name == "integration" and args.browser and totals["skipped"]:
            raise RuntimeError("Required integration/browser evidence cannot contain skips")
    (cache / "check-results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
