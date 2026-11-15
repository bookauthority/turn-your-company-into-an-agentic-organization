from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Protocol

from .agents import (
    ResolverAgentBaseline,
    ResolverAgentTuned,
    ReviewerAgent,
    RouterAgent,
)
from .workload import Ticket


@dataclass
class RunRecord:
    variant: str  # "baseline" or "treatment"
    workload_id: str
    run_id: str
    success: bool
    metrics: Dict[str, float]


class ResolverProtocol(Protocol):  # pragma: no cover - structural typing helper
    def resolve(self, ticket: Ticket, routing):  # type: ignore[override]
        ...


def _process_ticket(
    ticket: Ticket,
    variant: str,
    router: RouterAgent,
    resolver: ResolverProtocol,
    reviewer: ReviewerAgent,
    workload_id: str,
) -> RunRecord:
    run_id = f"{variant}_{ticket.ticket_id}"
    t_start = time.perf_counter()

    # Step 1: Router
    routing = router.route(ticket)

    # Step 2: Resolver
    resolution = resolver.resolve(ticket, routing)

    # Step 3: Reviewer
    review = reviewer.review(ticket, routing, resolution)

    t_end = time.perf_counter()
    latency_ms = (t_end - t_start) * 1000.0

    success = review.approved
    metrics: Dict[str, float] = {
        "latency_ms": float(latency_ms),
        "steps": 3.0,
    }

    return RunRecord(
        variant=variant,
        workload_id=workload_id,
        run_id=run_id,
        success=success,
        metrics=metrics,
    )


def run_baseline(tickets: List[Ticket], workload_id: str) -> List[RunRecord]:
    router = RouterAgent()
    resolver = ResolverAgentBaseline()
    reviewer = ReviewerAgent()
    runs: List[RunRecord] = []
    for ticket in tickets:
        record = _process_ticket(
            ticket=ticket,
            variant="baseline",
            router=router,
            resolver=resolver,
            reviewer=reviewer,
            workload_id=workload_id,
        )
        runs.append(record)
    return runs


def run_treatment(tickets: List[Ticket], workload_id: str) -> List[RunRecord]:
    router = RouterAgent()
    resolver = ResolverAgentTuned()
    reviewer = ReviewerAgent()
    runs: List[RunRecord] = []

    for ticket in tickets:
        record = _process_ticket(
            ticket=ticket,
            variant="treatment",
            router=router,
            resolver=resolver,
            reviewer=reviewer,
            workload_id=workload_id,
        )
        runs.append(record)

    # Treatment-only: higher-level SLIs/SLO-style checks are computed by
    # experiment.monitoring from these runs. We don't mutate per-run metrics.
    return runs
