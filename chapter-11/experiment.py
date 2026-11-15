from __future__ import annotations

from typing import List, Dict

from simulation import simulate_run, RunSummary


WORKLOADS = [
    "wl-hr-onboarding",
    "wl-hr-changes-faq",
    "wl-it-access-requests",
    "wl-it-break-fix-faq",
]


def run_experiment() -> List[Dict]:
    """Run baseline and treatment simulations for all workloads.

    Returns a list of run dictionaries ready to be written in results.json.
    Each workload gets at least one baseline and one treatment run.
    """

    runs: List[Dict] = []

    # Fixed base seed so results are deterministic but non-trivial
    base_seed = 42

    for w_index, workload_id in enumerate(WORKLOADS):
        # We create exactly one baseline and one treatment run per workload.
        for variant_index, variant in enumerate(["baseline", "treatment"]):
            run_id = f"{workload_id}-{variant}-0"
            # Derive seed deterministically from workload and variant index
            seed = base_seed + w_index * 10 + variant_index
            # Use a small but non-trivial number of tickets for speed
            n_tickets = 20

            summary: RunSummary = simulate_run(
                workload_id=workload_id,
                variant=variant,
                run_id=run_id,
                n_tickets=n_tickets,
                seed=seed,
            )

            run_dict: Dict = {
                "variant": summary.variant,
                "workload_id": summary.workload_id,
                "run_id": summary.run_id,
                "success": summary.success,
                "metrics": summary.metrics,
            }

            runs.append(run_dict)

    return runs
