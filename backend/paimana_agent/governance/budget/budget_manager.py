"""Master Budget and Resource Governance Manager.

Coordinates budget tracking, resource reservations, quota enforcement,
graceful degradation, cost-aware tool utility, and auditable accounting.
"""
from __future__ import annotations
import uuid
from typing import Any, Optional
from .models import InvestigationBudget, ResourceConsumption
from .budget_policy import BudgetPolicy
from .budget_ledger import ResourceLedger
from .budget_reservation import ReservationManager, BudgetReservation
from .tool_quota import ToolQuotaManager, ToolQuota
from .resource_cost import ToolCostProfile, get_tool_cost_profile
from .resource_estimator import ResourceEstimator
from .degradation import GracefulDegradationManager, DegradationLevel
from .quality_tier import QualityTierManager, InvestigationQualityTier
from .escalation import BudgetEscalator, BudgetExpansionRequest
from .governance_trace import GovernanceTraceBuilder, GovernanceDecisionTrace


class BudgetManager:
    """Master Resource Governor for an individual investigation."""

    def __init__(
        self,
        budget: Optional[InvestigationBudget] = None,
        policy: Optional[BudgetPolicy] = None,
        investigation_id: str = "",
    ):
        self.investigation_id = investigation_id or f"inv_{uuid.uuid4().hex[:8]}"
        self.policy = policy or BudgetPolicy.for_severity(getattr(budget, "severity", "MEDIUM"))
        self.budget = budget or self.policy.create_budget(self.investigation_id)

        self.ledger = ResourceLedger(investigation_id=self.investigation_id)
        self.reservations = ReservationManager(self.budget)
        self.quotas = ToolQuotaManager()
        self.expansion_requests: list[BudgetExpansionRequest] = []

    def can_afford_step(self, tool_name: str, is_emergency: bool = False) -> tuple[bool, Optional[str]]:
        """Checks both tool quota and budget affordability before dispatching a tool."""
        # 1. Quota check
        allowed, reason = self.quotas.check_quota(tool_name)
        if not allowed:
            return False, reason

        # 2. Budget affordability check
        profile = get_tool_cost_profile(tool_name)
        can_afford = self.budget.can_afford(
            estimated_cost=profile.estimated_cost,
            estimated_latency_ms=profile.estimated_latency_ms,
            estimated_tokens=profile.estimated_llm_tokens,
            external_calls=profile.estimated_external_calls,
            is_emergency=is_emergency,
        )

        if not can_afford:
            return False, f"BUDGET_INSUFFICIENT: Cannot afford '{tool_name}' under current resource envelope."

        return True, None

    def reserve(self, tool_name: str, is_emergency: bool = False) -> Optional[BudgetReservation]:
        """Pre-allocates resources for a tool execution."""
        profile = get_tool_cost_profile(tool_name)
        return self.reservations.reserve(
            tool_name=tool_name,
            estimated_cost=profile.estimated_cost,
            estimated_latency_ms=profile.estimated_latency_ms,
            estimated_tokens=profile.estimated_llm_tokens,
            external_calls=profile.estimated_external_calls,
            is_emergency=is_emergency,
        )

    def settle(
        self,
        reservation_id: str,
        actual_latency_ms: float = 0.0,
        actual_cost: float = 0.0,
        actual_input_tokens: int = 0,
        actual_output_tokens: int = 0,
        actual_external_calls: int = 0,
        tool_name: str = "",
    ) -> bool:
        """Settles an active reservation, applies consumption, and logs ledger variance."""
        res = self.reservations.reservations.get(reservation_id)
        est_cost = res.estimated_cost if res else 0.0
        est_lat = res.estimated_latency_ms if res else 0.0

        settled = self.reservations.settle(
            reservation_id=reservation_id,
            actual_latency_ms=actual_latency_ms,
            actual_cost=actual_cost,
            actual_input_tokens=actual_input_tokens,
            actual_output_tokens=actual_output_tokens,
            actual_external_calls=actual_external_calls,
        )

        if settled:
            t_name = tool_name or (res.tool_name if res else "unknown_tool")
            self.quotas.record_execution(t_name)
            self.ledger.record_entry(
                operation_id=reservation_id,
                resource_type="TOOL_EXECUTION",
                resource_name=t_name,
                estimated_quantity=est_lat,
                actual_quantity=actual_latency_ms,
                estimated_cost=est_cost,
                actual_cost=actual_cost,
            )

        return settled

    def record_direct_call(
        self,
        tool_name: str,
        latency_ms: float = 0.0,
        cost: float = 0.0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        external_calls: int = 0,
        llm_calls: int = 0,
    ):
        """Directly records execution (useful for backward-compatible call paths)."""
        self.quotas.record_execution(tool_name)
        self.budget.record_call(
            latency_ms=latency_ms,
            cost=cost,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            external_calls=external_calls,
            llm_calls=llm_calls,
        )
        self.ledger.record_entry(
            operation_id=f"op_{len(self.ledger.entries)+1}",
            resource_type="DIRECT_CALL",
            resource_name=tool_name,
            estimated_quantity=latency_ms,
            actual_quantity=latency_ms,
            estimated_cost=cost,
            actual_cost=cost,
        )

    def request_budget_expansion(
        self,
        reason: str,
        requested_resources: dict[str, Any],
        current_uncertainty: float,
        expected_information_gain: float,
    ) -> BudgetExpansionRequest:
        """Submits an expansion request for evaluation."""
        req = BudgetExpansionRequest(
            investigation_id=self.investigation_id,
            reason=reason,
            requested_resources=requested_resources,
            current_uncertainty=current_uncertainty,
            expected_information_gain=expected_information_gain,
            severity=self.budget.severity,
        )
        evaluated = BudgetEscalator.evaluate_request(req, self.budget)
        self.expansion_requests.append(evaluated)
        return evaluated

    @property
    def degradation_level(self) -> DegradationLevel:
        return GracefulDegradationManager.evaluate_tier(self.budget)

    @property
    def quality_tier(self) -> InvestigationQualityTier:
        return QualityTierManager.determine_tier(self.budget)

    def get_dashboard(self) -> dict[str, Any]:
        """Provides real-time governance dashboard."""
        dash = GovernanceTraceBuilder.build_dashboard(self.budget, self.ledger)
        dash["degradation_level"] = self.degradation_level.value
        dash["quality_tier"] = self.quality_tier.value
        dash["active_reservations"] = len([r for r in self.reservations.reservations.values() if r.status == "PENDING"])
        return dash

    def build_trace(self, termination_reason: Optional[str] = None) -> GovernanceDecisionTrace:
        """Emits final auditable governance trace."""
        return GovernanceTraceBuilder.build_trace(
            budget=self.budget,
            ledger=self.ledger,
            quota_mgr=self.quotas,
            expansions=self.expansion_requests,
            degradation_level=self.degradation_level,
            quality_tier=self.quality_tier,
            termination_reason=termination_reason,
        )
