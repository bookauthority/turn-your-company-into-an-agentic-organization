import json
import os
from typing import Any, Dict, List

from analysis_stub import metrics_to_dict
from baseline_engine import BaselineEngine
from treatment_engine import TreatmentEngine
from workflow_common import (
    CHAPTER_NUMBER,
    EXPERIMENT_ID,
    WORKLOAD_IDS,
    WorkflowConfig,
    compute_metrics_from_traces,
    deterministic_random,
    env_info,
    ensure_evidence_dir,
    get_workflow_config,
)


def run_variant_for_workload(variant: str, cfg: WorkflowConfig, seed: int) -> Dict[str, Any]:
    """Execute one run for a given variant and workload.

    Returns a dict for insertion into the evidence "runs" list.
    """

    rng = deterministic_random(seed)

    if variant == "baseline":
        engine = BaselineEngine(cfg, rng)
    elif variant == "treatment":
        # Treatment has a simple durable store per run (file path contains workload and seed)
        store_dir = os.path.join(".treatment_state")
        os.makedirs(store_dir, exist_ok=True)
        store_path = os.path.join(store_dir, f"{cfg.workload_id}-{seed}.json")
        engine = TreatmentEngine(cfg, rng, store_path)
    else:
        raise ValueError(f"Unknown variant: {variant}")

    traces = engine.run_workflows()
    metrics = compute_metrics_from_traces(traces)
    metrics_dict = metrics_to_dict(metrics)

    run_id = f"{cfg.workload_id}-{variant}-seed{seed}"
    success = True  # run succeeded if the code reached here without crashing

    return {
        "variant": variant,
        "workload_id": cfg.workload_id,
        "run_id": run_id,
        "success": success,
        "metrics": metrics_dict,
    }


def main() -> None:
    evidence_dir = ensure_evidence_dir()
    runs: List[Dict[str, Any]] = []

    # For reproducibility we pick a fixed seed per workload/variant pair.
    base_seed = 42

    for idx, workload_id in enumerate(WORKLOAD_IDS):
        cfg = get_workflow_config(workload_id)
        # baseline
        r_baseline = run_variant_for_workload("baseline", cfg, base_seed + idx * 2)
        runs.append(r_baseline)
        # treatment
        r_treatment = run_variant_for_workload("treatment", cfg, base_seed + idx * 2 + 1)
        runs.append(r_treatment)

    evidence: Dict[str, Any] = {
        "chapter": CHAPTER_NUMBER,
        "experiment_id": EXPERIMENT_ID,
        "environment": env_info(),
        "runs": runs,
        "notes": "Metrics are derived from a scaled-down, single-process simulation of baseline vs. durable state-machine workflow engines. Durability for treatment is emulated using a small JSON file-based store rather than a real database.",
    }

    out_path = os.path.join(evidence_dir, "results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)


if __name__ == "__main__":
    main()
