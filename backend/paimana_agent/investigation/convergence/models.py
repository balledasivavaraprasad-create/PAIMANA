"""Data models and constants for Multidimensional Investigation Convergence.

Defines first-class ConvergenceState, TerminationRecord, ReopenTrigger,
and ConvergenceStatus constants.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Optional


class ConvergenceStatus:
    """Formal convergence and termination lifecycle statuses."""
    NOT_CONVERGED = "NOT_CONVERGED"
    PROGRESSING = "PROGRESSING"
    NEAR_CONVERGED = "NEAR_CONVERGED"
    CONVERGED = "CONVERGED"
    PARTIALLY_CONVERGED = "PARTIALLY_CONVERGED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONTRADICTORY = "CONTRADICTORY"
    NO_HIGH_VALUE_EVIDENCE_AVAILABLE = "NO_HIGH_VALUE_EVIDENCE_AVAILABLE"
    NO_HIGH_VALUE_TOOL_REMAINING = "NO_HIGH_VALUE_TOOL_REMAINING"  # alias
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    TOOL_LIMIT_REACHED = "TOOL_LIMIT_REACHED"  # alias
    TOOL_ACCESS_BLOCKED = "TOOL_ACCESS_BLOCKED"
    SYSTEM_ERROR = "SYSTEM_ERROR"


@dataclass
class ConvergenceState:
    """First-class multidimensional convergence evaluation for an investigation."""
    evidence_coverage: float = 0.0
    hypothesis_separation: float = 0.0
    hypothesis_stability: float = 0.0
    contradiction_resolution: float = 1.0
    causal_support: float = 0.0
    decision_readiness: float = 0.0

    marginal_information_gain: float = 0.0
    expected_information_gain: float = 0.0
    unresolved_material_questions: int = 0
    remaining_high_value_tools: int = 0

    data_quality: float = 0.80
    confidence_stability: float = 1.0

    status: str = ConvergenceStatus.NOT_CONVERGED
    termination_reason: Optional[str] = None
    should_terminate: bool = False
    explanation: str = "Investigation actively gathering evidence."
    iteration: int = 0
    dimension_scores: dict[str, float] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    @property
    def is_converged(self) -> bool:
        return self.status == ConvergenceStatus.CONVERGED

    def to_dict(self) -> dict:
        return {
            "evidence_coverage": round(self.evidence_coverage, 3),
            "hypothesis_separation": round(self.hypothesis_separation, 3),
            "hypothesis_stability": round(self.hypothesis_stability, 3),
            "contradiction_resolution": round(self.contradiction_resolution, 3),
            "causal_support": round(self.causal_support, 3),
            "decision_readiness": round(self.decision_readiness, 3),
            "marginal_information_gain": round(self.marginal_information_gain, 3),
            "expected_information_gain": round(self.expected_information_gain, 3),
            "unresolved_material_questions": self.unresolved_material_questions,
            "remaining_high_value_tools": self.remaining_high_value_tools,
            "data_quality": round(self.data_quality, 3),
            "confidence_stability": round(self.confidence_stability, 3),
            "status": self.status,
            "termination_reason": self.termination_reason,
            "should_terminate": self.should_terminate,
            "is_converged": self.is_converged,
            "explanation": self.explanation,
            "iteration": self.iteration,
            "dimension_scores": {k: round(v, 3) for k, v in self.dimension_scores.items()},
            "timestamp": self.timestamp,
        }


@dataclass
class TerminationRecord:
    """Permanent audit record explaining exactly how and why an investigation concluded."""
    status: str
    evidence_coverage: float
    hypothesis_separation: float
    hypothesis_stability: float
    contradictions_remaining: int
    causal_support: float
    decision_readiness: float
    best_remaining_tool: Optional[str] = None
    expected_information_gain: float = 0.0
    threshold: float = 0.04
    iterations: int = 0
    tool_calls: int = 0
    termination_reason: str = "SUFFICIENT_EVIDENCE"
    explanation: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "evidence_coverage": round(self.evidence_coverage, 3),
            "hypothesis_separation": round(self.hypothesis_separation, 3),
            "hypothesis_stability": round(self.hypothesis_stability, 3),
            "contradictions_remaining": self.contradictions_remaining,
            "causal_support": round(self.causal_support, 3),
            "decision_readiness": round(self.decision_readiness, 3),
            "best_remaining_tool": self.best_remaining_tool,
            "expected_information_gain": round(self.expected_information_gain, 3),
            "threshold": round(self.threshold, 3),
            "iterations": self.iterations,
            "tool_calls": self.tool_calls,
            "termination_reason": self.termination_reason,
            "explanation": self.explanation,
            "timestamp": self.timestamp,
        }


@dataclass
class ReopenTrigger:
    """Specification of an empirical event capable of reopening a converged investigation."""
    trigger_type: str  # NEW_AUTHORITATIVE_EVIDENCE, MATERIAL_RISK_CHANGE, CAUSAL_CONTRADICTION, INTERVENTION_FAILURE, DATA_CORRECTION
    severity: str      # LOW, MEDIUM, HIGH, CRITICAL
    evidence_ids: list[str] = field(default_factory=list)
    materiality: float = 0.0
    description: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "trigger_type": self.trigger_type,
            "severity": self.severity,
            "evidence_ids": list(self.evidence_ids),
            "materiality": round(self.materiality, 3),
            "description": self.description,
            "timestamp": self.timestamp,
        }
