from __future__ import annotations

import json
import os
from pathlib import Path

from src.experiment import run_experiment


def main() -> None:
    evidence = run_experiment()

    evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
    out_dir = Path(evidence_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "results.json"

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
