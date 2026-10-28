"""Synthetic proposal data only. Never provider evidence or monetary authority."""

from datetime import UTC, datetime, timedelta

from future_training.providers.authority import AuthoritySpec, CountBound, frozen_assets

NOW = datetime(2026, 10, 25, 12, tzinfo=UTC)


def spec(**changes):
    values = dict(
        authority_id="synthetic-authority",
        account="synthetic-account",
        project="synthetic-project",
        grant="synthetic-grant",
        session="synthetic-session",
        operator="synthetic-operator",
        assets_sha256=frozen_assets(),
        starts_at=NOW,
        expires_at=NOW + timedelta(hours=1),
        project_limit_micro=200000,
        grant_limit_micro=180000,
        day_limit_micro=150000,
        session_limit_micro=100000,
        count_bound=CountBound(
            kind="synthetic_fixture",
            ceiling_micro=1000,
            evidence_ref="synthetic-count-bound-not-provider-proof",
        ),
    )
    values.update(changes)
    return AuthoritySpec(**values)
