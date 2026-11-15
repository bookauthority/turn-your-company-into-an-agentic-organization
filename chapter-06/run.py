import json
import os
import platform
from datetime import datetime

from experiments.ch06.config import EXPERIMENT_ID, WORKLOAD_IDS
from experiments.ch06.single_agent import run_baseline_for_workload
from experiments.ch06.multi_agent import run_treatment_for_workload


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def main() -> None:
    evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
    ensure_dir(evidence_dir)
    results_path = os.path.join(evidence_dir, "results.json")

    runs = []

    # For reproducibility keep run ids simple and deterministic.
    for workload_id in WORKLOAD_IDS:
        # Baseline variant
        baseline_metrics = run_baseline_for_workload(workload_id)
        runs.append(
            {
                "variant": "baseline",
                "workload_id": workload_id,
                "run_id": "baseline-1",
                "success": True,
                "metrics": baseline_metrics,
            }
        )

        # Treatment variant
        treatment_metrics = run_treatment_for_workload(workload_id)
        runs.append(
            {
                "variant": "treatment",
                "workload_id": workload_id,
                "run_id": "treatment-1",
                "success": True,
                "metrics": treatment_metrics,
            }
        )

    evidence = {
        "chapter": 6,
        "experiment_id": EXPERIMENT_ID,
        "environment": {
            "os": platform.platform(),
            "python": platform.python_version(),
        },
        "runs": runs,
        "notes": (
            "Synthetic, rule-based approximation of single-agent vs multi-agent "
            "onboarding workflows. Metrics are computed from actual in-process "
            "execution without external services."
        ),
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
    }

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
