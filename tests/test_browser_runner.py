import ctypes
import importlib.util
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from threading import Event

import browser_runner
import pytest

ROOT = Path(__file__).resolve().parents[1]


def running(pid):
    if os.name == "nt":
        from ctypes import wintypes as w

        api = ctypes.WinDLL("kernel32", use_last_error=True)
        api.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        api.OpenProcess.restype = w.HANDLE
        api.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
        api.CloseHandle.argtypes = [w.HANDLE]
        handle = api.OpenProcess(0x100000, False, pid)
        if not handle:
            return False
        try:
            return api.WaitForSingleObject(handle, 0) == 258
        finally:
            api.CloseHandle(handle)
    try:
        return Path(f"/proc/{pid}/stat").read_text().split(")", 1)[1].split()[0] != "Z"
    except FileNotFoundError:
        return False


@pytest.mark.parametrize("mode", ["normal_exit", "parent_crash", "timeout"])
def test_os_owner_terminates_descendant_even_when_node_exits_or_hangs(tmp_path, monkeypatch, mode):
    marker = tmp_path / "owned-child.json"
    program = """
const {spawn}=require('node:child_process'), fs=require('node:fs');
process.stdin.once('data',()=>{
 const child=spawn(process.execPath,['-e','setInterval(()=>{},1000)'],{stdio:'ignore'});
 child.once('spawn',()=>{
  fs.writeFileSync(process.argv[1]+'.tmp',JSON.stringify({pid:child.pid}));
  fs.renameSync(process.argv[1]+'.tmp',process.argv[1]);
  if(process.argv[2]==='normal_exit') process.exit(0);
  if(process.argv[2]==='parent_crash') process.exit(7);
 });
 setInterval(()=>{},1000);
});
"""
    if mode == "timeout":

        def controlled_timeout(process, input, timeout):
            process.stdin.write(input)
            process.stdin.flush()
            process.stdin.close()
            end = time.monotonic() + 5
            while not marker.exists() and time.monotonic() < end:
                Event().wait(0.01)
            assert marker.exists(), "Child must reach the spawn barrier before forced timeout"
            raise subprocess.TimeoutExpired(process.args, timeout)

        monkeypatch.setattr(subprocess.Popen, "communicate", controlled_timeout)
    result = browser_runner.owned_process(
        [shutil.which("node"), "-e", program, str(marker), mode],
        cwd=ROOT,
        env=dict(os.environ),
        timeout=10,
        release=b"go\n",
    )
    pid = json.loads(marker.read_text())["pid"]
    end = time.monotonic() + 5
    while running(pid) and time.monotonic() < end:
        Event().wait(0.01)
    assert not running(pid)
    assert result.returncode == {"normal_exit": 0, "parent_crash": 7, "timeout": 1}[mode]
    if mode == "timeout":
        assert json.loads(result.stderr)["failure"] == "browser_owner_timeout"


@pytest.mark.parametrize("data", [b"private-exception-canary", b'{"secret":"private-canary"}', b""])
def test_non_protocol_child_output_is_not_logged(monkeypatch, data):
    monkeypatch.setattr(browser_runner, "chrome_version", lambda *a, **k: "123.0.0.1")
    monkeypatch.setattr(
        browser_runner,
        "owned_process",
        lambda *a, **k: subprocess.CompletedProcess([], 1, b"", data),
    )
    result = browser_runner.run_browser(ROOT, "http://127.0.0.1:8000", "unused", {})
    assert result.stderr == '{"failure":"browser_harness_protocol_failed"}'
    assert "canary" not in result.stderr


