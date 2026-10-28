"""Reproduce the F3-03A mock experiment. No socket transport or live permit."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from future_training.agent.budget import Deadline, SystemClock  # noqa: E402
from future_training.agent.orchestration import Agent  # noqa: E402
from future_training.agent.protocol import parse_json  # noqa: E402
from future_training.domain.catalog import load_catalog  # noqa: E402
from future_training.experiments.token_admission import (  # noqa: E402
    COUNT_ENDPOINT,
    CountedMockWire,
    completed_frames,
    proposed_schedule_reference,
)
from future_training.identity import Principal, owner_id  # noqa: E402
from future_training.providers.gates import ENDPOINT  # noqa: E402
from future_training.providers.responses import ASSETS, ResponsesReplay  # noqa: E402
from future_training.schemas import GenerateRequest, SavedProfile  # noqa: E402


def fixture(name):
    return parse_json((ASSETS / "fixtures" / f"{name}.json").read_bytes())


class SyntheticProfiles:
    async def get(self, principal):
        owner_id(principal)
        profile = parse_json(fixture("plan")["output"][0]["content"][0]["text"])
        return SavedProfile(revision=1, preferences=profile["result"]["plan"]["profile"])


async def measure():
    cases = []
    for name, first in [("initial_plan", "plan"), ("tool_then_continuation", "tool")]:
        clock = SystemClock()
        paths = []

        async def backend(request, first=first, paths=paths):
            paths.append(request.url.path)
            if str(request.url) == COUNT_ENDPOINT:
                return httpx.Response(
                    200, json={"object": "response.input_tokens", "input_tokens": 1000}
                )
            if str(request.url) != ENDPOINT:
                raise AssertionError("Unexpected mock route")
            final = fixture(first)
            return httpx.Response(
                200,
                headers={"content-type": "text/event-stream"},
                content=completed_frames(final),
            )

        wire = CountedMockWire(
            httpx.MockTransport(backend),
            deadline=Deadline(clock),
            synthetic_count_ceiling_micro=1000,
        )
        agent = Agent(
            SyntheticProfiles(),
            load_catalog(),
            provider=ResponsesReplay(httpx.MockTransport(wire)),
            clock=clock,
        )
        async with agent.session(Principal.A, GenerateRequest(profile_revision=1)) as run:
            wire.deadline = run.deadline
            result = await run.execute()
        cases.append(
            {
                "case": name,
                "outcome": result.output().outcome,
                "diagnostic": result.diagnostic,
                "tool_dispatches": result.metrics.tool_dispatches,
                "mock_routes": paths,
                **wire.report(),
            }
        )
    assert cases[0]["outcome"] == "plan" and cases[0]["wire_requests"] == 2
    assert cases[1]["outcome"] == "error" and cases[1]["wire_requests"] == 2
    actions = [
        "count",
        "generation",
        "tool",
        "count",
        "generation",
        "repair",
        "count",
        "generation",
    ]
    return {
        "version": "f3-03a-token-admission-v1",
        "live_provider_requests": 0,
        "ratified_total_wire_limit": 3,
        "amendment_ratified": False,
        "cases": cases,
        "proposed_reference": {
            "source": "pure_reference_no_transport",
            "actions": actions,
            "result": proposed_schedule_reference(actions),
            "count_limit": 3,
            "generation_limit": 3,
            "combined_limit": 6,
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-evidence", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    with asyncio.Runner() as runner:
        report = runner.run(measure())
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    destination = ROOT / "docs/implementation/evidence/f3-03a-token-admission.json"
    if args.check:
        if not destination.exists() or destination.read_text(encoding="utf-8") != text:
            raise SystemExit("F3-03A experiment evidence drift")
    if args.write_evidence:
        destination.write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
