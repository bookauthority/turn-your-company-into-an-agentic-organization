import math
import random
import time
from typing import List

from workflow_common import WorkflowRunTrace, StepResult, WorkflowConfig, now


class BaselineEngine:
    """Naive, in-memory, linear orchestrator.

    Characteristics:
    - No persistence of workflow state.
    - Linear sequence of steps represented directly in code.
    - Approvals simulated but not durable.
    - Minimal retry behavior (single retry for some steps).
    """

    def __init__(self, cfg: WorkflowConfig, rng: random.Random) -> None:
        self.cfg = cfg
        self.rng = rng

    def _simulate_step(self, base_duration: float, can_fail: bool, retry_once: bool) -> StepResult:
        start = now()
        retries = 0
        success = True

        # Simulate execution time.
        duration = base_duration * (0.5 + self.rng.random())
        time.sleep(min(duration, 0.01))  # keep it fast in sandbox

        if can_fail and self.rng.random() < self.cfg.failure_prob:
            success = False

        if not success and retry_once:
            retries += 1
            # retry after a bit
            time.sleep(min(duration, 0.01))
            # on retry, still may fail, but with lower probability
            if self.rng.random() < (self.cfg.failure_prob * 0.5):
                success = False
            else:
                success = True

        end = now()
        return StepResult(success=success, retries=retries, duration=end - start)

    def _simulate_approval(self) -> StepResult:
        # Baseline: approvals are fragile - if they "time out", they just fail.
        # Simulate human delay with a small random sleep but ignore durability.
        start = now()
        retries = 0
        delay = 0.005 + self.rng.random() * 0.01
        time.sleep(delay)
        success = self.rng.random() < 0.85  # most approvals succeed
        end = now()
        return StepResult(success=success, retries=retries, duration=end - start)

    def run_workflows(self) -> List[WorkflowRunTrace]:
        traces: List[WorkflowRunTrace] = []

        for i in range(self.cfg.n_workflows):
            wf_id = f"baseline-{self.cfg.workload_id}-{i}"
            trace = WorkflowRunTrace(workflow_id=wf_id, start_time=now())

            # Step 1: account configuration (side-effecting, retry once)
            s1 = self._simulate_step(base_duration=0.005, can_fail=True, retry_once=True)
            trace.steps.append(s1)
            if not s1.success:
                trace.terminal_status = "failed"
                trace.end_time = now()
                traces.append(trace)
                continue

            # Step 2: internal approval (no retries, may fail)
            s2 = self._simulate_approval()
            trace.steps.append(s2)
            if not s2.success:
                trace.terminal_status = "failed"
                trace.end_time = now()
                traces.append(trace)
                continue

            # Step 3: provisioning (side-effecting, may fail, no structured retry)
            s3 = self._simulate_step(base_duration=0.01, can_fail=True, retry_once=False)
            trace.steps.append(s3)
            if not s3.success:
                trace.terminal_status = "failed"
                trace.end_time = now()
                traces.append(trace)
                continue

            # Step 4: welcome notification (simple, can rarely fail, no retry)
            s4 = self._simulate_step(base_duration=0.002, can_fail=True, retry_once=False)
            trace.steps.append(s4)
            if not s4.success:
                trace.terminal_status = "failed"
                trace.end_time = now()
                traces.append(trace)
                continue

            trace.terminal_status = "completed"
            trace.end_time = now()
            traces.append(trace)

        return traces
