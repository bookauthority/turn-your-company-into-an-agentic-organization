from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Document:
    id: str
    source_system: str
    source_url: str
    domain: str
    doc_type: str
    title: str
    body: str
    created_at: str
    updated_at: str
    owner: str
    confidentiality_level: str
    tags: Tuple[str, ...]
    validity_start: str
    validity_end: str | None
    canonical_version_id: str | None


@dataclass(frozen=True)
class Question:
    question_id: str
    workload: str
    domain: str
    question_text: str
    gold_answer_text: str
    gold_citations: Tuple[str, ...]
    # For freshness workload only
    gold_answer_t0: str | None = None
    gold_answer_t1: str | None = None


def _mk_doc(
    id: str,
    source_system: str,
    source_url: str,
    domain: str,
    doc_type: str,
    title: str,
    body: str,
    created_at: str,
    updated_at: str,
    owner: str,
    confidentiality_level: str,
    tags: List[str],
    validity_start: str,
    validity_end: str | None,
    canonical_version_id: str | None,
) -> Document:
    return Document(
        id=id,
        source_system=source_system,
        source_url=source_url,
        domain=domain,
        doc_type=doc_type,
        title=title,
        body=body,
        created_at=created_at,
        updated_at=updated_at,
        owner=owner,
        confidentiality_level=confidentiality_level,
        tags=tuple(tags),
        validity_start=validity_start,
        validity_end=validity_end,
        canonical_version_id=canonical_version_id,
    )


