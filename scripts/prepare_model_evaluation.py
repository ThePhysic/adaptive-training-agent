"""Create/check NEW authored assets only; never modifies frozen F1 evaluation."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from future_training.experiments.model_eval_assets import DIRECTORY, generated_assets  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for name, content in generated_assets().items():
        path = DIRECTORY / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                raise SystemExit("Model evaluation asset drift: " + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    print("50 authored cases; 40 development/10 exposed comparison candidates; live disabled")
