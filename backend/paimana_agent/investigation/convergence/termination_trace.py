"""Termination Trace Builder & Convergence Dashboard.

Assembles detailed audit records explaining why an investigation stopped and generates
the Executive Convergence Dashboard for administrative inspection.
"""
from __future__ import annotations
import time
from typing import Any, Optional
from .models import ConvergenceState, TerminationRecord


class TerminationTraceBuilder:
    """Builds auditable termination records and executive convergence dashboards."""

    @classmethod
    def build_termination_record(
        cls,
        conv_state: ConvergenceState,
        best_candidate: Optional[Any] = None,
        iterations: int = 0,
        tool_calls: int = 0,
        threshold: float = 0.04
    ) -> TerminationRecord:
        """Constructs a permanent TerminationRecord from the final ConvergenceState."""
        best_tool = getattr(best_candidate, "tool_name", None) if best_candidate else None
        expected_gain = getattr(best_candidate, "expected_information_gain", 0.0) if best_candidate else 0.0

        return TerminationRecord(
            status=conv_state.status,
            evidence_coverage=conv_state.evidence_coverage,
            hypothesis_separation=conv_state.hypothesis_separation,
            hypothesis_stability=conv_state.hypothesis_stability,
            contradictions_remaining=conv_state.unresolved_material_questions,
            causal_support=conv_state.causal_support,
            decision_readiness=conv_state.decision_readiness,
            best_remaining_tool=best_tool,
            expected_information_gain=expected_gain,
            threshold=threshold,
            iterations=iterations,
            tool_calls=tool_calls,
            termination_reason=conv_state.termination_reason or conv_state.status,
            explanation=conv_state.explanation,
            timestamp=time.time(),
        )

    @classmethod
    def build_convergence_dashboard(
        cls,
        conv_state: ConvergenceState,
        best_candidate: Optional[Any] = None,
        threshold: float = 0.04
    ) -> dict[str, Any]:
        """Constructs the executive convergence dashboard dictionary."""
        next_tool = getattr(best_candidate, "tool_name", "None") if best_candidate else "None"
        next_gain = getattr(best_candidate, "expected_information_gain", 0.0) if best_candidate else 0.0

        return {
            "evidence_coverage_pct": round(conv_state.evidence_coverage * 100.0, 1),
            "hypothesis_separation_pct": round(conv_state.hypothesis_separation * 100.0, 1),
            "hypothesis_stability_pct": round(conv_state.hypothesis_stability * 100.0, 1),
            "contradiction_resolution_pct": round(conv_state.contradiction_resolution * 100.0, 1),
            "causal_support_pct": round(conv_state.causal_support * 100.0, 1),
            "decision_readiness_pct": round(conv_state.decision_readiness * 100.0, 1),
            "expected_information_gain": {
                "next_best_tool": next_tool,
                "expected_gain": round(next_gain, 3),
                "threshold": round(threshold, 3),
            },
            "status": conv_state.status,
            "termination_reason": conv_state.termination_reason,
            "is_converged": conv_state.is_converged,
            "explanation": conv_state.explanation,
            "iteration": conv_state.iteration,
            "unresolved_contradictions": conv_state.unresolved_material_questions,
        }
