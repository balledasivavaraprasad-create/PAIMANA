"""Benefit model for evaluating candidate expected utility."""
from __future__ import annotations
from typing import Any, Optional


class BenefitModel:
    """Calculates expected benefit utility score (0.0 to 1.0) across operational dimensions."""

    def compute_benefit_score(
        self,
        candidate_benefit: float,
        risk_reduction: float,
        schedule_improvement: float = 0.50,
        cost_avoidance: float = 0.50,
        problem_resolution: float = 0.50,
    ) -> tuple[float, dict[str, Any]]:
        """Computes composite benefit utility and component breakdown."""
        # Weighted utility components
        w_rr, w_si, w_ca, w_pr = 0.35, 0.25, 0.25, 0.15
        component_utility = (
            w_rr * risk_reduction
            + w_si * schedule_improvement
            + w_ca * cost_avoidance
            + w_pr * problem_resolution
        )

        # Blend candidate's intrinsic estimate with component utility
        final_benefit = 0.50 * candidate_benefit + 0.50 * component_utility
        final_benefit = round(max(0.05, min(1.0, final_benefit)), 3)

        breakdown = {
            "score": final_benefit,
            "components": {
                "risk_reduction_contrib": round(w_rr * risk_reduction, 3),
                "schedule_improvement_contrib": round(w_si * schedule_improvement, 3),
                "cost_avoidance_contrib": round(w_ca * cost_avoidance, 3),
                "problem_resolution_contrib": round(w_pr * problem_resolution, 3),
            },
            "candidate_intrinsic_benefit": round(candidate_benefit, 3),
        }
        return final_benefit, breakdown
