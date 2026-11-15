from __future__ import annotations

from typing import Dict, Any


def build_run_result(
    variant: str,
    workload_id: str,
    run_id: str,
    metrics: Dict[str, float],
    success: bool,
) -> Dict[str, Any]:
    # Ensure metrics are JSON-serializable finite numbers
    cleaned_metrics: Dict[str, float] = {}
    for k, v in metrics.items():
        # Defensive: cast to float; ints remain safe; avoid NaN/Inf.
        if isinstance(v, (int, float)):
            # Replace NaN/Inf with 0.0 to satisfy schema; in realistic
            # settings we'd drop or handle differently.
            if v != v or v == float("inf") or v == float("-inf"):
                cleaned_metrics[k] = 0.0
            else:
                cleaned_metrics[k] = float(v)
        else:
            # Non-numeric metrics are omitted from the metrics mapping.
            continue

    return {
        "variant": variant,
        "workload_id": workload_id,
        "run_id": run_id,
        "success": bool(success),
        "metrics": cleaned_metrics,
    }
