"""Domain Schemas & Data Contracts for PAIMANA Cohort Intelligence.

Defines input/output contracts for:
- Comprehensive multidimensional cohort quality assessments
- Detailed similarity and feature distribution statistics
- Heterogeneity and entropy reports
- Domain-driven and algorithmic subgroup detection
- Multimodality and graph fragmentation reports
- Metric-specific confidence and cohort refinement decisions
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class CohortQualityLevel(str, Enum):
    """Holistic quality tier for a peer cohort."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INSUFFICIENT = "INSUFFICIENT"
    UNRELIABLE = "UNRELIABLE"


class CohortRefinementAction(str, Enum):
    """Actionable recommendation for cohort usage and refinement."""
    ACCEPT = "ACCEPT"
    ACCEPT_WITH_WARNINGS = "ACCEPT_WITH_WARNINGS"
    REFINE = "REFINE"
    SPLIT_INTO_SUBGROUPS = "SPLIT_INTO_SUBGROUPS"
    INSUFFICIENT = "INSUFFICIENT"
    REJECT = "REJECT"


@dataclass
class QualityDimensionAssessment:
    """Individual dimension health assessment within a cohort."""
    dimension_name: str
    score: float  # 0.0 to 1.0
    status: str   # EXCELLENT, ADEQUATE, MARGINAL, DEFICIENT
    details: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension_name": self.dimension_name,
            "score": round(self.score, 4),
            "status": self.status,
            "details": self.details,
        }


@dataclass
class CohortQualityAssessment:
    """Multidimensional quality assessment for a peer cohort."""
    overall_quality: CohortQualityLevel
    overall_score: float  # 0.0 to 1.0
    dimension_scores: Dict[str, float]
    dimension_details: Dict[str, QualityDimensionAssessment]
    quality_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_quality": self.overall_quality.value,
            "overall_score": round(self.overall_score, 4),
            "dimension_scores": {k: round(v, 4) for k, v in self.dimension_scores.items()},
            "dimension_details": {k: v.to_dict() for k, v in self.dimension_details.items()},
            "quality_reasons": self.quality_reasons,
        }


@dataclass
class DistributionStats:
    """Standard descriptive statistical distribution of a numerical series."""
    count: int
    mean: float
    median: float
    std_dev: float
    min_val: float
    max_val: float
    q1: float
    q3: float
    iqr: float
    cv: float  # Coefficient of Variation (std_dev / mean)
    percentiles: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "count": self.count,
            "mean": round(self.mean, 4),
            "median": round(self.median, 4),
            "std_dev": round(self.std_dev, 4),
            "min_val": round(self.min_val, 4),
            "max_val": round(self.max_val, 4),
            "q1": round(self.q1, 4),
            "q3": round(self.q3, 4),
            "iqr": round(self.iqr, 4),
            "cv": round(self.cv, 4),
            "percentiles": {k: round(v, 4) for k, v in self.percentiles.items()},
        }


@dataclass
class SimilarityDistributionReport:
    """Detailed distribution breakdown across peer similarity scores."""
    overall_distribution: DistributionStats
    dimension_distributions: Dict[str, DistributionStats] = field(default_factory=dict)
    peers_above_75_pct: int = 0
    peers_above_60_pct: int = 0
    is_fragmented: bool = False
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_distribution": self.overall_distribution.to_dict(),
            "dimension_distributions": {k: v.to_dict() for k, v in self.dimension_distributions.items()},
            "peers_above_75_pct": self.peers_above_75_pct,
            "peers_above_60_pct": self.peers_above_60_pct,
            "is_fragmented": self.is_fragmented,
            "details": self.details,
        }


@dataclass
class HeterogeneityReport:
    """Cohort heterogeneity report quantifying cross-member variation."""
    overall_level: str  # LOW, MODERATE, HIGH
    important_dimensions: List[str]
    numerical_variation: Dict[str, float]
    categorical_entropy: Dict[str, float]
    affected_peer_codes: List[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_level": self.overall_level,
            "important_dimensions": self.important_dimensions,
            "numerical_variation": {k: round(v, 4) for k, v in self.numerical_variation.items()},
            "categorical_entropy": {k: round(v, 4) for k, v in self.categorical_entropy.items()},
            "affected_peer_codes": self.affected_peer_codes,
            "summary": self.summary,
        }


