import json
import os
import platform
import sys
from typing import List

from experiment.workload import generate_synthetic_tickets
from experiment.orchestrator import run_baseline, run_treatment, RunRecord
from experiment.evidence import build_evidence
from experiment.monitoring import evaluate_slos


CHAPTER_NUMBER = 14
EXPERIMENT_ID = "exp-014-operate-monitor-improve-mas-v1"


def main() -> None:
    # Generate a deterministic synthetic workload
    seed = 42
    ticket_count = 40  # bounded for safe execution
    tickets = list(generate_synthetic_tickets(seed=seed, count=ticket_count))
    workload_id = "synthetic_ticket_stream_v1"

    # Run baseline and treatment
    baseline_runs: List[RunRecord] = run_baseline(tickets=tickets, workload_id=workload_id)
    treatment_runs: List[RunRecord] = run_treatment(tickets=tickets, workload_id=workload_id)

    # Build environment info
    env_info = {
        "os": platform.platform(),
        "python": sys.version.split()[0],
    }

    # Simple SLO-style evaluation on the treatment runs only (observed aggregates)
    slo_notes = evaluate_slos(treatment_runs)

    combined_notes = (
        "Synthetic multi-agent baseline vs treatment. "
        "Metrics are per-run latency_ms and steps; higher-level SLO-style aggregates "
        "are computed internally for the treatment variant. "
        + slo_notes
    )

    # Build evidence structure
    evidence = build_evidence(
        chapter=CHAPTER_NUMBER,
        experiment_id=EXPERIMENT_ID,
        environment=env_info,
        baseline_runs=baseline_runs,
        treatment_runs=treatment_runs,
        notes=combined_notes,
    )

    # Determine evidence directory
    evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
    os.makedirs(evidence_dir, exist_ok=True)
    out_path = os.path.join(evidence_dir, "results.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
