from __future__ import annotations

from dataclasses import dataclass

from .workload import Ticket, expected_resolution


@dataclass
class RouterOutput:
    category: str
    priority: str


@dataclass
class ResolverOutput:
    action: str
    details: str


@dataclass
class ReviewerOutput:
    approved: bool
    notes: str


class RouterAgent:
    """Very simple router that echoes the ticket's category and infers priority."""

    def route(self, ticket: Ticket) -> RouterOutput:
        if ticket.difficulty == "hard":
            priority = "high"
        elif ticket.difficulty == "medium":
            priority = "medium"
        else:
            priority = "low"
        return RouterOutput(category=ticket.category, priority=priority)


class ResolverAgentBaseline:
    """Baseline resolver: decent on easy/medium, weaker on hard tickets.

    On hard tickets it sometimes produces a generic action that does not
    precisely match the expected_resolution, simulating lower success rate.
    """

    def resolve(self, ticket: Ticket, routing: RouterOutput) -> ResolverOutput:
        expected = expected_resolution(routing.category)
        if ticket.difficulty in ("easy", "medium"):
            action = expected
        else:
            # hard: sometimes generic and thus 'incorrect'
            if routing.category in ("password_reset", "access_request"):
                action = "Follow standard procedure"
            else:
                action = expected
        details = f"Resolved {routing.category} with difficulty {ticket.difficulty}."
        return ResolverOutput(action=action, details=details)


class ResolverAgentTuned:
    """Tuned resolver: improved handling of hard tickets.

    Always returns the expected action regardless of difficulty, modeling
    a treatment that improves quality while keeping behavior similar.
    """

    def resolve(self, ticket: Ticket, routing: RouterOutput) -> ResolverOutput:
        expected = expected_resolution(routing.category)
        action = expected
        details = (
            f"Tuned resolver handled {routing.category} ({ticket.difficulty}) with "
            f"clear instructions."
        )
        return ResolverOutput(action=action, details=details)


class ReviewerAgent:
    """Reviewer that approves if the action matches expected_resolution.

    In real systems this could be a human or another agent. Here it's
    deterministic and acts as our synthetic feedback / offline evaluator.
    """

    def review(self, ticket: Ticket, routing: RouterOutput, resolution: ResolverOutput) -> ReviewerOutput:
        expected = expected_resolution(routing.category)
        approved = resolution.action == expected
        notes = "ok" if approved else "mismatch_with_expected_resolution"
        return ReviewerOutput(approved=approved, notes=notes)