@dataclass
class CohortSubgroupRecord:
    """A distinct structural subgroup identified within a cohort."""
    subgroup_id: str
    name: str
    grouping_dimension: str
    group_value: Any
    peer_codes: List[str]
    size: int
    mean_similarity: float
    key_characteristics: Dict[str, Any] = field(default_factory=dict)
    target_matches: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subgroup_id": self.subgroup_id,
            "name": self.name,
            "grouping_dimension": self.grouping_dimension,
            "group_value": self.group_value,
            "peer_codes": self.peer_codes,
            "size": self.size,
            "mean_similarity": round(self.mean_similarity, 4),
            "key_characteristics": self.key_characteristics,
            "target_matches": self.target_matches,
        }


@dataclass
class SubgroupDetectionReport:
    """Outcome of domain and algorithmic subgroup detection."""
    subgroups_detected: bool
    detection_method: str  # DOMAIN_DRIVEN, HIERARCHICAL_CLUSTERING, KMEANS
    subgroups: List[CohortSubgroupRecord] = field(default_factory=list)
    target_subgroup_id: Optional[str] = None
    between_group_divergence: float = 0.0
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subgroups_detected": self.subgroups_detected,
            "detection_method": self.detection_method,
            "subgroups": [s.to_dict() for s in self.subgroups],
            "target_subgroup_id": self.target_subgroup_id,
            "between_group_divergence": round(self.between_group_divergence, 4),
            "recommendation": self.recommendation,
        }


@dataclass
class MultimodalityReport:
    """Multimodality analysis for a numerical metric distribution."""
    metric: str
    is_multimodal: bool
    modes: List[float] = field(default_factory=list)
    confidence: str = "LOW"  # HIGH, MEDIUM, LOW
    recommended_action: str = "UNIFIED_BASELINE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric": self.metric,
            "is_multimodal": self.is_multimodal,
            "modes": [round(m, 2) for m in self.modes],
            "confidence": self.confidence,
            "recommended_action": self.recommended_action,
        }


@dataclass
class FragmentationReport:
    """Graph connectivity and isolation analysis for peer relationships."""
    fragmentation_detected: bool
    connected_components: int
    isolated_peers: List[str] = field(default_factory=list)
    largest_component_ratio: float = 1.0
    density: float = 1.0
    recommended_action: str = "ACCEPT_COHORT"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fragmentation_detected": self.fragmentation_detected,
            "connected_components": self.connected_components,
            "isolated_peers": self.isolated_peers,
            "largest_component_ratio": round(self.largest_component_ratio, 4),
            "density": round(self.density, 4),
            "recommended_action": self.recommended_action,
        }


@dataclass
class CohortIntelligenceResult:
    """Consolidated Cohort Intelligence assessment."""
    cohort_id: str
    target_project_code: str
    quality: CohortQualityAssessment
    similarity_distribution: SimilarityDistributionReport
    heterogeneity: HeterogeneityReport
    subgroups: SubgroupDetectionReport
    multimodality: Dict[str, MultimodalityReport] = field(default_factory=dict)
    fragmentation: Optional[FragmentationReport] = None
    stability_score: float = 1.0
    diversity_score: float = 1.0
    confidence_by_metric: Dict[str, str] = field(default_factory=dict)  # HIGH, MEDIUM, LOW
    recommendation: CohortRefinementAction = CohortRefinementAction.ACCEPT
    warnings: List[str] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    analyzed_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cohort_id": self.cohort_id,
            "target_project_code": self.target_project_code,
            "quality": self.quality.to_dict(),
            "similarity_distribution": self.similarity_distribution.to_dict(),
            "heterogeneity": self.heterogeneity.to_dict(),
            "subgroups": self.subgroups.to_dict(),
            "multimodality": {k: v.to_dict() for k, v in self.multimodality.items()},
            "fragmentation": self.fragmentation.to_dict() if self.fragmentation else None,
            "stability_score": round(self.stability_score, 4),
            "diversity_score": round(self.diversity_score, 4),
            "confidence_by_metric": self.confidence_by_metric,
            "recommendation": self.recommendation.value,
            "warnings": self.warnings,
            "evidence": self.evidence,
            "analyzed_at": self.analyzed_at,
        }
