"""Test-only ownership boundary: never let a timed-out Node leave Chrome running."""

import ctypes
import json
import os
import signal
import subprocess
import tempfile


class WindowsJob:
    """Kernel-owned descendant cleanup, established before Node's stdin release."""

    def __init__(self):
        from ctypes import wintypes as w

        class Basic(ctypes.Structure):
            _fields_ = [
                ("user", ctypes.c_int64),
                ("job", ctypes.c_int64),
                ("flags", w.DWORD),
                ("min", ctypes.c_size_t),
                ("max", ctypes.c_size_t),
                ("active", w.DWORD),
                ("affinity", ctypes.c_size_t),
                ("priority", w.DWORD),
                ("scheduling", w.DWORD),
            ]

        class IO(ctypes.Structure):
            _fields_ = [(name, ctypes.c_uint64) for name in ("r", "w", "o", "rb", "wb", "ob")]

        class Extended(ctypes.Structure):
            _fields_ = [
                ("basic", Basic),
                ("io", IO),
                ("process_memory", ctypes.c_size_t),
                ("job_memory", ctypes.c_size_t),
                ("peak_process", ctypes.c_size_t),
                ("peak_job", ctypes.c_size_t),
            ]

        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.CreateJobObjectW.argtypes = [ctypes.c_void_p, w.LPCWSTR]
        self.api.CreateJobObjectW.restype = w.HANDLE
        self.api.SetInformationJobObject.argtypes = [
            w.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            w.DWORD,
        ]
        self.api.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
        self.api.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        self.api.OpenProcess.restype = w.HANDLE
        self.api.CloseHandle.argtypes = [w.HANDLE]
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise RuntimeError("browser_owner_failed")
        limits = Extended()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no breakaway.
        if not self.api.SetInformationJobObject(
            self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)
        ):
            self.close()
            raise RuntimeError("browser_owner_failed")

    def attach(self, pid):
        handle = self.api.OpenProcess(0x0101, False, pid)  # SET_QUOTA | TERMINATE
        try:
            if not handle or not self.api.AssignProcessToJobObject(self.handle, handle):
                raise RuntimeError("browser_owner_failed")
        finally:
            if handle:
                self.api.CloseHandle(handle)

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None


def owned_process(command, *, cwd, env, timeout, release=None):
    """Only supplied child/group/job is terminated. Outputs never become raw logs."""
    job = WindowsJob() if os.name == "nt" else None
    process = None
    timed_out = False
    attached = False
    try:
        with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
            try:
                process = subprocess.Popen(
                    command,
                    cwd=cwd,
                    env=env,
                    stdin=subprocess.PIPE,
                    stdout=output,
                    stderr=errors,
                    start_new_session=os.name != "nt",
                )
                if job:
                    job.attach(process.pid)
                    attached = True
                try:
                    process.communicate(input=release, timeout=timeout)
                except subprocess.TimeoutExpired:
                    timed_out = True
            finally:
                if job:
                    if process and not attached:
                        process.kill()
                    job.close()  # Also handles descendants after a normal/abnormal Node exit.
                elif process:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                if process:
                    process.wait(timeout=5)
            output.seek(0)
            errors.seek(0)
            stdout, stderr = output.read(16385), errors.read(16385)
            if timed_out:
                return subprocess.CompletedProcess(
                    command, 1, b"", b'{"failure":"browser_owner_timeout"}'
                )
            if len(stdout) > 16384 or len(stderr) > 16384:
                return subprocess.CompletedProcess(
                    command, 1, b"", b'{"failure":"browser_output_oversized"}'
                )
            return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    finally:
        if job:
            job.close()


