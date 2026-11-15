from __future__ import annotations

from typing import Dict

from .config import CHAPTER_NUMBER, DURATIONS, EXPERIMENT_ID, API_COSTS
from .crm_sim import CRMSimulator


# --- Workload 1: Lead Enrichment and Routing ---


def run_lead_enrichment_and_routing(crm: CRMSimulator, variant: str) -> Dict[str, float]:
    """Simulate enrichment and routing for a batch of leads.

    Metrics:
    - lead_enrichment_time_per_lead (seconds/lead)
    - routing_decision_time_per_lead (seconds/lead)
    - system_cost_per_record (if treatment)
    """

    num_leads = 100
    segments = ["SMB", "MM", "ENT"]
    regions = ["NA", "EMEA", "APAC"]
    arr_bands = ["<10k", "10k-50k", ">50k"]

    leads = []
    for i in range(num_leads):
        seg = segments[i % len(segments)]
        reg = regions[i % len(regions)]
        band = arr_bands[i % len(arr_bands)]
        leads.append(crm.create_lead(segment=seg, region=reg, arr_band=band))

    human_actor_id = "user_sales_ops"
    agent_actor_id = "agent_sales_ops"

    enrichment_dur = DURATIONS[variant]["lead_enrichment_per_lead"]
    routing_dur = DURATIONS[variant]["lead_routing_per_lead"]
    api_cost_enrichment = 0.0
    api_cost_routing = 0.0
    if variant == "treatment":
        api_cost_enrichment = API_COSTS["treatment"]["lead_enrichment_per_lead"]
        api_cost_routing = API_COSTS["treatment"]["lead_routing_per_lead"]

    for lead in leads:
        # Enrichment
        if variant == "baseline":
            crm.log_action(
                experiment_id=EXPERIMENT_ID,
                record_id=lead.id,
                actor_type="human",
                actor_id=human_actor_id,
                agent_name=None,
                action_type="lead_enrichment",
                duration_seconds=enrichment_dur,
            )
        else:
            crm.log_action(
                experiment_id=EXPERIMENT_ID,
                record_id=lead.id,
                actor_type="agent",
                actor_id=agent_actor_id,
                agent_name="Lead_Enrichment_Agent",
                action_type="lead_enrichment_suggest",
                duration_seconds=enrichment_dur,
                api_cost=api_cost_enrichment,
            )
        lead.enriched = True

        # Routing
        owner_id = f"rep_{(hash(lead.region + lead.segment) % 5) + 1}"
        lead.owner_id = owner_id
        if variant == "baseline":
            crm.log_action(
                experiment_id=EXPERIMENT_ID,
                record_id=lead.id,
                actor_type="human",
                actor_id=human_actor_id,
                agent_name=None,
                action_type="lead_routing",
                duration_seconds=routing_dur,
            )
        else:
            crm.log_action(
                experiment_id=EXPERIMENT_ID,
                record_id=lead.id,
                actor_type="agent",
                actor_id=agent_actor_id,
                agent_name="Lead_Routing_Agent",
                action_type="lead_routing_auto",
                duration_seconds=routing_dur,
                api_cost=api_cost_routing,
            )

    total_enrichment_time = enrichment_dur * num_leads
    total_routing_time = routing_dur * num_leads
    lead_enrichment_time_per_lead = total_enrichment_time / num_leads
    routing_decision_time_per_lead = total_routing_time / num_leads

    total_api_cost = 0.0
    if variant == "treatment":
        total_api_cost = (api_cost_enrichment + api_cost_routing) * num_leads
        system_cost_per_record = total_api_cost / num_leads
    else:
        system_cost_per_record = 0.0

    metrics = {
        "lead_enrichment_time_per_lead": float(lead_enrichment_time_per_lead),
        "routing_decision_time_per_lead": float(routing_decision_time_per_lead),
        "system_cost_per_record": float(system_cost_per_record),
    }
    return metrics


# --- Workload 2: Pipeline Hygiene ---