def build_corpus() -> List[Document]:
    """Build a small synthetic multi-domain corpus.

    Includes support, sales, HR, IT, and versions for freshness experiments.
    """

    docs: List[Document] = []

    # Support
    docs.append(
        _mk_doc(
            id="support_faq_password_reset",
            source_system="support_kb",
            source_url="https://kb.example/support/password_reset",
            domain="support",
            doc_type="faq",
            title="Resetting your password",
            body=(
                "To reset your password, go to the login page, click 'Forgot password', "
                "and follow the email instructions. If you still cannot log in, contact "
                "support with your account email and last 4 digits of your phone number."
            ),
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
            owner="support_team",
            confidentiality_level="public",
            tags=["password", "login", "account"],
            validity_start="2024-01-01T00:00:00Z",
            validity_end=None,
            canonical_version_id="support_faq_password_reset_v1",
        )
    )

    docs.append(
        _mk_doc(
            id="support_troubleshooting_slow_app",
            source_system="support_kb",
            source_url="https://kb.example/support/slow_app",
            domain="support",
            doc_type="runbook",
            title="Troubleshooting a slow application",
            body=(
                "If the application is slow, first check the status page. If there are "
                "no incidents, ask the user to clear cache and restart the app. "
                "Collect logs if the problem persists."
            ),
            created_at="2024-01-05T00:00:00Z",
            updated_at="2024-01-05T00:00:00Z",
            owner="support_team",
            confidentiality_level="internal",
            tags=["performance", "latency"],
            validity_start="2024-01-05T00:00:00Z",
            validity_end=None,
            canonical_version_id="support_troubleshooting_slow_app_v1",
        )
    )

    # Sales - pricing and discounts
    docs.append(
        _mk_doc(
            id="sales_pricing_standard",
            source_system="sales_policies",
            source_url="https://kb.example/sales/pricing_standard",
            domain="sales",
            doc_type="pricing_policy",
            title="Standard pricing policy",
            body=(
                "Standard list price is $100 per seat per month. Annual contracts "
                "receive a 10 percent discount. Currency is USD unless specified."
            ),
            created_at="2024-02-01T00:00:00Z",
            updated_at="2024-02-01T00:00:00Z",
            owner="revops_team",
            confidentiality_level="internal",
            tags=["pricing", "standard"],
            validity_start="2024-02-01T00:00:00Z",
            validity_end=None,
            canonical_version_id="sales_pricing_standard_v1",
        )
    )

    docs.append(
        _mk_doc(
            id="sales_discount_approval_matrix_v1",
            source_system="sales_policies",
            source_url="https://kb.example/sales/discount_approval_v1",
            domain="sales",
            doc_type="approval_matrix",
            title="Discount approval matrix v1",
            body=(
                "For discounts up to 10 percent, sales managers can approve. "
                "For discounts between 10 and 25 percent, director approval is required. "
                "Discounts above 25 percent need VP approval."
            ),
            created_at="2024-02-10T00:00:00Z",
            updated_at="2024-02-10T00:00:00Z",
            owner="revops_team",
            confidentiality_level="internal",
            tags=["discount", "approval", "matrix"],
            validity_start="2024-02-10T00:00:00Z",
            validity_end="2024-06-01T00:00:00Z",
            canonical_version_id="sales_discount_approval_matrix",
        )
    )

    docs.append(
        _mk_doc(
            id="sales_discount_approval_matrix_v2",
            source_system="sales_policies",
            source_url="https://kb.example/sales/discount_approval_v2",
            domain="sales",
            doc_type="approval_matrix",
            title="Discount approval matrix v2",
            body=(
                "For discounts up to 15 percent, sales managers can approve. "
                "For discounts between 15 and 30 percent, director approval is required. "
                "Discounts above 30 percent need VP approval."
            ),
            created_at="2024-06-01T00:00:00Z",
            updated_at="2024-06-01T00:00:00Z",
            owner="revops_team",
            confidentiality_level="internal",
            tags=["discount", "approval", "matrix", "updated"],
            validity_start="2024-06-01T00:00:00Z",
            validity_end=None,
            canonical_version_id="sales_discount_approval_matrix",
        )
    )

    # HR
    docs.append(
        _mk_doc(
            id="hr_policy_pto_v1",
            source_system="hr_kb",
            source_url="https://kb.example/hr/pto_v1",
            domain="hr",
            doc_type="policy",
            title="Paid time off policy v1",
            body=(
                "Employees accrue 15 days of paid time off per year. "
                "Unused days can roll over up to 5 days."
            ),
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
            owner="hr_team",
            confidentiality_level="internal",
            tags=["pto", "vacation"],
            validity_start="2024-01-01T00:00:00Z",
            validity_end="2024-07-01T00:00:00Z",
            canonical_version_id="hr_policy_pto",
        )
    )

    docs.append(
        _mk_doc(
            id="hr_policy_pto_v2",
            source_system="hr_kb",
            source_url="https://kb.example/hr/pto_v2",
            domain="hr",
            doc_type="policy",
            title="Paid time off policy v2",
            body=(
                "Employees accrue 20 days of paid time off per year. "
                "Unused days can roll over up to 10 days."
            ),
            created_at="2024-07-01T00:00:00Z",
            updated_at="2024-07-01T00:00:00Z",
            owner="hr_team",
            confidentiality_level="internal",
            tags=["pto", "vacation", "updated"],
            validity_start="2024-07-01T00:00:00Z",
            validity_end=None,
            canonical_version_id="hr_policy_pto",
        )
    )

    # IT
    docs.append(
        _mk_doc(
            id="it_runbook_vpn_setup",
            source_system="it_runbooks",
            source_url="https://kb.example/it/vpn_setup",
            domain="it",
            doc_type="runbook",
            title="VPN setup",
            body=(
                "To set up VPN, install the corporate VPN client, enter your "
                "company email, and authenticate with your SSO credentials. "
                "For mobile devices, use the companion app."
            ),
            created_at="2024-03-01T00:00:00Z",
            updated_at="2024-03-01T00:00:00Z",
            owner="it_team",
            confidentiality_level="internal",
            tags=["vpn", "network"],
            validity_start="2024-03-01T00:00:00Z",
            validity_end=None,
            canonical_version_id="it_runbook_vpn_setup_v1",
        )
    )

    docs.append(
        _mk_doc(
            id="it_policy_password_v1",
            source_system="it_policies",
            source_url="https://kb.example/it/password_policy_v1",
            domain="it",
            doc_type="policy",
            title="Password policy v1",
            body=(
                "Passwords must be at least 8 characters long and include "
                "a number and a special character. Passwords expire every 90 days."
            ),
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
            owner="it_team",
            confidentiality_level="internal",
            tags=["password", "security"],
            validity_start="2024-01-01T00:00:00Z",
            validity_end="2024-05-01T00:00:00Z",
            canonical_version_id="it_policy_password",
        )
    )

    docs.append(
        _mk_doc(
            id="it_policy_password_v2",
            source_system="it_policies",
            source_url="https://kb.example/it/password_policy_v2",
            domain="it",
            doc_type="policy",
            title="Password policy v2",
            body=(
                "Passwords must be at least 12 characters long and include "
                "a number, a special character, and an uppercase letter. "
                "Passwords expire every 120 days."
            ),
            created_at="2024-05-01T00:00:00Z",
            updated_at="2024-05-01T00:00:00Z",
            owner="it_team",
            confidentiality_level="internal",
            tags=["password", "security", "updated"],
            validity_start="2024-05-01T00:00:00Z",
            validity_end=None,
            canonical_version_id="it_policy_password",
        )
    )

    return docs


