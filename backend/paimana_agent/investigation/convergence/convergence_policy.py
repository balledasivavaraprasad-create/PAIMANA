"""Risk-sensitive convergence policies for investigation termination.

Calibrates evidentiary thresholds based on project risk and anomaly severity.
High/Critical severity investigations demand stronger evidence coverage, higher
hypothesis separation, lower contradiction tolerance, and higher causal support.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class ConvergencePolicy:
    """Configurable multidimensional threshold rules for investigation convergence."""
    event_severity: str = "MEDIUM"

    min_evidence_coverage: float = 0.70
    min_hypothesis_separation: float = 0.20
    min_hypothesis_stability: float = 0.85
    min_contradiction_resolution: float = 0.80
    min_causal_support: float = 0.60
    min_decision_readiness: float = 0.55

    minimum_useful_gain: float = 0.04
    min_consecutive_stable_steps: int = 2
    diminishing_returns_window: int = 3
    diminishing_returns_threshold: float = 0.03

    max_unresolved_critical_contradictions: int = 0
    max_unresolved_high_contradictions: int = 0

    @classmethod
    def for_severity(cls, severity: str = "MEDIUM") -> ConvergencePolicy:
        """Constructs a risk-calibrated policy instance based on event/project severity."""
        sev = (severity or "MEDIUM").upper()

        if sev == "CRITICAL":
            return cls(
                event_severity="CRITICAL",
                min_evidence_coverage=0.85,
                min_hypothesis_separation=0.30,
                min_hypothesis_stability=0.90,
                min_contradiction_resolution=1.00,  # Zero tolerance for unresolved contradictions
                min_causal_support=0.75,            # Demands Level 4+ causal support
                min_decision_readiness=0.75,
                minimum_useful_gain=0.02,           # Willing to execute tools even for small gains
                diminishing_returns_window=3,
                diminishing_returns_threshold=0.02,
                max_unresolved_critical_contradictions=0,
                max_unresolved_high_contradictions=0,
            )
        elif sev == "HIGH":
            return cls(
                event_severity="HIGH",
                min_evidence_coverage=0.80,
                min_hypothesis_separation=0.25,
                min_hypothesis_stability=0.88,
                min_contradiction_resolution=0.90,
                min_causal_support=0.70,
                min_decision_readiness=0.65,
                minimum_useful_gain=0.03,
                diminishing_returns_window=3,
                diminishing_returns_threshold=0.025,
                max_unresolved_critical_contradictions=0,
                max_unresolved_high_contradictions=0,
            )
        elif sev == "LOW":
            return cls(
                event_severity="LOW",
                min_evidence_coverage=0.50,
                min_hypothesis_separation=0.15,
                min_hypothesis_stability=0.80,
                min_contradiction_resolution=0.70,
                min_causal_support=0.45,
                min_decision_readiness=0.45,
                minimum_useful_gain=0.06,           # Shuts down early if tool gains are modest
                diminishing_returns_window=2,
                diminishing_returns_threshold=0.04,
                max_unresolved_critical_contradictions=0,
                max_unresolved_high_contradictions=1,
            )
        else:  # MEDIUM
            return cls(
                event_severity="MEDIUM",
                min_evidence_coverage=0.70,
                min_hypothesis_separation=0.20,
                min_hypothesis_stability=0.85,
                min_contradiction_resolution=0.80,
                min_causal_support=0.60,
                min_decision_readiness=0.55,
                minimum_useful_gain=0.04,
                diminishing_returns_window=3,
                diminishing_returns_threshold=0.03,
                max_unresolved_critical_contradictions=0,
                max_unresolved_high_contradictions=0,
            )

    def to_dict(self) -> dict:
        return {
            "event_severity": self.event_severity,
            "min_evidence_coverage": self.min_evidence_coverage,
            "min_hypothesis_separation": self.min_hypothesis_separation,
            "min_hypothesis_stability": self.min_hypothesis_stability,
            "min_contradiction_resolution": self.min_contradiction_resolution,
            "min_causal_support": self.min_causal_support,
            "min_decision_readiness": self.min_decision_readiness,
            "minimum_useful_gain": self.minimum_useful_gain,
            "diminishing_returns_window": self.diminishing_returns_window,
            "diminishing_returns_threshold": self.diminishing_returns_threshold,
            "max_unresolved_critical_contradictions": self.max_unresolved_critical_contradictions,
            "max_unresolved_high_contradictions": self.max_unresolved_high_contradictions,
        }
