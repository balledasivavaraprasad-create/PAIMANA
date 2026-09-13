from typing import List, Dict, Any
from app.ml.feature_engineering.financial import compute_financial_features
from app.ml.feature_engineering.schedule import compute_schedule_features
from app.ml.feature_engineering.progress import compute_progress_features
from app.ml.feature_engineering.environmental import compute_environmental_features
from app.ml.feature_engineering.geospatial import compute_geospatial_features

FEATURE_COLUMNS = [
    "cost_escalation",
    "expenditure_ratio",
    "monthly_burn_rate",
    "cost_acceleration",
    "planned_duration_months",
    "deadline_slip_months",
    "schedule_gap_ratio",
    "milestone_delay_rate",
    "current_physical_progress",
    "current_financial_progress",
    "progress_velocity",
    "progress_acceleration",
    "physical_financial_gap",
    "stagnation_months",
    "avg_rainfall_mm",
    "weather_disruption_months",
    "environmental_hazard_index",
    "state_execution_index",
    "terrain_elevation_m",
]

def engineer_features(project: Dict[str, Any], snapshots: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Central Feature Engineering Service for PAIMANA:
    Input: Project details + Historical snapshots + Weather/GIS
    Output: Unified structured dictionary of time-aware features
    """
    features: Dict[str, float] = {}

    features.update(compute_financial_features(project, snapshots))
    features.update(compute_schedule_features(project, snapshots))
    features.update(compute_progress_features(snapshots))
    features.update(compute_environmental_features(project, snapshots))
    features.update(compute_geospatial_features(project))

    # Ensure all required FEATURE_COLUMNS exist with float values
    clean_features = {}
    for col in FEATURE_COLUMNS:
        clean_features[col] = float(features.get(col, 0.0))

    return clean_features
