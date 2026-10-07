"""Graceful Degradation and Confidence Coupling.

Manages dynamic operational degradation under increasing resource pressure,
and guarantees that resource constraints explicitly reflect in lower evidence completeness
and qualified confidence rather than silently masking reduced investigation depth.
"""
from __future__ import annotations
from enum import Enum
from typing import Any, Optional
from .models import InvestigationBudget


class DegradationLevel(str, Enum):
    """Operational degradation tiers based on resource pressure."""
    LEVEL_1_NORMAL = "LEVEL_1_NORMAL"                # Pressure <= 0.50: LLM planner, full tools, deep memory
    LEVEL_2_COST_AWARE = "LEVEL_2_COST_AWARE"        # Pressure 0.50 - 0.75: Top-value tools only, standard LLM
    LEVEL_3_CONSTRAINED = "LEVEL_3_CONSTRAINED"      # Pressure 0.75 - 0.90: Deterministic planning, local evidence
    LEVEL_4_SAFE_TERMINATION = "LEVEL_4_SAFE_TERMINATION"  # Pressure > 0.90 or exhausted: Stop safely


class GracefulDegradationManager:
    """Evaluates operational degradation tier and adjusts confidence qualifiers."""

    @classmethod
    def evaluate_tier(cls, budget: InvestigationBudget) -> DegradationLevel:
        """Determines active degradation tier from prevailing resource pressure."""
        if budget.is_exhausted():
            return DegradationLevel.LEVEL_4_SAFE_TERMINATION

        p = budget.resource_pressure
        if p <= 0.50:
            return DegradationLevel.LEVEL_1_NORMAL
        elif p <= 0.75:
            return DegradationLevel.LEVEL_2_COST_AWARE
        elif p <= 0.90:
            return DegradationLevel.LEVEL_3_CONSTRAINED
        else:
            return DegradationLevel.LEVEL_4_SAFE_TERMINATION

    @classmethod
    def apply_confidence_coupling(
        cls,
        tier: DegradationLevel,
        raw_confidence: float,
        evidence_coverage: float,
    ) -> dict[str, Any]:
        """Couples resource constraints to reported confidence and evidence completeness.
        
        Hard Rule:
        Resource constraints -> reduced investigation -> lower evidence completeness -> higher uncertainty.
        Never allow resource constraints to silently produce the same confidence.
        """
        if tier == DegradationLevel.LEVEL_1_NORMAL:
            return {
                "adjusted_confidence": raw_confidence,
                "confidence_qualifier": "HIGH_CONFIDENCE" if raw_confidence >= 0.80 else "MODERATE_CONFIDENCE",
                "is_resource_constrained": False,
                "evidence_completeness_factor": 1.0,
                "caveats": [],
            }
        elif tier == DegradationLevel.LEVEL_2_COST_AWARE:
            return {
                "adjusted_confidence": round(min(raw_confidence, 0.85), 3),
                "confidence_qualifier": "MODERATE_CONFIDENCE",
                "is_resource_constrained": True,
                "evidence_completeness_factor": 0.90,
                "caveats": ["Investigation executed under cost-aware tool filtering."],
            }
        elif tier == DegradationLevel.LEVEL_3_CONSTRAINED:
            # Explicitly cap confidence and adjust completeness
            adj_conf = round(min(raw_confidence, 0.65), 3)
            return {
                "adjusted_confidence": adj_conf,
                "confidence_qualifier": "LIMITED",
                "is_resource_constrained": True,
                "evidence_completeness_factor": 0.70,
                "caveats": [
                    "Investigation degraded to constrained local evidence due to budget pressure.",
                    "Secondary independent corroborations could not be acquired.",
                ],
            }
        else:  # LEVEL_4_SAFE_TERMINATION
            adj_conf = round(min(raw_confidence, 0.45), 3)
            return {
                "adjusted_confidence": adj_conf,
                "confidence_qualifier": "PRELIMINARY_QUALIFIED",
                "is_resource_constrained": True,
                "evidence_completeness_factor": round(min(evidence_coverage, 0.50), 3),
                "caveats": [
                    "Investigation terminated early due to resource budget exhaustion.",
                    "Root cause determination is preliminary and requires subsequent verification.",
                ],
            }
