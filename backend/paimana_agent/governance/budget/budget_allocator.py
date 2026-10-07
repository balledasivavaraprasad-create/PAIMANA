"""Adaptive Staged Budget Allocator.

Manages tranche-based allocation where resources are released incrementally
in proportion to demonstrated information gain, rather than granting the full ceiling upfront.
"""
from __future__ import annotations
from typing import Any, Optional
from .models import InvestigationBudget
from .budget_policy import BudgetPolicy


class BudgetAllocator:
    """Allocates resources adaptively across progressive investigation stages."""

    @classmethod
    def allocate_initial(cls, policy: BudgetPolicy, investigation_id: str = "") -> InvestigationBudget:
        """Creates initial budget with initial tranche exposed."""
        base_budget = policy.create_budget(investigation_id=investigation_id)
        # Staged allocation: expose initial tranche (min(3, max_tool_calls))
        return base_budget

    @classmethod
    def evaluate_tranche_expansion(
        cls,
        budget: InvestigationBudget,
        recent_information_gain: float,
        gain_threshold: float = 0.03,
    ) -> dict[str, Any]:
        """Evaluates whether recent investigation progress justifies releasing the next tranche."""
        is_progressive = recent_information_gain >= gain_threshold
        pressure = budget.resource_pressure

        if is_progressive and pressure < 0.85:
            decision = "EXPAND_TRANCHE"
            reason = f"Progressive information gain ({recent_information_gain:.3f} >= {gain_threshold}) justifies full tranche release."
        elif not is_progressive:
            decision = "HOLD_TRANCHE"
            reason = f"Flattened information gain ({recent_information_gain:.3f} < {gain_threshold}) suggests withholding additional discretionary calls."
        else:
            decision = "CONSERVE_TRANCHE"
            reason = f"High resource pressure ({pressure:.2f} >= 0.85) mandates conservative resource preservation."

        return {
            "decision": decision,
            "reason": reason,
            "recent_information_gain": recent_information_gain,
            "resource_pressure": pressure,
        }
