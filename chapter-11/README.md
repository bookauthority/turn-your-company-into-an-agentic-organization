# Chapter 11 Experiment: Agentic HR, IT Support, and Internal Services

This project is a fully self-contained Python 3.11+ simulation of an experiment
for Chapter 11:

> Agentic HR, IT Support, and Internal Services

It implements a **baseline** (human-only) and **treatment** (agent-assisted)
workflow for four internal service workloads:

- `wl-hr-onboarding` – HR employee onboarding administration
- `wl-hr-changes-faq` – HR employment changes and policy FAQs
- `wl-it-access-requests` – IT standard access requests
- `wl-it-break-fix-faq` – IT break/fix and FAQ self-service guidance

The goal is to illustrate the experimental design and evidence schema using an
offline, deterministic simulation. The code does **not** connect to real HRIS,
IAM, ticketing, or LLM systems; instead, it uses simple Python models to
simulate ticket processing times and outcomes under baseline and agentic
conditions.

## Key Design Points

- **No external dependencies** – Standard library only.
- **Offline, deterministic** – Randomness is seeded for reproducibility.
- **Actual execution-based metrics** – All metrics are derived from simulated
  workflow execution during `run.py`; no numbers are hard-coded as results.
- **Evidence format** – `run.py` writes `/evidence/results.json` following the
  contract defined in the prompt.
- **Fair comparison** – Baseline vs. treatment tickets are generated from the
  same underlying workload distributions; treatment changes processing
  behavior, not the workload itself.

## What Is Simulated

For each workload and variant (baseline vs. treatment), the simulator:

1. Generates a small set of synthetic tickets with:
   - creation timestamp
   - priority
   - workload ID
2. Runs them through a simple queue processor that models:
   - **Time to first response** – delay until first human/agent interaction
   - **Time to resolution** – delay until ticket is completed
   - **Human handling time** – cumulative active staff time on the ticket
3. Treatment runs apply optimistic but plausible improvements:
   - Faster first response and resolution
   - Reduced human handling time via automation and better routing
4. Aggregates per-run metrics and writes them to `results.json`.

Metrics captured in this sandbox:

- `time_to_first_response_minutes`
- `time_to_resolution_minutes`
- `human_handling_time_minutes`

All are **numeric** and derived from the simulated workflow.

## Files

- `run.py` – Main entry point. Runs the simulation and writes evidence.
- `simulation.py` – Core simulation models and helpers.
- `experiment.py` – Orchestrates experiment variants and workloads.
- `evidence_writer.py` – Logic for formatting and writing results.json.
- `tests/test_experiment.py` – Unittests checking the evidence file and schema.
- `requirements.txt` – Empty of external runtime deps.

## Running the Experiment

From the project root:

```bash
python run.py
```

This will:

- Run baseline and treatment simulations for all four workloads.
- Write `/evidence/results.json` (or `$BOOKMAS_EVIDENCE_DIR/results.json` if
  the environment variable is set).

Example (abridged) structure of the output file:

```json
{
  "chapter": 11,
  "experiment_id": "exp-ch11-agentic-internal-services-hr-it-v1",
  "environment": {
    "os": "posix",
    "python": "3.11.6"
  },
  "runs": [
    {
      "variant": "baseline",
      "workload_id": "wl-hr-onboarding",
      "run_id": "wl-hr-onboarding-baseline-0",
      "success": true,
      "metrics": {
        "time_to_first_response_minutes": 37.5,
        "time_to_resolution_minutes": 240.0,
        "human_handling_time_minutes": 45.0
      }
    },
    {
      "variant": "treatment",
      "workload_id": "wl-hr-onboarding",
      "run_id": "wl-hr-onboarding-treatment-0",
      "success": true,
      "metrics": {
        "time_to_first_response_minutes": 10.0,
        "time_to_resolution_minutes": 160.0,
        "human_handling_time_minutes": 30.0
      }
    }
  ],
  "notes": "..."
}
```

The exact numbers will differ but remain deterministic because of fixed random
seeds.

## Running Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Tests verify:

- `results.json` exists after running `run.py`.
- The top-level schema (chapter, experiment_id, environment, runs).
- Each run contains the required fields and numeric metrics.
- At least one baseline and one treatment run exist per workload.

## Extending the Simulation

You can extend `simulation.py` and `experiment.py` to:

- Add more sophisticated queue models (e.g., multi-agent simulation).
- Track more metrics (e.g., reopen rate, content errors) using additional
  synthetic processes.
- Model privacy guardrails and incident records.

For the purposes of this offline sandbox, only a small subset of metrics is
implemented as **directly measurable** quantities.
