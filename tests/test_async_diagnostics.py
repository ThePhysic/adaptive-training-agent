import asyncio
import json
import os
from pathlib import Path

import pytest
from agent_doubles import Hanging, make_agent

from future_training.agent.fake import ScriptedFake
from future_training.identity import Principal
from future_training.observability import LocalTracer, Span
from future_training.schemas import GenerateRequest


@pytest.mark.parametrize("stop", ["cancel", "deadline"])
async def test_final_cancellation_trace_preserves_state_and_cause(profile, stop):
    hanging = Hanging()
    agent = await make_agent(profile, provider=ScriptedFake([hanging]))
    tracer = LocalTracer()

    async def operation():
        with Span("http", tracer=tracer):
            return await agent.generate(Principal.A, GenerateRequest(profile_revision=1))

    task = asyncio.create_task(operation())
    await hanging.started.wait()
    if stop == "cancel":
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    else:
        agent.clock.advance(30)
        assert (await task).output().error.code == "budget_exceeded"
    assert hanging.cleaned.is_set() and not agent.clock.waiters
    rows = tracer.snapshot()
    if os.environ.get("FATA_F2_EVIDENCE") == "1":
        path = Path(f"docs/implementation/evidence/f2-01-{stop}-trace.json")
        path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    run = next(r for r in rows if r["stage"] == "agent.execute")["attributes"]
    assert run["state"] == ("cancelled" if stop == "cancel" else "failed")
    assert run["reason"] == ("cancelled" if stop == "cancel" else "deadline_exceeded")
    assert run["outcome"] == ("cancelled" if stop == "cancel" else "error")
    assert run["provider_requests"] == 1 and run["uncertain_attempts"] == 1
    assert run["output_tokens"] == 2000
    session = next(r for r in rows if r["stage"] == "agent.session")["attributes"]
    assert session["reason"] == ("cancelled" if stop == "cancel" else "deadline_exceeded")
