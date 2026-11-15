import math
import os
import random
import statistics
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


CHAPTER_NUMBER = 7
EXPERIMENT_ID = "ch7-durable-workflows-approvals-exceptions-v1"


WORKLOAD_IDS = [
    "normal_operation_workload",
    "resilience_under_partial_failures_workload",
    "load_and_chaos_resilience_workload",
]


@dataclass
class WorkflowConfig:
    """Configuration for simulated workflows per workload.

    Each workload is scaled down but still differentiates between
    normal operation and failure/chaos scenarios.
    """

    workload_id: str
    n_workflows: int
    # Probability of external failure on side-effecting steps.
    failure_prob: float
    # Whether to simulate an orchestrator crash for part of the run.
    simulate_crash: bool
    # Whether the environment is considered "chaotic" (more failures).
    chaos_factor: float


def get_workflow_config(workload_id: str) -> WorkflowConfig:
    if workload_id == "normal_operation_workload":
        return WorkflowConfig(
            workload_id=workload_id,
            n_workflows=30,
            failure_prob=0.02,
            simulate_crash=False,
            chaos_factor=1.0,
        )
    if workload_id == "resilience_under_partial_failures_workload":
        return WorkflowConfig(
            workload_id=workload_id,
            n_workflows=30,
            failure_prob=0.25,
            simulate_crash=True,
            chaos_factor=1.5,
        )
    if workload_id == "load_and_chaos_resilience_workload":
        return WorkflowConfig(
            workload_id=workload_id,
            n_workflows=50,
            failure_prob=0.2,
            simulate_crash=True,
            chaos_factor=2.0,
        )
    raise ValueError(f"Unknown workload_id: {workload_id}")


@dataclass
class StepResult:
    success: bool
    retries: int
    duration: float


@dataclass
class WorkflowRunTrace:
    workflow_id: str
    start_time: float
    end_time: Optional[float] = None
    terminal_status: Optional[str] = None  # completed|failed|human_takeover
    steps: List[StepResult] = field(default_factory=list)


@dataclass
class RunMetrics:
    workflow_completion_rate: float
    unrecovered_failure_rate: float
    median_workflow_latency: float
    mean_retries_per_retryable_step: float


def compute_metrics_from_traces(traces: List[WorkflowRunTrace]) -> RunMetrics:
    if not traces:
        return RunMetrics(0.0, 0.0, 0.0, 0.0)

    n_started = len(traces)
    n_completed = 0
    n_failed = 0
    latencies: List[float] = []
    retry_counts: List[int] = []

    for t in traces:
        if t.terminal_status in ("completed", "failed", "human_takeover"):
            n_completed += 1
        if t.terminal_status == "failed":
            n_failed += 1
        if t.end_time is not None and t.terminal_status is not None:
            lat = max(0.0, t.end_time - t.start_time)
            latencies.append(lat)
        for s in t.steps:
            if s.retries > 0:
                retry_counts.append(s.retries)

    completion_rate = n_completed / float(n_started)
    unrecovered_failure_rate = n_failed / float(n_started)
    if latencies:
        median_latency = statistics.median(latencies)
    else:
        median_latency = 0.0
    if retry_counts:
        mean_retries = sum(retry_counts) / float(len(retry_counts))
    else:
        mean_retries = 0.0

    return RunMetrics(
        workflow_completion_rate=completion_rate,
        unrecovered_failure_rate=unrecovered_failure_rate,
        median_workflow_latency=median_latency,
        mean_retries_per_retryable_step=mean_retries,
    )


def deterministic_random(seed: int) -> random.Random:
    return random.Random(seed)


def ensure_evidence_dir() -> str:
    base = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
    try:
        os.makedirs(base, exist_ok=True)
    except Exception:
        # Last resort: fall back to /tmp if /evidence unwritable.
        base = "/tmp/evidence"
        os.makedirs(base, exist_ok=True)
    return base


def env_info() -> Dict[str, str]:
    return {
        "os": sys.platform,
        "python": sys.version.split()[0],
    }


def now() -> float:
    return time.time()
