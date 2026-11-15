from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable


@dataclass
class WorkflowOutcome:
    case_id: str
    final_state: str  # DONE / ESCALATED / FAILED
    state_transitions: int
    enrichment_correct: bool
    risk_correct: bool
    contract_correct: bool


def compute_numeric_metrics(outcomes: Iterable[WorkflowOutcome]) -> Dict[str, float]:
    outs = list(outcomes)
    total = len(outs)
    if total == 0:
        return {
            "workflow_success_rate": 0.0,
            "state_transitions_per_workflow": 0.0,
        }

    success = sum(1 for o in outs if o.final_state == "DONE")
    avg_transitions = sum(o.state_transitions for o in outs) / float(total)

    return {
        # Fraction between 0 and 1.
        "workflow_success_rate": success / float(total),
        # Average number of state transitions.
        "state_transitions_per_workflow": avg_transitions,
    }
