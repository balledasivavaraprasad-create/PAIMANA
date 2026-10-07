"""Cost model for normalizing operational burden into ranking score (higher is better)."""
from __future__ import annotations
from typing import Any


class CostModel:
    """Calculates normalized cost utility score (0.0 to 1.0) where 1.0 represents lowest burden."""

    def compute_cost_score(
        self,
        candidate_cost: float,
        direct_monetary_burden: float = 0.20,
        staff_effort: float = 0.30,
        management_overhead: float = 0.20,
        delay_introduced_days: float = 0.0,
    ) -> tuple[float, dict[str, Any]]:
        """Computes cost score: cost_score = 1.0 - normalized_burden."""
        # Normalize delay (0 to 60 days maps to 0.0 to 1.0)
        delay_factor = min(1.0, delay_introduced_days / 60.0)

        # Composite burden
        composite_burden = (
            0.40 * candidate_cost
            + 0.20 * direct_monetary_burden
            + 0.20 * staff_effort
            + 0.10 * management_overhead
            + 0.10 * delay_factor
        )
        composite_burden = max(0.02, min(0.98, composite_burden))
        cost_score = round(1.0 - composite_burden, 3)

        breakdown = {
            "score": cost_score,
            "normalized_burden": round(composite_burden, 3),
            "candidate_intrinsic_cost": round(candidate_cost, 3),
            "delay_penalty": round(0.10 * delay_factor, 3),
        }
        return cost_score, breakdown
