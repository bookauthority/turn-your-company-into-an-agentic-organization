CHAPTER_NUMBER = 9
EXPERIMENT_ID = "exp-ch09-agentic-sales-ops-mas-vs-manual-v1"

# Stable workload identifiers used in evidence
WORKLOAD_IDS = {
    "lead_enrichment_and_routing": "Lead_Enrichment_and_Routing",
    "pipeline_hygiene": "Pipeline_Hygiene",
    "quote_to_order_assistance": "Quote_to_Order_Assistance",
    "followup_and_cycle_time": "Followup_and_Cycle_Time",
    "forecasting_support": "Forecasting_Support",
}

# Synthetic configuration for durations (seconds) and API cost (arbitrary units)
# These are deterministic constants used for simulation only.
DURATIONS = {
    "baseline": {
        "lead_enrichment_per_lead": 120.0,
        "lead_routing_per_lead": 30.0,
        "pipeline_hygiene_per_opportunity": 60.0,
        "quote_prep_per_quote": 180.0,
        "followup_task_per_event": 45.0,
        "forecast_prep_per_run": 600.0,
    },
    "treatment": {
        "lead_enrichment_per_lead": 40.0,
        "lead_routing_per_lead": 10.0,
        "pipeline_hygiene_per_opportunity": 20.0,
        "quote_prep_per_quote": 60.0,
        "followup_task_per_event": 15.0,
        "forecast_prep_per_run": 200.0,
    },
}

API_COSTS = {
    "treatment": {
        "lead_enrichment_per_lead": 0.02,
        "lead_routing_per_lead": 0.005,
        "pipeline_hygiene_per_opportunity": 0.01,
        "quote_prep_per_quote": 0.05,
        "followup_task_per_event": 0.005,
        "forecast_prep_per_run": 0.10,
    },
}
