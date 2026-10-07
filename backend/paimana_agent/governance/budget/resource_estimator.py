"""Resource Estimator and Cost-Aware Tool Utility Calculator.

Integrates dynamic information gain with operational resource costs, latency penalties,
and prevailing resource pressure to select the most resource-efficient next step.
"""
from __future__ import annotations
from typing import Any, Optional
from .models import InvestigationBudget
from .resource_cost import ToolCostProfile, get_tool_cost_profile
from .resource import ResourceDemand


class ResourceEstimator:
    """Estimates resource demand and computes resource-adjusted tool value."""

    @classmethod
    def estimate_demand(cls, tool_name: str, is_emergency: bool = False) -> ResourceDemand:
        """Estimates resource demands for a tool execution."""
        profile = get_tool_cost_profile(tool_name)
        return ResourceDemand(
            tool_name=tool_name,
            resource_class=profile.resource_class,
            estimated_latency_ms=profile.estimated_latency_ms,
            estimated_external_calls=profile.estimated_external_calls,
            estimated_llm_tokens=profile.estimated_llm_tokens,
            estimated_cost=profile.estimated_cost,
            is_emergency=is_emergency,
        )

    @classmethod
    def calculate_resource_adjusted_value(
        cls,
        tool_name: str,
        expected_information_gain: float,
        decision_relevance: float = 1.0,
        evidence_quality: float = 1.0,
        budget: Optional[InvestigationBudget] = None,
    ) -> float:
        """Calculates resource-adjusted tool utility:
        
        resource_adjusted_value = (
            expected_information_gain * decision_relevance * evidence_quality
        ) / (
            estimated_cost + latency_penalty + resource_pressure
        )
        """
        profile = get_tool_cost_profile(tool_name)

        # Latency penalty: normalized to 0.05 per 1000ms
        latency_penalty = max(0.01, profile.estimated_latency_ms / 20000.0)

        # Resource pressure from current budget [0.0, 1.0]
        pressure = budget.resource_pressure if budget else 0.10

        # Cost scale factor (avoid dividing by near-zero)
        cost_term = max(0.05, profile.estimated_cost * 2.0)

        denominator = cost_term + latency_penalty + pressure
        numerator = expected_information_gain * decision_relevance * evidence_quality

        adjusted_val = numerator / max(0.05, denominator)
        return round(float(adjusted_val), 4)
