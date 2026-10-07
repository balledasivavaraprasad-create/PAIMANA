"""Multidimensional Investigation Convergence Subpackage.

Provides disciplined convergence evaluation, explicit ConvergenceState,
risk-calibrated ConvergencePolicy, diminishing returns detection,
saturation and oscillation tracking, and auditable TerminationRecord logging.
"""
from .models import (
    ConvergenceStatus,
    ConvergenceState,
    TerminationRecord,
    ReopenTrigger,
)
from .convergence_policy import ConvergencePolicy
from .evidence_coverage import EvidenceCoverageEvaluator
from .hypothesis_separation import HypothesisSeparationEvaluator
from .hypothesis_stability import HypothesisStabilityEvaluator
from .contradiction_resolution import ContradictionResolutionEvaluator
from .causal_convergence import CausalConvergenceEvaluator
from .decision_readiness import DecisionReadinessEvaluator
from .information_gain import InformationGainEvaluator
from .diminishing_returns import DiminishingReturnsDetector
from .saturation import EvidenceSaturationDetector
from .oscillation import HypothesisOscillationDetector
from .reopen_policy import ReopenPolicyManager
from .termination_trace import TerminationTraceBuilder
from .convergence_engine import ConvergenceEngine

__all__ = [
    "ConvergenceStatus",
    "ConvergenceState",
    "TerminationRecord",
    "ReopenTrigger",
    "ConvergencePolicy",
    "EvidenceCoverageEvaluator",
    "HypothesisSeparationEvaluator",
    "HypothesisStabilityEvaluator",
    "ContradictionResolutionEvaluator",
    "CausalConvergenceEvaluator",
    "DecisionReadinessEvaluator",
    "InformationGainEvaluator",
    "DiminishingReturnsDetector",
    "EvidenceSaturationDetector",
    "HypothesisOscillationDetector",
    "ReopenPolicyManager",
    "TerminationTraceBuilder",
    "ConvergenceEngine",
]