def run_pipeline_hygiene(crm: CRMSimulator, variant: str) -> Dict[str, float]:
    """Simulate pipeline hygiene passes over opportunities.

    Metrics:
    - pipeline_hygiene_hours_per_week (simulated, from total human time)
    - admin_hours_per_opportunity (simulated)
    - system_cost_per_record (if treatment)
    """

    # Seed some leads/opportunities
    num_opps = 200
    for i in range(num_opps):
        lead = crm.create_lead(segment="MM", region="NA", arr_band="10k-50k")
        owner_id = f"rep_{(i % 5) + 1}"
        opp = crm.create_opportunity(lead_id=lead.id, arr_value=20000.0 + i * 10, owner_id=owner_id)
        crm.log_event(opp.id, "opportunity_stage_set", {"stage": "Proposal"})

    human_actor_id = "user_mgr"
    agent_actor_id = "agent_hygiene"

    hygiene_dur = DURATIONS[variant]["pipeline_hygiene_per_opportunity"]
    api_cost_hygiene = 0.0
    if variant == "treatment":
        api_cost_hygiene = API_COSTS["treatment"]["pipeline_hygiene_per_opportunity"]

    for opp in crm.opportunities.values():
        if variant == "baseline":
            crm.log_action(
                experiment_id=EXPERIMENT_ID,
                record_id=opp.id,
                actor_type="human",
                actor_id=human_actor_id,
                agent_name=None,
                action_type="pipeline_hygiene_review",
                duration_seconds=hygiene_dur,
            )
        else:
            # Agent suggests; human quickly reviews (modeled via same duration but agent gets api cost)
            crm.log_action(
                experiment_id=EXPERIMENT_ID,
                record_id=opp.id,
                actor_type="agent",
                actor_id=agent_actor_id,
                agent_name="Pipeline_Hygiene_Agent",
                action_type="pipeline_hygiene_suggest",
                duration_seconds=hygiene_dur * 0.5,
                api_cost=api_cost_hygiene,
            )
            crm.log_action(
                experiment_id=EXPERIMENT_ID,
                record_id=opp.id,
                actor_type="human",
                actor_id=human_actor_id,
                agent_name=None,
                action_type="pipeline_hygiene_review_accept",
                duration_seconds=hygiene_dur * 0.5,
            )

    # Total human time
    total_human_seconds = 0.0
    for a in crm.actions:
        if a.actor_type == "human" and a.duration_seconds is not None:
            total_human_seconds += a.duration_seconds

    admin_hours_per_opportunity = (total_human_seconds / 3600.0) / max(1, num_opps)

    # Represent a single week of hygiene work
    pipeline_hygiene_hours_per_week = total_human_seconds / 3600.0

    total_api_cost = crm.total_api_cost_for_records(list(crm.opportunities.keys()))
    system_cost_per_record = total_api_cost / max(1, num_opps)

    metrics = {
        "pipeline_hygiene_hours_per_week": float(pipeline_hygiene_hours_per_week),
        "admin_hours_per_opportunity": float(admin_hours_per_opportunity),
        "system_cost_per_record": float(system_cost_per_record),
    }
    return metrics


# --- Workload 3: Quote to Order Assistance ---


