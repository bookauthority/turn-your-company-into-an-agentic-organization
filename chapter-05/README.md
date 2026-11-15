# Chapter 5 – Standing Up Your First Production-Ready Agent

This is a self-contained Python 3.11+ experiment project for:

- **Chapter**: 5 – "Standing Up Your First Production-Ready Agent"
- **Experiment ID**: `ch05-prod-agent-001-manual-vs-agentic`

The project simulates a production-style workflow for low-complexity billing and account inquiries. It includes:

- A **baseline** (manual) process that handles tickets without agent assistance.
- A **treatment** (agentic) process with an agent that drafts responses using stubbed tools and a human-in-the-loop (HITL) review step.
- Structured logging and a small metrics pipeline to compare manual vs. agentic performance on synthetic data.

The code is fully offline, uses only the Python standard library, and writes experimental evidence conforming to the specified schema.

---

## Project Layout

```text
.
├── README.md
├── requirements.txt
├── run.py
├── config
│   ├── agent_config.yaml
│   └── routing_config.yaml
├── data
│   └── synthetic_tickets.csv
├── src
│   ├── __init__.py
│   ├── agent.py
│   ├── experiment.py
│   ├── hitl_ui_stub.py
│   ├── logging_utils.py
│   ├── metrics.py
│   ├── routing.py
│   ├── simulation.py
│   └── tools
│       ├── __init__.py
│       ├── crm_client.py
│       ├── kb_client.py
│       └── ticketing_client.py
└── tests
    ├── __init__.py
    └── test_experiment.py
```

- **`config/agent_config.yaml`** – Agent configuration (model params, tool availability, prompts summary).
- **`config/routing_config.yaml`** – Ticket randomization and lane assignment configuration.
- **`data/synthetic_tickets.csv`** – Synthetic customer tickets used as the workload.
- **`src/agent.py`** – Agent implementation with structured outputs and tool stubs.
- **`src/tools/*.py`** – Stubbed integrations for ticketing, CRM/billing, and KB search.
- **`src/hitl_ui_stub.py`** – Human-in-the-loop review flow simulation.
- **`src/simulation.py`** – End-to-end workflow simulation for both baseline and treatment lanes.
- **`src/metrics.py`** – Metric computation utilities.
- **`src/experiment.py`** – Orchestrates the experiment and produces run-level metrics.
- **`run.py`** – Entry point that runs the experiment and writes evidence to `/evidence/results.json` (or `BOOKMAS_EVIDENCE_DIR`).
- **`tests/test_experiment.py`** – Unit tests that validate the evidence schema and core invariants.

---

## How the Simulation Works

This repository does **not** connect to real ticketing or CRM systems. Instead, it uses deterministic synthetic data and stubbed tools to model the experimental design:

1. **Synthetic Tickets**  
   `data/synthetic_tickets.csv` contains a small, fixed set of synthetic tickets representing "low-complexity billing and account inquiries".

2. **Randomization & Routing**  
   `src/routing.py` assigns tickets to:
   - `manual_baseline` lane, or
   - `agentic_treatment` lane

   based on a simple hash of the ticket ID (simulating per-ticket randomization).

3. **Baseline (Manual) Processing**  
   `src/simulation.py` simulates a human agent reading the ticket and composing a response without AI assistance. Latencies are modeled deterministically from ticket text length.

4. **Agentic Treatment Processing**  
   - The agent (`src/agent.py`) reads the ticket and calls stubbed tools:
     - `ticketing_client` – returns synthetic ticket metadata.
     - `crm_client` – returns synthetic customer and billing summaries.
     - `kb_client` – returns predefined KB snippets.
   - The agent produces a **structured output** with fields:
     - `classification` (category, sub_category, requires_handover)
     - `resolution_plan`
     - `response_draft`
     - `tool_actions`
     - `confidence`
   - `src/hitl_ui_stub.py` simulates a human reviewer who either approves as-is, lightly edits, or rejects/handles manually, based on simple deterministic rules.

5. **Instrumentation & Metrics**  
   - `src/logging_utils.py` defines in-memory data structures matching the `ticket_record`, `agent_interaction_record`, and `config_record` schemas.
   - `src/metrics.py` computes per-run numeric metrics such as:
     - `handling_time_first_response`
     - `agent_draft_latency`
     - `labor_time_per_ticket`
     - `labor_cost_per_ticket`
     - `model_cost_per_ticket`
     - `total_variable_cost_per_ticket`
   - `src/experiment.py` aggregates these into **run-level** metrics for a single workload.

6. **Evidence Writing**  
   `run.py` runs the experiment once and writes `/evidence/results.json` (or `BOOKMAS_EVIDENCE_DIR/results.json`) with the exact required structure:

   ```json
   {
     "chapter": 5,
     "experiment_id": "ch05-prod-agent-001-manual-vs-agentic",
     "environment": {"os": "...", "python": "..."},
     "runs": [
       {
         "variant": "baseline",
         "workload_id": "low_complexity_billing_account_inquiries",
         "run_id": "baseline-...",
         "success": true,
         "metrics": {
           "handling_time_first_response_median": 12.3,
           "labor_cost_per_ticket_mean": 0.45,
           "total_variable_cost_per_ticket_mean": 0.45
         }
       },
       {
         "variant": "treatment",
         "workload_id": "low_complexity_billing_account_inquiries",
         "run_id": "treatment-...",
         "success": true,
         "metrics": {
           "handling_time_first_response_median": 7.8,
           "agent_draft_latency_mean": 0.5,
           "labor_cost_per_ticket_mean": 0.30,
           "model_cost_per_ticket_mean": 0.05,
           "total_variable_cost_per_ticket_mean": 0.35
         }
       }
     ],
     "notes": "..."
   }
   ```

   Metric values are computed from the simulated processing logic; they are **not fabricated constants**.

---

## Running the Experiment

### Prerequisites

- Python **3.11+**
- No external dependencies; everything uses the standard library.

### Install (nothing to install)

`requirements.txt` is intentionally empty of runtime dependencies. You may create a virtual environment and activate it:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate    # Windows
```

### Run

From the project root, run:

```bash
python run.py
```

By default, this writes evidence to `/evidence/results.json`. To override, set `BOOKMAS_EVIDENCE_DIR`:

```bash
export BOOKMAS_EVIDENCE_DIR=/tmp/evidence
mkdir -p "$BOOKMAS_EVIDENCE_DIR"
python run.py
cat "$BOOKMAS_EVIDENCE_DIR/results.json"
```

### Run Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The tests validate:

- Evidence file exists and is valid JSON.
- Schema fields and types (including metrics) match the contract.
- Both baseline and treatment runs are present for the workload.

---

## Limitations of the Offline Simulation

- No real PII, ticketing, or CRM data is used; all data is synthetic.
- Some metrics from the book specification (e.g., CSAT, QA scores) require human data and are **not** computed here. They are therefore omitted from `metrics` in the evidence.
- Time-based metrics are derived from deterministic heuristics (based on ticket length and lane) to allow reproducible comparisons without wall-clock timing.

This repository is meant as a **template** and teaching artifact for building a first production-ready agent with sound experimental design, not as a drop-in production system.