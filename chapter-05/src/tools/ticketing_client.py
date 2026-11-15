from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Ticket:
    ticket_id: str
    created_at: str
    customer_email: str
    subject: str
    body: str
    category: str


class TicketingClient:
    """Stubbed ticketing API Client.

    In a real system, this would wrap HTTP requests to a helpdesk platform
    like Zendesk or Freshdesk. Here we just read from an in-memory dict
    populated from the synthetic CSV.
    """

    def __init__(self, tickets: Dict[str, Ticket]):
        self._tickets = tickets

    def get_ticket(self, ticket_id: str) -> Ticket:
        return self._tickets[ticket_id]

    def get_ticket_metadata(self, ticket_id: str) -> Dict[str, Any]:
        t = self.get_ticket(ticket_id)
        return {
            "ticket_id": t.ticket_id,
            "created_at": t.created_at,
            "subject": t.subject,
            "category": t.category,
        }

    def add_internal_note(self, ticket_id: str, note: str) -> None:
        # No-op for simulation; in production this would persist the note.
        _ = (ticket_id, note)

    def update_ticket_tags(self, ticket_id: str, tags: Dict[str, str]) -> None:
        # No-op for simulation.
        _ = (ticket_id, tags)
