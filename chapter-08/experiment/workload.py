from __future__ import annotations

"""Deterministic synthetic workload generator for tickets."""

from dataclasses import dataclass
import random
from typing import Iterable, List

from .ticket import Ticket, Channel, Category, Complexity


@dataclass(frozen=True)
class WorkloadConfig:
    workload_id: str
    num_tickets: int
    seed: int


def _sample_channel(rng: random.Random) -> Channel:
    # Approximate realistic channel mix: email 50%, web 20%, chat 30%
    r = rng.random()
    if r < 0.5:
        return "email"
    if r < 0.7:
        return "web"
    return "chat"


def _sample_category(rng: random.Random) -> Category:
    # Rough mix across common support types.
    r = rng.random()
    if r < 0.25:
        return "login"
    if r < 0.45:
        return "billing"
    if r < 0.7:
        return "howto"
    if r < 0.88:
        return "bug"
    return "integration"


def _sample_complexity(rng: random.Random, category: Category) -> Complexity:
    # Category-conditioned complexity distribution.
    base = rng.random()
    if category in ("login", "howto"):
        if base < 0.7:
            return "low"
        if base < 0.9:
            return "medium"
        return "high"
    if category == "billing":
        if base < 0.3:
            return "low"
        if base < 0.7:
            return "medium"
        return "high"
    # bug / integration typically more complex
    if base < 0.2:
        return "low"
    if base < 0.6:
        return "medium"
    return "high"


def _is_high_risk(rng: random.Random, category: Category) -> bool:
    # Billing and security-like bugs may be high risk.
    base = rng.random()
    if category == "billing":
        return base < 0.3
    if category == "bug":
        return base < 0.1
    return base < 0.02


def generate_tickets(cfg: WorkloadConfig) -> List[Ticket]:
    """Generate a deterministic sequence of synthetic tickets.

    The RNG is re-seeded from cfg.seed for reproducible workloads.
    """
    rng = random.Random(cfg.seed)
    tickets: List[Ticket] = []
    for i in range(cfg.num_tickets):
        channel = _sample_channel(rng)
        category = _sample_category(rng)
        complexity = _sample_complexity(rng, category)
        is_high_risk = _is_high_risk(rng, category)
        ticket_id = f"{cfg.workload_id}-{i:05d}"
        tickets.append(
            Ticket(
                ticket_id=ticket_id,
                channel=channel,
                category=category,
                complexity=complexity,
                is_high_risk=is_high_risk,
            )
        )
    return tickets
