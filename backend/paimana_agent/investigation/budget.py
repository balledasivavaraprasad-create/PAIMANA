"""Investigation Budget, Operational Phases, and Convergence Detector.

Enforces execution constraints (step limits, latency budget, minimum utility thresholds)
and detects sound, evidence-grounded termination states.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Optional


class InvestigationPhase:
    """Operational investigation phases."""
    ORIENTATION = "ORIENTATION"          # Initial triage and foundational baseline metrics
    DISCRIMINATION = "DISCRIMINATION"    # Active separation of competing causal hypotheses
    VALIDATION = "VALIDATION"            # Independent corroboration of leading hypothesis
    DECISION_SUPPORT = "DECISION_SUPPORT"# Actionability checks and precedent learning
    CONCLUDED = "CONCLUDED"              # Terminal state reached


# CANONICAL RE-EXPORT: The single authoritative InvestigationBudget data model
# is defined in `paimana_agent.governance.budget.models`.
from ..governance.budget.models import InvestigationBudget, ResourceConsumption


class ConvergenceDetector:
    """Determines whether investigation has reached sound convergence or should terminate."""

    def __init__(self, budget: Optional[InvestigationBudget] = None, policy: Optional[Any] = None):
        self.budget = budget or InvestigationBudget()
        from .convergence import ConvergenceEngine, ConvergencePolicy
        self.policy = policy or ConvergencePolicy()
        self.engine = ConvergenceEngine(self.policy)

    def check_termination(self, state: Any, candidates: list[Any],
                          open_needs: list[Any]) -> tuple[bool, Optional[str], str]:
        """Returns (is_terminated, stop_reason, explanation)."""
        conv_state, term_record = self.engine.evaluate(
            state=state,
            candidates=candidates,
            open_needs=open_needs,
            budget=self.budget,
            iteration=len(getattr(state, "tools_used", []))
        )
        if hasattr(state, "convergence_state"):
            state.convergence_state = conv_state
            if hasattr(state, "convergence_history"):
                state.convergence_history.append(conv_state)
        if term_record and hasattr(state, "termination_record"):
            state.termination_record = term_record

        # Map stop reason for backwards compatibility with legacy strings
        stop_reason = conv_state.termination_reason or conv_state.status
        if conv_state.status == "BUDGET_EXHAUSTED":
            stop_reason = "TOOL_LIMIT_REACHED"
        elif conv_state.status == "CONVERGED":
            stop_reason = "SUFFICIENT_EVIDENCE"
        elif conv_state.status == "NO_HIGH_VALUE_EVIDENCE_AVAILABLE":
            stop_reason = "NO_HIGH_VALUE_TOOL_REMAINING"

        return conv_state.should_terminate, stop_reason, conv_state.explanation
