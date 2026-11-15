from __future__ import annotations

from typing import List

from .orchestrator import RunRecord


def aggregate_sli(runs: List[RunRecord], name: str) -> float:
    """Compute simple SLIs from a list of run records.

    These SLIs are illustrative and are used by the treatment orchestration
    and top-level script. They are not written as per-run metrics.

    - "success_rate": fraction of successful runs.
    - "avg_latency_ms": average latency in ms.
    """

    if not runs:
        return 0.0

    if name == "success_rate":
        successes = sum(1 for r in runs if r.success)
        return successes / float(len(runs))
    if name == "avg_latency_ms":
        total = sum(r.metrics.get("latency_ms", 0.0) for r in runs)
        return total / float(len(runs))
    raise ValueError(f"Unknown SLI name: {name}")


def evaluate_slos(runs: List[RunRecord]) -> str:
    """Evaluate simple SLO-style conditions on treatment runs.

    This returns a human-readable note string that can be appended to the
    top-level evidence "notes" field. It intentionally does not alter the
    metrics structure.

    SLO examples (synthetic):
    - success_rate >= 0.8
    - avg_latency_ms <= 200.0
    """

    if not runs:
        return " No treatment runs were available for SLO evaluation."

    success_rate = aggregate_sli(runs, name="success_rate")
    avg_latency = aggregate_sli(runs, name="avg_latency_ms")

    slo_target_success = 0.8
    slo_target_latency_ms = 200.0

    success_ok = success_rate >= slo_target_success
    latency_ok = avg_latency <= slo_target_latency_ms

    return (
        f" Treatment SLO evaluation (synthetic): success_rate={success_rate:.3f} "
        f"(target>={slo_target_success:.2f}, within_target={bool(success_ok)}), "
        f"avg_latency_ms={avg_latency:.3f} (target<={slo_target_latency_ms:.1f}, "
        f"within_target={bool(latency_ok)})."
    )
