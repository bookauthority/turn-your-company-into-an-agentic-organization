# Experiment 14 – Operating, Monitoring, and Continuously Improving Multi-Agent Systems

This repository contains a fully self-contained Python 3.11+ experiment project for:

> **Chapter 14 – Operating, Monitoring, and Continuously Improving Multi-Agent Systems**
>
> Experiment ID: `exp-014-operate-monitor-improve-mas-v1`

The goal is to simulate a small multi-agent ticket-handling system with both a **baseline** deployment and a **treatment** deployment that uses SRE-like observability, SLO-style checks, and a simple improvement loop. The experiment is deterministic and offline, relying only on the Python standard library.

The experiment produces **structured evidence** in `/evidence/results.json` following the contract provided in the prompt.

## Overview

- **Baseline variant**
  - Simple multi-agent workflow: router → resolver → reviewer.
  - Minimal observability (we only measure end-to-end latency and a synthetic success flag).
  - No explicit SLOs, alerts, or feedback loop.

- **Treatment variant**
  - Same ticket workflow, plus:
    - Explicit SLIs (success, latency) computed from per-run data.
    - Simple SLO-style checks (target success rate and latency threshold) evaluated in-code.
    - Per-step timing and a lightweight feedback signal.
    - A trivial "tuned" resolver that performs slightly better on hard tickets.

This is not a real LLM integration (the sandbox is offline); instead, we use deterministic, rule-based agents to *simulate* behavior so that metrics are truly measured during execution.

## Project layout

- `run.py` – Main entrypoint. Runs both baseline and treatment over a shared synthetic workload and writes evidence to `/evidence/results.json`.
- `experiment/__init__.py` – Package marker.
- `experiment/workload.py` – Synthetic ticket stream generator (deterministic given a seed).
- `experiment/agents.py` – Simple router, resolver, and reviewer agents.
- `experiment/orchestrator.py` – Orchestrates multi-agent runs for baseline and treatment; produces per-run metrics.
- `experiment/monitoring.py` – Treatment-only monitoring utilities (SLI aggregation and simple SLO evaluation helpers).
- `experiment/evidence.py` – Evidence assembly and serialization helpers.
- `tests/test_experiment.py` – Unittest-based tests that verify the evidence schema and basic behavior.
- `requirements.txt` – Empty of runtime dependencies (standard library only).

## How to run

1. **Ensure Python 3.11+ is available.**

2. **Install (no external deps needed)**

   Optionally create a virtual environment and activate it, then:

   ```bash
   pip install -r requirements.txt
   ```

   The file is present for completeness but contains no runtime dependencies.

3. **Run the experiment**

   From the project root:

   ```bash
   python run.py
   ```

   This will:

   - Generate a synthetic workload of tickets.
   - Run the baseline and treatment orchestrators on that workload.
   - Collect metrics (at least one shared numeric measurement per run – we use `latency_ms` and `steps`).
   - Write evidence to:
     - `BOOKMAS_EVIDENCE_DIR/results.json` if `BOOKMAS_EVIDENCE_DIR` is set, otherwise
     - `/evidence/results.json`.

4. **Run tests**

   ```bash
   python -m unittest discover -s tests -p "test_*.py"
   ```

   The tests will:

   - Execute `run.py` in-process.
   - Load the resulting evidence JSON.
   - Verify that it follows the required schema and that both baseline and treatment entries exist for the shared workload.

## What is measured

Each run record in `results.json` has a `metrics` object that includes at least:

- `latency_ms` – End-to-end latency per session in milliseconds (numeric).
- `steps` – Number of agent steps taken (numeric).

We also compute a synthetic `success` boolean per run based on whether the resolver's output matches a simple, deterministic rule-derived expectation (our stand-in for ground truth). This is exposed as the top-level `success` field of each run, *not* as a numeric metric.

Some higher-level metrics (e.g., aggregate success rate and average latency) are used internally by the treatment orchestration and mentioned in `notes`, but not written into the `metrics` dict per-run because they are aggregates rather than direct per-run measurements.

## Limitations

- No real LLMs or external services (offline sandbox).
- Monitoring, SLI, SLO, and alerting features are simplified but illustrate the core ideas.
- Real-time dashboards and alerts are represented via in-code evaluation rather than external systems like Prometheus or Grafana.

## Extending the experiment

You can extend this framework by:

- Increasing workload size or complexity.
- Modifying `agents.py` to add more nuanced behavior, additional tools, or safety checks.
- Implementing additional metrics (e.g., offline accuracy on a richer ground truth structure) while keeping per-run `metrics` numerical.
- Adding multi-experiment routing and more sophisticated A/B logic to `orchestrator.py`.
