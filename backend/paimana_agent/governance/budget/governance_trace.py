"""Governance Decision Trace and Audit Builder.

Captures end-to-end resource governance telemetry: initial budget envelopes,
actual ledger consumption, reservations, expansions, degradations, and quotas.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Optional
from .models import InvestigationBudget
from .budget_ledger import ResourceLedger
from .budget_reservation import ReservationManager
from .tool_quota import ToolQuotaManager
from .degradation import DegradationLevel
from .quality_tier import InvestigationQualityTier


@dataclass
class GovernanceDecisionTrace:
    """Immutable audit record of all resource governance actions in an investigation."""
    investigation_id: str
    initial_budget: dict[str, Any]
    actual_usage: dict[str, Any]
    resource_pressure: float
    degradation_level: str
    quality_tier: str
    termination_reason: Optional[str] = None
    budget_expansions: list[dict[str, Any]] = field(default_factory=list)
    quotas_triggered: list[str] = field(default_factory=list)
    variance_summary: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "investigation_id": self.investigation_id,
            "initial_budget": self.initial_budget,
            "actual_usage": self.actual_usage,
            "resource_pressure": self.resource_pressure,
            "degradation_level": self.degradation_level,
            "quality_tier": self.quality_tier,
            "termination_reason": self.termination_reason,
            "budget_expansions": list(self.budget_expansions),
            "quotas_triggered": list(self.quotas_triggered),
            "variance_summary": self.variance_summary,
            "timestamp": self.timestamp,
        }


class GovernanceTraceBuilder:
    """Constructs auditable governance traces and dashboards."""

    @classmethod
    def build_trace(
        cls,
        budget: InvestigationBudget,
        ledger: Optional[ResourceLedger] = None,
        quota_mgr: Optional[ToolQuotaManager] = None,
        expansions: Optional[list[Any]] = None,
        degradation_level: DegradationLevel = DegradationLevel.LEVEL_1_NORMAL,
        quality_tier: InvestigationQualityTier = InvestigationQualityTier.TIER_1_FULL,
        termination_reason: Optional[str] = None,
    ) -> GovernanceDecisionTrace:
        """Constructs an auditable GovernanceDecisionTrace from live subsystems."""
        var_summary = ledger.get_variance_summary() if ledger else {}
        exps = [e.to_dict() if hasattr(e, "to_dict") else dict(e) for e in (expansions or [])]

        quotas_hit = []
        if quota_mgr:
            for t_name, count in quota_mgr.invocation_counts.items():
                q = quota_mgr.get_quota(t_name)
                if count >= q.max_calls_per_investigation:
                    quotas_hit.append(f"{t_name} ({count}/{q.max_calls_per_investigation})")

        return GovernanceDecisionTrace(
            investigation_id=budget.investigation_id,
            initial_budget={
                "max_tool_calls": budget.max_tool_calls,
                "max_iterations": budget.max_iterations,
                "max_llm_calls": budget.max_llm_calls,
                "max_execution_seconds": budget.max_execution_seconds,
                "max_estimated_cost": budget.max_estimated_cost,
                "reserved_emergency_budget": budget.reserved_emergency_budget,
            },
            actual_usage=budget.consumed.to_dict(),
            resource_pressure=budget.resource_pressure,
            degradation_level=degradation_level.value if hasattr(degradation_level, "value") else str(degradation_level),
            quality_tier=quality_tier.value if hasattr(quality_tier, "value") else str(quality_tier),
            termination_reason=termination_reason,
            budget_expansions=exps,
            quotas_triggered=quotas_hit,
            variance_summary=var_summary,
        )

    @classmethod
    def build_dashboard(cls, budget: InvestigationBudget, ledger: Optional[ResourceLedger] = None) -> dict[str, Any]:
        """Builds an operational resource health dashboard summary."""
        used_calls = max(budget.tool_calls_used, budget.consumed.tool_calls)
        pressure = budget.resource_pressure
        p_label = "NORMAL" if pressure < 0.50 else "COST_AWARE" if pressure < 0.75 else "CONSERVATIVE" if pressure < 0.90 else "EMERGENCY_ONLY"

        return {
            "investigation_id": budget.investigation_id,
            "resource_pressure": pressure,
            "resource_pressure_label": p_label,
            "tool_calls_progress": f"{used_calls} / {budget.max_tool_calls}",
            "llm_calls_progress": f"{budget.consumed.llm_calls} / {budget.max_llm_calls}",
            "execution_seconds_progress": f"{budget.consumed.execution_seconds:.1f} / {budget.max_execution_seconds:.1f}s",
            "cost_progress": f"${budget.consumed.estimated_cost:.3f} / ${budget.max_estimated_cost:.2f}",
            "is_exhausted": budget.is_exhausted(),
            "variance": ledger.get_variance_summary() if ledger else {},
        }
