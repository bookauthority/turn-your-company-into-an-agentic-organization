import json
import os
import platform
import uuid

from experiment.config import CHAPTER_NUMBER, EXPERIMENT_ID, WORKLOAD_IDS
from experiment.crm_sim import CRMSimulator
from experiment.agents import (
    run_lead_enrichment_and_routing,
    run_pipeline_hygiene,
    run_quote_to_order_assistance,
    run_followup_and_cycle_time,
    run_forecasting_support,
)
from experiment.metrics import (
    build_run_result,
)


def get_evidence_dir() -> str:
    return os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")


def main() -> None:
    evidence_dir = get_evidence_dir()
    os.makedirs(evidence_dir, exist_ok=True)

    env = {
        "os": platform.platform(),
        "python": platform.python_version(),
    }

    runs = []

    # Lead Enrichment and Routing
    for variant in ("baseline", "treatment"):
        crm = CRMSimulator(seed=42)
        workload_id = WORKLOAD_IDS["lead_enrichment_and_routing"]
        metrics = run_lead_enrichment_and_routing(crm, variant=variant)
        run_id = f"{workload_id}-{variant}-{uuid.uuid4().hex[:8]}"
        runs.append(build_run_result(variant, workload_id, run_id, metrics, success=True))

    # Pipeline Hygiene
    for variant in ("baseline", "treatment"):
        crm = CRMSimulator(seed=123)
        workload_id = WORKLOAD_IDS["pipeline_hygiene"]
        metrics = run_pipeline_hygiene(crm, variant=variant)
        run_id = f"{workload_id}-{variant}-{uuid.uuid4().hex[:8]}"
        runs.append(build_run_result(variant, workload_id, run_id, metrics, success=True))

    # Quote to Order Assistance
    for variant in ("baseline", "treatment"):
        crm = CRMSimulator(seed=777)
        workload_id = WORKLOAD_IDS["quote_to_order_assistance"]
        metrics = run_quote_to_order_assistance(crm, variant=variant)
        run_id = f"{workload_id}-{variant}-{uuid.uuid4().hex[:8]}"
        runs.append(build_run_result(variant, workload_id, run_id, metrics, success=True))

    # Followup and Cycle Time
    for variant in ("baseline", "treatment"):
        crm = CRMSimulator(seed=1001)
        workload_id = WORKLOAD_IDS["followup_and_cycle_time"]
        metrics = run_followup_and_cycle_time(crm, variant=variant)
        run_id = f"{workload_id}-{variant}-{uuid.uuid4().hex[:8]}"
        runs.append(build_run_result(variant, workload_id, run_id, metrics, success=True))

    # Forecasting Support
    for variant in ("baseline", "treatment"):
        crm = CRMSimulator(seed=2024)
        workload_id = WORKLOAD_IDS["forecasting_support"]
        metrics = run_forecasting_support(crm, variant=variant)
        run_id = f"{workload_id}-{variant}-{uuid.uuid4().hex[:8]}"
        runs.append(build_run_result(variant, workload_id, run_id, metrics, success=True))

    results = {
        "chapter": CHAPTER_NUMBER,
        "experiment_id": EXPERIMENT_ID,
        "environment": env,
        "runs": runs,
        "notes": (
            "Synthetic offline simulation of agentic vs. manual sales operations. "
            "Durations and costs are simulated and deterministic; no real CRM or LLM calls."
        ),
    }

    out_path = os.path.join(evidence_dir, "results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, sort_keys=False)


if __name__ == "__main__":
    main()
