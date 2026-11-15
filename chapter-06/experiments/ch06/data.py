from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class OnboardingCase:
    case_id: str
    segment: str  # "standard" or "high_risk"
    company_profile: str
    country: str
    annual_revenue_band: str
    known_issues: str = ""


@dataclass
class GroundTruth:
    case_id: str
    target_enriched_profile: Dict[str, Any]
    target_risk_category: str
    target_contract_summary: Dict[str, Any]
    target_sla_class: str
    should_escalate: bool
    required_additional_checks: List[str]


def _make_case(idx: int, segment: str) -> OnboardingCase:
    # Simple synthetic generator; content is not semantically rich but
    # consistent across runs.
    if segment == "standard":
        known_issues = ""
        revenue = "mid"
    else:
        known_issues = "late_payments" if idx % 2 == 0 else "regulatory_flags"
        revenue = "enterprise" if idx % 2 == 0 else "mid"

    return OnboardingCase(
        case_id=f"case_{segment}_{idx}",
        segment=segment,
        company_profile=f"Synthetic {segment} company {idx}",
        country="US" if idx % 3 != 0 else "DE",
        annual_revenue_band=revenue,
        known_issues=known_issues,
    )


def _risk_category_for(case: OnboardingCase) -> str:
    if case.segment == "high_risk":
        return "high"
    if case.known_issues:
        return "medium"
    return "low"


def _sla_for(case: OnboardingCase) -> str:
    if case.segment == "standard":
        return "SLA_STANDARD"
    return "SLA_HIGH_TOUCH"


def _contract_terms_for(case: OnboardingCase) -> Dict[str, Any]:
    risk = _risk_category_for(case)
    if risk == "high":
        discount = 5
        term_months = 12
    elif risk == "medium":
        discount = 10
        term_months = 12
    else:
        discount = 15
        term_months = 24
    return {
        "risk": risk,
        "term_months": term_months,
        "discount_percent": discount,
    }


def _should_escalate_for(case: OnboardingCase) -> bool:
    return case.segment == "high_risk"


def _required_checks_for(case: OnboardingCase) -> List[str]:
    if case.segment == "high_risk":
        return ["manual_kyc", "credit_committee"]
    return []


def _enriched_profile_for(case: OnboardingCase) -> Dict[str, Any]:
    return {
        "case_id": case.case_id,
        "country": case.country,
        "annual_revenue_band": case.annual_revenue_band,
        "segment": case.segment,
        "known_issues": case.known_issues,
    }


def generate_workload_standard(n: int = 10) -> tuple[List[OnboardingCase], Dict[str, GroundTruth]]:
    cases: List[OnboardingCase] = []
    gt: Dict[str, GroundTruth] = {}
    for i in range(n):
        case = _make_case(i, "standard")
        cases.append(case)
        gt[case.case_id] = GroundTruth(
            case_id=case.case_id,
            target_enriched_profile=_enriched_profile_for(case),
            target_risk_category=_risk_category_for(case),
            target_contract_summary=_contract_terms_for(case),
            target_sla_class=_sla_for(case),
            should_escalate=_should_escalate_for(case),
            required_additional_checks=_required_checks_for(case),
        )
    return cases, gt


def generate_workload_high_risk(n: int = 10) -> tuple[List[OnboardingCase], Dict[str, GroundTruth]]:
    cases: List[OnboardingCase] = []
    gt: Dict[str, GroundTruth] = {}
    for i in range(n):
        case = _make_case(i, "high_risk")
        cases.append(case)
        gt[case.case_id] = GroundTruth(
            case_id=case.case_id,
            target_enriched_profile=_enriched_profile_for(case),
            target_risk_category=_risk_category_for(case),
            target_contract_summary=_contract_terms_for(case),
            target_sla_class=_sla_for(case),
            should_escalate=_should_escalate_for(case),
            required_additional_checks=_required_checks_for(case),
        )
    return cases, gt


def generate_workload_mixed(n_each: int = 5) -> tuple[List[OnboardingCase], Dict[str, GroundTruth]]:
    # Half standard, half high_risk, interleaved.
    cases: List[OnboardingCase] = []
    gt: Dict[str, GroundTruth] = {}
    std_cases, std_gt = generate_workload_standard(n_each)
    hr_cases, hr_gt = generate_workload_high_risk(n_each)
    for a, b in zip(std_cases, hr_cases):
        cases.append(a)
        cases.append(b)
    gt.update(std_gt)
    gt.update(hr_gt)
    return cases, gt
