from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Generator


@dataclass
class Ticket:
    ticket_id: str
    created_at_ms: int
    channel: str
    category: str
    difficulty: str
    language: str
    text: str


CATEGORIES = ["password_reset", "access_request", "billing_question", "bug_report"]
DIFFICULTIES = ["easy", "medium", "hard"]
CHANNELS = ["email", "chat"]
LANGUAGES = ["en"]


def _ticket_text(category: str, difficulty: str) -> str:
    base = {
        "password_reset": "I cannot log in and need to reset my password.",
        "access_request": "Please give me access to the reporting dashboard.",
        "billing_question": "I have a question about a charge on my invoice.",
        "bug_report": "The application crashes when I click the save button.",
    }[category]
    if difficulty == "easy":
        return base
    if difficulty == "medium":
        return base + " It happens occasionally and I am not sure why."
    # hard
    return base + " There are multiple edge cases and previous attempts to fix this have failed."


def generate_synthetic_tickets(seed: int, count: int) -> Generator[Ticket, None, None]:
    """Deterministic ticket generator used by both baseline and treatment.

    This represents the synthetic_ticket_stream workload.
    """

    rng = random.Random(seed)
    start_time_ms = 0
    for i in range(count):
        ticket_id = f"t_{i:05d}"
        category = rng.choice(CATEGORIES)
        difficulty = rng.choice(DIFFICULTIES)
        channel = rng.choice(CHANNELS)
        language = rng.choice(LANGUAGES)
        text = _ticket_text(category, difficulty)
        created_at_ms = start_time_ms + i * 1000  # 1 second between arrivals
        yield Ticket(
            ticket_id=ticket_id,
            created_at_ms=created_at_ms,
            channel=channel,
            category=category,
            difficulty=difficulty,
            language=language,
            text=text,
        )


def expected_resolution(category: str) -> str:
    """Simple 'ground truth' mapping for whether a run is considered successful.

    This is deliberately simple and deterministic so we can compute a boolean
    success per run without external services.
    """

    mapping: Dict[str, str] = {
        "password_reset": "Reset the user's password",
        "access_request": "Grant requested access",
        "billing_question": "Explain the billing charge",
        "bug_report": "Log and triage the bug",
    }
    return mapping[category]
