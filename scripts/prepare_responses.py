"""Generate/check bounded offline Responses assets. Never opens a transport."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from future_training.providers.artifacts import assets  # noqa: E402
from future_training.providers.responses import ASSETS  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = assets()
    for name, text in expected.items():
        path = ASSETS / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                raise SystemExit(f"Offline Responses asset drift: {name}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
    print({"assets": len(expected), "mode": "checked" if args.check else "written", "live": False})
