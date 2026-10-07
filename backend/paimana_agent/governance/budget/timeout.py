"""Hierarchical Timeout Governance.

Enforces strict timeout hierarchy across investigation, supervisor, tool calls,
and external APIs: Child timeouts can NEVER exceed parent remaining time budget.
"""
from __future__ import annotations
from typing import Any, Optional
from .models import InvestigationBudget


class TimeoutHierarchy:
    """Calculates and bounds execution timeouts across operation tiers."""

    DEFAULT_TOOL_TIMEOUT_MS = 5000.0
    DEFAULT_API_TIMEOUT_MS = 3000.0

    @classmethod
    def calculate_effective_tool_timeout(
        cls,
        budget: Optional[InvestigationBudget],
        requested_timeout_ms: Optional[float] = None,
    ) -> float:
        """Determines the maximum allowed tool timeout bounded by remaining budget time.
        
        Child tool timeout <= parent investigation remaining wall-clock seconds.
        """
        requested = requested_timeout_ms or cls.DEFAULT_TOOL_TIMEOUT_MS
        if not budget:
            return requested

        # Remaining seconds in budget
        rem_sec = budget.remaining_execution_seconds
        rem_ms = max(50.0, rem_sec * 1000.0)

        # Effective timeout is the strictly smaller value
        return min(requested, rem_ms)

    @classmethod
    def calculate_effective_api_timeout(
        cls,
        budget: Optional[InvestigationBudget],
        requested_timeout_ms: Optional[float] = None,
    ) -> float:
        """Determines child API timeout, bounded by parent tool timeout and budget."""
        tool_to = cls.calculate_effective_tool_timeout(budget, requested_timeout_ms)
        requested_api = requested_timeout_ms or cls.DEFAULT_API_TIMEOUT_MS
        return min(requested_api, tool_to)
