"""Offline-only evaluator. There is deliberately no --live/provider/key option."""

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from future_training.evaluation import ROOT  # noqa: E402
from future_training.experiments.model_eval_assets import (  # noqa: E402
    SCORE_REFERENCE,
    compatible_score_reference,
)
from future_training.experiments.model_evaluation import (  # noqa: E402
    evaluate,
    load_suite,
    reproducible,
)
from future_training.experiments.model_review import review_packet  # noqa: E402

SCORES = SCORE_REFERENCE


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="Compare stable scores without writing"
    )
    parser.add_argument("--output", type=Path, default=ROOT / ".cache/f3-04a")
    parser.add_argument(
        "--record-offline",
        action="store_true",
        help="Explicitly replace the tracked synthetic regression score artifact",
    )
    args = parser.parse_args()
    if args.check and args.record_offline:
        parser.error("--check cannot replace recorded evidence")
    run_started = datetime.now(UTC)
    destination = args.output.resolve() / run_started.strftime("%Y%m%dT%H%M%S%fZ")
    if not destination.is_relative_to((ROOT / ".cache").resolve()):
        parser.error("Synthetic detailed artifacts must remain under local ignored .cache")
    report = asyncio.run(evaluate(), loop_factory=asyncio.SelectorEventLoop)
    stable = reproducible(report)
    serialized = json.dumps(stable, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not SCORES.exists() or compatible_score_reference() != stable:
            raise SystemExit("Offline scores or source manifest drift")
    else:
        report["manifest"]["started_at"] = run_started.isoformat()
        report["manifest"]["observed_at"] = datetime.now(UTC).isoformat()
        destination.mkdir(parents=True, exist_ok=False)
        (destination / "run.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        for name, value in review_packet(report, load_suite()[1]).items():
            path = destination / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        if args.record_offline:
            SCORES.write_text(serialized, encoding="utf-8", newline="\n")
        print("Local synthetic evidence: " + str(destination.relative_to(ROOT)))
    print(json.dumps(report["summary"], sort_keys=True))
    # Authored negative fixtures must be reported as hard failures; only safe
    # disposition is a software regression gate. Never hide them in a mean score.
    if any(not r["handling_passed"] for r in report["cases"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
