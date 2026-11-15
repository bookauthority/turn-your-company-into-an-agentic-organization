import json
import os
import platform
import sys
import time

from experiment.config import CHAPTER_NUMBER, EXPERIMENT_ID, WORKLOAD_IDS
from experiment.runner import run_full_experiment


def main() -> None:
    # Determine evidence directory
    evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
    os.makedirs(evidence_dir, exist_ok=True)
    evidence_path = os.path.join(evidence_dir, "results.json")

    # Run experiment
    runs = run_full_experiment()

    # Assemble evidence object
    evidence = {
        "chapter": CHAPTER_NUMBER,
        "experiment_id": EXPERIMENT_ID,
        "environment": {
            "os": platform.platform(),
            "python": sys.version.split()[0],
        },
        "runs": runs,
        "notes": (
            "Synthetic, deterministic Chapter 10 finance/procurement experiment. "
            "Baseline vs. treatment differ only in processing logic; workloads and "
            "random seeds are shared to allow fair comparison. Metrics are limited "
            "to processing_latency_seconds due to offline sandbox constraints."
        ),
    }

    # Write evidence JSON
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    t0 = time.perf_counter()
    try:
        main()
    finally:
        # Lightweight local timing (not added to metrics) for debugging only
        t1 = time.perf_counter()
        sys.stderr.write(f"Total run.py execution time: {t1 - t0:.4f} seconds\n")
