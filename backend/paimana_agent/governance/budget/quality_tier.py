"""Investigation Quality Tiers and Minimum Viable Investigation (MVI).

Defines explicit quality guarantees for each resource tier, preventing silent
quality degradation and establishing minimum evidentiary standards.
"""
from __future__ import annotations
from enum import Enum
from typing import Any, Optional
from .models import InvestigationBudget


class InvestigationQualityTier(str, Enum):
    """Investigation depth and evidentiary rigor guarantee tiers."""
    TIER_1_FULL = "TIER_1_FULL"                # Full tools, LLM planner, deep memory, causal corroboration
    TIER_2_CONSTRAINED = "TIER_2_CONSTRAINED"  # Constrained tools, deterministic fallback, reduced memory
    TIER_3_RAPID_TRIAGE = "TIER_3_RAPID_TRIAGE"# Initial baseline triage only
    TIER_4_UNABLE = "TIER_4_UNABLE"            # Insufficient resources; human review required


class QualityTierManager:
    """Enforces minimum viable investigation (MVI) and classifies quality tier."""

    @classmethod
    def determine_tier(cls, budget: Optional[InvestigationBudget]) -> InvestigationQualityTier:
        """Assigns quality tier based on budget limits and remaining capacity."""
        if not budget:
            return InvestigationQualityTier.TIER_1_FULL

        if budget.is_exhausted() or budget.max_tool_calls <= 1:
            return InvestigationQualityTier.TIER_4_UNABLE
        elif budget.max_tool_calls <= 3 or budget.resource_pressure > 0.75:
            return InvestigationQualityTier.TIER_3_RAPID_TRIAGE
        elif budget.max_tool_calls <= 5 or budget.resource_pressure > 0.50:
            return InvestigationQualityTier.TIER_2_CONSTRAINED
        else:
            return InvestigationQualityTier.TIER_1_FULL

    @classmethod
    def check_minimum_viable_investigation(
        cls,
        evidence_items: list[Any],
        tools_used: list[str],
        severity: str = "MEDIUM",
    ) -> tuple[bool, list[str]]:
        """Verifies if the investigation satisfies the Minimum Viable Investigation (MVI) contract.
        
        MVI Contract:
        - LOW / MEDIUM: At least 2 distinct tools used and >= 2 evidence items.
        - HIGH / CRITICAL: At least 3 distinct tools used, >= 3 evidence items, and >= 2 independent source groups.
        """
        sev = (severity or "MEDIUM").upper()
        violations = []

        distinct_tools = set(tools_used)
        if len(distinct_tools) < 2:
            violations.append(f"MVI violation: Expected >= 2 distinct tools; only used {len(distinct_tools)}.")

        if len(evidence_items) < 2:
            violations.append(f"MVI violation: Expected >= 2 evidence items; only gathered {len(evidence_items)}.")

        if sev in ("HIGH", "CRITICAL"):
            if len(distinct_tools) < 3:
                violations.append(f"High-severity MVI violation: Expected >= 3 distinct tools; used {len(distinct_tools)}.")
            groups = set(getattr(e, "independence_group_id", getattr(e, "independence_group", None)) for e in evidence_items if getattr(e, "independence_group_id", getattr(e, "independence_group", None)))
            if len(groups) < 2:
                violations.append(f"High-severity MVI violation: Demands >= 2 independent source groups; found {len(groups)}.")

        is_satisfied = len(violations) == 0
        return is_satisfied, violations
