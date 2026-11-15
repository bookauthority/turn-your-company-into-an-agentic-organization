from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from .data import Document, Question
from .vector_index import VectorIndex, tokenize


@dataclass
class RetrievedDoc:
    document_id: str
    score: float
    rank: int


@dataclass
class Answer:
    text: str
    citations: List[str]
    retrieved_docs: List[RetrievedDoc]
    retrieval_latency_ms: float
    answer_latency_ms: float


class BaselineAgent:
    """Baseline agent using per-domain indexes and naive retrieval.

    - Siloed domain indexes.
    - No special handling of document versions or freshness.
    """

    def __init__(self, docs: Iterable[Document]) -> None:
        self._docs_by_domain: Dict[str, List[Document]] = {}
        for d in docs:
            self._docs_by_domain.setdefault(d.domain, []).append(d)
        self._index_by_domain: Dict[str, VectorIndex] = {
            domain: VectorIndex(dlist) for domain, dlist in self._docs_by_domain.items()
        }

    def answer(self, question: Question, top_k: int = 3) -> Answer:
        # retrieval
        t0 = time.perf_counter()
        index = self._index_by_domain[question.domain]
        scored = index.search(query=question.question_text, top_k=top_k, domain=question.domain)
        t1 = time.perf_counter()

        retrieved_docs: List[RetrievedDoc] = [
            RetrievedDoc(document_id=d.id, score=s, rank=i + 1) for i, (d, s) in enumerate(scored)
        ]

        # Simple rule-based answer generation: choose best doc body
        if not scored:
            answer_text = "I don't know based on the available documentation."
            citations: List[str] = []
        else:
            # Baseline: just repeat the doc body of best match
            best_doc, _ = scored[0]
            answer_text = best_doc.body
            citations = [best_doc.id]

        t2 = time.perf_counter()

        return Answer(
            text=answer_text,
            citations=citations,
            retrieved_docs=retrieved_docs,
            retrieval_latency_ms=(t1 - t0) * 1000.0,
            answer_latency_ms=(t2 - t1) * 1000.0,
        )


class TreatmentAgent:
    """Treatment agent using centralized knowledge layer and metadata-aware retrieval.

    - Single global index over all documents.
    - Domain, doc_type, and simple freshness handling.
    - Deprecation behavior for superseded docs via canonical_version_id and validity_end.
    """

    def __init__(self, docs: Iterable[Document]) -> None:
        self._all_docs: List[Document] = list(docs)
        self._index = VectorIndex(self._all_docs)

        # Map canonical_version_id -> most recent doc id
        latest_by_canonical: Dict[str, Tuple[str, str]] = {}
        for d in self._all_docs:
            if d.canonical_version_id is None:
                continue
            current = latest_by_canonical.get(d.canonical_version_id)
            if current is None or d.updated_at > current[1]:
                latest_by_canonical[d.canonical_version_id] = (d.id, d.updated_at)
        self._deprecated_ids = set()
        for d in self._all_docs:
            if d.canonical_version_id is None:
                continue
            latest_id, _ = latest_by_canonical[d.canonical_version_id]
            if d.id != latest_id:
                self._deprecated_ids.add(d.id)

    def _doc_type_filter_for_workload(self, workload: str, domain: str) -> List[str] | None:
        if workload == "sales_ops_policy_and_process_lookup" and domain == "sales":
            return ["pricing_policy", "approval_matrix"]
        if workload == "hr_it_internal_service_qa" and domain in {"hr", "it"}:
            return ["policy", "runbook"]
        return None

    def answer(self, question: Question, top_k: int = 3) -> Answer:
        t0 = time.perf_counter()
        # Avoid deprecated docs when possible
        doc_type_filter = self._doc_type_filter_for_workload(question.workload, question.domain)
        scored = self._index.search(
            query=question.question_text,
            top_k=top_k + len(self._deprecated_ids),
            domain=question.domain,
            doc_type_filter=doc_type_filter,
            prefer_recent=True,
            exclude_ids=self._deprecated_ids,
        )

        # If no results, relax exclusions
        if not scored:
            scored = self._index.search(
                query=question.question_text,
                top_k=top_k,
                domain=question.domain,
                doc_type_filter=doc_type_filter,
                prefer_recent=True,
            )

        # Trim to top_k
        scored = scored[:top_k]
        t1 = time.perf_counter()

        retrieved_docs: List[RetrievedDoc] = [
            RetrievedDoc(document_id=d.id, score=s, rank=i + 1) for i, (d, s) in enumerate(scored)
        ]

        if not scored:
            answer_text = "I don't know based on the available documentation."
            citations: List[str] = []
        else:
            # Build an answer summarizing relevant docs: for simplicity, concatenate
            pieces: List[str] = []
            citations = []
            question_tokens = set(tokenize(question.question_text))
            for d, _ in scored:
                body_tokens = set(tokenize(d.body))
                if question_tokens & body_tokens:
                    pieces.append(d.body)
                    citations.append(d.id)
            if not pieces:
                # fallback to best doc body
                best_doc, _ = scored[0]
                pieces.append(best_doc.body)
                citations.append(best_doc.id)
            answer_text = " ".join(pieces)

        t2 = time.perf_counter()

        return Answer(
            text=answer_text,
            citations=citations,
            retrieved_docs=retrieved_docs,
            retrieval_latency_ms=(t1 - t0) * 1000.0,
            answer_latency_ms=(t2 - t1) * 1000.0,
        )
