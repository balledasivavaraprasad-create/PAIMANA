from typing import Dict, Any, Optional
from app.models.risk import DPHISScore, RiskLevel, RiskComponents, RiskTrend

WEIGHTS = {
    "time": 0.25,
    "cost": 0.20,
    "progress": 0.20,
    "milestone": 0.15,
    "financial": 0.10,
    "implementation": 0.10,
}

def calculate_dphis(
    project_id: str,
    features: Dict[str, float],
    cost_risk: float,
    time_risk: float,
    previous_dphis: Optional[float] = None
) -> DPHISScore:
    """
    Computes the Dynamic Project Health and Intervention Score (DPHIS 0-100)
    combining predictive ML risks, physical-financial gaps, and trend acceleration.
    """
    # 1. Component Risks (0.0 to 1.0)
    time_comp = min(1.0, max(0.0, time_risk))
    cost_comp = min(1.0, max(0.0, cost_risk))

    # Progress risk: combination of PFD (gap) and stagnation months
    pfd = features.get("physical_financial_gap", 0.0)
    stagnation = features.get("stagnation_months", 0.0)
    progress_comp = min(1.0, max(0.0, (pfd / 35.0) * 0.6 + (stagnation / 4.0) * 0.4))

    # Milestone risk: delay rate
    milestone_comp = min(1.0, max(0.0, features.get("milestone_delay_rate", 0.0)))

    # Financial risk: expenditure ratio vs completion
    exp_ratio = features.get("expenditure_ratio", 0.0)
    phys_prog = features.get("current_physical_progress", 0.0) / 100.0
    fin_comp = min(1.0, max(0.0, max(0.0, exp_ratio - phys_prog)))

    # Implementation: environmental hazard & state execution factor
    hazard = features.get("environmental_hazard_index", 0.0)
    state_factor = 1.0 - features.get("state_execution_index", 0.7)
    impl_comp = min(1.0, max(0.0, hazard * 0.6 + state_factor * 0.4))

    # 2. Weighted Base Score (0 to 1)
    base_score = (
        time_comp * WEIGHTS["time"] +
        cost_comp * WEIGHTS["cost"] +
        progress_comp * WEIGHTS["progress"] +
        milestone_comp * WEIGHTS["milestone"] +
        fin_comp * WEIGHTS["financial"] +
        impl_comp * WEIGHTS["implementation"]
    )

    # 3. Trend Multiplier
    trend_multiplier = 1.0
    if previous_dphis is not None and previous_dphis > 0:
        prev_fraction = previous_dphis / 100.0
        if base_score > prev_fraction:
            # Worsening trajectory adds up to 15% momentum multiplier
            trend_multiplier = min(1.15, 1.0 + (base_score - prev_fraction) * 0.5)

    final_dphis = round(min(100.0, max(5.0, base_score * trend_multiplier * 100.0)), 1)

    # 4. Determine Risk Tier
    if final_dphis >= 75.0:
        level = RiskLevel.CRITICAL
    elif final_dphis >= 50.0:
        level = RiskLevel.HIGH
    elif final_dphis >= 25.0:
        level = RiskLevel.MODERATE
    else:
        level = RiskLevel.LOW

    # 5. Trend Analysis
    prev_val = previous_dphis if previous_dphis is not None else round(max(10.0, final_dphis - 4.1), 1)
    change = round(final_dphis - prev_val, 1)
    if change > 1.5:
        direction = "WORSENING"
    elif change < -1.5:
        direction = "IMPROVING"
    else:
        direction = "STABLE"

    return DPHISScore(
        project_id=project_id,
        dphis=final_dphis,
        level=level,
        components=RiskComponents(
            time=round(time_comp, 3),
            cost=round(cost_comp, 3),
            progress=round(progress_comp, 3),
            milestone=round(milestone_comp, 3),
            financial=round(fin_comp, 3),
            implementation=round(impl_comp, 3),
        ),
        trend=RiskTrend(
            previous=prev_val,
            current=final_dphis,
            change_pts=change,
            direction=direction,
        ),
        trend_multiplier=round(trend_multiplier, 3),
    )
