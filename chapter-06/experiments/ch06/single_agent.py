from __future__ import annotations

from typing import Dict, List

from .config import BASELINE_MAX_STEPS
from .data import (
    generate_workload_standard,
    generate_workload_high_risk,
    generate_workload_mixed,
)
from .metrics import WorkflowOutcome, compute_numeric_metrics
from .config import (
    WORKLOAD_STANDARD,
    WORKLOAD_HIGH_RISK,
    WORKLOAD_MIXED,
)


def _run_single_case(case, gt) -> WorkflowOutcome:
    # The baseline does the full workflow in a linear sequence with an
    # internal step counter (representing prompt/tool rounds).
    steps = 0

    # Step 1: "understand" request
    steps += 1

    # Step 2: enrich data (here: copy simple fields)
    steps += 1
    enriched = {
        "case_id": case.case_id,
        "country": case.country,
        "annual_revenue_band": case.annual_revenue_band,
        "segment": case.segment,
        "known_issues": case.known_issues,
    }

    # Step 3: risk classification (simple heuristic)
    steps += 1
    if case.known_issues:
        risk = "high"
    elif case.segment == "high_risk":
        risk = "high"
    else:
        risk = "low"

    # Step 4: contract drafting (simplified)
    steps += 1
    if risk == "high":
        discount = 5
        term_months = 12
    else:
        discount = 15
        term_months = 24
    contract = {
        "risk": risk,
        "term_months": term_months,
        "discount_percent": discount,
    }

    # Step 5: internal self-check (no rework for baseline)
    steps += 1

    # Determine correctness vs ground truth.
    truth = gt[case.case_id]
    enrichment_correct = enriched == truth.target_enriched_profile
    risk_correct = risk == truth.target_risk_category
    contract_correct = contract == truth.target_contract_summary

    # Baseline always marks as DONE if steps under budget.
    final_state = "DONE" if steps <= BASELINE_MAX_STEPS else "FAILED"

    return WorkflowOutcome(
        case_id=case.case_id,
        final_state=final_state,
        state_transitions=1,  # single linear flow, treat as one logical transition
        enrichment_correct=enrichment_correct,
        risk_correct=risk_correct,
        contract_correct=contract_correct,
    )


def _run_workload(cases, gt) -> Dict[str, float]:
    outcomes: List[WorkflowOutcome] = []
    for case in cases:
        outcomes.append(_run_single_case(case, gt))
    return compute_numeric_metrics(outcomes)


def run_baseline_for_workload(workload_id: str) -> Dict[str, float]:
    if workload_id == WORKLOAD_STANDARD:
        cases, gt = generate_workload_standard()
    elif workload_id == WORKLOAD_HIGH_RISK:
        cases, gt = generate_workload_high_risk()
    elif workload_id == WORKLOAD_MIXED:
        cases, gt = generate_workload_mixed()
    else:
        raise ValueError(f"Unknown workload_id: {workload_id}")

    return _run_workload(cases, gt)
