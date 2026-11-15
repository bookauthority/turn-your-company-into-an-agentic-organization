from __future__ import annotations

from typing import List, Dict, Any


class KnowledgeBaseClient:
    """Very small, deterministic KB search stub.

    Instead of full-text search, we use simple keyword rules to return
    relevant article snippets.
    """

    def __init__(self) -> None:
        self._articles: List[Dict[str, Any]] = [
            {
                "id": "kb-invoice-copy",
                "title": "Sending invoice copies",
                "keywords": ["invoice", "copy", "receipt"],
                "snippet": "You can provide a PDF copy of the customer's last invoice based on their account.",
            },
            {
                "id": "kb-plan-status",
                "title": "Checking plan and renewal date",
                "keywords": ["plan", "renew", "subscription"],
                "snippet": "Agents can view the customer's current plan and next renewal date in the billing system.",
            },
            {
                "id": "kb-address-update",
                "title": "Billing address information",
                "keywords": ["address", "billing"],
                "snippet": "To update billing address, collect the new address and submit a secure change request.",
            },
            {
                "id": "kb-payment-status",
                "title": "Confirming payment receipt",
                "keywords": ["payment", "received", "active"],
                "snippet": "Verify whether the last payment was received and whether the account is active.",
            },
        ]

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        scored: List[Dict[str, Any]] = []
        for art in self._articles:
            score = 0
            for kw in art["keywords"]:
                if kw in query_lower:
                    score += 1
            if score > 0:
                scored.append({"article": art, "score": score})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return [s["article"] for s in scored[:top_k]]