def test_os_owner_never_terminates_unrelated_sibling():
    sibling = subprocess.Popen(
        [shutil.which("node"), "-e", "setInterval(()=>{},1000)"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        result = browser_runner.owned_process(
            [shutil.which("node"), "-e", "process.stdin.once('data',()=>process.exit(0))"],
            cwd=ROOT,
            env=dict(os.environ),
            timeout=5,
            release=b"go\n",
        )
        assert result.returncode == 0 and sibling.poll() is None
    finally:
        sibling.kill()
        sibling.wait(timeout=5)


def test_owned_output_limit_does_not_publish_partial_private_output():
    result = browser_runner.owned_process(
        [
            shutil.which("node"),
            "-e",
            "process.stdin.once('data',()=>process.stdout.write('private-canary'.repeat(2000)))",
        ],
        cwd=ROOT,
        env=dict(os.environ),
        timeout=5,
        release=b"go\n",
    )
    assert result.stdout == b""
    assert json.loads(result.stderr)["failure"] == "browser_output_oversized"


def test_preflight_failure_is_classified_and_never_launches_node(monkeypatch):
    def invalid(*a, **k):
        raise RuntimeError("browser_version_unavailable")

    monkeypatch.setattr(browser_runner, "chrome_version", invalid)
    monkeypatch.setattr(
        browser_runner, "owned_process", lambda *a, **k: pytest.fail("Must not launch")
    )
    assert (
        json.loads(browser_runner.run_browser(ROOT, "http://127.0.0.1:8000", "unused", {}).stderr)[
            "failure"
        ]
        == "browser_version_unavailable"
    )


def gate():
    spec = importlib.util.spec_from_file_location("browser_gate", ROOT / "scripts/check_browser.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "counts, expected",
    [
        ('tests="1" errors="0" failures="0" skipped="0"', True),
        ('tests="1" skipped="1"', False),
        ('tests="0"', False),
        ('tests="1" failures="1"', False),
        ('tests="2"', False),
    ],
)
def test_mandatory_gate_rejects_skipped_empty_failed_or_duplicate_populations(
    tmp_path, counts, expected
):
    report = tmp_path / "result.xml"
    report.write_text(f"<testsuites><testsuite {counts}/></testsuites>")
    assert gate().valid_report(report) is expected


def test_ci_browser_gate_is_mandatory_separate_and_not_duplicated_in_batch():
    workflow = (ROOT / ".github/workflows/offline.yml").read_text()
    browser = workflow.index("- name: Mandatory isolated installed-Chrome workflow")
    batch = workflow.index("- name: Remaining PostgreSQL HTTP TLS and fault integration checks")
    assert browser < batch
    assert "scripts/check_browser.py" in workflow[browser:batch]
    assert "continue-on-error" not in workflow and "--no-sandbox" not in workflow
    assert "--ignore=tests/test_browser_ui.py" in workflow[batch:]
    assert '"skipped"' in workflow[batch:]
    assert "scripts/check.py --evidence" in workflow[:browser]


def test_ci_phase_budgets_and_read_only_permissions_parse_with_locked_yaml_tool():
    program = """const fs=require('node:fs');
const yaml=require('js-yaml');
console.log(JSON.stringify(yaml.load(fs.readFileSync('../.github/workflows/offline.yml','utf8'))));
"""
    result = subprocess.run(
        [shutil.which("node"), "-e", program],
        cwd=ROOT / "web",
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    workflow = json.loads(result.stdout)
    job = workflow["jobs"]["offline"]
    steps = {s["name"]: s for s in job["steps"] if "name" in s}
    routine = steps["Routine offline checks and frontend build"]
    native = steps["Remaining PostgreSQL HTTP TLS and fault integration checks"]
    browser = steps["Mandatory isolated installed-Chrome workflow"]
    assert routine["timeout-minutes"] == 45
    assert native["timeout-minutes"] == 15
    assert browser["timeout-minutes"] == 3
    assert job["timeout-minutes"] == 45 + 15 + 3 + 12
    assert workflow["permissions"] == {"contents": "read"}
    assert job["env"]["FATA_PROVIDER"] == "fake"
    assert job["env"]["FATA_TELEMETRY_EXPORTER"] == "none"
    assert "strategy" not in job  # Shared local DB/ports remain sequential.
    assert set(workflow["on"]) == {"push", "pull_request", "workflow_dispatch"}


def test_mandatory_gate_fails_missing_installation_before_test_launch(monkeypatch, capsys):
    module = gate()
    monkeypatch.setattr(module.sys, "argv", ["scripts/check_browser.py"])
    monkeypatch.delenv("FATA_BROWSER_EXECUTABLE", raising=False)
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **k: pytest.fail("Must not launch"))
    assert module.main() == 1
    assert json.loads(capsys.readouterr().out)["failure"] == "required_browser_not_installed"
