from __future__ import annotations

"""Metric computation utilities for the support experiment."""

from dataclasses import dataclass
from typing import Iterable, Dict

from .ticket import SimulationOutcome


@dataclass
class AggregatedMetrics:
    avg_handle_time_minutes: float
    cost_per_ticket: float
    auto_resolution_rate: float | None
    escalation_rate_to_human: float | None


def aggregate_metrics(
    outcomes: Iterable[SimulationOutcome], *, include_agent_specific: bool
) -> AggregatedMetrics:
    total_time = 0.0
    total_cost = 0.0
    auto_count = 0
    human_escalations = 0
    n = 0
    for o in outcomes:
        n += 1
        total_time += o.total_handle_time_minutes
        total_cost += o.human_cost + o.agent_cost
        if include_agent_specific:
            if o.auto_resolved_by_agents:
                auto_count += 1
            if o.escalated_to_human:
                human_escalations += 1

    if n == 0:
        raise ValueError("No outcomes provided for metric aggregation")

    avg_time = total_time / n
    cost_per_ticket = total_cost / n

    if include_agent_specific:
        auto_rate = auto_count / n
        esc_rate = human_escalations / n
    else:
        auto_rate = None
        esc_rate = None

    return AggregatedMetrics(
        avg_handle_time_minutes=avg_time,
        cost_per_ticket=cost_per_ticket,
        auto_resolution_rate=auto_rate,
        escalation_rate_to_human=esc_rate,
    )


def metrics_to_dict(metrics: AggregatedMetrics) -> Dict[str, float]:
    """Convert AggregatedMetrics into a dict of numeric metrics.

    Only include fields that are not None to honor the requirement that
    metrics values must be numbers, not null or other types.
    """

    data: Dict[str, float] = {
        "avg_handle_time_minutes": float(metrics.avg_handle_time_minutes),
        "cost_per_ticket": float(metrics.cost_per_ticket),
    }
    if metrics.auto_resolution_rate is not None:
        data["auto_resolution_rate"] = float(metrics.auto_resolution_rate)
    if metrics.escalation_rate_to_human is not None:
        data["escalation_rate_to_human"] = float(metrics.escalation_rate_to_human)
    return data
