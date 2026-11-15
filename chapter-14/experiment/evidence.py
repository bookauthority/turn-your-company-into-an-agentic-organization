from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List

from .orchestrator import RunRecord


@dataclass
class EvidenceRun:
    variant: str
    workload_id: str
    run_id: str
    success: bool
    metrics: Dict[str, float]


def _convert_run(record: RunRecord) -> EvidenceRun:
    return EvidenceRun(
        variant=record.variant,
        workload_id=record.workload_id,
        run_id=record.run_id,
        success=record.success,
        metrics=record.metrics,
    )


def build_evidence(
    chapter: int,
    experiment_id: str,
    environment: Dict[str, str],
    baseline_runs: List[RunRecord],
    treatment_runs: List[RunRecord],
    notes: str | None = None,
) -> Dict[str, Any]:
    runs: List[EvidenceRun] = []
    for r in baseline_runs:
        runs.append(_convert_run(r))
    for r in treatment_runs:
        runs.append(_convert_run(r))

    evidence_runs_dicts: List[Dict[str, Any]] = [asdict(r) for r in runs]

    evidence: Dict[str, Any] = {
        "chapter": int(chapter),
        "experiment_id": experiment_id,
        "environment": environment,
        "runs": evidence_runs_dicts,
    }
    if notes:
        evidence["notes"] = notes
    return evidence
