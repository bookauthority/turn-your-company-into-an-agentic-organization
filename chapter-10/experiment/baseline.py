from __future__ import annotations

import time
from typing import Dict, List

from .metrics import elapsed_seconds
from .data import Invoice, PurchaseRequest, ReconCase, SpendTransaction


# ------------------------- Baseline Implementations --------------------


def process_invoices_baseline(invoices: List[Invoice]) -> Dict[str, float]:
    """Baseline invoice processing.

    Simulates manual steps by iterating and performing simple arithmetic.
    Returns a dict with a single numeric metric: total processing latency.
    """
    start = time.perf_counter()
    total = 0.0
    count = 0
    for inv in invoices:
        # Simulate manual work: simple arithmetic and branching
        total += inv.amount * (1.0 if inv.has_po else 1.01)
        if inv.num_lines > 1:
            total -= 0.01 * inv.num_lines
        count += 1
    end = time.perf_counter()
    latency = elapsed_seconds(start, end)
    return {"processing_latency_seconds": latency}


def process_prs_baseline(prs: List[PurchaseRequest]) -> Dict[str, float]:
    start = time.perf_counter()
    approvals = 0
    for pr in prs:
        # Simple policy: approve if amount < 50000 or preferred vendor, else flag
        if pr.amount < 50000.0 or pr.preferred_vendor:
            approvals += 1
        else:
            approvals -= 1  # pretend to track rework; unused but mimics effort
    end = time.perf_counter()
    latency = elapsed_seconds(start, end)
    return {"processing_latency_seconds": latency}


def process_recon_baseline(cases: List[ReconCase]) -> Dict[str, float]:
    start = time.perf_counter()
    matched = 0
    for case in cases:
        # Simulate reconciliation by iterating a synthetic list of transactions
        for i in range(case.n_transactions):
            if (i + case.vendor_id) % 3 == 0:
                matched += 1
    end = time.perf_counter()
    latency = elapsed_seconds(start, end)
    return {"processing_latency_seconds": latency}


def process_spend_baseline(txs: List[SpendTransaction]) -> Dict[str, float]:
    start = time.perf_counter()
    totals_by_cat = {}
    for tx in txs:
        totals_by_cat.setdefault(tx.category, 0.0)
        totals_by_cat[tx.category] += tx.base_amount
    # Simple extra passes to mimic report building
    summary = 0.0
    for cat, total in totals_by_cat.items():
        if total > 10000.0:
            summary += total * 0.001
        else:
            summary += total * 0.0005
    end = time.perf_counter()
    latency = elapsed_seconds(start, end)
    return {"processing_latency_seconds": latency}
