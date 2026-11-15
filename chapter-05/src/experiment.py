from __future__ import annotations

import platform
from typing import Dict, Any, List

from .simulation import run_simulation
from .logging_utils import ticket_record_to_dict, agent_interaction_to_dict, config_record_to_dict, ConfigRecord
from .metrics import compute_ticket_level_metrics, aggregate_run_metrics
from .tools.ticketing_client import Ticket
from .simulation import Ticket as SimTicket  # reuse definition


EXPERIMENT_ID = "ch05-prod-agent-001-manual-vs-agentic"
WORKLOAD_ID = "low_complexity_billing_account_inquiries"
CHAPTER_NUMBER = 5


def run_experiment() -> Dict[str, Any]:
    """Execute the synthetic experiment and return evidence dict.

    The returned dict is later serialized to JSON by run.py.
    """

    sim_result = run_simulation()

    # Recreate ticket lookup used for metrics based on simulation's synthetic tickets.
    # We build Ticket objects with body and created_at from the simulation.
    ticket_lookup: Dict[str, Ticket] = {}
    # We cannot import the original synthetic dataset directly, but we know
    # simulation tickets correspond to SimTicket records; rebuild mapping.
    # NOTE: This requires a small reconstruction; to keep it simple we embed
    # the synthetic definitions again.
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
        ticket_lookup[tid] = Ticket(
            ticket_id=tid,
            created_at=created,
            customer_email=email,
            subject=subject,
            body=body,
            category=category,
        )

    # Partition logs by lane
    baseline_tickets = [t for t in sim_result.tickets if t.lane == "manual_baseline"]
    treatment_tickets = [t for t in sim_result.tickets if t.lane == "agentic_treatment"]

    # All interactions are for treatment lane
    treatment_interactions = sim_result.interactions

    # Global config record (simplified timing as placeholders; not used in metrics)
    config_record = ConfigRecord(
        experiment_id=EXPERIMENT_ID,
        start_at="2024-01-01T09:00:00Z",
        end_at="2024-01-01T10:00:00Z",
        model_name="synthetic-llm-sim-v1",
        model_params={"temperature": 0.1, "max_tokens": 512},
        tools_enabled=["ticketing_api", "crm_billing_api", "kb_search_api"],
        routing_rule_version="v1-hash-mod2",
        notes="Synthetic offline simulation; no real PII or external systems.",
    )

    # Compute per-ticket metrics, separately for baseline and treatment
    human_hourly_rate = 30.0
    model_cost_per_1k_tokens = 0.002

    from .metrics import compute_ticket_level_metrics as compute_tm
    baseline_per_ticket = compute_tm(
        baseline_tickets,
        [],
        human_hourly_rate,
        model_cost_per_1k_tokens,
        ticket_lookup,
    )
    treatment_per_ticket = compute_tm(
        treatment_tickets,
        treatment_interactions,
        human_hourly_rate,
        model_cost_per_1k_tokens,
        ticket_lookup,
    )

    from .metrics import aggregate_run_metrics

    baseline_run_metrics = aggregate_run_metrics(baseline_tickets, baseline_per_ticket)
    treatment_run_metrics = aggregate_run_metrics(treatment_tickets, treatment_per_ticket)

    # Build runs array according to evidence schema
    baseline_run = {
        "variant": "baseline",
        "workload_id": WORKLOAD_ID,
        "run_id": "baseline-001",
        "success": True,
        "metrics": baseline_run_metrics,
        # Optional extra fields
        "ticket_count": len(baseline_tickets),
    }

    treatment_run = {
        "variant": "treatment",
        "workload_id": WORKLOAD_ID,
        "run_id": "treatment-001",
        "success": True,
        "metrics": treatment_run_metrics,
        "ticket_count": len(treatment_tickets),
    }

    evidence: Dict[str, Any] = {
        "chapter": CHAPTER_NUMBER,
        "experiment_id": EXPERIMENT_ID,
        "environment": {
            "os": platform.system(),
            "python": platform.python_version(),
        },
        "runs": [baseline_run, treatment_run],
        "config_record": config_record_to_dict(config_record),
        "ticket_logs": [ticket_record_to_dict(t) for t in sim_result.tickets],
        "agent_interactions": [agent_interaction_to_dict(i) for i in treatment_interactions],
        "notes": (
            "Synthetic offline simulation of manual vs. agentic support workflow. "
            "Metrics are derived from deterministic models of handling time and cost; "
            "quality-related metrics requiring human judgment (e.g., QA scores, CSAT) "
            "are omitted from metrics as they cannot be observed in this sandbox."
        ),
    }

    return evidence
