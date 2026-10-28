"""Offline typed authority/binding/gate tests, no positive monetary authority."""

from datetime import datetime, timedelta

import httpx
import pytest
from authority_doubles import NOW, spec
from pydantic import ValidationError
from test_observability import console as console

from future_training.agent.budget import AgentFault
from future_training.agent.orchestration import Agent
from future_training.candidates import CandidateStore
from future_training.domain.catalog import load_catalog
from future_training.persistence.authority import AuthorityLedger
from future_training.persistence.spending import LedgerFault
from future_training.providers.authority import CountBound
from future_training.providers.gates import ENDPOINT, LiveGate, LivePermit
from future_training.providers.probe import FixedProfile, ResponsesProbe, SingleProbe
from future_training.providers.sender import BearerCredential, OpenAIHTTPS, provider_request
from future_training.schemas import GenerateRequest


@pytest.mark.parametrize("kind", ["replay", "live"])
async def test_mutated_fake_label_cannot_enter_native_provider_setup(kind):
    agent = Agent(FixedProfile(), load_catalog())
    agent.provider.kind = kind
    from future_training.identity import Principal

    result = await agent.generate(Principal.A, GenerateRequest(profile_revision=1))
    assert result.diagnostic == "live_provider_disabled"
    assert result.output().outcome == "error"
    assert result.metrics.provider_requests == 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("model", "other-model"),
        ("tier", "priority"),
        ("endpoints", ("https://evil.invalid", ENDPOINT)),
        ("project_limit_micro", 0),
        ("grant_limit_micro", True),
        ("day_limit_micro", 1.5),
        ("session_limit_micro", 10**9 + 1),
        ("expires_at", NOW),
        ("starts_at", datetime(2026, 10, 25)),
        ("expires_at", NOW + timedelta(hours=3)),
        ("project", "bad\r\nHost:evil"),
    ],
)
def test_strict_authority_bounds_and_fixed_bindings(field, value):
    with pytest.raises(ValidationError):
        spec(**{field: value})


@pytest.mark.parametrize(
    "value",
    [
        dict(kind="unknown", ceiling_micro=0, evidence_ref=None),
        dict(kind="provider_reviewed", ceiling_micro=None, evidence_ref="evidence"),
        dict(kind="provider_reviewed", ceiling_micro=1000, evidence_ref=None),
        dict(kind="synthetic_fixture", ceiling_micro=True, evidence_ref="evidence"),
    ],
)
def test_count_charge_never_inferred_or_coerced(value):
    with pytest.raises(ValidationError):
        CountBound(**value)


async def test_unknown_pricing_cannot_issue_or_build(monkeypatch):
    s = spec(count_bound=CountBound(kind="unknown", ceiling_micro=None, evidence_ref=None))

    async def no_sql():
        pytest.fail("No SQL or transport for unknown pricing")

    ledger = AuthorityLedger(s, connect=no_sql, now=lambda: NOW)
    with pytest.raises(LedgerFault, match="count_pricing_unverified"):
        await ledger.prepare()
    with pytest.raises(LedgerFault, match="count_pricing_unverified"):
        await ledger.simulate()
    with pytest.raises(LedgerFault, match="count_pricing_unverified"):
        ResponsesProbe(ledger, httpx.MockTransport(lambda r: None))


async def test_both_actual_network_barriers_remain_independent(monkeypatch):
    reviewed = CountBound(
        kind="provider_reviewed",
        ceiling_micro=1000,
        evidence_ref="synthetic-hypothetical-not-real-review",
    )
    s = spec(count_bound=reviewed)

    async def no_sql():
        pytest.fail("No active authority may be created")

    ledger = AuthorityLedger(s, execution="live", connect=no_sql, now=lambda: NOW)
    gate = LiveGate(enabled=True, permit=LivePermit(ENDPOINT, s.model, s.expires_at, s.grant, True))
    credential = BearerCredential("synthetic-key-canary")
    connector = OpenAIHTTPS(gate=gate, credential=credential, binding=s)
    provider = ResponsesProbe(ledger, connector, gate=gate)
    try:
        for _ in range(2):
            with pytest.raises(AgentFault):
                await ledger.activate(gate)
            with pytest.raises(AgentFault):
                await SingleProbe(provider).run()
            with pytest.raises(AgentFault):
                await connector.handle_async_request(httpx.Request("POST", ENDPOINT, content=b"{}"))
            monkeypatch.setattr(LiveGate, "check", lambda self: None)
        assert connector._transport is None
    finally:
        await connector.aclose()
    assert connector._credential is None


def test_binding_supplies_only_explicit_account_project_headers():
    s = spec()
    outbound = provider_request(
        httpx.Request(
            "POST",
            ENDPOINT,
            content=b"{}",
            headers={"OpenAI-Project": "attacker", "OpenAI-Organization": "attacker"},
        ),
        BearerCredential("synthetic-secret"),
        binding=s,
    )
    assert outbound.headers["openai-project"] == s.project
    assert outbound.headers["openai-organization"] == s.account
    assert "synthetic-account" not in repr(s) + str(s)


def test_probe_cannot_be_attached_to_application_candidate_store():
    ledger = AuthorityLedger(spec(), connect=lambda: None, now=lambda: NOW)
    provider = ResponsesProbe(ledger, httpx.MockTransport(lambda r: None))
    profiles = FixedProfile()
    candidates = CandidateStore(profiles, load_catalog())
    with pytest.raises(ValueError, match="unpublished"):
        Agent(profiles, load_catalog(), provider=provider, candidates=candidates)


def test_frozen_assets_change_fails_closed(monkeypatch):
    from future_training.providers import authority

    s = spec()
    monkeypatch.setattr(authority, "frozen_assets", lambda: "0" * 64)
    with pytest.raises(LedgerFault, match="assets_changed"):
        s.checked(positive=True)
    # Cleanup/reconciliation repositories can still be constructed after a
    # catalog/assets change; admission remains blocked by the current check.
    assert AuthorityLedger(s).spec == s
