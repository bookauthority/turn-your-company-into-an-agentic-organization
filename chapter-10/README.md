# Chapter 10 Experiment – Finance, Accounting, and Procurement: Agents in High-Control Domains

This project implements a **fully offline, deterministic** experiment for:

> **exp-ch10-finance-ap-procurement-v1** – Finance, Accounting, and Procurement: Agents in High-Control Domains

It simulates baseline (human-only) vs. treatment (agent-assisted) workflows for:

- Invoice processing
- PO creation
- Reconciliations
- Spend analysis

The implementation:

- Uses only the Python standard library (no external runtime dependencies).
- Generates small, deterministic synthetic datasets for each workload.
- Implements simple baseline and treatment processors per workload.
- Measures **processing latency** (wall-clock seconds) for baseline and treatment runs, with identical workloads.
- Writes evidence to `/evidence/results.json` (or `$BOOKMAS_EVIDENCE_DIR/results.json`) following the required schema.

This is a *toy but faithful* implementation of high-control agent patterns:

- Treatment variants simulate agents with strict tools and guardrails, but no network or external services.
- Baseline variants perform equivalent work using simpler, less structured logic.
- Both operate over the same deterministic synthetic data for fair comparison.

## Project Layout

- `run.py` – Entry point; runs the experiment and writes evidence JSON.
- `experiment/__init__.py` – Package marker.
- `experiment/config.py` – Constants for chapter, experiment ID, workloads.
- `experiment/data.py` – Deterministic synthetic data generators for all workloads.
- `experiment/metrics.py` – Simple metric measurement utilities.
- `experiment/baseline.py` – Baseline workflow implementations.
- `experiment/treatment.py` – Agentic (treatment) workflow implementations.
- `experiment/runner.py` – Orchestrates experiment runs and evidence assembly.
- `tests/test_experiment.py` – Unit tests that run the experiment and validate the evidence schema.
- `requirements.txt` – Empty of runtime dependencies (standard library only).

## Running the Experiment

1. **Ensure Python 3.11+ is available.**

2. **Install dependencies** (none beyond the standard library, but this is a no-op placeholder):

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the experiment**:

   ```bash
   python run.py
   ```

   This will:

   - Generate small synthetic datasets for four workloads.
   - Run **baseline** and **treatment** variants for each workload ID.
   - Measure at least one numeric metric (`processing_latency_seconds`) per run.
   - Write evidence JSON to:
     - `$BOOKMAS_EVIDENCE_DIR/results.json` if `BOOKMAS_EVIDENCE_DIR` is set, otherwise
     - `/evidence/results.json`.

4. **Inspect the evidence** (example):

   ```bash
   cat /evidence/results.json
   ```

   The file will contain a JSON object:

   ```json
   {
     "chapter": 10,
     "experiment_id": "exp-ch10-finance-ap-procurement-v1",
     "environment": {
       "os": "...",
       "python": "3.11.x"
     },
     "runs": [
       {
         "variant": "baseline",
         "workload_id": "dataset-invoices-v1",
         "run_id": "baseline-dataset-invoices-v1-0",
         "success": true,
         "metrics": {
           "processing_latency_seconds": 0.0123
         }
       },
       {
         "variant": "treatment",
         "workload_id": "dataset-invoices-v1",
         "run_id": "treatment-dataset-invoices-v1-0",
         "success": true,
         "metrics": {
           "processing_latency_seconds": 0.0098
         }
       }
       // ... more runs for other workloads
     ],
     "notes": "..."
   }
   ```

## Running Tests

Execute the unit tests with:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The tests will:

- Invoke `run.py` within the same interpreter.
- Load `/evidence/results.json` (or `$BOOKMAS_EVIDENCE_DIR/results.json`).
- Validate that the schema matches the required contract:
  - `chapter` (int), `experiment_id` (str), `environment` (os+python), `runs` (list), optional `notes`.
  - At least one **baseline** and one **treatment** run per workload ID.
  - Every run has numeric metrics; all metric values are finite numbers.

## Design Notes – High-Control Agent Patterns

Although this sandboxed project cannot integrate with real ERP/AP systems or LLM APIs, it mirrors the **patterns** described in the specification:

- **Strict tools and schemas** – Treatment processors use more structured data flows (e.g., separating parsing, policy checks, coding suggestions).
- **Guardrails** – Agents never commit or approve; they only propose derived values on the synthetic data, echoing segregation of duties.
- **Auditability** – While full audit logs are not persisted, the experiment captures deterministic metrics and variant tags adequate for reproducible comparison.
- **Reproducibility** – All randomness is seeded (`random.seed(42)`), no clocks are used to generate non-deterministic IDs, and environment details are recorded in the evidence.

In a real deployment, these components would wrap actual ERP/AP tools, OCR, approval chains, and audit storage, but many of the safety and control ideas can be prototyped and reasoned about using this minimal framework.
