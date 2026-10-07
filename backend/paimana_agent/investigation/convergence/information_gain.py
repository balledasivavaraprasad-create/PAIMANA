"""Information Gain and Expected Value Evaluator.

Measures realized marginal information gain between iterations and calculates
the Expected Value of Next Investigation Step (EV) to determine whether
an additional tool invocation is economically and scientifically justified.
"""
from __future__ import annotations
from typing import Any, Optional


class InformationGainEvaluator:
    """Evaluates realized and expected information gains across investigation steps."""

    @classmethod
    def compute_marginal_gain(
        cls,
        previous_uncertainty: float,
        current_uncertainty: float
    ) -> float:
        """Calculates realized reduction in uncertainty after a tool execution."""
        return max(0.0, float(previous_uncertainty - current_uncertainty))

    @classmethod
    def evaluate_expected_value_of_next_step(
        cls,
        candidate: Any,
        event_severity: str = "MEDIUM",
        state: Optional[Any] = None
    ) -> dict[str, Any]:
        """Calculates Expected Value of Next Step:

        EV = expected_information_gain * decision_relevance * impact - cost - delay
        """
        gain = getattr(candidate, "expected_information_gain", 0.05)
        disc = getattr(candidate, "discrimination_power", 0.50)
        auth = getattr(candidate, "source_authority", 0.80)
        cost = getattr(candidate, "acquisition_cost", 0.05)
        delay = getattr(candidate, "latency_cost", 0.02)

        # Impact multiplier by event severity
        sev = (event_severity or "MEDIUM").upper()
        if sev == "CRITICAL":
            impact = 1.60
        elif sev == "HIGH":
            impact = 1.30
        elif sev == "LOW":
            impact = 0.75
        else:
            impact = 1.00

        # Decision relevance incorporates discrimination power and authority
        decision_relevance = min(1.0, 0.50 * disc + 0.50 * auth)

        # EV calculation
        gross_value = gain * decision_relevance * impact
        net_ev = gross_value - (cost + delay)

        return {
            "expected_value": round(net_ev, 3),
            "expected_gain": round(gain, 3),
            "decision_relevance": round(decision_relevance, 3),
            "impact_multiplier": impact,
            "cost_burden": round(cost + delay, 3),
            "is_worthwhile": net_ev > 0.0,
        }
