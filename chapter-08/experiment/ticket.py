from __future__ import annotations

"""Data structures representing support tickets and outcomes."""

from dataclasses import dataclass
from typing import Literal


Channel = Literal["email", "web", "chat"]
Complexity = Literal["low", "medium", "high"]
Category = Literal["login", "billing", "howto", "bug", "integration"]


@dataclass(frozen=True)
class Ticket:
    ticket_id: str
    channel: Channel
    category: Category
    complexity: Complexity
    # Indicates potentially sensitive / high-risk tickets (e.g., billing disputes).
    is_high_risk: bool


@dataclass
class SimulationOutcome:
    """Result of processing a ticket under a specific workflow.

    All time units are minutes.
    """

    total_handle_time_minutes: float
    human_handle_time_minutes: float
    agent_compute_time_minutes: float
    human_cost: float
    agent_cost: float
    auto_resolved_by_agents: bool
    escalated_to_human: bool
