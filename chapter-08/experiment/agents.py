from __future__ import annotations

"""Simulated baseline and agentic workflows.

This module does **not** use real LLMs. Instead, it encodes simplified,
probabilistic behavior to mimic:

- Human-only baseline operation (Tier 1 / Tier 2).
- Agentic treatment with triage, knowledge, resolver, and quality review.

All randomness is driven by a `random.Random` instance injected from the
caller to ensure determinism.
"""

import random

from .config import (
    HUMAN_COST_MODEL,
    AGENTIC_COST_MODEL,
    BASELINE_TIME_MODEL,
    TREATMENT_TIME_MODEL,
)
from .ticket import Ticket, SimulationOutcome


def _uniform(rng: random.Random, low: float, high: float) -> float:
    return low + (high - low) * rng.random()


def simulate_baseline(ticket: Ticket, rng: random.Random) -> SimulationOutcome:
    """Simulate handling of a ticket in the human-only baseline.

    We model a single human agent for low-complexity tickets, with
    probability of escalation to a second agent (Tier 2) for more complex
    tickets.
    """

    cfg = BASELINE_TIME_MODEL

    # Base handle time at L1 depending on complexity.
    if ticket.complexity == "low":
        l1_time = _uniform(rng, cfg.l1_simple_min, cfg.l1_simple_max)
        escalate = False
    elif ticket.complexity == "medium":
        l1_time = _uniform(rng, cfg.l1_complex_min, cfg.l1_complex_max)
        escalate = rng.random() < cfg.escalation_prob_medium
    else:  # high
        l1_time = _uniform(rng, cfg.l1_complex_min, cfg.l1_complex_max)
        escalate = rng.random() < cfg.escalation_prob_complex

    l2_time = 0.0
    if escalate:
        l2_time = _uniform(rng, cfg.l2_additional_min, cfg.l2_additional_max)

    human_time = l1_time + l2_time
    agent_time = 0.0

    human_cost = (human_time / 60.0) * HUMAN_COST_MODEL.hourly_rate
    agent_cost = 0.0

    return SimulationOutcome(
        total_handle_time_minutes=human_time + agent_time,
        human_handle_time_minutes=human_time,
        agent_compute_time_minutes=agent_time,
        human_cost=human_cost,
        agent_cost=agent_cost,
        auto_resolved_by_agents=False,
        escalated_to_human=escalate,
    )


def simulate_treatment(ticket: Ticket, rng: random.Random) -> SimulationOutcome:
    """Simulate handling of a ticket in the multi-agent treatment.

    The flow is:
    - Triage agent always runs.
    - If high risk, force human handling (no auto-resolve; agentic tools
      supply suggestions only).
    - Otherwise, try agent auto-resolution with probability based on
      ticket complexity; if not auto-resolved, humans intervene but with
      reduced time thanks to agent assistance.
    """

    tcfg = TREATMENT_TIME_MODEL

    # Agentic compute time is accumulated regardless of outcome.
    agent_time = (
        tcfg.triage_time
        + tcfg.knowledge_time
        + tcfg.resolver_time
        + tcfg.quality_review_time
    )

    auto_resolved = False
    escalated_to_human = False
    human_time = 0.0

    # High-risk tickets are always escalated to humans.
    if ticket.is_high_risk:
        escalated_to_human = True
        if ticket.complexity == "low":
            human_time = _uniform(rng, tcfg.human_simple_min, tcfg.human_simple_max)
        elif ticket.complexity == "medium":
            human_time = _uniform(rng, tcfg.human_complex_min, tcfg.human_complex_max)
        else:
            # High-complexity high-risk tickets take longer even with agentic help.
            human_time = _uniform(rng, tcfg.human_complex_min + 2.0, tcfg.human_complex_max + 4.0)
    else:
        # Non-high-risk tickets: possible auto-resolution.
        if ticket.complexity == "low":
            auto_prob = tcfg.auto_resolution_prob_low_complexity
        elif ticket.complexity == "medium":
            auto_prob = tcfg.auto_resolution_prob_medium_complexity
        else:
            auto_prob = tcfg.auto_resolution_prob_complex

        if rng.random() < auto_prob:
            auto_resolved = True
            # No human time.
            human_time = 0.0
        else:
            # Agents failed to fully resolve; human now steps in.
            escalated_to_human = True
            if ticket.complexity == "low":
                human_time = _uniform(rng, tcfg.human_simple_min, tcfg.human_simple_max)
            elif ticket.complexity == "medium":
                human_time = _uniform(rng, tcfg.human_complex_min, tcfg.human_complex_max)
            else:
                human_time = _uniform(rng, tcfg.human_complex_min + 1.0, tcfg.human_complex_max + 2.0)

            # Additional chance that even after agents, complex tickets need more human effort.
            if ticket.complexity in ("medium", "high"):
                if ticket.complexity == "medium":
                    if rng.random() < tcfg.escalation_after_agent_prob_medium:
                        human_time *= 1.3
                else:
                    if rng.random() < tcfg.escalation_after_agent_prob_complex:
                        human_time *= 1.5

    # Compute costs.
    human_cost = (human_time / 60.0) * HUMAN_COST_MODEL.hourly_rate
    # Flat agent cost per ticket regardless of auto-resolution or escalation.
    agent_cost = AGENTIC_COST_MODEL.cost_per_ticket

    total_time = human_time + agent_time

    return SimulationOutcome(
        total_handle_time_minutes=total_time,
        human_handle_time_minutes=human_time,
        agent_compute_time_minutes=agent_time,
        human_cost=human_cost,
        agent_cost=agent_cost,
        auto_resolved_by_agents=auto_resolved,
        escalated_to_human=escalated_to_human,
    )
