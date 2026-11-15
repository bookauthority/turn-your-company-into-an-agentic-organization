from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Dict

# --- Core domain models ----------------------------------------------------


@dataclass
class Ticket:
    ticket_id: str
    workload_id: str
    priority: str  # low | normal | high | urgent
    created_at: datetime


@dataclass
class TicketOutcome:
    ticket: Ticket
    first_response_at: datetime
    resolved_at: datetime
    human_handling_time_minutes: float


@dataclass
class RunSummary:
    variant: str  # baseline | treatment
    workload_id: str
    run_id: str
    success: bool
    metrics: Dict[str, float]


# --- Simulation helpers ----------------------------------------------------


def _priority_multiplier(priority: str) -> float:
    """Return a multiplier for response and resolution times by priority.

    Lower than 1 means faster handling for higher priority.
    """

    mapping = {
        "urgent": 0.5,
        "high": 0.75,
        "normal": 1.0,
        "low": 1.25,
    }
    return mapping.get(priority, 1.0)


def generate_tickets(workload_id: str, n: int, seed: int) -> List[Ticket]:
    """Generate synthetic tickets for a workload.

    Tickets are distributed within a small time window starting from now.
    Randomness is seeded for reproducibility.
    """

    rng = random.Random(seed)
    base_time = datetime.now(timezone.utc).replace(microsecond=0)
    tickets: List[Ticket] = []

    priorities = ["low", "normal", "high", "urgent"]
    priority_weights = [0.1, 0.6, 0.25, 0.05]

    for i in range(n):
        priority = rng.choices(priorities, weights=priority_weights, k=1)[0]
        # Spread creation times over 8 hours
        offset_minutes = rng.uniform(0, 8 * 60)
        created_at = base_time + timedelta(minutes=offset_minutes)
        ticket_id = f"{workload_id}-{i}"
        tickets.append(Ticket(ticket_id=ticket_id, workload_id=workload_id, priority=priority, created_at=created_at))

    # Sort by created_at to simulate arrival order
    tickets.sort(key=lambda t: t.created_at)
    return tickets


# --- Processing models -----------------------------------------------------


def _simulate_ticket_baseline(ticket: Ticket, rng: random.Random) -> TicketOutcome:
    """Simulate baseline (human-only) handling of a ticket.

    Model:
    - First response time: base between 15 and 90 minutes, scaled by priority.
    - Resolution time: base between 1 and 8 hours after first response.
    - Human handling time: proportional to total duration but capped.
    """

    p_mult = _priority_multiplier(ticket.priority)

    # First response delay in minutes
    fr_delay = rng.uniform(15, 90) * p_mult
    first_response_at = ticket.created_at + timedelta(minutes=fr_delay)

    # Resolution delay after first response in minutes
    res_delay = rng.uniform(60, 8 * 60) * p_mult
    resolved_at = first_response_at + timedelta(minutes=res_delay)

    total_minutes = (resolved_at - ticket.created_at).total_seconds() / 60.0
    # Assume humans spend between 15% and 35% of end-to-end time actively
    human_fraction = rng.uniform(0.15, 0.35)
    human_minutes = total_minutes * human_fraction

    return TicketOutcome(
        ticket=ticket,
        first_response_at=first_response_at,
        resolved_at=resolved_at,
        human_handling_time_minutes=human_minutes,
    )


def _simulate_ticket_treatment(ticket: Ticket, rng: random.Random) -> TicketOutcome:
    """Simulate treatment (agent-assisted) handling of a ticket.

    We assume improvements while keeping randomness for realistic variation.

    Model (per workload type via multipliers):
    - HR workloads: strong gains in prep and triage, moderate in resolution.
    - IT workloads: larger gains in resolution for FAQs/break-fix.

    Implementation simplifies by using the same formula and adjusting
    coefficients by workload prefix.
    """

    p_mult = _priority_multiplier(ticket.priority)

    wl = ticket.workload_id
    if wl == "wl-hr-onboarding":
        fr_factor, res_factor, human_factor = 0.4, 0.7, 0.7
    elif wl == "wl-hr-changes-faq":
        fr_factor, res_factor, human_factor = 0.45, 0.7, 0.65
    elif wl == "wl-it-access-requests":
        fr_factor, res_factor, human_factor = 0.5, 0.65, 0.6
    elif wl == "wl-it-break-fix-faq":
        fr_factor, res_factor, human_factor = 0.35, 0.6, 0.55
    else:
        fr_factor, res_factor, human_factor = 0.5, 0.7, 0.7

    # First response
    base_fr = rng.uniform(10, 60) * p_mult
    fr_delay = base_fr * fr_factor
    first_response_at = ticket.created_at + timedelta(minutes=fr_delay)

    # Resolution after first response
    base_res = rng.uniform(30, 6 * 60) * p_mult
    res_delay = base_res * res_factor
    resolved_at = first_response_at + timedelta(minutes=res_delay)

    total_minutes = (resolved_at - ticket.created_at).total_seconds() / 60.0
    # Reduced human fraction due to automation and better suggestions
    human_fraction = rng.uniform(0.08, 0.22) * human_factor
    human_minutes = total_minutes * human_fraction

    return TicketOutcome(
        ticket=ticket,
        first_response_at=first_response_at,
        resolved_at=resolved_at,
        human_handling_time_minutes=human_minutes,
    )


def simulate_run(workload_id: str, variant: str, run_id: str, n_tickets: int, seed: int) -> RunSummary:
    """Simulate a single run for a workload and variant.

    Returns aggregated metrics across all tickets in the run.
    """

    rng = random.Random(seed)
    tickets = generate_tickets(workload_id, n_tickets, seed=seed + 1000)

    outcomes: List[TicketOutcome] = []
    for ticket in tickets:
        if variant == "baseline":
            outcome = _simulate_ticket_baseline(ticket, rng)
        elif variant == "treatment":
            outcome = _simulate_ticket_treatment(ticket, rng)
        else:
            raise ValueError(f"Unknown variant: {variant}")
        outcomes.append(outcome)

    # Aggregate metrics (means across tickets)
    if not outcomes:
        success = False
        metrics: Dict[str, float] = {}
    else:
        fr_minutes = [
            (o.first_response_at - o.ticket.created_at).total_seconds() / 60.0
            for o in outcomes
        ]
        res_minutes = [
            (o.resolved_at - o.ticket.created_at).total_seconds() / 60.0
            for o in outcomes
        ]
        human_minutes = [o.human_handling_time_minutes for o in outcomes]

        def mean(values: List[float]) -> float:
            return float(sum(values) / len(values)) if values else math.nan

        metrics = {
            "time_to_first_response_minutes": mean(fr_minutes),
            "time_to_resolution_minutes": mean(res_minutes),
            "human_handling_time_minutes": mean(human_minutes),
        }
        success = True

    return RunSummary(
        variant=variant,
        workload_id=workload_id,
        run_id=run_id,
        success=success,
        metrics=metrics,
    )
