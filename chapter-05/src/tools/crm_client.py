from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class CustomerRecord:
    email: str
    name: str
    plan: str
    active: bool
    next_renewal_date: str
    last_invoice_id: str
    last_payment_received: bool
    billing_address: str


class CrmBillingClient:
    """Stubbed CRM/Billing read-only client.

    This client returns synthetic customer and subscription data.
    """

    def __init__(self, records: Dict[str, CustomerRecord]):
        self._records = records

    def lookup_by_email(self, email: str) -> CustomerRecord | None:
        return self._records.get(email)

    def get_summary(self, email: str) -> Dict[str, Any]:
        rec = self.lookup_by_email(email)
        if rec is None:
            return {"found": False}
        return {
            "found": True,
            "email": rec.email,
            "name": rec.name,
            "plan": rec.plan,
            "active": rec.active,
            "next_renewal_date": rec.next_renewal_date,
            "last_invoice_id": rec.last_invoice_id,
            "last_payment_received": rec.last_payment_received,
            "billing_address": rec.billing_address,
        }
