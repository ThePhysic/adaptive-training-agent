"""Versioned offline assets, not a live evaluation runner or a quality result."""

import hashlib
import json
from pathlib import Path

from pydantic import ValidationError

from future_training.agent.protocol import SYSTEM_PROMPT
from future_training.domain.catalog import load_catalog
from future_training.evaluation import load_scenarios
from future_training.providers.accounting import MODEL, RATE_VERSION
from future_training.providers.gates import ENDPOINT
from future_training.providers.schemas import output_schema, provider_tools
from future_training.schemas import ProfilePreferences


def assets():
    catalog = load_catalog()
    manifest, cases = load_scenarios(catalog)
    eligibility = []
    for case in cases:
        reason = "validator_only"
        if case.task != "validate":
            try:
                profile = ProfilePreferences.model_validate(case.profile)
            except ValidationError:
                reason = "profile_rejected"
            else:
                reason = (
                    "save_rejected"
                    if catalog.unknown_exclusions(profile)
                    else "decline_flag_not_in_agent_api"
                    if case.choices_declined
                    else "agent_reachable"
                )
        eligibility.append({"case_id": case.case_id, "split": case.split, "eligibility": reason})
    values = {
        "prompt.txt": SYSTEM_PROMPT
        + (
            " Use the exact supplied domain timing and prescription schema. "
            "If constraints are infeasible, clarify without replacing them. "
            "Return only the required result envelope; do not reveal hidden reasoning.\n"
        ),
        "config.json": {
            "version": "real-model-config-v1",
            "endpoint": ENDPOINT,
            "model": MODEL,
            "service_tier": "default",
            "reasoning": {"effort": "low"},
            "store": False,
            "background": False,
            "stream": True,
            "tool_choice": "auto",
            "parallel_tool_calls": False,
            "prompt_cache_options": {"mode": "implicit", "ttl": "30m"},
        },
        "tools.json": {"version": "real-read-tools-v1", "tools": provider_tools()},
        "output.json": {"version": "real-plan-envelope-v1", "schema": output_schema()},
    }
    serialized = {
        name: value
        if isinstance(value, str)
        else json.dumps(value, indent=2, sort_keys=True) + "\n"
        for name, value in values.items()
    }
    serialized["manifest.json"] = (
        json.dumps(
            {
                "version": "offline-provider-manifest-v1",
                "evidence_source": "replay",
                "live_enabled": False,
                "input_admission": "unproven_live_fixture_allowances_only",
                "explanation_clarity": "not_measured_no_explanation_contract",
                "rate_version": RATE_VERSION,
                "catalog_sha256": catalog.fingerprint(),
                "dataset_sha256": manifest["dataset_sha256"],
                "legacy_held_out_is_developer_exposed": True,
                "permitted_evidence_labels": ["template", "fake", "replay", "live"],
                "cases": eligibility,
                "fixture_provenance": "authored_synthetic_not_provider_capture",
                "fixture_sha256": {
                    path.name: hashlib.sha256(path.read_text(encoding="utf-8").encode()).hexdigest()
                    for path in sorted(
                        (
                            Path(__file__).resolve().parents[3]
                            / "data/experiments/f3-02/v1/fixtures"
                        ).glob("*.json")
                    )
                },
                "sha256": {
                    name: hashlib.sha256(text.encode()).hexdigest()
                    for name, text in serialized.items()
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return serialized
