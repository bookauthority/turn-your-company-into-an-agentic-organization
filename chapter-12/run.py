import json
import os
import platform
import time
import uuid

from knowledge_layer.evaluation import run_full_experiment


def main() -> None:
    chapter = 12
    experiment_id = "exp-12-knowledge-layer-rag-impact-v1"

    evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", ".")
    os.makedirs(evidence_dir, exist_ok=True)
    evidence_path = os.path.join(evidence_dir, "results.json")

    environment = {
        "os": platform.platform(),
        "python": platform.python_version(),
    }

    # Run the experiment once for each workload and variant
    runs = []
    experiment_results = run_full_experiment()

    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    for (variant, workload_id), metrics in experiment_results.items():
        run_record = {
            "variant": variant,
            "workload_id": workload_id,
            "run_id": f"{variant}-{workload_id}-{uuid.uuid4().hex}",
            "success": True,
            "metrics": metrics,
            "timestamp_utc": timestamp,
        }
        runs.append(run_record)

    evidence = {
        "chapter": chapter,
        "experiment_id": experiment_id,
        "environment": environment,
        "runs": runs,
        "notes": (
            "Offline deterministic simulation of baseline vs. centralized knowledge "
            "layer RAG agents over synthetic corpora and workloads. Metrics are "
            "computed from real execution within this sandbox. Index update latency "
            "is not reported because genuine update events are not simulated."
        ),
    }

    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
