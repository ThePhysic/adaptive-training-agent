"""Immutable one-request authority proposals; no network or grant activation."""

import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, StrictInt, model_validator

from future_training.agent.protocol import Wire, canonical
from future_training.domain.catalog import load_catalog
from future_training.domain.validator import VALIDATOR_VERSION
from future_training.persistence.spending import LedgerFault
from future_training.providers.accounting import RATE_VERSION
from future_training.providers.counting import COUNT_ENDPOINT
from future_training.providers.gates import ENDPOINT
from future_training.providers.schemas import output_schema, provider_tools
from future_training.schemas import ContentHash, Identifier, ProfilePreferences

ASSETS = Path(__file__).resolve().parents[3] / "data/experiments/f3-02/v1"


def frozen_assets():
    files = {
        name: hashlib.sha256((ASSETS / name).read_text(encoding="utf-8").encode()).hexdigest()
        for name in ("prompt.txt", "tools.json", "output.json", "config.json")
    }
    return hashlib.sha256(
        canonical(
            {
                "files": files,
                "catalog": load_catalog().fingerprint(),
                "validator": VALIDATOR_VERSION,
                "tools": provider_tools(),
                "output": output_schema(),
                "rate": RATE_VERSION,
                "input": "compatibility-profile-v1",
            }
        )
    ).hexdigest()


def approved_preferences():
    return ProfilePreferences(
        adult=True,
        goal="general_strength",
        equipment="bodyweight",
        experience="beginner",
        days_per_week=2,
        session_minutes=20,
    )


class CountBound(Wire):
    kind: Literal["unknown", "synthetic_fixture", "provider_reviewed"]
    ceiling_micro: Annotated[StrictInt, Field(ge=1, le=10**9)] | None
    evidence_ref: Identifier | None

    @model_validator(mode="after")
    def explicit_evidence(self):
        if self.kind == "unknown":
            if self.ceiling_micro is not None or self.evidence_ref is not None:
                raise ValueError("Unknown count pricing has no ceiling")
        elif self.ceiling_micro is None or self.evidence_ref is None:
            raise ValueError("Explicit count bound and evidence required")
        return self


class AuthoritySpec(Wire):
    authority_id: Identifier
    account: Identifier
    project: Identifier
    grant: Identifier
    session: Identifier
    operator: Identifier
    model: Literal["gpt-6.1-sol"] = "gpt-6.1-sol"
    tier: Literal["default"] = "default"
    endpoints: tuple[Literal[ENDPOINT], Literal[COUNT_ENDPOINT]] = (ENDPOINT, COUNT_ENDPOINT)
    rate_version: Literal[RATE_VERSION] = RATE_VERSION
    input_version: Literal["compatibility-profile-v1"] = "compatibility-profile-v1"
    assets_sha256: ContentHash
    starts_at: datetime
    expires_at: datetime
    project_limit_micro: Annotated[StrictInt, Field(ge=1, le=10**9)]
    grant_limit_micro: Annotated[StrictInt, Field(ge=1, le=10**9)]
    day_limit_micro: Annotated[StrictInt, Field(ge=1, le=10**9)]
    session_limit_micro: Annotated[StrictInt, Field(ge=1, le=10**9)]
    count_bound: CountBound

    def __repr__(self):
        return "<AuthoritySpec redacted>"

    def __str__(self):
        return self.__repr__()

    @model_validator(mode="after")
    def utc_window(self):
        if any(t.utcoffset() != timedelta(0) for t in (self.starts_at, self.expires_at)):
            raise ValueError("Explicit UTC timestamps required")
        if not timedelta(0) < self.expires_at - self.starts_at <= timedelta(hours=2):
            raise ValueError("Authority window must be positive and at most two hours")
        return self

    def checked(self, *, positive=False, network=False):
        checked = AuthoritySpec.model_validate_json(self.model_dump_json())
        if checked.assets_sha256 != frozen_assets():
            raise LedgerFault("authority_assets_changed")
        if positive and checked.count_bound.kind == "unknown":
            raise LedgerFault("count_pricing_unverified")
        if network and checked.count_bound.kind != "provider_reviewed":
            raise LedgerFault("count_pricing_unverified")
        return checked

    def fingerprint(self):
        return hashlib.sha256(canonical(self.model_dump(mode="json"))).hexdigest()
