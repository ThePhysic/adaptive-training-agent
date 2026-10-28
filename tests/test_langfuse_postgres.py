import pytest
from test_approvals_postgres import request
from test_approvals_postgres import rig as rig
from test_profile_postgres import pg_schema as pg_schema

from future_training.identity import Principal
from future_training.langfuse_local import LangfuseTracer, Observations
from future_training.observability import Span

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("state", ["failing", "closed", "full"])
async def test_unavailable_telemetry_cannot_interrupt_real_approval(rig, state):
    class Broken(Observations):
        def append(self, value):
            raise RuntimeError("synthetic-private-export-failure")

    observations = Broken() if state == "failing" else Observations(capacity=1)
    if state == "closed":
        observations.close()
    tracer = LangfuseTracer(observations=observations)
    with Span("http", tracer=tracer):
        snapshot = await rig.candidate()
        result = await rig.service.approve(Principal.A, request(snapshot))
        repeated = await rig.service.approve(Principal.A, request(snapshot))
    assert result == repeated
    assert await rig.counts() == (1, 1, 1)
    if state == "failing":
        assert tracer.projection_failures > 0
