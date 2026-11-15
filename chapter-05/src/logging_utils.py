from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List


@dataclass
class TicketRecord:
    ticket_id: str
    lane: str  # manual_baseline or agentic_treatment
    created_at: str
    first_response_at: str
    agent_id: str
    category: str
    sub_category: str
    resolution_code: str
    csat_score: float | None = None


@dataclass
class AgentInteractionRecord:
    ticket_id: str
    agent_request_at: str
    agent_response_at: str
    model_version: str
    prompt_version: str
    agent_output: Dict[str, Any]
    review_mode: str
    edit_distance_characters: float
    edit_distance_ratio: float
    human_comments: str | None = None


@dataclass
class ConfigRecord:
    experiment_id: str
    start_at: str
    end_at: str
    model_name: str
    model_params: Dict[str, Any]
    tools_enabled: List[str]
    routing_rule_version: str
    notes: str | None = None


def ticket_record_to_dict(rec: TicketRecord) -> Dict[str, Any]:
    return asdict(rec)


def agent_interaction_to_dict(rec: AgentInteractionRecord) -> Dict[str, Any]:
    return asdict(rec)


def config_record_to_dict(rec: ConfigRecord) -> Dict[str, Any]:
    return asdict(rec)
