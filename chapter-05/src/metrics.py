from __future__ import annotations

from typing import List, Dict, Any

from .logging_utils import TicketRecord, AgentInteractionRecord
from .tools.ticketing_client import Ticket


def _parse_iso(ts: str) -> float:
    """Parse a minimal RFC3339/ISO 8601 timestamp with 'Z' suffix to seconds.

    We avoid external libraries for compatibility.
    """

    # Expected format: YYYY-MM-DDTHH:MM:SSZ
    date, time = ts.split("T")
    year_s, month_s, day_s = date.split("-")
    time_s = time.rstrip("Z")
    hour_s, minute_s, second_s = time_s.split(":")
    year = int(year_s)
    month = int(month_s)
    day = int(day_s)
    hour = int(hour_s)
    minute = int(minute_s)
    second = int(second_s)

    # Simplified conversion: assume 30-day months and 365-day year offset is irrelevant
    # because we only care about differences within the dataset.
    days = (year * 365) + (month * 30) + day
    return float(days * 24 * 3600 + hour * 3600 + minute * 60 + second)


def compute_ticket_level_metrics(
    tickets: List[TicketRecord],
    agent_interactions: List[AgentInteractionRecord],
    human_hourly_rate: float,
    model_cost_per_1k_tokens: float,
    ticket_lookup: Dict[str, Ticket],
) -> Dict[str, Dict[str, Any]]:
    """Compute per-ticket derived quantities used later by aggregators.

    Returns mapping ticket_id -> metrics dict.
    """

    interactions_by_ticket: Dict[str, AgentInteractionRecord] = {
        i.ticket_id: i for i in agent_interactions
    }

    per_ticket: Dict[str, Dict[str, Any]] = {}

    for t in tickets:
        created = _parse_iso(t.created_at)
        first_resp = _parse_iso(t.first_response_at)
        handling_time = first_resp - created

        ticket_obj = ticket_lookup[t.ticket_id]
        n_chars = len(ticket_obj.body)

        if t.lane == "manual_baseline":
            # Simulate manual handling time and labor: per-character cost
            # We assume that handling_time_first_response already approximates
            # the active labor time for this sandbox, so we set labor_time = handling_time.
            labor_time = handling_time
            model_cost = 0.0
            agent_draft_latency = None
        else:
            inter = interactions_by_ticket.get(t.ticket_id)
            if inter is None:
                # Should not happen in this simulation
                labor_time = handling_time
                agent_draft_latency = None
                model_cost = 0.0
            else:
                req_ts = _parse_iso(inter.agent_request_at)
                resp_ts = _parse_iso(inter.agent_response_at)
                agent_draft_latency = resp_ts - req_ts

                # Active human time is assumed shorter than wall-clock handling
                # because the agent does the drafting work. We approximate this
                # as 40% of manual reading/writing time for sandbox purposes.
                manual_like_time = handling_time
                labor_time = manual_like_time * 0.4

                # Estimate tokens and cost from response length
                response_draft = inter.agent_output.get("response_draft", "")
                est_tokens = max(1, len(response_draft) // 4)
                model_cost = (est_tokens / 1000.0) * model_cost_per_1k_tokens

        labor_cost = (labor_time / 3600.0) * human_hourly_rate
        total_variable_cost = labor_cost + model_cost

        per_ticket[t.ticket_id] = {
            "handling_time_first_response": handling_time,
            "labor_time_per_ticket": labor_time,
            "labor_cost_per_ticket": labor_cost,
            "model_cost_per_ticket": model_cost,
            "total_variable_cost_per_ticket": total_variable_cost,
        }
        if t.lane == "agentic_treatment" and agent_draft_latency is not None:
            per_ticket[t.ticket_id]["agent_draft_latency"] = agent_draft_latency

    return per_ticket


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _median(values: List[float]) -> float:
    n = len(values)
    if n == 0:
        return 0.0
    s = sorted(values)
    mid = n // 2
    if n % 2 == 1:
        return float(s[mid])
    return float((s[mid - 1] + s[mid]) / 2.0)


def aggregate_run_metrics(
    tickets: List[TicketRecord],
    per_ticket_metrics: Dict[str, Dict[str, Any]],
) -> Dict[str, float]:
    """Aggregate ticket-level metrics into run-level metrics.

    Only numeric metrics are returned.
    """

    handling_times: List[float] = []
    labor_costs: List[float] = []
    model_costs: List[float] = []
    total_costs: List[float] = []
    draft_latencies: List[float] = []

    for t in tickets:
        m = per_ticket_metrics[t.ticket_id]
        handling_times.append(float(m["handling_time_first_response"]))
        labor_costs.append(float(m["labor_cost_per_ticket"]))
        model_costs.append(float(m["model_cost_per_ticket"]))
        total_costs.append(float(m["total_variable_cost_per_ticket"]))
        if "agent_draft_latency" in m:
            draft_latencies.append(float(m["agent_draft_latency"]))

    metrics: Dict[str, float] = {}
    metrics["handling_time_first_response_median"] = _median(handling_times)
    metrics["labor_cost_per_ticket_mean"] = _mean(labor_costs)
    metrics["model_cost_per_ticket_mean"] = _mean(model_costs)
    metrics["total_variable_cost_per_ticket_mean"] = _mean(total_costs)
    if draft_latencies:
        metrics["agent_draft_latency_mean"] = _mean(draft_latencies)

    return metrics
