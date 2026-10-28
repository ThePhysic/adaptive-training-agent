"""Generate only bounded local metadata from the existing evaluator, no SDK."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from future_training.evaluation import ROOT  # noqa: E402
from future_training.experiments.model_evaluation import evaluate  # noqa: E402
from future_training.langfuse_local import LangfuseTracer, experiment_projection  # noqa: E402


def main():
    if len(sys.argv) != 1:
        raise SystemExit("No network, credential, destination or live options")
    tracer = LangfuseTracer()
    report = asyncio.run(evaluate(tracer=tracer), loop_factory=asyncio.SelectorEventLoop)
    packet = {
        "version": "langfuse-metadata-v1",
        "manifest": report["manifest"],
        "summary": report["summary"],
        "experiment": experiment_projection(report),
        "observations": tracer.observations.snapshot(),
        "dropped": tracer.observations.dropped,
    }
    destination = ROOT / ".cache/f3-05a/packet.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "observations": len(packet["observations"]),
                "scored_items": len(packet["experiment"]["items"]),
                "dropped": packet["dropped"],
                "external_requests": 0,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
