from typing import Dict

from workflow_common import RunMetrics


def metrics_to_dict(m: RunMetrics) -> Dict[str, float]:
    return {
        "workflow_completion_rate": float(m.workflow_completion_rate),
        "unrecovered_failure_rate": float(m.unrecovered_failure_rate),
        "median_workflow_latency": float(m.median_workflow_latency),
        "mean_retries_per_retryable_step": float(m.mean_retries_per_retryable_step),
    }
