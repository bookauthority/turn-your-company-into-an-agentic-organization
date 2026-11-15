from __future__ import annotations

# Chapter and experiment identifiers
CHAPTER_NUMBER: int = 10
EXPERIMENT_ID: str = "exp-ch10-finance-ap-procurement-v1"

# Workload IDs defined in the specification
WORKLOAD_INVOICES: str = "dataset-invoices-v1"
WORKLOAD_POS: str = "dataset-pos-v1"
WORKLOAD_RECON: str = "dataset-recon-v1"
WORKLOAD_SPEND: str = "dataset-spend-v1"

WORKLOAD_IDS = [
    WORKLOAD_INVOICES,
    WORKLOAD_POS,
    WORKLOAD_RECON,
    WORKLOAD_SPEND,
]

# Shared random seed for reproducibility
GLOBAL_RANDOM_SEED: int = 42

# Per-workload small synthetic sizes to keep execution fast in CI
WORKLOAD_SIZES = {
    WORKLOAD_INVOICES: 20,  # number of invoices
    WORKLOAD_POS: 10,       # number of purchase requests
    WORKLOAD_RECON: 5,      # number of vendors to reconcile
    WORKLOAD_SPEND: 100,    # number of AP transactions
}
