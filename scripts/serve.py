"""Run only the approved single-process, host-loopback foundation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import uvicorn  # noqa: E402

from future_training.config import Settings  # noqa: E402
from future_training.observability import configure_logging  # noqa: E402

if __name__ == "__main__":
    settings = Settings.from_env()
    configure_logging()
    uvicorn.run(
        "future_training.api:create_app",
        factory=True,
        host=settings.host,
        port=8000,
        workers=1,
        access_log=False,
        proxy_headers=False,
        timeout_graceful_shutdown=35,
        log_config=None,
        loop="future_training.runtime:loop_factory",
    )
