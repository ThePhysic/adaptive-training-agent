"""Negative real-process browser-startup regression; no Chrome, database or external I/O."""

import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Event, Thread

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_early_exit_reports_launch_and_server_state_without_private_output():
    class Metadata(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            body = b"synthetic-private-server-body-canary"
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (
                BrokenPipeError,
                ConnectionResetError,
            ):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Metadata)
    worker = Thread(target=server.serve_forever)
    worker.start()
    try:
        # Python rejects Chrome's --headless flag and exits before a ready signal.
        # This reproduces the observer failure with a real owned child, no sleeps.
        result = subprocess.run(
            [
                shutil.which("node"),
                "scripts/browser-smoke.mjs",
                f"http://127.0.0.1:{server.server_port}",
                sys.executable,
            ],
            cwd=ROOT / "web",
            capture_output=True,
            text=True,
            timeout=20,
            env={**os.environ, "FATA_BROWSER_EVIDENCE_STAGE": "f4-03b-r5a-ci"},
        )
        assert result.returncode == 1 and result.stdout == ""
        report = json.loads(result.stderr)
        assert report["failure"] == "browser_exited_before_ready"
        assert report["browserSmokeFailure"]["stage"] == "launch"
        assert report["server"] == {"health": 200, "ready": 200}
        assert any(event.get("exitCode") == 2 for event in report["browserSmokeFailure"]["events"])
        assert "canary" not in result.stderr and sys.executable not in result.stderr
        assert "unknown option" not in result.stderr  # Child stderr is classified, never echoed.
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)
        assert not worker.is_alive()


@pytest.mark.parametrize("mode", ["delayed", "malformed", "unavailable", "exit"])
def test_devtools_ready_can_precede_usable_http_target_with_bounded_recovery(mode):
    """Real loopback HTTP/body interruption, controlled by events, not a startup sleep."""
    requests = Counter()
    release = Event()

    class DevTools(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            requests[(self.command, self.path)] += 1
            self.send_response(200)
            self.end_headers()
            if mode == "delayed" and requests[(self.command, self.path)] == 1:
                self.wfile.write(b"[")
                self.wfile.flush()
                release.wait(5)  # Safety bound; second GET/teardown releases this handler.
                return
            release.set()
            target = {
                "id": "A" * 32,
                "type": "page",
                "url": "about:blank",
                "webSocketDebuggerUrl": (
                    f"ws://127.0.0.1:{self.server.server_port}/devtools/page/" + "A" * 32
                ),
            }
            body = (
                b"private-devtools-body-canary"
                if mode == "malformed"
                else json.dumps([] if mode == "unavailable" else [target]).encode()
            )
            try:
                self.wfile.write(body)
            except (
                BrokenPipeError,
                ConnectionResetError,
            ):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), DevTools)
    worker = Thread(target=server.serve_forever)
    worker.start()
    program = """
import { EventEmitter } from 'node:events';
import { diagnostics, waitForPageTarget } from './scripts/browser-support.mjs';
const [port, mode] = process.argv.slice(2);
const child = Object.assign(new EventEmitter(), {exitCode: null, signalCode: null});
const d = diagnostics('http://127.0.0.1:8000');
d.add('browser', {code: 'devtools_ready'});
d.stage('devtools');
let expire, calls = 0, clock = 0;
const request = async (url, options) => {
  calls++;
  const response = await fetch(url, options);
  if (mode === 'delayed' && calls === 1) queueMicrotask(() => expire());
  if (mode === 'exit') child.emit('exit', 1);
  return response;
};
let result;
try {
  const value = await waitForPageTarget(child, Number(port), d, {
    request, deadline: 6000, now: () => clock,
    pause: async ms => {clock += ms;},
    timer: (fn, ms) => {expire = fn; return setTimeout(fn, ms);},
  });
  result = {outcome: 'ready', attempts: value.attempts};
} catch (error) {
  result = {outcome: error.message};
}
console.log(JSON.stringify({...result, calls, diagnostic: d.snapshot()}));
"""
    try:
        result = subprocess.run(
            [shutil.which("node"), "--input-type=module", "-", str(server.server_port), mode],
            input=program,
            cwd=ROOT / "web",
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0 and not result.stderr
        report = json.loads(result.stdout)
        expected = {
            "delayed": "ready",
            "malformed": "devtools_invalid_json",
            "unavailable": "devtools_target_unavailable",
            "exit": "browser_exited_during_devtools",
        }
        assert report["outcome"] == expected[mode]
        assert report["calls"] == {"delayed": 2, "unavailable": 24}.get(mode, 1)
        assert requests == {("GET", "/json/list"): report["calls"]}
        if mode == "delayed":
            assert "devtools_http_timeout" in result.stdout and report["attempts"] == 2
        assert "canary" not in result.stdout and "AAAAAAAA" not in result.stdout
        assert str(server.server_port) not in result.stdout
    finally:
        release.set()
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)
        assert not worker.is_alive()
