"""Fixed synthetic release workload, run by docker exec, never a web endpoint."""

import concurrent.futures
import http.client
import json
import math
import statistics
import sys
import time

PROFILE = dict(
    adult=True,
    goal="general_strength",
    equipment="bodyweight",
    experience="beginner",
    days_per_week=2,
    session_minutes=20,
    excluded_ids=[],
    excluded_tags=[],
)


def request(method, path, body=None, *, owner="synthetic-a", extra=None):
    c = http.client.HTTPConnection("127.0.0.1", 8000, timeout=35)
    headers = {"X-Synthetic-Principal": owner, "Content-Type": "application/json", **(extra or {})}
    try:
        c.request(method, path, json.dumps(body) if body is not None else None, headers)
        r = c.getresponse()
        raw = r.read(262145)
        if len(raw) > 262144:
            raise ValueError("Oversized release response")
        return r.status, raw.decode()
    finally:
        c.close()


def generate(*, owner="synthetic-a", revision=1, path="/api/v1/drafts/stream", body=None):
    c = http.client.HTTPConnection("127.0.0.1", 8000, timeout=35)
    started = time.perf_counter()
    first = None
    frames = []
    try:
        c.request(
            "POST",
            path,
            json.dumps(body or {"profile_revision": revision}),
            {"X-Synthetic-Principal": owner, "Content-Type": "application/json"},
        )
        r = c.getresponse()
        if r.status != 200:
            return {
                "status": r.status,
                "outcome": "http_error",
                "ms": (time.perf_counter() - started) * 1000,
            }
        total = 0
        while line := r.readline(32769):
            total += len(line)
            if total > 262144 or len(line) > 32768:
                raise ValueError("Oversized SSE")
            if line.startswith(b"data: "):
                event = json.loads(line[6:])
                frames.append(event)
                if first is None and event["event_type"] in ("status", "draft"):
                    first = (time.perf_counter() - started) * 1000
        if not frames or frames[-1]["event_type"] != "done":
            raise ValueError("Incomplete release stream")
        done = frames[-1]["payload"]
        result = {
            "status": 200,
            "outcome": done["outcome"],
            "ms": (time.perf_counter() - started) * 1000,
            "first_update_ms": first,
            "events": len(frames),
        }
        if done["outcome"] == "plan":
            result.update(
                candidate=done["candidate"],
                plan=next(f["payload"] for f in frames if f["event_type"] == "draft"),
            )
        return result
    finally:
        c.close()


def seed():
    for owner in ("synthetic-a", "synthetic-b"):
        status, _ = request(
            "PUT", "/api/v1/profile", {"expected_revision": 0, "preferences": PROFILE}, owner=owner
        )
        assert status == 200, "Release drill needs a fresh isolated database"
    initial = generate()
    assert initial["outcome"] == "plan"
    identity = initial["candidate"]
    revised = generate(
        path=f"/api/v1/drafts/{identity['candidate_id']}/revise/stream",
        body={"candidate": identity, "profile_revision": 1},
    )
    assert revised["outcome"] == "plan"
    identity = revised["candidate"]
    approve = {**identity, "idempotency_key": "release-approval-key"}
    path = f"/api/v1/drafts/{identity['candidate_id']}/approve"
    status, raw = request("POST", path, approve)
    assert status == 200
    approval = json.loads(raw)
    plan_id = approval["plan_id"]
    status, saved = request("GET", f"/api/v1/plans/{plan_id}")
    assert status == 200
    snapshot = json.loads(saved)
    submission = dict(
        expected_revision=0,
        plan_revision=identity["revision"],
        plan_content_hash=identity["content_hash"],
        status="completed",
        effort="moderate",
        rating=4,
        idempotency_key="release-completion-key",
    )
    completion_path = f"/api/v1/plans/{plan_id}/sessions/1/completion"
    status, completion = request("POST", completion_path, submission)
    assert status == 200
    assert (
        request(
            "PUT",
            "/api/v1/profile",
            {"expected_revision": 1, "preferences": {**PROFILE, "session_minutes": 30}},
        )[0]
        == 200
    )
    return dict(
        timings={"first_generation_ms": initial["ms"], "revision_ms": revised["ms"]},
        approval_path=path,
        approval_body=approve,
        approval=approval,
        saved=snapshot,
        completion_path=completion_path,
        completion_body=submission,
        completion=json.loads(completion),
    )


def verify(state):
    code, raw = request("POST", state["approval_path"], state["approval_body"])
    assert code == 200 and json.loads(raw) == state["approval"]
    code, body = request("GET", f"/api/v1/plans/{state['approval']['plan_id']}")
    assert code == 200 and json.loads(body) == state["saved"]
    assert (
        request("GET", f"/api/v1/plans/{state['approval']['plan_id']}", owner="synthetic-b")[0]
        == 404
    )
    code, raw = request("POST", state["completion_path"], state["completion_body"])
    assert code == 200 and json.loads(raw) == state["completion"]
    code, raw = request("GET", "/api/v1/plans")
    assert code == 200 and state["approval"]["plan_id"] in raw
    assert request("GET", state["completion_path"], owner="synthetic-b")[0] == 404
    for headers in ({"Host": "outside.invalid"}, {"X-Forwarded-For": "127.0.0.1"}):
        assert request("GET", "/api/v1/profile", extra=headers)[0] == 403
    return {
        "immutable_readback": True,
        "approval_retry": True,
        "completion_retry": True,
        "owner_isolation": True,
    }


def measure():
    for i in range(4):
        assert (
            generate(owner="synthetic-a" if i % 2 else "synthetic-b", revision=2 if i % 2 else 1)[
                "outcome"
            ]
            == "plan"
        )
    modes = {}
    for concurrency in (1, 2):

        def work(i):
            return generate(
                owner="synthetic-a" if i % 2 else "synthetic-b",
                revision=2 if i % 2 else 1,
            )

        samples = []
        # Each batch uses distinct principals. Do not hide admission failures or
        # introduce a retry when the supported concurrency limit is encountered.
        for offset in range(0, 60, concurrency):
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
                samples.extend(pool.map(work, range(offset, offset + concurrency)))

        def distribution(key, samples=samples):
            values = sorted(s[key] for s in samples if key in s and s[key] is not None)
            return {
                "n": len(values),
                "p50": statistics.median(values),
                "p95": values[math.ceil(0.95 * len(values)) - 1],
            }

        modes[str(concurrency)] = {
            "requests": len(samples),
            "errors": sum(s["outcome"] != "plan" for s in samples),
            "latency_ms": distribution("ms"),
            "first_status_ms": distribution("first_update_ms"),
            "samples": [
                {k: v for k, v in row.items() if k not in ("candidate", "plan")} for row in samples
            ],
        }
    return {
        "version": "release-fake-load-v1",
        "warmup": 4,
        "modes": modes,
        "source": "fake_over_loopback_TCP",
        "artificial_delay_ms": 0,
        "catalog_cache": "application_uncached",
        "request_retries": 0,
        "backend_memory_kib": {
            line.split(":")[0]: int(line.split()[1])
            for line in open("/proc/1/status", encoding="utf-8")
            if line.startswith(("VmRSS:", "VmHWM:"))
        },
    }


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("seed", "verify", "measure", "generate"):
        raise SystemExit("Unsupported synthetic release probe")
    result = (
        seed()
        if sys.argv[1] == "seed"
        else verify(json.load(sys.stdin))
        if sys.argv[1] == "verify"
        else measure()
        if sys.argv[1] == "measure"
        else generate(owner="synthetic-b")
    )
    print(json.dumps(result))