def build_questions() -> List[Question]:
    """Return synthetic questions for all workloads."""

    qs: List[Question] = []

    # Support FAQ resolution
    qs.append(
        Question(
            question_id="support_q1",
            workload="support_faq_resolution",
            domain="support",
            question_text="How do I reset my password?",
            gold_answer_text=(
                "To reset your password, go to the login page, click 'Forgot password', "
                "and follow the email instructions. If you still cannot log in, contact "
                "support with your account email and last 4 digits of your phone number."
            ),
            gold_citations=("support_faq_password_reset",),
        )
    )

    qs.append(
        Question(
            question_id="support_q2",
            workload="support_faq_resolution",
            domain="support",
            question_text="What should I do if the app is very slow?",
            gold_answer_text=(
                "If the application is slow, first check the status page. If there are "
                "no incidents, ask the user to clear cache and restart the app. "
                "Collect logs if the problem persists."
            ),
            gold_citations=("support_troubleshooting_slow_app",),
        )
    )

    # Sales ops
    qs.append(
        Question(
            question_id="sales_q1",
            workload="sales_ops_policy_and_process_lookup",
            domain="sales",
            question_text="What is the standard list price per seat per month?",
            gold_answer_text="Standard list price is $100 per seat per month.",
            gold_citations=("sales_pricing_standard",),
        )
    )

    qs.append(
        Question(
            question_id="sales_q2",
            workload="sales_ops_policy_and_process_lookup",
            domain="sales",
            question_text=(
                "Who can approve a 20 percent discount according to the latest policy?"
            ),
            gold_answer_text=(
                "According to the latest discount approval matrix, a 20 percent discount "
                "requires director approval."
            ),
            gold_citations=("sales_discount_approval_matrix_v2",),
        )
    )

    # HR/IT internal service QA
    qs.append(
        Question(
            question_id="hr_q1",
            workload="hr_it_internal_service_qa",
            domain="hr",
            question_text="How many days of paid time off do employees accrue per year now?",
            gold_answer_text=(
                "Employees accrue 20 days of paid time off per year. Unused days can roll "
                "over up to 10 days."
            ),
            gold_citations=("hr_policy_pto_v2",),
        )
    )

    qs.append(
        Question(
            question_id="it_q1",
            workload="hr_it_internal_service_qa",
            domain="it",
            question_text="How do I set up the corporate VPN?",
            gold_answer_text=(
                "To set up VPN, install the corporate VPN client, enter your company "
                "email, and authenticate with your SSO credentials. For mobile devices, "
                "use the companion app."
            ),
            gold_citations=("it_runbook_vpn_setup",),
        )
    )

    # Freshness regression suite: questions sensitive to T0 vs T1
    qs.append(
        Question(
            question_id="fresh_sales_discount",
            workload="freshness_regression_suite",
            domain="sales",
            question_text="For a 12 percent discount, who needs to approve?",
            gold_answer_text=(
                "According to the latest discount approval matrix, a 12 percent discount "
                "can be approved by a sales manager."
            ),
            gold_citations=("sales_discount_approval_matrix_v2",),
            gold_answer_t0=(
                "According to the earlier discount approval matrix, a 12 percent "
                "discount required director approval."
            ),
            gold_answer_t1=(
                "According to the latest discount approval matrix, a 12 percent discount "
                "can be approved by a sales manager."
            ),
        )
    )

    qs.append(
        Question(
            question_id="fresh_hr_pto",
            workload="freshness_regression_suite",
            domain="hr",
            question_text="How many PTO days per year do employees accrue after the policy update?",
            gold_answer_text=(
                "Employees accrue 20 days of paid time off per year. Unused days can roll "
                "over up to 10 days."
            ),
            gold_citations=("hr_policy_pto_v2",),
            gold_answer_t0=(
                "Under the old policy, employees accrued 15 days of paid time off per "
                "year and unused days could roll over up to 5 days."
            ),
            gold_answer_t1=(
                "Employees accrue 20 days of paid time off per year. Unused days can roll "
                "over up to 10 days."
            ),
        )
    )

    qs.append(
        Question(
            question_id="fresh_it_password_policy",
            workload="freshness_regression_suite",
            domain="it",
            question_text="What is the current minimum password length?",
            gold_answer_text=(
                "Passwords must be at least 12 characters long and include a number, a "
                "special character, and an uppercase letter. Passwords expire every 120 days."
            ),
            gold_citations=("it_policy_password_v2",),
            gold_answer_t0=(
                "Under the old policy, passwords had to be at least 8 characters long and "
                "expired every 90 days."
            ),
            gold_answer_t1=(
                "Passwords must be at least 12 characters long and include a number, a "
                "special character, and an uppercase letter. Passwords expire every 120 days."
            ),
        )
    )

    return qs


def group_questions_by_workload(questions: List[Question]) -> Dict[str, List[Question]]:
    grouped: Dict[str, List[Question]] = {}
    for q in questions:
        grouped.setdefault(q.workload, []).append(q)
    return grouped
