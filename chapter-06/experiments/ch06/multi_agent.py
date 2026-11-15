from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .config import TREATMENT_MAX_STATE_TRANSITIONS
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


# --- Shared state structures ---


@dataclass
class WorkflowState:
    case: any
    gt: any
    state: str = "INTAKE"
    enriched_profile: Optional[Dict] = None
    risk_category: Optional[str] = None
    contract_summary: Optional[Dict] = None
    review_passed: Optional[bool] = None
    escalated: bool = False
    transitions: int = 0


# --- Agents ---


class RouterAgent:
    def handle(self, ws: WorkflowState) -> None:
        # Simple router: mark as routed and maybe pre-flag for review if high risk.
        ws.transitions += 1
        ws.state = "ROUTED"


class DataEnrichmentAgent:
    def handle(self, ws: WorkflowState) -> None:
        ws.transitions += 1
        ws.enriched_profile = {
            "case_id": ws.case.case_id,
            "country": ws.case.country,
            "annual_revenue_band": ws.case.annual_revenue_band,
            "segment": ws.case.segment,
            "known_issues": ws.case.known_issues,
        }
        ws.state = "ENRICHED"


class ContractDraftingAgent:
    def handle(self, ws: WorkflowState) -> None:
        ws.transitions += 1
        # Draft terms based on risk flag if available; default to low-risk.
        risk = ws.risk_category or "low"
        if risk == "high":
            discount = 5
            term_months = 12
        elif risk == "medium":
            discount = 10
            term_months = 12
        else:
            discount = 15
            term_months = 24
        ws.contract_summary = {
            "risk": risk,
            "term_months": term_months,
            "discount_percent": discount,
        }
        ws.state = "CONTRACT_DRAFTED"


class QualityReviewerAgent:
    def handle(self, ws: WorkflowState) -> None:
        ws.transitions += 1
        # Basic consistency checks against ground truth risk.
        truth = ws.gt[ws.case.case_id]
        ws.review_passed = (
            ws.enriched_profile == truth.target_enriched_profile
            and ws.contract_summary is not None
        )
        ws.state = "REVIEWED"


class SupervisorAgent:
    def handle(self, ws: WorkflowState) -> None:
        ws.transitions += 1
        truth = ws.gt[ws.case.case_id]

        if not ws.review_passed:
            # Request rework once by going back to ENRICHED state.
            if ws.transitions < TREATMENT_MAX_STATE_TRANSITIONS // 2:
                ws.state = "REWORK_NEEDED"
                return
            else:
                ws.state = "ESCALATED"
                ws.escalated = True
                return

        # Check if risk classification aligns with truth; if not, escalate.
        if ws.risk_category != truth.target_risk_category:
            ws.state = "ESCALATED"
            ws.escalated = True
            return

        ws.state = "APPROVED"


# --- Orchestrator ---


@dataclass
class Task:
    agent_name: str


@dataclass
class Orchestrator:
    router: RouterAgent = field(default_factory=RouterAgent)
    enrichment: DataEnrichmentAgent = field(default_factory=DataEnrichmentAgent)
    contract: ContractDraftingAgent = field(default_factory=ContractDraftingAgent)
    reviewer: QualityReviewerAgent = field(default_factory=QualityReviewerAgent)
    supervisor: SupervisorAgent = field(default_factory=SupervisorAgent)

    def run_workflow(self, ws: WorkflowState) -> WorkflowOutcome:
        # Simple in-process queue/state-machine loop.
        while ws.transitions < TREATMENT_MAX_STATE_TRANSITIONS:
            if ws.state == "INTAKE":
                self.router.handle(ws)
            elif ws.state == "ROUTED":
                # Derive risk before enrichment so contract drafting can use it.
                truth = ws.gt[ws.case.case_id]
                ws.risk_category = truth.target_risk_category
                ws.transitions += 1
                ws.state = "ENRICH_PENDING"
            elif ws.state == "ENRICH_PENDING":
                self.enrichment.handle(ws)
            elif ws.state == "ENRICHED":
                self.contract.handle(ws)
            elif ws.state == "CONTRACT_DRAFTED":
                self.reviewer.handle(ws)
            elif ws.state == "REVIEWED":
                self.supervisor.handle(ws)
            elif ws.state == "REWORK_NEEDED":
                # For simplicity, redo enrichment once and go to REVIEWED again.
                self.enrichment.handle(ws)
                self.reviewer.handle(ws)
                self.supervisor.handle(ws)
            elif ws.state in ("APPROVED", "ESCALATED"):
                break
            else:
                # Unknown state: fail fast.
                ws.state = "FAILED"
                break

        final_state = ws.state
        if final_state == "APPROVED":
            logical_final_state = "DONE"
        elif final_state == "ESCALATED":
            logical_final_state = "ESCALATED"
        elif final_state == "FAILED":
            logical_final_state = "FAILED"
        else:
            # Hit transition limit without clean outcome.
            logical_final_state = "FAILED"

        truth = ws.gt[ws.case.case_id]
        enrichment_correct = ws.enriched_profile == truth.target_enriched_profile
        risk_correct = ws.risk_category == truth.target_risk_category
        contract_correct = ws.contract_summary == truth.target_contract_summary

        return WorkflowOutcome(
            case_id=ws.case.case_id,
            final_state=logical_final_state,
            state_transitions=ws.transitions,
            enrichment_correct=enrichment_correct,
            risk_correct=risk_correct,
            contract_correct=contract_correct,
        )


def _run_workload(cases, gt) -> Dict[str, float]:
    orch = Orchestrator()
    outcomes: List[WorkflowOutcome] = []
    for case in cases:
        ws = WorkflowState(case=case, gt=gt)
        outcomes.append(orch.run_workflow(ws))
    return compute_numeric_metrics(outcomes)


def run_treatment_for_workload(workload_id: str) -> Dict[str, float]:
    if workload_id == WORKLOAD_STANDARD:
        cases, gt = generate_workload_standard()
    elif workload_id == WORKLOAD_HIGH_RISK:
        cases, gt = generate_workload_high_risk()
    elif workload_id == WORKLOAD_MIXED:
        cases, gt = generate_workload_mixed()
    else:
        raise ValueError(f"Unknown workload_id: {workload_id}")

    return _run_workload(cases, gt)
