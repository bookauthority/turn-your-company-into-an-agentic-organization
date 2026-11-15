# Chapter 9 Experiment: Agentic Sales Operations and Revenue Enablement

This project is a **self-contained, offline, synthetic experiment** for:

- **Chapter:** 9 — Agentic Sales Operations and Revenue Enablement  
- **Experiment ID:** `exp-ch09-agentic-sales-ops-mas-vs-manual-v1`

It compares a synthetic **baseline (manual/semi-automated)** sales-ops workflow against a **treatment (multi-agent)** workflow. The focus is on:

- Lead enrichment and routing
- Pipeline hygiene
- Quote-to-order assistance
- Follow-up and cycle time support
- Forecasting support

The implementation is intentionally lightweight and synthetic, but wired similarly to a real CRM + agent stack. It measures **time-like administrative costs** in a deterministic way using local simulation (no real wall-clock measurement or external services).

## Contents

- `run.py` – main entry point. Runs all workloads and writes experiment evidence.
- `experiment/__init__.py` – package marker.
- `experiment/config.py` – constants and configuration (chapter, experiment ID, workloads).
- `experiment/crm_sim.py` – in-memory synthetic CRM and event store.
- `experiment/agents.py` – baseline vs. agentic behaviors and simple orchestration.
- `experiment/metrics.py` – metric computation helpers and evidence-structure builder.
- `experiment/random_utils.py` – deterministic random utilities based on fixed seeds.
- `tests/test_experiment.py` – unit tests checking evidence schema and basic properties.

## How the Simulation Works

The code runs fully offline, using only the Python standard library.

### Synthetic CRM Model

`experiment/crm_sim.py` defines a simple in-memory model for:

- **Leads**
- **Opportunities**
- **Quotes**
- **Events** (lead/opportunity lifecycle events)
- **Actions Log** (human/agent actions with synthetic durations and costs)

This mirrors the evidence schema (e.g., `actions_log`, `lead_and_opportunity_events`) but is held purely in memory for this experiment run.

### Workloads

The experiment covers five workloads:

1. `Lead_Enrichment_and_Routing`
2. `Pipeline_Hygiene`
3. `Quote_to_Order_Assistance`
4. `Followup_and_Cycle_Time`
5. `Forecasting_Support`

Each workload is run **twice**:

- **baseline** variant with manual-style logic
- **treatment** variant with simplified multi-agent logic

All randomness is driven by deterministic seeds so that the experiment is completely repeatable.

### Metrics

In a real deployment the full metric set (admin hours, response times, quote error rates, forecast errors, etc.) would be measured from real timestamps and logs. In this offline synthetic environment we:

- Implement **time-like metrics** using **synthetic durations** associated with each action.
- Use the same metric names for a subset that we can meaningfully simulate.
- Provide **per-workload metrics** that are clearly derived from executed code.

For each workload run, we report at least one numeric metric that is derived from the simulation. Metrics are **never fabricated**: they come from computed values inside the run.

Examples of metrics produced (depending on workload):

- `admin_hours_per_opportunity`
- `lead_enrichment_time_per_lead`
- `routing_decision_time_per_lead`
- `quote_cycle_time`
- `forecast_absolute_error`
- `system_cost_per_record`

Some metrics from the chapter spec that require real user actions or wall-clock timings (e.g., real lead-response time to genuine emails, true user trust scores, real API cost) are not measured here; they are omitted from the per-run `metrics` objects.

## Evidence Contract

Running `python run.py` will:

1. Execute each workload for **baseline** and **treatment** variants.
2. Compute a small set of numeric metrics for each run.
3. Write a JSON file to the directory given by `$BOOKMAS_EVIDENCE_DIR` (default `/evidence`) at path:

```text
/evidence/results.json
```

with this exact top-level structure:

```json
{
  "chapter": 9,
  "experiment_id": "exp-ch09-agentic-sales-ops-mas-vs-manual-v1",
  "environment": {"os": "...", "python": "..."},
  "runs": [
    {
      "variant": "baseline" | "treatment",
      "workload_id": "<workload stable id>",
      "run_id": "<unique string>",
      "success": true,
      "metrics": {"some_metric": 1.23, "another_metric": 4.56}
    }
  ],
  "notes": "optional explanatory text"
}
```

### Requirements Enforced by Tests

The tests in `tests/test_experiment.py` assert that:

- `results.json` exists in the evidence directory.
- The JSON is well-formed and matches the contract above.
- `chapter` is the integer `9`.
- `experiment_id` is exactly `exp-ch09-agentic-sales-ops-mas-vs-manual-v1`.
- `environment.os` and `environment.python` are strings.
- For each workload_id there is **at least one** `baseline` and at least one `treatment` run.
- For each run:
  - `variant` ∈ {`baseline`, `treatment`}
  - `workload_id` and `run_id` are strings
  - `success` is a boolean
  - `metrics` exists and is a dict mapping strings to **finite numeric values**

The tests use **only Python standard library** (`unittest`, `json`, `os`, etc.).

## Running the Experiment

From the project root:

1. **Run the experiment**

```bash
python run.py
```

Optionally specify a custom evidence directory:

```bash
BOOKMAS_EVIDENCE_DIR=/tmp/evidence python run.py
```

This will generate `/tmp/evidence/results.json` (or `/evidence/results.json` if not overridden).

2. **Run the tests**

```bash
python -m unittest discover -s tests -p "test_*.py"
```

This validates the evidence file and basic invariants.

## Limitations

- The CRM, agents, and workloads are **simplified synthetic models**. They are not connected to real CRMs, queues, or LLMs.
- Time/cost values are **synthetic durations and costs** attached to actions, not real wall-clock or external billing.
- Many rich behaviors described in the chapter (e.g., real human approval flows, bi-directional integrations, user trust surveys) are represented only in structure/logs, not as real external integrations.

Despite these limits, the project demonstrates a reproducible pattern for:

- Experimental assignment (baseline vs. treatment)
- Multi-agent orchestration vs. manual workflows
- Evidence logging and metric calculation

and can be adapted to real CRM and agentic deployments with appropriate connectors and security.
