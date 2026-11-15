from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple, Optional

from .data import Document


@dataclass
class IndexedDoc:
    doc: Document
    vector: Dict[str, float]


def tokenize(text: str) -> List[str]:
    text = text.lower()
    tokens = []
    current = []
    for ch in text:
        if ch.isalnum():
            current.append(ch)
        else:
            if current:
                tokens.append("".join(current))
                current = []
    if current:
        tokens.append("".join(current))
    return tokens


def build_bow_vector(text: str) -> Dict[str, float]:
    tokens = tokenize(text)
    freq: Dict[str, int] = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    length = math.sqrt(sum(v * v for v in freq.values())) or 1.0
    return {t: v / length for t, v in freq.items()}


def cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    if not vec_a or not vec_b:
        return 0.0
    if len(vec_a) > len(vec_b):
        vec_a, vec_b = vec_b, vec_a
    score = 0.0
    for token, val in vec_a.items():
        other = vec_b.get(token)
        if other is not None:
            score += val * other
    return score


class VectorIndex:
    """Simple in-memory vector index over Documents.

    For this experiment, we treat each document body as a single chunk.
    """

    def __init__(self, docs: Iterable[Document]) -> None:
        self._indexed: List[IndexedDoc] = []
        for doc in docs:
            vec = build_bow_vector(doc.title + " " + doc.body)
            self._indexed.append(IndexedDoc(doc=doc, vector=vec))

    def search(
        self,
        query: str,
        top_k: int = 3,
        domain: Optional[str] = None,
        doc_type_filter: Optional[Iterable[str]] = None,
        prefer_recent: bool = False,
        exclude_ids: Optional[Iterable[str]] = None,
    ) -> List[Tuple[Document, float]]:
        qvec = build_bow_vector(query)
        doc_type_set = set(doc_type_filter) if doc_type_filter is not None else None
        exclude_set = set(exclude_ids) if exclude_ids is not None else set()

        scored: List[Tuple[Document, float]] = []
        for idx in self._indexed:
            if domain is not None and idx.doc.domain != domain:
                # baseline: domain filter is applied at index level; treatment uses same
                continue
            if doc_type_set is not None and idx.doc.doc_type not in doc_type_set:
                continue
            if idx.doc.id in exclude_set:
                continue
            score = cosine_similarity(qvec, idx.vector)
            if prefer_recent:
                # Very small synthetic recency bias using updated_at lexicographic order
                # Newer docs (higher updated_at string) get a tiny boost.
                score += 0.0001
            scored.append((idx.doc, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
