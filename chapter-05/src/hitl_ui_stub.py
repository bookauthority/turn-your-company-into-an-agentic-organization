from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Tuple


@dataclass
class HitlConfig:
    edit_minor_threshold_ratio: float
    approve_confidence_threshold: float


def _levenshtein(a: str, b: str) -> int:
    """Compute Levenshtein distance between two strings.

    Implementation is iterative and suitable for short texts.
    """

    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev_row = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr_row = [i]
        for j, cb in enumerate(b, start=1):
            insert_cost = curr_row[j - 1] + 1
            delete_cost = prev_row[j] + 1
            replace_cost = prev_row[j - 1] + (0 if ca == cb else 1)
            curr_row.append(min(insert_cost, delete_cost, replace_cost))
        prev_row = curr_row
    return prev_row[-1]


def simulate_review(
    original_ticket_body: str,
    agent_output: Dict[str, Any],
    config: HitlConfig,
) -> Tuple[str, str, float, int, float]:
    """Simulate a human-in-the-loop review decision.

    Returns:
        review_mode: one of approve_as_is, edit_then_approve, reject_and_handle_manually, redirect_out_of_scope
        final_response: string actually sent to the customer
        confidence: agent-reported confidence
        edit_distance: Levenshtein distance between draft and final
        edit_ratio: normalized edit distance (0-1)
    """

    draft = agent_output["response_draft"]
    confidence = float(agent_output.get("confidence", 0.0))
    classification = agent_output.get("classification", {})
    category = classification.get("category", "")

    # Simple rule-set:
    # - If category is out-of-scope: redirect_out_of_scope
    # - If confidence is high: approve_as_is
    # - If medium confidence: small deterministic edit
    # - If low confidence: reject_and_handle_manually

    if category == "out-of-scope":
        review_mode = "redirect_out_of_scope"
        final_response = ""  # Would be handled by another workflow; omitted here.
    elif confidence >= config.approve_confidence_threshold:
        review_mode = "approve_as_is"
        final_response = draft
    elif confidence >= (config.approve_confidence_threshold - 0.2):
        # Edit slightly: prepend a mild softener sentence.
        review_mode = "edit_then_approve"
        intro = (
            "Thanks for your patience. "
            "I have reviewed your request and below is the updated response.\n\n"
        )
        final_response = intro + draft
    else:
        review_mode = "reject_and_handle_manually"
        # Human writes new response from scratch (simple deterministic template)
        final_response = (
            "Hi there,\n\n"
            "Thanks for contacting support. A human agent is reviewing your "
            "billing question and will follow up with a detailed answer.\n\n"
            "Best regards,\nSupport Team"
        )

    edit_distance = _levenshtein(draft, final_response)
    max_len = max(len(draft), len(final_response)) or 1
    edit_ratio = edit_distance / max_len

    return review_mode, final_response, confidence, edit_distance, edit_ratio
