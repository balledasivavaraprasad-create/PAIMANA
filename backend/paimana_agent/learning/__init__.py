"""Outcome Learning Subpackage for PAIMANA Agentic Layer.

Implements the canonical closed loop:
    recommendation
    → approval
    → intervention
    → outcome
    → effectiveness
    → memory
    → recommendation evaluation
"""
from .models import (
    OutcomeAttribution,
    OutcomeObservation,
    EffectivenessAssessment,
    RecommendationCalibration,
    LearningMilestone,
)
from .effectiveness import EffectivenessAnalyzer
from .memory_syncer import InstitutionalMemorySyncer
from .recommendation_evaluator import RecommendationEvaluator
from .outcome_loop import OutcomeLearningEngine

__all__ = [
    "OutcomeAttribution",
    "OutcomeObservation",
    "EffectivenessAssessment",
    "RecommendationCalibration",
    "LearningMilestone",
    "EffectivenessAnalyzer",
    "InstitutionalMemorySyncer",
    "RecommendationEvaluator",
    "OutcomeLearningEngine",
]
