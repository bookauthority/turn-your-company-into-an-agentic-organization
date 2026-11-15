# Chapter 6 Multi-Agent Orchestration Experiment

This is a self-contained, offline-friendly Python 3.11+ experiment for

> **From One Agent to Many: Designing Multi-Agent Workflows**

It compares a **single-agent baseline** vs a **multi-agent treatment** on a
synthetic B2B customer onboarding workflow, implementing a simple
state-machine orchestrator and agent roles.

The implementation is intentionally lightweight and deterministic:

- Uses only the Python standard library (no external dependencies).
- Uses synthetic, in-memory datasets instead of real files.
- Uses rule-based "agents" instead of actual LLM calls, but keeps the
  architecture similar to an LLM-based MAS setup.
- Computes simple numeric metrics (at minimum: `workflow_success_rate` and
  `state_transitions_per_workflow`) derived from actual execution.

It also writes experiment evidence to `/evidence/results.json` conforming to
an explicit schema so an external validator can consume it.

## Project Layout

- `run.py` – main entry point that runs the experiment and writes evidence.
- `experiments/ch06/`
  - `data.py` – synthetic workloads and ground truth.
  - `single_agent.py` – baseline single-agent workflow implementation.
  - `multi_agent.py` – multi-agent workflow + orchestrator.
  - `metrics.py` – metric computation helpers.
  - `config.py` – shared constants and configuration.
- `tests/test_experiment.py` – unit tests for evidence schema and basic behavior.
- `requirements.txt` – empty at runtime (standard library only).

## Running the Experiment

From the repository root:

```bash
python run.py
``

This will:

1. Run at least one baseline and one treatment run for each workload
   (standard, high_risk, mixed).
2. Compute a minimal but valid set of numeric metrics per run.
3. Write evidence to `${BOOKMAS_EVIDENCE_DIR:-/evidence}/results.json`.

Environment variables:

- `BOOKMAS_EVIDENCE_DIR` – directory where `results.json` will be written.
  Defaults to `/evidence`.

## Running Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The tests assert that:

- `run.py` produces a JSON file at `/evidence/results.json` following the
  required schema.
- All metrics are numeric.
- Both baseline and treatment variants are present for each workload.

## Notes

This experiment is **not** a full realization of the chapter's production
architecture. Instead, it is a compact, fully reproducible approximation
showing:

- How to move from a single agent that does everything to a decomposed
  workflow with Router, DataEnrichment, ContractDrafting, QualityReviewer,
  and Supervisor roles.
- How to coordinate agents via a state machine and queue.
- How to instrument and compare basic outcomes.

You can extend it by:

- Replacing rule-based logic with real LLM calls.
- Swapping the in-memory queue for a durable backend.
- Persisting workflow state in a real database.
- Adding richer metrics and per-step audit logs.
