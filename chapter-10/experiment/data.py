from __future__ import annotations

import dataclasses
import random
from typing import Dict, List, Tuple

from .config import GLOBAL_RANDOM_SEED, WORKLOAD_SIZES, WORKLOAD_INVOICES, WORKLOAD_POS, WORKLOAD_RECON, WORKLOAD_SPEND


# ----------------------------- Data Models -----------------------------

@dataclasses.dataclass(frozen=True)
class Invoice:
    invoice_id: str
    vendor_id: int
    amount: float
    num_lines: int
    has_po: bool


@dataclasses.dataclass(frozen=True)
class PurchaseRequest:
    pr_id: str
    department: str
    amount: float
    preferred_vendor: bool


@dataclasses.dataclass(frozen=True)
class ReconCase:
    vendor_id: int
    n_transactions: int


@dataclasses.dataclass(frozen=True)
class SpendTransaction:
    tx_id: str
    base_amount: float
    category: str


# -------------------------- Synthetic Generators -----------------------


def _seed() -> None:
    """Seed all RNGs once for deterministic data generation."""
    random.seed(GLOBAL_RANDOM_SEED)


def generate_invoices() -> List[Invoice]:
    _seed()
    n = WORKLOAD_SIZES[WORKLOAD_INVOICES]
    invoices: List[Invoice] = []
    for i in range(n):
        vendor_id = random.randint(1, 10)
        num_lines = random.choice([1, 1, 1, 3, 5])
        has_po = random.random() < 0.8
        base = random.uniform(100.0, 5000.0)
        noise = random.uniform(-5.0, 5.0)
        amount = round(base + noise, 2)
        invoices.append(
            Invoice(
                invoice_id=f"INV-{i:03d}",
                vendor_id=vendor_id,
                amount=amount,
                num_lines=num_lines,
                has_po=has_po,
            )
        )
    return invoices


def generate_purchase_requests() -> List[PurchaseRequest]:
    _seed()
    n = WORKLOAD_SIZES[WORKLOAD_POS]
    departments = ["Engineering", "Marketing", "Sales", "IT", "Operations"]
    prs: List[PurchaseRequest] = []
    for i in range(n):
        dept = departments[i % len(departments)]
        # Choose range based on simple distribution
        r = random.random()
        if r < 0.6:
            amount = random.uniform(100.0, 5000.0)
        elif r < 0.9:
            amount = random.uniform(5000.0, 25000.0)
        else:
            amount = random.uniform(25000.0, 100000.0)
        preferred_vendor = random.random() < 0.7
        prs.append(
            PurchaseRequest(
                pr_id=f"PR-{i:03d}",
                department=dept,
                amount=round(amount, 2),
                preferred_vendor=preferred_vendor,
            )
        )
    return prs


def generate_recon_cases() -> List[ReconCase]:
    _seed()
    n = WORKLOAD_SIZES[WORKLOAD_RECON]
    cases: List[ReconCase] = []
    for i in range(n):
        vendor_id = i + 1
        n_tx = random.randint(20, 100)
        cases.append(ReconCase(vendor_id=vendor_id, n_transactions=n_tx))
    return cases


def generate_spend_transactions() -> List[SpendTransaction]:
    _seed()
    n = WORKLOAD_SIZES[WORKLOAD_SPEND]
    categories = [
        "Software",
        "Hardware",
        "Professional_Services",
        "Travel",
        "Facilities",
        "Marketing",
        "Miscellaneous",
    ]
    txs: List[SpendTransaction] = []
    for i in range(n):
        base_amount = random.uniform(50.0, 10000.0)
        cat = categories[i % len(categories)]
        txs.append(
            SpendTransaction(
                tx_id=f"TX-{i:04d}",
                base_amount=round(base_amount, 2),
                category=cat,
            )
        )
    return txs


# ------------------------- Workload Accessors --------------------------


def load_workload(workload_id: str):
    """Return synthetic dataset for the given workload ID.

    This keeps generation logic centralized and deterministic.
    """
    if workload_id == WORKLOAD_INVOICES:
        return generate_invoices()
    if workload_id == WORKLOAD_POS:
        return generate_purchase_requests()
    if workload_id == WORKLOAD_RECON:
        return generate_recon_cases()
    if workload_id == WORKLOAD_SPEND:
        return generate_spend_transactions()
    raise ValueError(f"Unknown workload_id: {workload_id}")
