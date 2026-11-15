from __future__ import annotations

import time
from typing import Dict, List

from .metrics import elapsed_seconds
from .data import Invoice, PurchaseRequest, ReconCase, SpendTransaction


# ----------------------- Treatment (Agentic) Logic ---------------------

# The treatment implementations simulate a more structured, tool-based
# agent workflow. They are intentionally a bit more computationally
# structured (e.g., extra loops, small validations) to reflect additional
# control logic, but remain lightweight for CI.


def _agent_invoice_tools(inv: Invoice) -> float:
    """Simulate agent tools: parsing, matching, coding.

    Returns a synthetic score (unused outside but forces some computation).
    """
    # Tool 1: parse header (trivial here)
    header_score = 1.0 if inv.has_po else 0.9
    # Tool 2: analyze lines
    line_factor = 1.0 + (inv.num_lines * 0.001)
    # Tool 3: policy check (boundary at 1000 and 3000)
    if inv.amount < 1000:
        policy_score = 1.0
    elif inv.amount < 3000:
        policy_score = 0.98
    else:
        policy_score = 0.95
    return header_score * line_factor * policy_score


def process_invoices_treatment(invoices: List[Invoice]) -> Dict[str, float]:
    start = time.perf_counter()
    scores = 0.0
    for inv in invoices:
        scores += _agent_invoice_tools(inv)
    end = time.perf_counter()
    latency = elapsed_seconds(start, end)
    return {"processing_latency_seconds": latency}


def _agent_pr_tools(pr: PurchaseRequest) -> float:
    # Normalize department name
    dept = pr.department.strip().lower()
    name_score = 1.0 if dept in {"engineering", "it", "operations"} else 0.97
    # Budget check tiers
    if pr.amount < 5000:
        budget_score = 1.0
    elif pr.amount < 25000:
        budget_score = 0.99
    else:
        budget_score = 0.96
    # Preferred vendor bonus
    vendor_score = 1.02 if pr.preferred_vendor else 0.98
    return name_score * budget_score * vendor_score


def process_prs_treatment(prs: List[PurchaseRequest]) -> Dict[str, float]:
    start = time.perf_counter()
    scores = 0.0
    for pr in prs:
        scores += _agent_pr_tools(pr)
    end = time.perf_counter()
    latency = elapsed_seconds(start, end)
    return {"processing_latency_seconds": latency}


def _agent_recon_tools(case: ReconCase) -> int:
    # Simulate fuzzy matching across transactions
    matched = 0
    for i in range(case.n_transactions):
        key = (i * 7 + case.vendor_id * 13) % 11
        if key in (0, 3, 5):
            matched += 1
    return matched


def process_recon_treatment(cases: List[ReconCase]) -> Dict[str, float]:
    start = time.perf_counter()
    total_matched = 0
    for case in cases:
        total_matched += _agent_recon_tools(case)
    end = time.perf_counter()
    latency = elapsed_seconds(start, end)
    return {"processing_latency_seconds": latency}


def _agent_spend_tools(tx: SpendTransaction) -> float:
    # Normalize vendor/category; here we just use category as proxy
    base = tx.base_amount
    if tx.category in ("Software", "Hardware"):
        factor = 1.01
    elif tx.category in ("Professional_Services", "Marketing"):
        factor = 1.005
    else:
        factor = 1.0
    # Simple anomaly heuristic
    anomaly_penalty = 0.99 if base > 8000.0 else 1.0
    return base * factor * anomaly_penalty


def process_spend_treatment(txs: List[SpendTransaction]) -> Dict[str, float]:
    start = time.perf_counter()
    aggregate = 0.0
    for tx in txs:
        aggregate += _agent_spend_tools(tx)
    # Extra pass to simulate report builder creating multiple views
    adjusted = aggregate
    for _ in range(3):
        adjusted = adjusted * 0.999 + 0.5
    end = time.perf_counter()
    latency = elapsed_seconds(start, end)
    return {"processing_latency_seconds": latency}
