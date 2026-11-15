from __future__ import annotations

"""Static configuration for the synthetic customer support experiment.

This module captures assumptions for both baseline (human-only) and
agentic (treatment) workflows.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class HumanCostModel:
    hourly_rate: float  # currency per hour


@dataclass(frozen=True)
class AgenticCostModel:
    cost_per_ticket: float  # flat currency cost per ticket for LLM+infra


@dataclass(frozen=True)
class BaselineTimeModel:
    """Handle time model for baseline human-only flows (minutes)."""

    l1_simple_min: float = 3.0
    l1_simple_max: float = 7.0
    l1_complex_min: float = 8.0
    l1_complex_max: float = 18.0
    l2_additional_min: float = 10.0
    l2_additional_max: float = 25.0
    escalation_prob_medium: float = 0.35
    escalation_prob_complex: float = 0.7


@dataclass(frozen=True)
class TreatmentTimeModel:
    """Handle time model for agentic flows (minutes)."""

    # Agent compute "time" is conceptual and later converted to cost.
    triage_time: float = 0.3
    knowledge_time: float = 0.4
    resolver_time: float = 0.6
    quality_review_time: float = 0.4

    # When humans are involved, they spend less time than in baseline.
    human_simple_min: float = 1.5
    human_simple_max: float = 4.0
    human_complex_min: float = 5.0
    human_complex_max: float = 12.0

    # Fractions of tickets handled in different ways.
    auto_resolution_prob_low_complexity: float = 0.55
    auto_resolution_prob_medium_complexity: float = 0.25
    auto_resolution_prob_complex: float = 0.05
    forced_human_high_risk_prob: float = 0.15

    escalation_after_agent_prob_medium: float = 0.3
    escalation_after_agent_prob_complex: float = 0.6


@dataclass(frozen=True)
class WorkloadSize:
    historical_replay_tickets: int = 400
    live_ab_tickets: int = 600


# Global configuration instances used throughout the experiment.

HUMAN_COST_MODEL = HumanCostModel(hourly_rate=30.0)
AGENTIC_COST_MODEL = AgenticCostModel(cost_per_ticket=0.05)
BASELINE_TIME_MODEL = BaselineTimeModel()
TREATMENT_TIME_MODEL = TreatmentTimeModel()
WORKLOAD_SIZE = WorkloadSize()
