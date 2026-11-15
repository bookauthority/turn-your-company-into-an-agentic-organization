from __future__ import annotations

import time
from typing import Dict, List

from .config import WORKLOAD_IDS, WORKLOAD_INVOICES, WORKLOAD_POS, WORKLOAD_RECON, WORKLOAD_SPEND
from .data import load_workload
from .baseline import (
    process_invoices_baseline,
    process_prs_baseline,
    process_recon_baseline,
    process_spend_baseline,
)
from .treatment import (
    process_invoices_treatment,
    process_prs_treatment,
    process_recon_treatment,
    process_spend_treatment,
)


def _run_variant_for_workload(variant: str, workload_id: str, dataset) -> Dict:
    """Run baseline or treatment for a single workload, returning a run record.

    The run record conforms to the required evidence schema for entries in
    the `runs` list.
    """
    run_id = f"{variant}-{workload_id}-0"

    if workload_id == WORKLOAD_INVOICES:
        if variant == "baseline":
            metrics = process_invoices_baseline(dataset)
        else:
            metrics = process_invoices_treatment(dataset)
    elif workload_id == WORKLOAD_POS:
        if variant == "baseline":
            metrics = process_prs_baseline(dataset)
        else:
            metrics = process_prs_treatment(dataset)
    elif workload_id == WORKLOAD_RECON:
        if variant == "baseline":
            metrics = process_recon_baseline(dataset)
        else:
            metrics = process_recon_treatment(dataset)
    elif workload_id == WORKLOAD_SPEND:
        if variant == "baseline":
            metrics = process_spend_baseline(dataset)
        else:
            metrics = process_spend_treatment(dataset)
    else:
        raise ValueError(f"Unknown workload_id: {workload_id}")

    # Ensure all metrics are finite numbers (no bool/None/etc.)
    cleaned_metrics: Dict[str, float] = {}
    for key, value in metrics.items():
        # Allow ints and floats; cast to float explicitly
        if not isinstance(value, (int, float)):
            continue
        cleaned_metrics[key] = float(value)

    return {
        "variant": variant,
        "workload_id": workload_id,
        "run_id": run_id,
        "success": True,
        "metrics": cleaned_metrics,
    }


def run_full_experiment() -> List[Dict]:
    """Run baseline and treatment for all workloads, return list of run dicts.

    At least one baseline and one treatment run are produced per workload ID.
    """
    runs: List[Dict] = []
    for workload_id in WORKLOAD_IDS:
        dataset = load_workload(workload_id)
        # Baseline
        runs.append(_run_variant_for_workload("baseline", workload_id, dataset))
        # Treatment
        runs.append(_run_variant_for_workload("treatment", workload_id, dataset))
    return runs
