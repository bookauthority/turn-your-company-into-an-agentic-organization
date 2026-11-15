from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Tuple

from .tools.ticketing_client import Ticket, TicketingClient
from .tools.crm_client import CrmBillingClient, CustomerRecord
from .tools.kb_client import KnowledgeBaseClient
from .agent import DraftingAgent, AgentConfig
from .hitl_ui_stub import simulate_review, HitlConfig
from .logging_utils import TicketRecord, AgentInteractionRecord
from .routing import assign_lane, filter_workload_tickets


@dataclass
class SimulationConfig:
    human_hourly_rate: float
    model_cost_per_1k_tokens: float
    approve_confidence_threshold: float
    edit_minor_threshold_ratio: float


@dataclass
class SimulationResult:
    tickets: List[TicketRecord]
    interactions: List[AgentInteractionRecord]


def _simulate_manual_first_response_time(ticket: Ticket) -> float:
    """Deterministic approximation of handling time (seconds) for manual lane.

    We use a simple linear function of ticket body length to avoid relying
    on wall-clock measurements.
    """

    base = 60.0  # base reading/thinking time
    per_char = 0.3  # extra time per character
    return base + per_char * len(ticket.body)


def _simulate_agent_first_response_time(ticket: Ticket) -> Tuple[float, float]:
    """Return (agent_draft_latency, total_handling_time) in seconds.

    The agent's draft latency is much smaller than total handling time, and
    total time is reduced vs. manual by design.
    """

    manual_time = _simulate_manual_first_response_time(ticket)
    agent_draft_latency = 10.0 + 0.05 * len(ticket.body)
    total = manual_time * 0.7  # assume 30% reduction in wall-clock time
    return agent_draft_latency, total


