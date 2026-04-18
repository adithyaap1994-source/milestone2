from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from phase1_pipeline.pipeline import run_phase1  # noqa: E402


def main() -> None:
    summary = run_phase1(ROOT)
    print("Phase 1 pipeline completed.")
    for key, value in summary.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
