from typing import Dict, Any, Optional
from datetime import datetime
from app.models.risk import DPHISScore, RiskLevel, RiskComponents, RiskTrend
from app.services.paimana_ml_service import paimana_ml

def calculate_dphis(
    project_id: str,
    features: Dict[str, Any],
    cost_risk: Optional[float] = None,
    time_risk: Optional[float] = None,
    previous_dphis: Optional[float] = None
) -> DPHISScore:
    """
    Computes the Dynamic Project Health and Intervention Score (DPHIS 0-100)
    using the calibrated LightGBM ML models, stage-aware progress/financial risk,
    and velocity/acceleration dynamics from PAIMANA.
    """
    # 1. Model inference
    probs = paimana_ml.predict_probabilities(features)
    if cost_risk is not None and cost_risk > 0:
        probs["cost_risk_1m"] = min(1.0, max(0.0, cost_risk))
    if time_risk is not None and time_risk > 0:
        probs["schedule_risk_1m"] = min(1.0, max(0.0, time_risk))

    # 2. Component risks (T, C, P, F, ML_combined)
    comps = paimana_ml.compute_component_risks(features, probs)

    # 3. Composite DPHIS calculation
    snapshots_so_far = int(features.get("snapshots_so_far", 1) or 1)
    res = paimana_ml.compute_composite_dphis(
        components=comps,
        previous_current_risk=previous_dphis,
        previous_velocity=features.get("previous_risk_velocity"),
        snapshots_so_far=snapshots_so_far
    )

    final_dphis = res["dphis"]
    tier_str = res["risk_tier"].lower()
    if tier_str == "critical":
        level = RiskLevel.CRITICAL
    elif tier_str == "high":
        level = RiskLevel.HIGH
    elif tier_str in ("medium", "watch"):
        level = RiskLevel.MODERATE
    else:
        level = RiskLevel.LOW

    # Trend calculation
    prev_val = previous_dphis if previous_dphis is not None else round(max(5.0, final_dphis - res["risk_velocity"]), 1)
    change = round(final_dphis - prev_val, 1)
    if res["risk_velocity"] >= 1.5:
        direction = "WORSENING"
    elif res["risk_velocity"] <= -1.5:
        direction = "IMPROVING"
    else:
        direction = "STABLE"

    return DPHISScore(
        project_id=project_id,
        dphis=final_dphis,
        level=level,
        components=RiskComponents(
            time=round(comps["T_time_risk"], 3),
            cost=round(comps["C_cost_risk"], 3),
            progress=round(comps["P_progress_risk"], 3),
            milestone=round(float(features.get("schedule_slippage_months", 0.0) or 0.0) / 36.0, 3),
            financial=round(comps["F_financial_risk"], 3),
            implementation=round(comps["ML_combined_risk"], 3),
        ),
        trend=RiskTrend(
            previous=prev_val,
            current=final_dphis,
            change_pts=change,
            direction=direction,
        ),
        trend_multiplier=round(1.0 + (res["emerging_risk"] - 50.0) / 100.0 * 0.15, 3),
        timestamp=datetime.utcnow()
    )