def _offset_iso(ts: str, delta_seconds: float) -> str:
    """Offset a minimal ISO timestamp string by a number of seconds.

    For simplicity we don't handle month/year wrap; we only care about
    relative ordering, and deltas are small.
    """

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

    total_seconds = hour * 3600 + minute * 60 + second + int(delta_seconds)
    if total_seconds < 0:
        total_seconds = 0
    new_hour = (total_seconds // 3600) % 24
    new_minute = (total_seconds % 3600) // 60
    new_second = total_seconds % 60
    return f"{year:04d}-{month:02d}-{day:02d}T{new_hour:02d}:{new_minute:02d}:{new_second:02d}Z"


def run_simulation() -> SimulationResult:
    """Run the synthetic experiment for both baseline and treatment lanes.

    This constructs the stub tools, runs each ticket through its assigned
    lane, and returns ticket- and interaction-level logs.
    """

    # Synthetic tickets roughly mirror data/synthetic_tickets.csv
    tickets: Dict[str, Ticket] = {}
    raw_rows = [
        ("T001", "2024-01-01T09:00:00Z", "alice@example.com", "Invoice copy", "Hi, can you send me a copy of my last invoice?", "billing-simple"),
        ("T002", "2024-01-01T09:05:00Z", "bob@example.com", "Plan status", "Hello, what plan am I on and when does it renew?", "billing-simple"),
        ("T003", "2024-01-01T09:10:00Z", "charlie@example.com", "Billing address change", "I need to update the billing address on my account.", "billing-simple"),
        ("T004", "2024-01-01T09:15:00Z", "dan@example.com", "Payment received", "Was my last payment received? I want to make sure my account is active.", "billing-simple"),
        ("T005", "2024-01-01T09:20:00Z", "erin@example.com", "Account status", "Is my subscription currently active and paid up?", "account-info"),
        ("T006", "2024-01-01T09:25:00Z", "frank@example.com", "Next invoice", "When will my next invoice be generated?", "billing-simple"),
        ("T007", "2024-01-01T09:30:00Z", "grace@example.com", "Plan change info", "Can you tell me the difference between the basic and pro plans?", "billing-simple"),
        ("T008", "2024-01-01T09:35:00Z", "henry@example.com", "Address info", "What address do you currently have on file for my billing?", "billing-simple"),
        ("T009", "2024-01-01T09:40:00Z", "irene@example.com", "Invoice history", "Could I get invoices for the last three months?", "billing-simple"),
        ("T010", "2024-01-01T09:45:00Z", "jack@example.com", "Next renewal", "When does my current subscription period end?", "account-info"),
    ]
    for tid, created, email, subject, body, category in raw_rows:
        tickets[tid] = Ticket(
            ticket_id=tid,
            created_at=created,
            customer_email=email,
            subject=subject,
            body=body,
            category=category,
        )

    # Synthetic CRM records
    crm_records: Dict[str, CustomerRecord] = {
        "alice@example.com": CustomerRecord(
            email="alice@example.com",
            name="Alice",
            plan="Pro",
            active=True,
            next_renewal_date="2024-02-01",
            last_invoice_id="INV-1001",
            last_payment_received=True,
            billing_address="123 Main St, Springfield",
        ),
        "bob@example.com": CustomerRecord(
            email="bob@example.com",
            name="Bob",
            plan="Basic",
            active=True,
            next_renewal_date="2024-03-10",
            last_invoice_id="INV-1002",
            last_payment_received=True,
            billing_address="456 Oak Ave, Metropolis",
        ),
        "charlie@example.com": CustomerRecord(
            email="charlie@example.com",
            name="Charlie",
            plan="Pro",
            active=True,
            next_renewal_date="2024-01-20",
            last_invoice_id="INV-1003",
            last_payment_received=True,
            billing_address="789 Pine Rd, Smallville",
        ),
        "dan@example.com": CustomerRecord(
            email="dan@example.com",
            name="Dan",
            plan="Basic",
            active=True,
            next_renewal_date="2024-04-05",
            last_invoice_id="INV-1004",
            last_payment_received=True,
            billing_address="321 Cedar St, Gotham",
        ),
        "erin@example.com": CustomerRecord(
            email="erin@example.com",
            name="Erin",
            plan="Pro",
            active=True,
            next_renewal_date="2024-02-15",
            last_invoice_id="INV-1005",
            last_payment_received=True,
            billing_address="654 Birch Blvd, Star City",
        ),
        "frank@example.com": CustomerRecord(
            email="frank@example.com",
            name="Frank",
            plan="Basic",
            active=True,
            next_renewal_date="2024-03-01",
            last_invoice_id="INV-1006",
            last_payment_received=True,
            billing_address="987 Elm St, Central City",
        ),
        "grace@example.com": CustomerRecord(
            email="grace@example.com",
            name="Grace",
            plan="Pro",
            active=True,
            next_renewal_date="2024-02-28",
            last_invoice_id="INV-1007",
            last_payment_received=True,
            billing_address="111 Maple Ln, Coast City",
        ),
        "henry@example.com": CustomerRecord(
            email="henry@example.com",
            name="Henry",
            plan="Basic",
            active=True,
            next_renewal_date="2024-03-15",
            last_invoice_id="INV-1008",
            last_payment_received=True,
            billing_address="222 Walnut Dr, Keystone",
        ),
        "irene@example.com": CustomerRecord(
            email="irene@example.com",
            name="Irene",
            plan="Pro",
            active=True,
            next_renewal_date="2024-02-10",
            last_invoice_id="INV-1009",
            last_payment_received=True,
            billing_address="333 Cherry St, Bludhaven",
        ),
        "jack@example.com": CustomerRecord(
            email="jack@example.com",
            name="Jack",
            plan="Basic",
            active=True,
            next_renewal_date="2024-04-01",
            last_invoice_id="INV-1010",
            last_payment_received=True,
            billing_address="444 Ash Ave, National City",
        ),
    }

    ticketing_client = TicketingClient(tickets)
    crm_client = CrmBillingClient(crm_records)
    kb_client = KnowledgeBaseClient()

    cfg = SimulationConfig(
        human_hourly_rate=30.0,
        model_cost_per_1k_tokens=0.002,
        approve_confidence_threshold=0.7,
        edit_minor_threshold_ratio=0.2,
    )
    agent_cfg = AgentConfig(
        human_hourly_rate=cfg.human_hourly_rate,
        model_cost_per_1k_tokens=cfg.model_cost_per_1k_tokens,
        edit_minor_threshold_ratio=cfg.edit_minor_threshold_ratio,
        approve_confidence_threshold=cfg.approve_confidence_threshold,
    )

    agent = DraftingAgent(ticketing_client, crm_client, kb_client, agent_cfg)
    hitl_cfg = HitlConfig(
        edit_minor_threshold_ratio=cfg.edit_minor_threshold_ratio,
        approve_confidence_threshold=cfg.approve_confidence_threshold,
    )

    workload_tickets = filter_workload_tickets(tickets)

    ticket_logs: List[TicketRecord] = []
    interaction_logs: List[AgentInteractionRecord] = []

    # Deterministic 'agent id' assignments
    manual_agent_id = "human_manual_1"
    treatment_agent_id = "human_hitl_1"

    for t in workload_tickets:
        lane = assign_lane(t.ticket_id)
        if lane == "manual_baseline":
            handling_seconds = _simulate_manual_first_response_time(t)
            first_response_at = _offset_iso(t.created_at, handling_seconds)

            ticket_logs.append(
                TicketRecord(
                    ticket_id=t.ticket_id,
                    lane=lane,
                    created_at=t.created_at,
                    first_response_at=first_response_at,
                    agent_id=manual_agent_id,
                    category=t.category,
                    sub_category="",
                    resolution_code="resolved_first_touch",
                    csat_score=None,
                )
            )
        else:
            # Treatment lane: run agent and HITL
            draft_latency, total_handling = _simulate_agent_first_response_time(t)
            agent_request_at = _offset_iso(t.created_at, 5.0)  # 5s after ticket creation
            agent_response_at = _offset_iso(agent_request_at, draft_latency)
            first_response_at = _offset_iso(t.created_at, total_handling)

            output = agent.draft_for_ticket(t.ticket_id)
            review_mode, final_response, confidence, edit_dist, edit_ratio = simulate_review(
                t.body, output, hitl_cfg
            )

            ticket_logs.append(
                TicketRecord(
                    ticket_id=t.ticket_id,
                    lane=lane,
                    created_at=t.created_at,
                    first_response_at=first_response_at,
                    agent_id=treatment_agent_id,
                    category=t.category,
                    sub_category=output["classification"]["sub_category"],
                    resolution_code="resolved_first_touch",
                    csat_score=None,
                )
            )

            interaction_logs.append(
                AgentInteractionRecord(
                    ticket_id=t.ticket_id,
                    agent_request_at=agent_request_at,
                    agent_response_at=agent_response_at,
                    model_version="synthetic-llm-sim-v1",
                    prompt_version="v1",
                    agent_output=output,
                    review_mode=review_mode,
                    edit_distance_characters=float(edit_dist),
                    edit_distance_ratio=float(edit_ratio),
                    human_comments=None,
                )
            )

    return SimulationResult(tickets=ticket_logs, interactions=interaction_logs)
