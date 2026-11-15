from __future__ import annotations

from typing import List, Dict

from .tools.ticketing_client import Ticket


def assign_lane(ticket_id: str) -> str:
    """Deterministic per-ticket lane assignment based on ticket_id hash.

    Returns "manual_baseline" or "agentic_treatment".
    """

    # Simple deterministic splitter: sum of character ordinals modulo 2
    s = sum(ord(c) for c in ticket_id)
    if s % 2 == 0:
        return "manual_baseline"
    return "agentic_treatment"


def filter_workload_tickets(tickets: Dict[str, Ticket]) -> List[Ticket]:
    """Return tickets that satisfy inclusion criteria for the workload.

    For this synthetic example, we include tickets whose category is either
    'billing-simple' or 'account-info'.
    """

    result: List[Ticket] = []
    for t in tickets.values():
        if t.category in ("billing-simple", "account-info"):
            result.append(t)
    return result
