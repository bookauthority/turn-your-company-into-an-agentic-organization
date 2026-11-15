from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .tools.ticketing_client import TicketingClient
from .tools.crm_client import CrmBillingClient
from .tools.kb_client import KnowledgeBaseClient


@dataclass
class AgentConfig:
    human_hourly_rate: float
    model_cost_per_1k_tokens: float
    edit_minor_threshold_ratio: float
    approve_confidence_threshold: float


class DraftingAgent:
    """Rule-based stand-in for an LLM-powered customer support agent.

    It implements the structured_output_schema from the experiment
    specification using deterministic logic based on ticket content
    and stubbed tools.
    """

    def __init__(
        self,
        ticketing: TicketingClient,
        crm: CrmBillingClient,
        kb: KnowledgeBaseClient,
        config: AgentConfig,
    ) -> None:
        self.ticketing = ticketing
        self.crm = crm
        self.kb = kb
        self.config = config

    def _classify(self, body: str) -> Dict[str, Any]:
        text = body.lower()
        if "invoice" in text:
            category = "invoice-copy-request"
            sub = "last-invoice" if "last" in text or "recent" in text else "invoice-history"
        elif "address" in text:
            category = "address-update-info"
            sub = "billing-address"
        elif "plan" in text or "subscription" in text:
            category = "plan-change-info" if "difference" in text or "change" in text else "account-status-info"
            sub = "plan-status"
        elif "payment" in text or "active" in text:
            category = "account-status-info"
            sub = "payment-status"
        else:
            category = "billing-question"
            sub = "generic"
        requires_handover = False
        return {
            "category": category,
            "sub_category": sub,
            "requires_handover": requires_handover,
        }

    def _build_response(self, ticket_id: str) -> Dict[str, Any]:
        ticket = self.ticketing.get_ticket(ticket_id)
        crm_summary = self.crm.get_summary(ticket.customer_email)
        kb_articles = self.kb.search(ticket.body)

        classification = self._classify(ticket.body)
        base_confidence = 0.8 if crm_summary.get("found") else 0.6
        if not kb_articles:
            base_confidence -= 0.1
        confidence = max(0.0, min(1.0, base_confidence))

        # Short resolution plan
        plan_parts: List[str] = []
        if crm_summary.get("found"):
            plan_parts.append("Used CRM summary (plan and status).")
        if kb_articles:
            plan_parts.append("Referenced KB articles: " + ", ".join(a["id"] for a in kb_articles))
        if not plan_parts:
            plan_parts.append("No structured data available; responded with general information.")
        resolution_plan = " ".join(plan_parts)

        # Simple deterministic drafting template
        greeting = "Hi there,"  # No PII
        closing = "Best regards,\nSupport Team"

        body_lower = ticket.body.lower()
        lines: List[str] = [greeting, ""]

        if classification["category"] == "invoice-copy-request":
            if crm_summary.get("found"):
                last_invoice = crm_summary.get("last_invoice_id", "your last invoice")
                lines.append(
                    f"You requested a copy of your last invoice. Based on your account, the most recent invoice is {last_invoice}. "
                    "In a production system, we would attach that invoice as a PDF."
                )
            else:
                lines.append(
                    "You requested a copy of your last invoice. I could not locate your account based on this email, "
                    "so please reply with your account ID so we can help further."
                )
        elif classification["category"] == "address-update-info":
            lines.append(
                "You asked about updating your billing address. For security, we cannot change it directly via email in this sandbox. "
                "In production, we would guide you through a secure form or settings page to update your address."
            )
            if crm_summary.get("found"):
                lines.append(
                    f"Our records currently show your billing address as: {crm_summary.get('billing_address')}."
                )
        elif classification["category"] == "plan-change-info":
            lines.append(
                "You requested information about plan options. In this sandbox we cannot change your plan, "
                "but we can describe the typical differences between basic and pro tiers."
            )
        elif classification["category"] == "account-status-info":
            if "payment" in body_lower or "received" in body_lower:
                if crm_summary.get("found") and crm_summary.get("last_payment_received"):
                    lines.append("We can confirm that your last payment was received successfully.")
                else:
                    lines.append(
                        "We were not able to confirm your last payment in this sandbox environment. In production, "
                        "an agent would verify payment status in the billing system."
                    )
            if crm_summary.get("found"):
                active = crm_summary.get("active")
                next_renewal = crm_summary.get("next_renewal_date")
                state = "active" if active else "inactive"
                lines.append(f"Your subscription is currently {state}. The next renewal date is {next_renewal}.")
        else:  # billing-question generic
            lines.append(
                "Thanks for reaching out with your billing question. In this sandbox, we provide general guidance only; "
                "in production, we would look up your specific account details."
            )

        lines.append("")
        lines.append(closing)
        response_draft = "\n".join(lines)

        tool_actions: List[Dict[str, Any]] = []
        for art in kb_articles:
            tool_actions.append(
                {
                    "tool_name": "kb_search_api",
                    "action_type": "attach_article_link",
                    "arguments": {"article_id": art["id"], "title": art["title"]},
                }
            )

        return {
            "classification": classification,
            "resolution_plan": resolution_plan,
            "response_draft": response_draft,
            "tool_actions": tool_actions,
            "confidence": confidence,
        }

    def draft_for_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """Public method used by the experiment.

        Returns the structured output schema instance as a dict.
        """

        return self._build_response(ticket_id)

    def estimate_token_usage(self, response_draft: str) -> int:
        # Very rough heuristic: assume 1 token per 4 characters.
        return max(1, len(response_draft) // 4)
