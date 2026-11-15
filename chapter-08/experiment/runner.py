from __future__ import annotations

"""Experiment runner that simulates workloads and prepares evidence runs."""

from dataclasses import dataclass
import random
from typing import Dict, List, Tuple

from .config import WORKLOAD_SIZE
from .workload import WorkloadConfig, generate_tickets
from .agents import simulate_baseline, simulate_treatment
from .metrics import aggregate_metrics, metrics_to_dict


@dataclass(frozen=True)
class RunDescriptor:
    variant: str  # "baseline" or "treatment"
    workload_id: str
    run_id: str
    success: bool
    metrics: Dict[str, float]


def _run_single(
    *, workload_id: str, variant: str, tickets_seed: int, rng_seed: int
) -> RunDescriptor:
    """Run a single variant on a generated workload and return metrics.

    tickets_seed controls the ticket generation, while rng_seed controls
    stochastic behavior inside the simulators. Both are fixed to achieve
    determinism.
    """

    if workload_id == "historical_replay_workload":
        num_tickets = WORKLOAD_SIZE.historical_replay_tickets
    elif workload_id == "live_ab_workload":
        num_tickets = WORKLOAD_SIZE.live_ab_tickets
    else:
        raise ValueError(f"Unknown workload_id: {workload_id}")

    wcfg = WorkloadConfig(workload_id=workload_id, num_tickets=num_tickets, seed=tickets_seed)
    tickets = generate_tickets(wcfg)

    rng = random.Random(rng_seed)

    outcomes = []
    if variant == "baseline":
        for t in tickets:
            outcomes.append(simulate_baseline(t, rng))
        include_agent_metrics = False
    elif variant == "treatment":
        for t in tickets:
            outcomes.append(simulate_treatment(t, rng))
        include_agent_metrics = True
    else:
        raise ValueError(f"Unknown variant: {variant}")

    agg = aggregate_metrics(outcomes, include_agent_specific=include_agent_metrics)
    metrics_dict = metrics_to_dict(agg)

    run_id = f"{workload_id}-{variant}-seed{tickets_seed}-{rng_seed}"

    return RunDescriptor(
        variant=variant,
        workload_id=workload_id,
        run_id=run_id,
        success=True,
        metrics=metrics_dict,
    )


def run_all_workloads() -> Tuple[List[Dict[str, object]], str]:
    """Execute all workloads for baseline and treatment.

    Returns a tuple of:
    - runs: list of dicts compatible with the evidence schema's `runs`
      entries.
    - notes: free-form string summarizing the simulation characteristics.
    """

    runs: List[Dict[str, object]] = []

    workloads = [
        "historical_replay_workload",
        "live_ab_workload",
    ]

    # Use distinct but fixed seeds per workload to ensure determinism.
    base_ticket_seeds = {
        "historical_replay_workload": 42,
        "live_ab_workload": 314,
    }
    base_rng_seeds = {
        "historical_replay_workload": 7,
        "live_ab_workload": 11,
    }

    for wid in workloads:
        t_seed = base_ticket_seeds[wid]
        r_seed = base_rng_seeds[wid]

        baseline_desc = _run_single(
            workload_id=wid,
            variant="baseline",
            tickets_seed=t_seed,
            rng_seed=r_seed,
        )
        treatment_desc = _run_single(
            workload_id=wid,
            variant="treatment",
            tickets_seed=t_seed,
            rng_seed=r_seed + 1,
        )

        for desc in (baseline_desc, treatment_desc):
            runs.append(
                {
                    "variant": desc.variant,
                    "workload_id": desc.workload_id,
                    "run_id": desc.run_id,
                    "success": bool(desc.success),
                    "metrics": {k: float(v) for k, v in desc.metrics.items()},
                }
            )

    notes = (
        "Synthetic offline simulation of customer support workloads. "
        "Metrics include avg_handle_time_minutes and cost_per_ticket for "
        "both baseline (human-only) and treatment (agentic) variants. "
        "Additional agent-specific metrics auto_resolution_rate and "
        "escalation_rate_to_human are reported for treatment runs only. "
        "Metrics that require real customer signals (CSAT, NPS, true first "
        "response time) are intentionally omitted."
    )

    return runs, notes
