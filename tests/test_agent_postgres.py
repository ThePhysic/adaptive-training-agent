"""Actual PostgreSQL read composition; no approval tables or generation writes."""

import pytest
from agent_doubles import tool_response, valid_final
from test_profile_postgres import pg_schema as pg_schema
from test_profile_postgres import repository as repository

from future_training.agent.fake import ScriptedFake
from future_training.agent.orchestration import Agent
from future_training.agent.tools import ToolResult
from future_training.domain.catalog import load_catalog
from future_training.identity import Principal
from future_training.schemas import GenerateRequest, ProfileSaveRequest

pytestmark = pytest.mark.integration


async def test_orchestrator_uses_real_owned_profile_reads_without_writes(repository, profile):
    await repository.save(Principal.A, ProfileSaveRequest(expected_revision=0, preferences=profile))
    await repository.save(
        Principal.B,
        ProfileSaveRequest(
            expected_revision=0,
            preferences={
                **profile,
                "session_minutes": 30,
            },
        ),
    )
    before = {principal: await repository.get(principal) for principal in Principal}

    def read_profile(request):
        return tool_response(request, name="get_user_preferences")

    def continuation(request):
        read = ToolResult.model_validate_json(request.context().messages[-1].data_json)
        assert read.data.profile == request.context().profile
        return valid_final(request)

    agent = Agent(repository, load_catalog(), provider=ScriptedFake([read_profile, continuation]))
    for principal, minutes in [(Principal.A, 20), (Principal.B, 30)]:
        result = await agent.generate(principal, GenerateRequest(profile_revision=1))
        assert result.output().outcome == "plan"
        assert result.output().plan.profile.session_minutes == minutes
        assert result.metrics.tool_dispatches == 1
        assert result.metrics.provider_requests == 2
    assert {principal: await repository.get(principal) for principal in Principal} == before
