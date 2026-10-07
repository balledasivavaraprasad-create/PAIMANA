"""Resource Classifications and Resource Demand Models."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional
from .models import ResourceClass


@dataclass
class ResourceDemand:
    """Estimated demand of a single tool execution or planning step."""
    tool_name: str
    resource_class: ResourceClass = ResourceClass.COMPUTE
    estimated_latency_ms: float = 200.0
    estimated_external_calls: int = 0
    estimated_llm_tokens: int = 0
    estimated_cost: float = 0.02
    is_emergency: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "resource_class": self.resource_class.value if hasattr(self.resource_class, "value") else str(self.resource_class),
            "estimated_latency_ms": self.estimated_latency_ms,
            "estimated_external_calls": self.estimated_external_calls,
            "estimated_llm_tokens": self.estimated_llm_tokens,
            "estimated_cost": self.estimated_cost,
            "is_emergency": self.is_emergency,
        }
