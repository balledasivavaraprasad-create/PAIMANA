"""Per-Tool Quotas and Duplicate Execution Detection.

Prevents runaway repetition of expensive tools and flags duplicate tool requests
when state has not materially mutated since previous invocation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolQuota:
    """Invocation constraints bounding specific tools within an investigation and over time."""
    tool_name: str
    max_calls_per_investigation: int = 2
    max_calls_per_hour: int = 10
    max_concurrent_calls: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "max_calls_per_investigation": self.max_calls_per_investigation,
            "max_calls_per_hour": self.max_calls_per_hour,
            "max_concurrent_calls": self.max_concurrent_calls,
        }


# Standard default quotas for tools
STANDARD_QUOTAS: dict[str, ToolQuota] = {
    "financial_velocity": ToolQuota(tool_name="financial_velocity", max_calls_per_investigation=2),
    "milestone_audit": ToolQuota(tool_name="milestone_audit", max_calls_per_investigation=2),
    "peer_intelligence": ToolQuota(tool_name="peer_intelligence", max_calls_per_investigation=1),
    "approval_timeline": ToolQuota(tool_name="approval_timeline", max_calls_per_investigation=2),
    "memory_retrieval": ToolQuota(tool_name="memory_retrieval", max_calls_per_investigation=2),
    "shap_attribution": ToolQuota(tool_name="shap_attribution", max_calls_per_investigation=1),
    "gis_satellite_validation": ToolQuota(tool_name="gis_satellite_validation", max_calls_per_investigation=1),
    "field_muster_rolls": ToolQuota(tool_name="field_muster_rolls", max_calls_per_investigation=1),
}


class ToolQuotaManager:
    """Enforces per-tool execution limits and detects semantic repetition."""

    def __init__(self, quotas: Optional[dict[str, ToolQuota]] = None):
        self.quotas: dict[str, ToolQuota] = dict(STANDARD_QUOTAS)
        if quotas:
            self.quotas.update(quotas)
        self.invocation_counts: dict[str, int] = {}
        self.last_tool_params: dict[str, Any] = {}

    def get_quota(self, tool_name: str) -> ToolQuota:
        """Retrieves quota for a tool or provides default."""
        base = tool_name.replace("tool_", "").lower()
        for k, q in self.quotas.items():
            if k in base or base in k:
                return q
        return ToolQuota(tool_name=tool_name, max_calls_per_investigation=2)

    def check_quota(self, tool_name: str) -> tuple[bool, Optional[str]]:
        """Verifies if the tool invocation satisfies its allocated quota.
        
        Returns (is_allowed, error_reason).
        """
        quota = self.get_quota(tool_name)
        count = self.invocation_counts.get(tool_name, 0)

        if count >= quota.max_calls_per_investigation:
            return False, f"TOOL_QUOTA_EXCEEDED: '{tool_name}' reached limit ({count}/{quota.max_calls_per_investigation} calls)."

        return True, None

    def record_execution(self, tool_name: str, params: Optional[dict[str, Any]] = None):
        """Records an execution of the given tool."""
        self.invocation_counts[tool_name] = self.invocation_counts.get(tool_name, 0) + 1
        if params is not None:
            self.last_tool_params[tool_name] = params

    def check_duplicate_request(self, tool_name: str, params: Optional[dict[str, Any]] = None) -> tuple[bool, Optional[str]]:
        """Detects whether this tool is being invoked with identical parameters consecutively."""
        if tool_name in self.last_tool_params and params is not None:
            if self.last_tool_params[tool_name] == params:
                return True, f"DUPLICATE_TOOL_REQUEST: Tool '{tool_name}' requested with identical parameters without state mutation."
        return False, None
