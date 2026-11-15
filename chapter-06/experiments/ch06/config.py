EXPERIMENT_ID = "ch06-mas-orchestration-vs-single-agent-v1"

# Workload identifiers used across the experiment and evidence.
WORKLOAD_STANDARD = "synthetic_customer_onboarding_standard"
WORKLOAD_HIGH_RISK = "synthetic_customer_onboarding_high_risk"
WORKLOAD_MIXED = "synthetic_customer_onboarding_mixed_batch"

WORKLOAD_IDS = [
    WORKLOAD_STANDARD,
    WORKLOAD_HIGH_RISK,
    WORKLOAD_MIXED,
]

# Synthetic configuration knobs. In a real system these would align with
# YAML configs and environment variables.
BASELINE_MAX_STEPS = 12
TREATMENT_MAX_STATE_TRANSITIONS = 20

# For this offline, deterministic experiment we use a fixed seed but keep
# the logic mostly rule-based so randomness is minimal.
RANDOM_SEED = 42
