"""Generate or verify the reproducible, synthetic-only F1-02 baseline artifact."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from future_training.evaluation import RESULTS, evaluate  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Verify without writing files")
    args = parser.parse_args()
    report = evaluate()
    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not RESULTS.exists() or RESULTS.read_text(encoding="utf-8") != serialized:
            raise SystemExit("Baseline artifact is stale or missing")
    else:
        RESULTS.parent.mkdir(parents=True, exist_ok=True)
        RESULTS.write_text(serialized, encoding="utf-8", newline="\n")
    print(json.dumps({"summary": report["summary"], "failed_cases": report["failed_cases"]}))
    coverage_ok = all(
        row["eligible_records"] >= 6 and all(p["valid"] for p in row["presets"])
        for row in report["catalog_coverage"]
    )
    if report["failed_cases"] or not coverage_ok:
        raise SystemExit(1)
