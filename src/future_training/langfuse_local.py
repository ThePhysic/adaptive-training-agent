"""Metadata-only, bounded local projection. No SDK import, exporter or network.

The separately locked SDK harness consumes snapshots after business work. No
telemetry delivery or SDK callback executes inside an approval transaction.
"""

import json
import threading
import time
from collections import OrderedDict

from future_training.observability import LocalTracer, safe_record

VERSION = "langfuse-metadata-v1"


class Observations:
    def __init__(self, capacity=2048, byte_limit=4 * 1024 * 1024, *, now=time.time_ns):
        if type(capacity) is not int or not 1 <= capacity <= 2048:
            raise ValueError("Invalid observation capacity")
        if type(byte_limit) is not int or not 1024 <= byte_limit <= 4 * 1024 * 1024:
            raise ValueError("Invalid observation byte limit")
        self.capacity, self.byte_limit, self.now = capacity, byte_limit, now
        self._rows, self._bytes = OrderedDict(), 0
        self._lock = threading.Lock()
        self.closed = False
        self.dropped = self.duplicates = self.conflicts = self.invalid = 0

    def append(self, value):
        row = safe_record(value)
        if row is None or any(int(row[k], 16) == 0 for k in ("trace_id", "span_id")):
            self.invalid += 1
            return
        key = (row["trace_id"], row["span_id"])
        identity = json.dumps(row, sort_keys=True, separators=(",", ":"))
        with self._lock:
            if self.closed:
                self.dropped += 1
                return
            if key in self._rows:
                if self._rows[key][0] == identity:
                    self.duplicates += 1
                else:
                    self.conflicts += 1
                return
            row["ended_ns"] = self.now()
            if type(row["ended_ns"]) is not int or not 0 < row["ended_ns"] < 2**63:
                self.invalid += 1
                return
            blob = json.dumps(row, sort_keys=True, separators=(",", ":")).encode()
            if len(blob) > min(8192, self.byte_limit):
                self.dropped += 1
                return
            while self._rows and (
                len(self._rows) >= self.capacity or self._bytes + len(blob) > self.byte_limit
            ):
                _, (_, old) = self._rows.popitem(last=False)
                self._bytes -= len(old)
                self.dropped += 1
            self._rows[key] = (identity, blob)
            self._bytes += len(blob)

    def snapshot(self):
        with self._lock:
            return [json.loads(blob) for _, blob in self._rows.values()]

    def close(self):
        with self._lock:
            self.closed = True
            self._rows.clear()
            self._bytes = 0


class LangfuseTracer(LocalTracer):
    """Explicit local injection only; exceptions never affect business semantics."""

    def __init__(self, *, observations=None, **kwargs):
        super().__init__(**kwargs)
        self.observations = observations if observations is not None else Observations()
        self.projection_failures = 0

    def append(self, value):
        super().append(value)
        try:
            self.observations.append(value)
        except Exception:
            self.projection_failures += 1


def experiment_projection(report):
    """Project existing scored results; never score, upload content or add judgments."""
    from future_training.experiments.model_evaluation import load_suite

    _, cases, _ = load_suite()
    expected = {(s, c.case_id) for s in ("template", "fake", "replay") for c in cases}
    rows = report["cases"]
    if len(rows) != 150 or {(r["source"], r["case_id"]) for r in rows} != expected:
        raise ValueError("Exact existing 150 observations required")
    known = {c.case_id: c for c in cases}
    links = {(r["source"], r["case_id"]): r["trace_id"] for r in report.get("trace_links", [])}
    projected = []
    for row in rows:
        case = known[row["case_id"]]
        if row["split"] != case.split or row["quality_scores"] is not None:
            raise ValueError("Unreviewed split or fabricated quality score")
        if any(type(row[k]) is not bool for k in ("hard_passed", "handling_passed")):
            raise ValueError("Strict scorer verdicts required")
        if row["hard_passed"] and (row["failures"] or not all(row["checks"].values())):
            raise ValueError("Hard failure cannot be masked")
        trace_id = links.get((row["source"], case.case_id))
        if trace_id is not None and (
            type(trace_id) is not str
            or len(trace_id) != 32
            or any(c not in "0123456789abcdef" for c in trace_id)
        ):
            raise ValueError("Invalid trace correlation")
        projected.append(
            {
                "case_id": case.case_id,
                "source": row["source"],
                "split": case.split,
                "exposure": case.exposure,
                "eligibility": case.eligibility,
                "trace_id": links.get((row["source"], case.case_id)),
                "scores": [
                    {"name": k, "value": int(row[k]), "data_type": "BOOLEAN"}
                    for k in ("hard_passed", "handling_passed")
                ],
                "quality_scores": None,
                "explanation_clarity": "not_applicable_no_explanation_field",
            }
        )
    return {"version": VERSION, "items": projected, "human_scores": 0, "judge_scores": 0}