def run_quote_to_order_assistance(crm: CRMSimulator, variant: str) -> Dict[str, float]:
    """Simulate quote generation and approval.

    Metrics:
    - quote_cycle_time (seconds; synthetic)
    - admin_hours_per_opportunity (synthetic, quote-prep time)
    - system_cost_per_record (if treatment)
    """

    num_quotes = 50
    human_actor_id = "ae_user"
    mgr_actor_id = "mgr_user"
    agent_actor_id = "agent_quote"

    quote_dur = DURATIONS[variant]["quote_prep_per_quote"]
    api_cost_quote = 0.0
    if variant == "treatment":
        api_cost_quote = API_COSTS["treatment"]["quote_prep_per_quote"]

    quotes = []
    for i in range(num_quotes):
        lead = crm.create_lead(segment="MM", region="NA", arr_band="10k-50k")
        opp = crm.create_opportunity(lead_id=lead.id, arr_value=30000.0 + i * 100, owner_id="ae_user")
        quote = crm.create_quote(opportunity_id=opp.id, total_value=opp.arr_value)
        quotes.append(quote)

        if variant == "baseline":
            # AE manually prepares quote
            crm.log_action(
                experiment_id=EXPERIMENT_ID,
                record_id=quote.id,
                actor_type="human",
                actor_id=human_actor_id,
                agent_name=None,
                action_type="quote_prepare_manual",
                duration_seconds=quote_dur,
            )
        else:
            # Agent drafts, AE reviews
            crm.log_action(
                experiment_id=EXPERIMENT_ID,
                record_id=quote.id,
                actor_type="agent",
                actor_id=agent_actor_id,
                agent_name="Quote_Assistant_Agent",
                action_type="quote_draft",
                duration_seconds=quote_dur * 0.5,
                api_cost=api_cost_quote,
            )
            crm.log_action(
                experiment_id=EXPERIMENT_ID,
                record_id=quote.id,
                actor_type="human",
                actor_id=human_actor_id,
                agent_name=None,
                action_type="quote_review",
                duration_seconds=quote_dur * 0.5,
            )

        # Manager approval step (same for both)
        crm.log_action(
            experiment_id=EXPERIMENT_ID,
            record_id=quote.id,
            actor_type="human",
            actor_id=mgr_actor_id,
            agent_name=None,
            action_type="quote_approve",
            duration_seconds=quote_dur * 0.25,
        )
        crm.log_event(quote.id, "quote_final_approved")
        quote.approved = True

    # Compute average quote_cycle_time from events
    cycle_times = []
    for quote in quotes:
        ct = crm.quote_cycle_time_seconds(quote.id)
        if ct is not None:
            cycle_times.append(ct)

    avg_quote_cycle_time = sum(cycle_times) / len(cycle_times) if cycle_times else 0.0

    # Compute admin hours per opportunity (from human actions only)
    total_human_seconds = 0.0
    for a in crm.actions:
        if a.actor_type == "human" and a.duration_seconds is not None:
            total_human_seconds += a.duration_seconds
    admin_hours_per_opportunity = (total_human_seconds / 3600.0) / max(1, num_quotes)

    total_api_cost = crm.total_api_cost_for_records([q.id for q in quotes])
    system_cost_per_record = total_api_cost / max(1, num_quotes)

    metrics = {
        "quote_cycle_time": float(avg_quote_cycle_time),
        "admin_hours_per_opportunity": float(admin_hours_per_opportunity),
        "system_cost_per_record": float(system_cost_per_record),
    }
    return metrics


# --- Workload 4: Followup and Cycle Time ---


def run_followup_and_cycle_time(crm: CRMSimulator, variant: str) -> Dict[str, float]:
    """Simulate follow-up task planning after lead creation.

    Metrics:
    - lead_response_time (seconds; synthetic)
    - admin_hours_per_opportunity (simplified)
    - system_cost_per_record (if treatment)
    """

    num_leads = 80
    human_actor_id = "ae_user"
    agent_actor_id = "agent_followup"

    followup_dur = DURATIONS[variant]["followup_task_per_event"]
    api_cost_follow = 0.0
    if variant == "treatment":
        api_cost_follow = API_COSTS["treatment"]["followup_task_per_event"]

    leads = []
    for i in range(num_leads):
        lead = crm.create_lead(segment="SMB", region="NA", arr_band="<10k")
        leads.append(lead)

        # Follow-up task creation
        if variant == "baseline":
            crm.log_action(
                experiment_id=EXPERIMENT_ID,
                record_id=lead.id,
                actor_type="human",
                actor_id=human_actor_id,
                agent_name=None,
                action_type="followup_task_create_manual",
                duration_seconds=followup_dur,
            )
        else:
            crm.log_action(
                experiment_id=EXPERIMENT_ID,
                record_id=lead.id,
                actor_type="agent",
                actor_id=agent_actor_id,
                agent_name="Followup_Cadence_Agent",
                action_type="followup_task_suggest",
                duration_seconds=followup_dur * 0.5,
                api_cost=api_cost_follow,
            )
            crm.log_action(
                experiment_id=EXPERIMENT_ID,
                record_id=lead.id,
                actor_type="human",
                actor_id=human_actor_id,
                agent_name=None,
                action_type="followup_task_confirm",
                duration_seconds=followup_dur * 0.5,
            )
        crm.log_event(lead.id, "followup_task_created")

    # Lead response time: synthetic difference between lead_created and followup_task_created
    response_times = []
    for lead in leads:
        rt = crm.lead_response_time_seconds(lead.id)
        if rt is not None:
            response_times.append(rt)

    avg_lead_response_time = sum(response_times) / len(response_times) if response_times else 0.0

    total_human_seconds = 0.0
    for a in crm.actions:
        if a.actor_type == "human" and a.duration_seconds is not None:
            total_human_seconds += a.duration_seconds
    admin_hours_per_opportunity = (total_human_seconds / 3600.0) / max(1, num_leads)

    total_api_cost = crm.total_api_cost_for_records([l.id for l in leads])
    system_cost_per_record = total_api_cost / max(1, num_leads)

    metrics = {
        "lead_response_time": float(avg_lead_response_time),
        "admin_hours_per_opportunity": float(admin_hours_per_opportunity),
        "system_cost_per_record": float(system_cost_per_record),
    }
    return metrics


