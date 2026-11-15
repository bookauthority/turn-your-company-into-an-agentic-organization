import json
import os
import platform
from pathlib import Path

from experiment import run_experiment
from evidence_writer import write_evidence


def main() -> None:
    chapter = 11
    experiment_id = "exp-ch11-agentic-internal-services-hr-it-v1"

    # Run simulated experiment and collect per-run metric summaries
    runs = run_experiment()

    environment = {
        "os": os.name,
        "python": platform.python_version(),
    }

    evidence = {
        "chapter": chapter,
        "experiment_id": experiment_id,
        "environment": environment,
        "runs": runs,
        "notes": (
            "Simulated internal services experiment for Chapter 11. "
            "Metrics are derived from deterministic offline workflow "
            "simulation (no external systems)."
        ),
    }

    # Determine evidence directory (default /evidence)
    evidence_dir = os.getenv("BOOKMAS_EVIDENCE_DIR", "/evidence")
    evidence_path = Path(evidence_dir) / "results.json"

    write_evidence(evidence, evidence_path)


if __name__ == "__main__":
    main()
