# Customer Service and Support as an Agentic System

This project is a self-contained Python 3.11+ experiment for Chapter 8:
"Customer Service and Support as an Agentic System".

It simulates a mid-market B2B SaaS support operation with two variants:

- **Baseline**: Human-only tiered queues (Tier 1 / Tier 2) across channels.
- **Treatment**: A governed multi-agent support workflow (triage, knowledge,
  resolver, quality-review agents) with human escalations.

The experiment is **offline and synthetic**: it generates deterministic
workloads of tickets, runs both variants on identical tickets, and measures
operational metrics such as handle time and cost per ticket. No external
APIs, LLMs, or network connectivity are used.

## Project structure

- `run.py` – Main entrypoint. Runs both workloads across baseline and
  treatment, writes evidence JSON to `/evidence/results.json`.
- `experiment/__init__.py` – Package marker.
- `experiment/config.py` – Static configuration and parameters for
  baseline and treatment, including cost and time models.
- `experiment/ticket.py` – Data structures for tickets and events.
- `experiment/workload.py` – Deterministic synthetic workload generator.
- `experiment/agents.py` – Simplified agentic system simulation
  (triage, knowledge, resolver, quality-review) and baseline human
  workflow simulator.
- `experiment/metrics.py` – Metric computation utilities.
- `experiment/runner.py` – Orchestrates running workloads and variants,
  producing metric summaries.
- `tests/test_experiment.py` – Unittests validating schema and basic
  behavior.

## Requirements

- Python 3.11+
- No third-party packages are required.

`requirements.txt` is intentionally empty to emphasize that only the
standard library is used.

## Running the experiment

1. Ensure you are in the project root directory.
2. Make sure the evidence directory exists (the code will also try to
   create it if needed):

   ```bash
   mkdir -p /evidence
   ```

3. Run the experiment:

   ```bash
   python run.py
   ```

4. After completion, inspect the generated evidence file:

   ```bash
   cat /evidence/results.json
   ```

The file will follow the required runtime contract:

```json
{
  "chapter": 8,
  "experiment_id": "exp-ch08-cx-agentic-support-v1",
  "environment": {"os": "...", "python": "..."},
  "runs": [
    {
      "variant": "baseline",
      "workload_id": "historical_replay_workload",
      "run_id": "...",
      "success": true,
      "metrics": {
        "avg_handle_time_minutes": 12.3,
        "cost_per_ticket": 4.56
      }
    },
    {
      "variant": "treatment",
      "workload_id": "historical_replay_workload",
      "run_id": "...",
      "success": true,
      "metrics": {
        "avg_handle_time_minutes": 9.1,
        "cost_per_ticket": 3.80
      }
    }
    // plus baseline/treatment for live_ab_workload
  ],
  "notes": "..."
}
```

Metrics are **actual** measurements derived from the simulation; no
values are fabricated.

## Running tests

Run:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The tests confirm that:

- `/evidence/results.json` exists after `run.py` is executed.
- The schema matches the required contract (types and presence of fields).
- At least one baseline and one treatment run are present per workload.
- All metric values are finite numbers.

## Design overview

### Workloads

The simulation includes two workloads mirroring the specification:

1. `historical_replay_workload` – Synthetic replay of previously
   "resolved" tickets. Here, tickets are generated deterministically with
   fixed distributions of issue types, channels, and complexity.
2. `live_ab_workload` – Synthetic simulation of a live A/B test, using
   the same generator but with different random seeds and traffic
   allocation parameters.

Each workload produces a fixed number of tickets, and **both variants**
operate on the same tickets to keep comparisons fair.

### Baseline vs. treatment

The baseline workflow simulates:

- Tier 1 vs. Tier 2 handling.
- Probabilities of escalation given ticket complexity.
- Per-step handle times (in minutes) and a blended human hourly cost.

The treatment workflow simulates:

- Triage, knowledge, resolver, and quality-review agents.
- Fraction of tickets auto-resolved vs. escalated to humans.
- Reduced human handle time due to better routing and automation.
- Additional agentic computation cost per ticket.

The parameters are chosen so that treatment generally reduces handle
time and cost per ticket, though the exact numbers depend on the random
mix of tickets.

### Metrics collected

To keep the implementation focused and deterministic, the simulation
measures a small but meaningful subset of the chapter's metrics:

- `avg_handle_time_minutes` – Average simulated active handling time per
  ticket, combining human and agentic computation (converted to minutes).
- `cost_per_ticket` – Operational cost per ticket combining human labor
  and estimated agentic cost.
- `auto_resolution_rate` – Fraction of tickets fully handled by agents
  without human edits (treatment only; omitted for baseline).
- `escalation_rate_to_human` – Fraction of treatment tickets that needed
  human intervention after agent steps (treatment only).

Metrics that require real customers or external systems (e.g., first
response time in wall-clock minutes, real CSAT/NPS, policy violation
incidents based on QA audits) are **not** reported here; doing so in this
offline sandbox would be speculative.

### Determinism

The simulation seeds Python's `random.Random` with fixed seeds per
workload to ensure reproducibility across runs. This is important for
reproducible experiments and consistent testing.

## Extensibility

Although no external integrations are used, the internal structure is
ready to be extended:

- Replace synthetic workloads with real ticket exports.
- Swap the agentic simulation with actual LLM-based agents using
  retrieval and guardrails.
- Extend metrics to compute first-contact resolution rates, CSAT, NPS,
  and policy violations when those data become available.

All such extensions can continue to write results into the same evidence
schema.
