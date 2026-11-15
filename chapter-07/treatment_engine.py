import json
import os
import random
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from workflow_common import WorkflowRunTrace, StepResult, WorkflowConfig, now


@dataclass
class StateMachineStep:
    name: str
    base_duration: float
    can_fail: bool
    max_retries: int
    is_approval: bool = False


class DurableStore:
    """Extremely small file-backed store to approximate durability.

    In a real system this would be a database; here we only need to show
    that treatment persists enough state to resume after a simulated crash.
    """

    def __init__(self, path: str) -> None:
        self.path = path
        self._state: Dict[str, Dict[str, str]] = {}
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self._state = data
            except Exception:
                self._state = {}
        self._loaded = True

    def _flush(self) -> None:
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._state, f)
        os.replace(tmp, self.path)

    def set_status(self, workflow_id: str, status: str) -> None:
        self._load()
        self._state.setdefault(workflow_id, {})["status"] = status
        self._flush()

    def get_status(self, workflow_id: str) -> Optional[str]:
        self._load()
        data = self._state.get(workflow_id) or {}
        return data.get("status")


class TreatmentEngine:
    """Durable state-machine-based workflow engine.

    It supports simple retries and a persistent view of workflow status.
    """

    def __init__(self, cfg: WorkflowConfig, rng: random.Random, store_path: str) -> None:
        self.cfg = cfg
        self.rng = rng
        self.store = DurableStore(store_path)
        self.steps: List[StateMachineStep] = [
            StateMachineStep("configure_account", base_duration=0.005, can_fail=True, max_retries=2),
            StateMachineStep("approval", base_duration=0.005, can_fail=True, max_retries=3, is_approval=True),
            StateMachineStep("provision", base_duration=0.01, can_fail=True, max_retries=3),
            StateMachineStep("welcome", base_duration=0.002, can_fail=True, max_retries=1),
        ]

    def _simulate_step(self, step: StateMachineStep) -> StepResult:
        start = now()
        retries = 0
        attempt = 0
        while True:
            attempt += 1
            # Simulate work
            duration = step.base_duration * (0.5 + self.rng.random())
            time.sleep(min(duration, 0.01))

            # Determine success
            success = True
            eff_failure_prob = self.cfg.failure_prob
            if step.is_approval:
                # approvals in treatment are slightly more reliable and retried
                eff_failure_prob *= 0.7
            if step.can_fail and self.rng.random() < eff_failure_prob:
                success = False

            if success:
                end = now()
                return StepResult(success=True, retries=retries, duration=end - start)

            if attempt > step.max_retries:
                end = now()
                return StepResult(success=False, retries=retries, duration=end - start)

            retries += 1
            # backoff
            backoff = min(0.005 * attempt, 0.02)
            time.sleep(backoff)

    def run_workflows(self) -> List[WorkflowRunTrace]:
        traces: List[WorkflowRunTrace] = []

        for i in range(self.cfg.n_workflows):
            wf_id = f"treatment-{self.cfg.workload_id}-{i}"
            self.store.set_status(wf_id, "started")
            trace = WorkflowRunTrace(workflow_id=wf_id, start_time=now())

            for step in self.steps:
                sres = self._simulate_step(step)
                trace.steps.append(sres)
                if not sres.success:
                    self.store.set_status(wf_id, "failed")
                    trace.terminal_status = "failed"
                    trace.end_time = now()
                    break

            if trace.terminal_status is None:
                self.store.set_status(wf_id, "completed")
                trace.terminal_status = "completed"
                trace.end_time = now()

            traces.append(trace)

        return traces
