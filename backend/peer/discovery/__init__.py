"""PAIMANA Question-Conditioned Peer Discovery Subsystem.

Provides question-conditioned context, deterministic question classification,
domain strategy registries, feature selectors, candidate generation, hard eligibility filtering,
modular feature similarity, adaptive cohort relaxation, heterogeneity detection,
Top-K diversity ranking, stability analysis, and explainability dossiers.
"""
from .adaptive_selection import (
    AdaptiveCohortResult,
    AdaptiveCohortSelector,
    RelaxationStep,
)
from .candidate_generator import CandidateGenerationResult, CandidateGenerator
from .context import PeerInvestigationContext
from .eligibility import (
    EligibilityEvaluation,
    HardEligibilityFilter,
    RejectionReason,
)
from .explainability import (
    PeerExplainabilityEngine,
    PeerSelectionDossier,
)
from .feature_selector import FeatureSelector, SelectedFeaturesReport
from .heterogeneity import (
    CohortHeterogeneityDetector,
    CohortSubgroup,
    HeterogeneityAnalysisResult,
)
from .modular_similarity import ModularSimilarityEngine
from .question_classifier import (
    ClassificationResult,
    InvestigationType,
    QuestionClassifier,
)
from .ranking import (
    PeerRankingEngine,
    RankedCandidate,
    RankingResult,
)
from .stability import (
    PeerStabilityAnalyzer,
    PerturbationEvaluation,
    StabilityAnalysisResult,
)
from .strategy_registry import PeerStrategyDefinition, PeerStrategyRegistry

__all__ = [
    "AdaptiveCohortResult",
    "AdaptiveCohortSelector",
    "CandidateGenerationResult",
    "CandidateGenerator",
    "ClassificationResult",
    "CohortHeterogeneityDetector",
    "CohortSubgroup",
    "EligibilityEvaluation",
    "FeatureSelector",
    "HardEligibilityFilter",
    "HeterogeneityAnalysisResult",
    "InvestigationType",
    "ModularSimilarityEngine",
    "PeerExplainabilityEngine",
    "PeerInvestigationContext",
    "PeerRankingEngine",
    "PeerSelectionDossier",
    "PeerStabilityAnalyzer",
    "PeerStrategyDefinition",
    "PeerStrategyRegistry",
    "PerturbationEvaluation",
    "QuestionClassifier",
    "RankedCandidate",
    "RankingResult",
    "RejectionReason",
    "RelaxationStep",
    "SelectedFeaturesReport",
    "StabilityAnalysisResult",
]
