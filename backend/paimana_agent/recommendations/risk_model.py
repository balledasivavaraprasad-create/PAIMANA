"""Risk model separating expected project risk reduction from new implementation risk."""
from __future__ import annotations
from typing import Any


class RiskModel:
    """Calculates balanced risk score = risk_reduction * (1.0 - implementation_risk)."""

    def compute_risk_score(
        self,
        risk_reduction: float,
        implementation_risk: float
    ) -> tuple[float, dict[str, Any]]:
        """Calculates risk score and audit breakdown.
        
        Ensures a dangerous intervention with high potential benefit cannot win
        if its execution risk is unacceptably high.
        """
        clamped_rr = max(0.05, min(1.0, risk_reduction))
        clamped_ir = max(0.0, min(0.95, implementation_risk))
        risk_score = round(clamped_rr * (1.0 - clamped_ir), 3)

        breakdown = {
            "score": risk_score,
            "risk_reduction": round(clamped_rr, 3),
            "implementation_risk": round(clamped_ir, 3),
            "safety_factor": round(1.0 - clamped_ir, 3),
        }
        return risk_score, breakdown
