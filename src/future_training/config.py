"""No SDK, .env loading, provider credentials, exporters, or live-mode path."""

import os
from collections.abc import Mapping
from typing import Literal

from pydantic import ValidationError

from future_training.schemas import Contract


class Settings(Contract):
    host: Literal["127.0.0.1"] = "127.0.0.1"
    workers: Literal["1"] = "1"
    provider: Literal["fake"] = "fake"
    telemetry_exporter: Literal["none"] = "none"
    local_development: Literal["0", "1"] = "0"
    environment: Literal["local"] = "local"

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        env = os.environ if env is None else env
        names = {
            "host": "FATA_HOST",
            "workers": "FATA_WORKERS",
            "provider": "FATA_PROVIDER",
            "telemetry_exporter": "FATA_TELEMETRY_EXPORTER",
            "local_development": "FATA_LOCAL_DEV",
            "environment": "FATA_ENV",
        }
        try:
            return cls.model_validate(
                {key: env[name] for key, name in names.items() if name in env}
            )
        except ValidationError:
            raise RuntimeError("Unsupported F1-01 configuration") from None
