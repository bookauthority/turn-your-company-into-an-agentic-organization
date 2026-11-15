# Chapter 12 Experiment: Knowledge Layer RAG Impact

Experiment ID: `exp-12-knowledge-layer-rag-impact-v1`

This project implements a fully offline, deterministic simulation of a knowledge-layer RAG system and evaluates baseline vs. treatment agents on multiple workloads.

## Goals

- Simulate an **agentic knowledge layer** with centralized ingestion, indexing, and retrieval.
- Compare against a baseline with **siloed per-domain indexes** and weaker retrieval.
- Measure impact on answer quality and latency metrics derived from actual execution.
- Produce reproducible evidence in `/evidence/results.json` using the exact schema required.

## Design Overview

### Synthetic Corpus and Knowledge Layer

We use small, deterministic synthetic corpora for four domains:

- Support
- Sales
- HR
- IT

Each document is structured using a shared schema-like dict with fields such as:

```python
{
  "id": "support_faq_1",
  "source_system": "support_kb",
  "source_url": "https://kb.example/support/1",
  "domain": "support",
  "doc_type": "faq",
  "title": "Resetting your password",
  "body": "...",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "owner": "support_team",
  "confidentiality_level": "public",
  "tags": ["password", "login"],
  "validity_start": "2024-01-01T00:00:00Z",
  "validity_end": None,
  "canonical_version_id": "support_faq_1_v1"
}
```

### Index and Retrieval

- **Vector representation**: simple bag-of-words vectors over a fixed vocabulary with cosine similarity (no external libraries).
- **Baseline**:
  - Independent per-domain indexes.
  - Naive retrieval: only the small domain slice is searched.
  - No metadata filtering beyond the domain.
- **Treatment**:
  - Centralized global index over all domains, plus domain+doc_type+recency filters.
  - Retrieval uses:
    - Domain filter.
    - Recency preference (higher weight for newer docs when scores tie).
    - Simple deprecation handling for superseded docs in the freshness scenario.

### QA Agents (No external LLM)

To keep the experiment offline and reproducible, the agents are simulated rule-based QA systems that:

- Retrieve top-k passages.
- Check for keyword matches related to the question.
- Construct answers and citations from the retrieved docs.

Although no real LLM is used, the structure mirrors RAG pipelines and allows measuring relative performance between baseline and treatment.

### Workloads

We implement four workloads analogous to the specification:

1. `support_faq_resolution`
2. `sales_ops_policy_and_process_lookup`
3. `hr_it_internal_service_qa`
4. `freshness_regression_suite`

Each workload has deterministic synthetic questions with:

- Question text.
- Gold answer.
- Gold citations (document IDs).

The **freshness** workload has T0 and T1 answers; the treatment uses updated documents while the baseline may continue to use stale ones depending on retrieval.

### Metrics

Within the offline sandbox, we compute numeric metrics we can genuinely measure from the executed simulation:

- `answer_exact_match_rate`: fraction of answers whose normalized text exactly matches the gold.
- `answer_semantic_accuracy`: approximated via a deterministic scoring function (substring/keyword overlap) returning [0, 1].
- `citation_precision`: fraction of cited document IDs that are in the gold citation list.
- `citation_recall`: fraction of gold citation document IDs that appear in the agent citations.
- `coverage_rate`: fraction of questions where the system returns a non-empty answer that is not an explicit "I don't know".
- `hallucination_rate`: fraction of answers that are non-empty while none of the cited docs match the gold citations.
- `stale_answer_rate`: for the freshness workload, fraction of answers that more closely match T0 instead of T1 according to the deterministic semantic score.
- `task_completion_time_p50` / `task_completion_time_p90`: median and 90th percentile of measured wall-clock execution time of each QA call in seconds, using `time.perf_counter()` around retrieval and answer construction.

`index_update_latency_p50` and `index_update_latency_p90` are **not** included as metrics in this offline experiment because there is no genuine index-update process to time. Measuring realistic update latencies would require simulating external document changes and timed ingestion processes, which are outside the current scope.

All reported metrics in `metrics` come from real, instrumented execution of the simulation.

## Files

- `run.py`: main entry point. Runs all workloads for both baseline and treatment, aggregates metrics, and writes `/evidence/results.json`.
- `knowledge_layer/`: core simulation code.
  - `__init__.py`
  - `data.py`: synthetic corpora and questions.
  - `vector_index.py`: in-memory vector index and retrieval.
  - `agents.py`: baseline and treatment QA agents.
  - `evaluation.py`: metric computation and experiment orchestration.
- `tests/test_experiment.py`: unit tests that validate the evidence schema and basic behavior.
- `requirements.txt`: empty (standard-library-only runtime).

## Running the Experiment

1. Ensure Python 3.11+.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the experiment:

   ```bash
   mkdir -p /evidence
   BOOKMAS_EVIDENCE_DIR=/evidence python run.py
   ```

4. Inspect the evidence file:

   ```bash
   cat /evidence/results.json
   ```

5. Run tests:

   ```bash
   python -m unittest discover -s tests -p "test_*.py"
   ```

## Evidence Schema

`run.py` writes a JSON file at `BOOKMAS_EVIDENCE_DIR + '/results.json'` with the following structure:

```json
{
  "chapter": 12,
  "experiment_id": "exp-12-knowledge-layer-rag-impact-v1",
  "environment": {"os": "...", "python": "..."},
  "runs": [
    {
      "variant": "baseline",
      "workload_id": "support_faq_resolution",
      "run_id": "...",
      "success": true,
      "metrics": {
        "answer_exact_match_rate": 0.8,
        "answer_semantic_accuracy": 0.9,
        "citation_precision": 1.0,
        "citation_recall": 1.0,
        "coverage_rate": 1.0,
        "hallucination_rate": 0.0,
        "stale_answer_rate": 0.0,
        "task_completion_time_p50": 0.001,
        "task_completion_time_p90": 0.002
      }
    },
    {
      "variant": "treatment",
      "workload_id": "support_faq_resolution",
      "run_id": "...",
      "success": true,
      "metrics": {"...": 0.0}
    }
  ],
  "notes": "Freeform text about the run."
}
```

All metric values are numeric (no strings, booleans, objects, or null inside `metrics`). Baseline and treatment have at least one run each per workload.

## Limitations

- No external LLM or vector DB is used; instead we simulate behavior with deterministic algorithms over synthetic data.
- Semantic accuracy and hallucination detection are simplified proxies, not human or LLM judgments.
- Index-update latency metrics are omitted because there is no real index-update process to time in this offline setup. Any discussion of index-update behavior must therefore remain qualitative, outside the numeric `metrics` object.

Despite these simplifications, the experiment fairly and reproducibly compares a siloed vs. centralized knowledge layer under controlled conditions.