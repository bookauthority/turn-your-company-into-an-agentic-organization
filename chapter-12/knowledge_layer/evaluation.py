from __future__ import annotations

import statistics
from typing import Dict, Iterable, List, Tuple

from .agents import Answer, BaselineAgent, TreatmentAgent
from .data import Question, build_corpus, build_questions, group_questions_by_workload


def normalize_text(s: str) -> str:
    return " ".join(s.strip().lower().split())


def semantic_score(pred: str, gold: str) -> float:
    """Deterministic pseudo-semantic score between 0 and 1.

    Uses token overlap and substring checks.
    """

    p = normalize_text(pred)
    g = normalize_text(gold)
    if not p and not g:
        return 1.0
    if not p or not g:
        return 0.0
    if p == g:
        return 1.0
    if p in g or g in p:
        return 0.9
    p_tokens = set(p.split())
    g_tokens = set(g.split())
    if not g_tokens:
        return 0.0
    overlap = len(p_tokens & g_tokens) / len(g_tokens)
    # Squash into [0,1] more aggressively
    return max(0.0, min(1.0, overlap))


def compute_metrics_for_answers(
    questions: Iterable[Question],
    answers: Iterable[Answer],
    freshness: bool = False,
) -> Dict[str, float]:
    q_list = list(questions)
    a_list = list(answers)
    assert len(q_list) == len(a_list)

    n = len(q_list)
    exact_matches = 0
    semantic_scores: List[float] = []
    coverage = 0
    hallucinations = 0
    stale_count = 0

    citation_precisions: List[float] = []
    citation_recalls: List[float] = []

    q_times: List[float] = []

    for q, a in zip(q_list, a_list):
        gold = q.gold_answer_text
        exact = normalize_text(a.text) == normalize_text(gold)
        if exact:
            exact_matches += 1
        semantic = semantic_score(a.text, gold)
        semantic_scores.append(semantic)

        has_answer = bool(a.text.strip()) and not a.text.lower().startswith("i don't know")
        if has_answer:
            coverage += 1

        # Simple hallucination proxy: if we have an answer but none of the retrieved
        # docs are in the gold citations, treat as hallucinated.
        gold_cits = set(q.gold_citations)
        cited_docs = set(a.citations)
        if has_answer and gold_cits and not (cited_docs & gold_cits):
            hallucinations += 1

        # Staleness for freshness workload: if gold_answer_t1 exists and
        # the answer more closely matches t0 than t1, mark as stale.
        if freshness and q.gold_answer_t0 and q.gold_answer_t1:
            score_t0 = semantic_score(a.text, q.gold_answer_t0)
            score_t1 = semantic_score(a.text, q.gold_answer_t1)
            if score_t0 > score_t1:
                stale_count += 1

        # Citation precision/recall
        if cited_docs:
            precision = (
                len(cited_docs & gold_cits) / len(cited_docs) if cited_docs else 0.0
            )
        else:
            precision = 0.0
        if gold_cits:
            recall = len(cited_docs & gold_cits) / len(gold_cits)
        else:
            recall = 0.0
        citation_precisions.append(precision)
        citation_recalls.append(recall)

        # Total time per question (retrieval + answer) in seconds
        q_times.append((a.retrieval_latency_ms + a.answer_latency_ms) / 1000.0)

    # Aggregate metrics
    answer_exact_match_rate = exact_matches / n if n else 0.0
    answer_semantic_accuracy = sum(semantic_scores) / n if n else 0.0
    coverage_rate = coverage / n if n else 0.0
    hallucination_rate = hallucinations / n if n else 0.0
    stale_answer_rate = stale_count / n if n else 0.0

    # Percentiles for completion time
    if q_times:
        sorted_times = sorted(q_times)
        p50 = statistics.median(sorted_times)
        # Simple p90 calculation
        idx_90 = int(0.9 * (len(sorted_times) - 1))
        p90 = sorted_times[idx_90]
    else:
        p50 = 0.0
        p90 = 0.0

    citation_precision = sum(citation_precisions) / n if n else 0.0
    citation_recall = sum(citation_recalls) / n if n else 0.0

    return {
        "answer_exact_match_rate": float(answer_exact_match_rate),
        "answer_semantic_accuracy": float(answer_semantic_accuracy),
        "citation_precision": float(citation_precision),
        "citation_recall": float(citation_recall),
        "coverage_rate": float(coverage_rate),
        "hallucination_rate": float(hallucination_rate),
        "stale_answer_rate": float(stale_answer_rate),
        "task_completion_time_p50": float(p50),
        "task_completion_time_p90": float(p90),
    }


def run_full_experiment() -> Dict[Tuple[str, str], Dict[str, float]]:
    """Run baseline and treatment on all workloads.

    Returns mapping (variant, workload_id) -> metrics dict.
    """

    docs = build_corpus()
    questions = build_questions()
    grouped = group_questions_by_workload(questions)

    baseline_agent = BaselineAgent(docs)
    treatment_agent = TreatmentAgent(docs)

    results: Dict[Tuple[str, str], Dict[str, float]] = {}

    for workload_id, qs in grouped.items():
        # Baseline answers
        baseline_answers: List[Answer] = []
        for q in qs:
            baseline_answers.append(baseline_agent.answer(q))
        baseline_metrics = compute_metrics_for_answers(
            qs, baseline_answers, freshness=(workload_id == "freshness_regression_suite")
        )

        # Treatment answers
        treatment_answers: List[Answer] = []
        for q in qs:
            treatment_answers.append(treatment_agent.answer(q))
        treatment_metrics = compute_metrics_for_answers(
            qs, treatment_answers, freshness=(workload_id == "freshness_regression_suite")
        )

        results[("baseline", workload_id)] = baseline_metrics
        results[("treatment", workload_id)] = treatment_metrics

    return results
