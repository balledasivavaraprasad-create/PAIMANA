"""Tool Cost Profiles for Resource Governance.

Specifies computational, latency, token, and external API cost profiles
for every tool in the PAIMANA ecosystem.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional
from .models import ResourceClass


@dataclass
class ToolCostProfile:
    """Standardized cost and performance profile for a registered tool."""
    tool_name: str
    resource_class: ResourceClass = ResourceClass.COMPUTE
    estimated_latency_ms: float = 200.0
    estimated_external_calls: int = 0
    estimated_llm_tokens: int = 0
    estimated_cost: float = 0.02
    historical_latency_p50: float = 180.0
    historical_latency_p95: float = 350.0
    failure_probability: float = 0.02

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "resource_class": self.resource_class.value if hasattr(self.resource_class, "value") else str(self.resource_class),
            "estimated_latency_ms": self.estimated_latency_ms,
            "estimated_external_calls": self.estimated_external_calls,
            "estimated_llm_tokens": self.estimated_llm_tokens,
            "estimated_cost": self.estimated_cost,
            "historical_latency_p50": self.historical_latency_p50,
            "historical_latency_p95": self.historical_latency_p95,
            "failure_probability": self.failure_probability,
        }


# Standard profiles for known PAIMANA tools
STANDARD_TOOL_PROFILES: dict[str, ToolCostProfile] = {
    "financial_velocity": ToolCostProfile(
        tool_name="financial_velocity",
        resource_class=ResourceClass.DATABASE,
        estimated_latency_ms=250.0,
        estimated_external_calls=1,
        estimated_llm_tokens=0,
        estimated_cost=0.03,
        historical_latency_p50=220.0,
        historical_latency_p95=400.0,
        failure_probability=0.01,
    ),
    "milestone_audit": ToolCostProfile(
        tool_name="milestone_audit",
        resource_class=ResourceClass.DATABASE,
        estimated_latency_ms=180.0,
        estimated_external_calls=0,
        estimated_llm_tokens=0,
        estimated_cost=0.015,
        historical_latency_p50=160.0,
        historical_latency_p95=280.0,
        failure_probability=0.01,
    ),
    "peer_intelligence": ToolCostProfile(
        tool_name="peer_intelligence",
        resource_class=ResourceClass.COMPUTE,
        estimated_latency_ms=500.0,
        estimated_external_calls=1,
        estimated_llm_tokens=400,
        estimated_cost=0.05,
        historical_latency_p50=450.0,
        historical_latency_p95=850.0,
        failure_probability=0.03,
    ),
    "approval_timeline": ToolCostProfile(
        tool_name="approval_timeline",
        resource_class=ResourceClass.EXTERNAL_API,
        estimated_latency_ms=750.0,
        estimated_external_calls=2,
        estimated_llm_tokens=0,
        estimated_cost=0.08,
        historical_latency_p50=650.0,
        historical_latency_p95=1200.0,
        failure_probability=0.05,
    ),
    "memory_retrieval": ToolCostProfile(
        tool_name="memory_retrieval",
        resource_class=ResourceClass.COMPUTE,
        estimated_latency_ms=120.0,
        estimated_external_calls=0,
        estimated_llm_tokens=200,
        estimated_cost=0.01,
        historical_latency_p50=100.0,
        historical_latency_p95=200.0,
        failure_probability=0.005,
    ),
    "shap_attribution": ToolCostProfile(
        tool_name="shap_attribution",
        resource_class=ResourceClass.COMPUTE,
        estimated_latency_ms=220.0,
        estimated_external_calls=0,
        estimated_llm_tokens=0,
        estimated_cost=0.02,
        historical_latency_p50=200.0,
        historical_latency_p95=350.0,
        failure_probability=0.01,
    ),
    "gis_satellite_validation": ToolCostProfile(
        tool_name="gis_satellite_validation",
        resource_class=ResourceClass.EXTERNAL_API,
        estimated_latency_ms=1200.0,
        estimated_external_calls=2,
        estimated_llm_tokens=0,
        estimated_cost=0.15,
        historical_latency_p50=1000.0,
        historical_latency_p95=2200.0,
        failure_probability=0.08,
    ),
    "field_muster_rolls": ToolCostProfile(
        tool_name="field_muster_rolls",
        resource_class=ResourceClass.EXTERNAL_API,
        estimated_latency_ms=850.0,
        estimated_external_calls=1,
        estimated_llm_tokens=0,
        estimated_cost=0.09,
        historical_latency_p50=750.0,
        historical_latency_p95=1500.0,
        failure_probability=0.04,
    ),
    "default": ToolCostProfile(
        tool_name="default",
        resource_class=ResourceClass.COMPUTE,
        estimated_latency_ms=200.0,
        estimated_external_calls=0,
        estimated_llm_tokens=0,
        estimated_cost=0.02,
        historical_latency_p50=180.0,
        historical_latency_p95=350.0,
        failure_probability=0.02,
    ),
}


def get_tool_cost_profile(tool_name: str) -> ToolCostProfile:
    """Retrieves the cost profile for a given tool name or returns default."""
    base_name = tool_name.replace("tool_", "").lower()
    for key, prof in STANDARD_TOOL_PROFILES.items():
        if key in base_name or base_name in key:
            return prof
    return STANDARD_TOOL_PROFILES["default"]
