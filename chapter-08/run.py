import json
import os
import sys
from pathlib import Path

from experiment.runner import run_all_workloads


def main() -> None:
    chapter_number = 8
    experiment_id = "exp-ch08-cx-agentic-support-v1"

    # Detect environment
    env_info = {
        "os": os.name,
        "python": sys.version.split()[0],
    }

    # Run workloads for both baseline and treatment
    runs, extra_notes = run_all_workloads()

    evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
    evidence_path = Path(evidence_dir)
    evidence_path.mkdir(parents=True, exist_ok=True)
    results_file = evidence_path / "results.json"

    evidence = {
        "chapter": chapter_number,
        "experiment_id": experiment_id,
        "environment": env_info,
        "runs": runs,
    }
    if extra_notes:
        evidence["notes"] = extra_notes

    with results_file.open("w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
