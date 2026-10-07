"""PAIMANA Cohort Intelligence Subsystem.

Provides comprehensive diagnostic health assessment, similarity distribution analysis,
within-cohort heterogeneity, domain and algorithmic subgroup detection, multimodality,
fragmentation, stability, diversity, metric-specific confidence, and actionable refinement recommendations.
"""
from .clustering import CohortClusterAnalyzer
from .confidence import MetricConfidenceAssessor
from .distribution import DistributionAnalyzer
from .diversity import CohortDiversityEvaluator
from .fragmentation import FragmentationDetector
from .heterogeneity import CohortHeterogeneityAnalyzer
from .multimodality import MultimodalityDetector
from .quality import CohortQualityAssessor
from .refinement import CohortRefinementEngine
from .schemas import (
    CohortIntelligenceResult,
    CohortQualityAssessment,
    CohortQualityLevel,
    CohortRefinementAction,
    CohortSubgroupRecord,
    DistributionStats,
    FragmentationReport,
    HeterogeneityReport,
    MultimodalityReport,
    QualityDimensionAssessment,
    SimilarityDistributionReport,
    SubgroupDetectionReport,
)
from .service import CohortIntelligenceService
from .stability import CohortStabilityEvaluator
from .subgroup import SubgroupDetector

__all__ = [
    "CohortClusterAnalyzer",
    "CohortDiversityEvaluator",
    "CohortFragmentationDetector",
    "CohortHeterogeneityAnalyzer",
    "CohortIntelligenceResult",
    "CohortIntelligenceService",
    "CohortQualityAssessment",
    "CohortQualityAssessor",
    "CohortQualityLevel",
    "CohortRefinementAction",
    "CohortRefinementEngine",
    "CohortStabilityEvaluator",
    "CohortSubgroupRecord",
    "DistributionAnalyzer",
    "DistributionStats",
    "FragmentationDetector",
    "FragmentationReport",
    "HeterogeneityReport",
    "MetricConfidenceAssessor",
    "MultimodalityDetector",
    "MultimodalityReport",
    "QualityDimensionAssessment",
    "SimilarityDistributionReport",
    "SubgroupDetectionReport",
    "SubgroupDetector",
]
