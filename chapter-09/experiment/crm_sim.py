from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .random_utils import DeterministicRandom


@dataclass
class Lead:
    id: str
    segment: str
    region: str
    arr_band: str
    owner_id: Optional[str] = None
    enriched: bool = False


@dataclass
class Opportunity:
    id: str
    lead_id: str
    arr_value: float
    stage: str
    owner_id: str


@dataclass
class Quote:
    id: str
    opportunity_id: str
    total_value: float
    approved: bool = False


@dataclass
class Event:
    event_id: str
    record_id: str
    event_type: str
    timestamp: float
    metadata: dict = field(default_factory=dict)


@dataclass
class Action:
    action_id: str
    experiment_id: str
    record_id: str
    actor_type: str  # 'human' or 'agent'
    actor_id: str
    agent_name: Optional[str]
    action_type: str
    timestamp: float
    duration_seconds: Optional[float]
    requires_approval: bool
    approval_status: str
    api_cost: Optional[float] = None


class CRMSimulator:
    """In-memory synthetic CRM / event / action logger.

    This is intentionally simple and self-contained. It provides utility
    methods for workloads to create leads, opportunities, and quotes,
    and to log events and actions.
    """

    def __init__(self, seed: int = 0) -> None:
        self.rng = DeterministicRandom(seed)
        self.leads: Dict[str, Lead] = {}
        self.opportunities: Dict[str, Opportunity] = {}
        self.quotes: Dict[str, Quote] = {}
        self.events: List[Event] = []
        self.actions: List[Action] = []
        self._now = 1_700_000_000.0  # synthetic epoch time base
        self._id_counter = 0

    def _next_id(self, prefix: str) -> str:
        self._id_counter += 1
        return f"{prefix}{self._id_counter:06d}"

    def _tick(self, seconds: float) -> float:
        self._now += seconds
        return self._now

    # --- Lead / Opportunity / Quote creation ---

    def create_lead(self, segment: str, region: str, arr_band: str) -> Lead:
        lead_id = self._next_id("L")
        lead = Lead(id=lead_id, segment=segment, region=region, arr_band=arr_band)
        self.leads[lead_id] = lead
        self.log_event(lead_id, "lead_created")
        return lead

    def create_opportunity(self, lead_id: str, arr_value: float, owner_id: str) -> Opportunity:
        opp_id = self._next_id("O")
        opp = Opportunity(id=opp_id, lead_id=lead_id, arr_value=arr_value, stage="Prospecting", owner_id=owner_id)
        self.opportunities[opp_id] = opp
        self.log_event(opp_id, "opportunity_created")
        return opp

    def create_quote(self, opportunity_id: str, total_value: float) -> Quote:
        quote_id = self._next_id("Q")
        quote = Quote(id=quote_id, opportunity_id=opportunity_id, total_value=total_value)
        self.quotes[quote_id] = quote
        self.log_event(quote_id, "quote_requested")
        return quote

    # --- Logging helpers ---

    def log_event(self, record_id: str, event_type: str, metadata: Optional[dict] = None) -> None:
        ev = Event(
            event_id=self._next_id("E"),
            record_id=record_id,
            event_type=event_type,
            timestamp=self._now,
            metadata=metadata or {},
        )
        self.events.append(ev)

    def log_action(
        self,
        experiment_id: str,
        record_id: str,
        actor_type: str,
        actor_id: str,
        agent_name: Optional[str],
        action_type: str,
        duration_seconds: Optional[float],
        requires_approval: bool = False,
        approval_status: str = "not_required",
        api_cost: Optional[float] = None,
    ) -> None:
        # Advance synthetic time by duration if provided
        ts = self._tick(duration_seconds or 0.0)
        act = Action(
            action_id=self._next_id("A"),
            experiment_id=experiment_id,
            record_id=record_id,
            actor_type=actor_type,
            actor_id=actor_id,
            agent_name=agent_name,
            action_type=action_type,
            timestamp=ts,
            duration_seconds=duration_seconds,
            requires_approval=requires_approval,
            approval_status=approval_status,
            api_cost=api_cost,
        )
        self.actions.append(act)

    # --- Query helpers for metrics ---

    def get_actions_for_records(self, record_ids) -> List[Action]:
        rs = set(record_ids)
        return [a for a in self.actions if a.record_id in rs]

    def total_api_cost_for_records(self, record_ids) -> float:
        rs = set(record_ids)
        total = 0.0
        for a in self.actions:
            if a.record_id in rs and a.api_cost is not None:
                total += a.api_cost
        return total

    def lead_response_time_seconds(self, lead_id: str) -> Optional[float]:
        """Synthetic lead-response time based on first follow-up event.

        For this synthetic simulator, we look for the first of
        'followup_task_created' events and subtract 'lead_created'.
        """
        created_ts = None
        first_follow_ts = None
        for ev in self.events:
            if ev.record_id == lead_id and ev.event_type == "lead_created":
                created_ts = ev.timestamp
                break
        if created_ts is None:
            return None
        for ev in self.events:
            if ev.record_id == lead_id and ev.event_type == "followup_task_created":
                first_follow_ts = ev.timestamp
                break
        if first_follow_ts is None:
            return None
        return max(0.0, first_follow_ts - created_ts)

    def quote_cycle_time_seconds(self, quote_id: str) -> Optional[float]:
        start_ts = None
        final_ts = None
        for ev in self.events:
            if ev.record_id == quote_id and ev.event_type == "quote_requested":
                start_ts = ev.timestamp
                break
        if start_ts is None:
            return None
        for ev in self.events:
            if ev.record_id == quote_id and ev.event_type == "quote_final_approved":
                final_ts = ev.timestamp
                break
        if final_ts is None:
            return None
        return max(0.0, final_ts - start_ts)

    def forecast_error(self, baseline_value: float, actual_value: float) -> float:
        return abs(baseline_value - actual_value)

    def is_finite_number(self, value: float) -> bool:
        return isinstance(value, (int, float)) and not (math.isnan(value) or math.isinf(value))
