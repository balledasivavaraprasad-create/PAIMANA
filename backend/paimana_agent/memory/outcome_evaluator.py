"""Closed-Loop Outcome Evaluator.

Analyzes empirical project metrics before and after an intervention to assess
true intervention effectiveness vs mere correlation or confounding.
"""
from __future__ import annotations
from typing import Any, Optional
from .models import AttributionClass


class OutcomeEvaluator:
    """Evaluates empirical outcomes and assigns rigorous causal attribution."""

    @classmethod
    def evaluate_outcome(cls, pre_metrics: dict, post_metrics: dict,
                         intervention_details: Optional[dict] = None,
                         confounders_reported: Optional[list[str]] = None) -> dict:
        """Evaluates delta metrics and returns attribution classification,

        effectiveness ratio, and outcome quality.
        """
        confounders = confounders_reported or []
        pre_risk = float(pre_metrics.get("risk_score", 50.0))
        post_risk = float(post_metrics.get("risk_score", 50.0))
        risk_delta = post_risk - pre_risk  # Negative is good (risk decreased)

        pre_gap = float(pre_metrics.get("progress_expenditure_gap_pct", 0.0))
        post_gap = float(post_metrics.get("progress_expenditure_gap_pct", 0.0))
        gap_delta = post_gap - pre_gap  # Negative is good (gap closed)

        pre_delay = float(pre_metrics.get("completion_delay_months", 0.0))
        post_delay = float(post_metrics.get("completion_delay_months", 0.0))
        delay_delta = post_delay - pre_delay  # Negative or zero is good

        # 1. Base Score calculation
        # Risk reduction up to 15 pts = 1.0 effectiveness
        risk_score_component = max(0.0, min(1.0, (-risk_delta) / 15.0)) if risk_delta < 0 else 0.0
        gap_score_component = max(0.0, min(1.0, (-gap_delta) / 10.0)) if gap_delta < 0 else 0.0
        delay_score_component = 1.0 if delay_delta <= 0 else max(0.0, 1.0 - (delay_delta / 6.0))

        raw_effectiveness = 0.50 * risk_score_component + 0.30 * gap_score_component + 0.20 * delay_score_component

        # Deterioration penalty
        if risk_delta > 5.0 or delay_delta > 3.0:
            raw_effectiveness = max(0.0, raw_effectiveness - 0.40)

        # 2. Confounder Discounting
        has_confounders = len(confounders) > 0
        discount = 0.70 if has_confounders else 1.00
        effectiveness = round(raw_effectiveness * discount, 3)

        # 3. Attribution Classification
        if risk_delta <= -8.0 and delay_delta <= 0.0 and not has_confounders:
            attribution: AttributionClass = "LIKELY_EFFECTIVE"
        elif risk_delta < -2.0 or (gap_delta < -3.0 and delay_delta <= 1.0):
            attribution = "POSSIBLY_EFFECTIVE"
        elif risk_delta >= 8.0 or delay_delta >= 4.0:
            attribution = "FAILED"
        elif risk_delta > 2.0 or delay_delta > 1.0:
            attribution = "LIKELY_INEFFECTIVE"
        else:
            attribution = "INCONCLUSIVE"

        # 4. Outcome Quality (data completeness and confidence in measurement)
        data_points_present = sum(1 for k in ["risk_score", "progress_expenditure_gap_pct", "completion_delay_months"]
                                  if k in post_metrics)
        outcome_quality = round(data_points_present / 3.0, 2)

        return {
            "attribution_class": attribution,
            "effectiveness_ratio": effectiveness,
            "outcome_quality": outcome_quality,
            "risk_delta": round(risk_delta, 1),
            "gap_delta": round(gap_delta, 1),
            "delay_delta": round(delay_delta, 1),
            "confounders_present": confounders,
            "is_success": attribution in {"LIKELY_EFFECTIVE", "POSSIBLY_EFFECTIVE"},
        }
