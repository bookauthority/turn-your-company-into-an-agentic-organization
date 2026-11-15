# Chapter 7 Experiment: Durable Workflows, Approvals, and Exception Handling

This project implements a **self-contained, offline** Python 3.11+ experiment for:

- **Chapter**: 7
- **Title**: Durable Workflows, Approvals, and Exception Handling
- **Experiment ID**: `ch7-durable-workflows-approvals-exceptions-v1`

It compares two implementations of a simplified **customer onboarding** workflow:

1. **Baseline** – naive, in-memory, linear orchestrator with fragile approvals and failure handling.
2. **Treatment** – durable, explicit state-machine workflow engine with persisted state, approvals, retries, and audit logs.

The code is intentionally scaled down to run safely inside a restricted sandbox, but preserves key architectural differences and collects **real, instrumented metrics** from actual runs.

## What this experiment demonstrates

- Modeling workflows as:
  - Imperative linear code (baseline).
  - An explicit state machine with transitions and approval states (treatment).
- Simulated long-running tasks using sleeps and simple retry logic.
- Approval steps with different behavior in baseline vs treatment.
- Exception paths and partial failures.
- Simple durability via a JSON file for the treatment engine (simulating a database).
- Basic metrics collection for three workloads:
  - `normal_operation_workload`
  - `resilience_under_partial_failures_workload`
  - `load_and_chaos_resilience_workload`

The implementation is single-process and uses only the Python standard library to satisfy sandbox constraints. Durability is emulated via **on-disk JSON state** rather than a real database.

## Repository layout

- `run.py` – Main entrypoint. Runs the miniature workloads for both baseline and treatment and writes evidence JSON.
- `workflow_common.py` – Shared configuration, random helpers, and data structures.
- `baseline_engine.py` – Naive in-memory orchestrator.
- `treatment_engine.py` – Durable state-machine workflow engine with persisted state and retries.
- `analysis_stub.py` – Very small helper to aggregate per-run metrics (used by `run.py`).
- `tests/test_experiment.py` – Unittests that validate the evidence schema and some behavioral expectations.
- `requirements.txt` – Empty of third-party runtime deps (standard library only).

## Evidence format contract

`run.py` **must** write a JSON file to:

- Path: `${BOOKMAS_EVIDENCE_DIR}/results.json` (default directory: `/evidence` if env var unset).

Schema (validated by tests):

```json
{
  "chapter": 7,
  "experiment_id": "ch7-durable-workflows-approvals-exceptions-v1",
  "environment": {"os": "...", "python": "..."},
  "runs": [
    {
      "variant": "baseline" | "treatment",
      "workload_id": "normal_operation_workload" | "resilience_under_partial_failures_workload" | "load_and_chaos_resilience_workload",
      "run_id": "string unique per workload+variant",
      "success": true | false,
      "metrics": {
        "<metric_name>": <number>,
        "...": <number>
      }
    }
  ],
  "notes": "optional string"
}
```

Additional top-level fields are allowed, but **every metric value must be a finite JSON number**. No strings, objects, lists, booleans, or null inside the `metrics` object.

The implementation reports a small, realistic subset of metrics that can be measured inside this sandbox:

- `workflow_completion_rate` – fraction of started workflows that ended in any terminal state.
- `unrecovered_failure_rate` – fraction of started workflows that ended in `failed`.
- `median_workflow_latency` – median latency (seconds) between workflow start and terminal state.
- `mean_retries_per_retryable_step` – average retry count for steps that were retried.

All metrics are computed from in-memory traces in the same process that runs the experiment.

## Running the experiment

From the project root (where `run.py` is located):

```bash
python run.py
``

This will:

1. Discover environment info (OS, Python version).
2. Execute **one run per workload per variant** (6 runs total):
   - Baseline + treatment for each workload ID.
3. For each run, it simulates a small number of workflows (e.g. 20–60) with deterministic seeds.
4. Collect metrics per run.
5. Write the evidence file to `${BOOKMAS_EVIDENCE_DIR:-/evidence}/results.json`.

If the `/evidence` directory does not exist, `run.py` will create it.

## Running tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The tests verify that:

- The evidence file exists and is valid JSON.
- The top-level schema obeys the specified contract.
- At least one baseline and one treatment run exist for each workload ID.
- `metrics` is present, non-empty, and all metric values are numbers.

## Safety and limitations

- **No external network** calls are used.
- No external databases, message queues, or subprocesses are invoked.
- Durability is approximated using a JSON file under the project directory or `/tmp`.
- The full production design from the chapter (PostgreSQL, Redis, HTTP APIs) is modeled conceptually, not literally implemented, due to sandbox constraints.

## Extending the experiment

If you want to bring this closer to the full architecture outlined in the spec:

- Replace the treatment engine's file-based store with a real DB (e.g. Postgres) and an ORM.
- Add a FastAPI layer on top of each engine to accept HTTP workflow commands.
- Replace the in-process scheduler with background workers or an async queue.
- Expand metrics collection and export them into the richer `evidence_schema` from the specification.

This minimal implementation focuses on **reproducible comparison of baseline vs. treatment durability behaviors** within a single, isolated Python process.