# --- Workload 5: Forecasting Support ---


def run_forecasting_support(crm: CRMSimulator, variant: str) -> Dict[str, float]:
    """Simulate forecast preparation and error.

    Metrics:
    - forecast_absolute_error (synthetic)
    - system_cost_per_record (if treatment; per opportunity)
    - admin_hours_per_opportunity (forecast-prep time / opportunities)
    """

    num_opps = 60
    human_actor_id = "ops_user"
    agent_actor_id = "agent_forecast"

    # create opportunities with known actual values
    actual_values = []
    for i in range(num_opps):
        lead = crm.create_lead(segment="MM", region="EMEA", arr_band="10k-50k")
        arr_value = 50000.0 + i * 200.0
        opp = crm.create_opportunity(lead_id=lead.id, arr_value=arr_value, owner_id="rep_1")
        actual_values.append(arr_value)

    forecast_dur = DURATIONS[variant]["forecast_prep_per_run"]
    api_cost_forecast = 0.0
    if variant == "treatment":
        api_cost_forecast = API_COSTS["treatment"]["forecast_prep_per_run"]

    actual_total = sum(actual_values)

    if variant == "baseline":
        # baseline forecast is actual plus some synthetic bias
        forecast_value = actual_total * 1.05
        crm.log_action(
            experiment_id=EXPERIMENT_ID,
            record_id="forecast_period_1",
            actor_type="human",
            actor_id=human_actor_id,
            agent_name=None,
            action_type="forecast_prepare_manual",
            duration_seconds=forecast_dur,
        )
    else:
        # treatment: agent proposes closer forecast, human reviews
        forecast_value = actual_total * 1.02
        crm.log_action(
            experiment_id=EXPERIMENT_ID,
            record_id="forecast_period_1",
            actor_type="agent",
            actor_id=agent_actor_id,
            agent_name="Forecast_Support_Agent",
            action_type="forecast_propose",
            duration_seconds=forecast_dur * 0.5,
            api_cost=api_cost_forecast,
        )
        crm.log_action(
            experiment_id=EXPERIMENT_ID,
            record_id="forecast_period_1",
            actor_type="human",
            actor_id=human_actor_id,
            agent_name=None,
            action_type="forecast_review",
            duration_seconds=forecast_dur * 0.5,
        )

    abs_error = crm.forecast_error(forecast_value, actual_total)

    total_human_seconds = 0.0
    for a in crm.actions:
        if a.actor_type == "human" and a.duration_seconds is not None:
            total_human_seconds += a.duration_seconds
    admin_hours_per_opportunity = (total_human_seconds / 3600.0) / max(1, num_opps)

    total_api_cost = crm.total_api_cost_for_records(["forecast_period_1"])
    system_cost_per_record = total_api_cost / max(1, num_opps)

    metrics = {
        "forecast_absolute_error": float(abs_error),
        "admin_hours_per_opportunity": float(admin_hours_per_opportunity),
        "system_cost_per_record": float(system_cost_per_record),
    }
    return metrics