def chrome_version(executable, *, cwd, env):
    if os.name == "nt":
        # Chrome --version is not a reliable Windows command. Read the signed PE's
        # fixed version resource without launching another browser or a shell.
        api = ctypes.WinDLL("version", use_last_error=True)
        api.GetFileVersionInfoSizeW.argtypes = [ctypes.c_wchar_p, ctypes.c_void_p]
        api.GetFileVersionInfoW.argtypes = [
            ctypes.c_wchar_p,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_void_p,
        ]
        api.VerQueryValueW.argtypes = [
            ctypes.c_void_p,
            ctypes.c_wchar_p,
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_uint32),
        ]
        size = api.GetFileVersionInfoSizeW(str(executable), None)
        if not size or size > 1048576:
            raise RuntimeError("browser_version_unavailable")
        buffer = ctypes.create_string_buffer(size)
        value, length = ctypes.c_void_p(), ctypes.c_uint32()
        if not api.GetFileVersionInfoW(str(executable), 0, size, buffer) or not api.VerQueryValueW(
            buffer, "\\", ctypes.byref(value), ctypes.byref(length)
        ):
            raise RuntimeError("browser_version_unavailable")
        info = ctypes.cast(value, ctypes.POINTER(ctypes.c_uint32))
        if length.value < 52 or info[0] != 0xFEEF04BD:
            raise RuntimeError("browser_version_unavailable")
        return ".".join(
            str(x) for x in (info[2] >> 16, info[2] & 65535, info[3] >> 16, info[3] & 65535)
        )
    import re

    result = owned_process([executable, "--version"], cwd=cwd, env=env, timeout=5)
    match = re.fullmatch(
        rb"(?:Google Chrome(?: for Testing)?|Chromium) (\d{1,3}\.\d{1,4}\.\d{1,6}\.\d{1,6})\s*",
        result.stdout,
    )
    if result.returncode or not match:
        raise RuntimeError("browser_version_unavailable")
    return match[1].decode("ascii")


def run_browser(root, base, executable, env):
    """Supported browser entry: mandatory version evidence and independent 90s owner."""
    try:
        version = chrome_version(executable, cwd=root / "web", env=env)
        result = owned_process(
            ["node", "scripts/browser-smoke.mjs", base, executable],
            cwd=root / "web",
            env={**env, "FATA_BROWSER_VERSION": version, "FATA_BROWSER_SUPERVISED": "1"},
            timeout=90,
            release=b"go\n",
        )
        if result.stderr in (
            b'{"failure":"browser_owner_timeout"}',
            b'{"failure":"browser_output_oversized"}',
        ):
            report = json.loads(result.stderr)
            report["environment"] = {"chromeVersion": version}
            result.stderr = json.dumps(report).encode()
        # Never echo raw Node loader, OS, executable or process errors into CI.
        for stream in (result.stdout, result.stderr):
            for line in stream.splitlines():
                report = json.loads(line)
                allowed = {
                    "failure",
                    "browserSmokeFailure",
                    "startup",
                    "environment",
                    "budgets",
                    "server",
                    "ui",
                    "sameKeyRetry",
                    "completionSameKeyRetry",
                    "sessionRecords",
                    "mobileErrorRecovery",
                    "horizontalOverflow",
                    "approval",
                    "runtimeErrors",
                    "externalPageRequests",
                    "timing",
                    "screenshots",
                }
                if (
                    not isinstance(report, dict)
                    or set(report) - allowed
                    or not ({"failure", "ui"} & set(report))
                ):
                    raise ValueError()
        if not result.stdout and not result.stderr:
            raise ValueError()
        return subprocess.CompletedProcess(
            result.args, result.returncode, result.stdout.decode(), result.stderr.decode()
        )
    except (
        ValueError,
        UnicodeError,
    ):
        return subprocess.CompletedProcess(
            [], 1, "", '{"failure":"browser_harness_protocol_failed"}'
        )
    except RuntimeError as error:
        code = (
            str(error)
            if str(error) in ("browser_version_unavailable", "browser_owner_failed")
            else "browser_owner_failed"
        )
        return subprocess.CompletedProcess([], 1, "", json.dumps({"failure": code}))
    except Exception:
        return subprocess.CompletedProcess([], 1, "", '{"failure":"browser_owner_failed"}')
