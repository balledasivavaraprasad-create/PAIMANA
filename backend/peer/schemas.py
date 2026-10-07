"""Domain Schemas & Data Contracts for the PAIMANA Peer Intelligence Subsystem.

Defines all structured types, enums, and result contracts for:
- Peer discovery & similarity scoring
- Statistical benchmarking
- Target-vs-peer deviation
- Trajectory tracking across historical snapshots
- Peer-relative anomaly & outlier detection
- Cohort health & lineage tracking
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class CohortQuality(str, Enum):
    """Quality and confidence level of a peer cohort."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INSUFFICIENT = "INSUFFICIENT"


class DeviationDirection(str, Enum):
    """Directional interpretation of target metric vs peer baseline."""
    AHEAD_OF_PEERS = "AHEAD_OF_PEERS"
    ALIGNED_WITH_PEERS = "ALIGNED_WITH_PEERS"
    LAGGING_PEERS = "LAGGING_PEERS"
    HIGHER_THAN_PEERS = "HIGHER_THAN_PEERS"
    LOWER_THAN_PEERS = "LOWER_THAN_PEERS"
    SIGNIFICANTLY_ABOVE_PEERS = "SIGNIFICANTLY_ABOVE_PEERS"
    SIGNIFICANTLY_BELOW_PEERS = "SIGNIFICANTLY_BELOW_PEERS"
    INCONCLUSIVE = "INCONCLUSIVE"


class OutlierSeverity(str, Enum):
    """Severity of peer-relative deviation."""
    NONE = "NONE"
    MILD = "MILD"
    EXTREME = "EXTREME"


@dataclass
class SimilarityBreakdown:
    """Detailed explainable breakdown of similarity between two projects."""
    peer_code: str
    peer_name: str
    overall_similarity: float  # Normalized 0.0 to 1.0
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    matching_dimensions: List[str] = field(default_factory=list)
    differing_dimensions: List[str] = field(default_factory=list)
    missing_dimensions: List[str] = field(default_factory=list)
    inclusion_reasons: List[str] = field(default_factory=list)
    exclusion_reasons: List[str] = field(default_factory=list)
    raw_attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "peer_code": self.peer_code,
            "peer_name": self.peer_name,
            "overall_similarity": round(self.overall_similarity, 4),
            "dimension_scores": {k: round(v, 4) for k, v in self.dimension_scores.items()},
            "matching_dimensions": self.matching_dimensions,
            "differing_dimensions": self.differing_dimensions,
            "missing_dimensions": self.missing_dimensions,
            "inclusion_reasons": self.inclusion_reasons,
            "exclusion_reasons": self.exclusion_reasons,
            "raw_attributes": self.raw_attributes,
        }


@dataclass
class CohortDiscoveryResult:
    """Result of peer discovery containing candidates and cohort health."""
    target_project_code: str
    target_project_name: str
    cohort_size: int
    quality: CohortQuality
    is_sufficient: bool
    peers: List[SimilarityBreakdown] = field(default_factory=list)
    excluded_count: int = 0
    exclusion_summary: Dict[str, int] = field(default_factory=dict)
    average_similarity: float = 0.0
    quality_reasons: List[str] = field(default_factory=list)
    source_lineage: Dict[str, Any] = field(default_factory=dict)
    generated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_project_code": self.target_project_code,
            "target_project_name": self.target_project_name,
            "cohort_size": self.cohort_size,
            "quality": self.quality.value,
            "is_sufficient": self.is_sufficient,
            "peers": [p.to_dict() for p in self.peers],
            "excluded_count": self.excluded_count,
            "exclusion_summary": self.exclusion_summary,
            "average_similarity": round(self.average_similarity, 4),
            "quality_reasons": self.quality_reasons,
            "source_lineage": self.source_lineage,
            "generated_at": self.generated_at,
        }


@dataclass
class MetricDistribution:
    """Robust statistical distribution for a single numerical metric across a cohort."""
    metric_name: str
    count: int
    mean: float
    std: float
    median: float
    p25: float
    p75: float
    iqr: float
    min_val: float
    max_val: float
    valid_observations: int
    missing_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "count": self.count,
            "mean": round(self.mean, 4),
            "std": round(self.std, 4),
            "median": round(self.median, 4),
            "p25": round(self.p25, 4),
            "p75": round(self.p75, 4),
            "iqr": round(self.iqr, 4),
            "min": round(self.min_val, 4),
            "max": round(self.max_val, 4),
            "valid_observations": self.valid_observations,
            "missing_count": self.missing_count,
        }


@dataclass
class PeerBenchmarkResult:
    """Statistical benchmarks across all requested metrics for a peer cohort."""
    target_project_code: str
    cohort_size: int
    cohort_quality: CohortQuality
    is_sufficient: bool
    distributions: Dict[str, MetricDistribution] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)
    source_lineage: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_project_code": self.target_project_code,
            "cohort_size": self.cohort_size,
            "cohort_quality": self.cohort_quality.value,
            "is_sufficient": self.is_sufficient,
            "distributions": {k: v.to_dict() for k, v in self.distributions.items()},
            "notes": self.notes,
            "source_lineage": self.source_lineage,
        }


@dataclass
class MetricDeviation:
    """Target-vs-peer deviation for a single metric."""
    metric_name: str
    target_value: Optional[float]
    peer_median: Optional[float]
    peer_p25: Optional[float]
    peer_p75: Optional[float]
    absolute_difference: Optional[float]
    relative_difference: Optional[float]  # (target - median) / |median|
    percentile_rank: Optional[float]      # Target's rank in peer cohort (0.0 to 1.0)
    direction: DeviationDirection
    is_significant: bool
    interpretation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "target_value": round(self.target_value, 4) if self.target_value is not None else None,
            "peer_median": round(self.peer_median, 4) if self.peer_median is not None else None,
            "peer_p25": round(self.peer_p25, 4) if self.peer_p25 is not None else None,
            "peer_p75": round(self.peer_p75, 4) if self.peer_p75 is not None else None,
            "absolute_difference": round(self.absolute_difference, 4) if self.absolute_difference is not None else None,
            "relative_difference": round(self.relative_difference, 4) if self.relative_difference is not None else None,
            "percentile_rank": round(self.percentile_rank, 4) if self.percentile_rank is not None else None,
            "direction": self.direction.value,
            "is_significant": self.is_significant,
            "interpretation": self.interpretation,
        }


@dataclass
class PeerDeviationResult:
    """Target vs peer baseline deviation analysis across metrics."""
    target_project_code: str
    cohort_size: int
    cohort_quality: CohortQuality
    is_sufficient: bool
    deviations: Dict[str, MetricDeviation] = field(default_factory=dict)
    summary: str = ""
    source_lineage: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_project_code": self.target_project_code,
            "cohort_size": self.cohort_size,
            "cohort_quality": self.cohort_quality.value,
            "is_sufficient": self.is_sufficient,
            "deviations": {k: v.to_dict() for k, v in self.deviations.items()},
            "summary": self.summary,
            "source_lineage": self.source_lineage,
        }


@dataclass
class TrajectoryMetricComparison:
    """Comparison of multi-snapshot change rate for target vs peer cohort."""
    metric_name: str
    target_delta_per_month: Optional[float]
    peer_median_delta_per_month: Optional[float]
    trajectory_gap: Optional[float]
    direction: DeviationDirection
    status: str  # OK, DATA_INSUFFICIENT
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "target_delta_per_month": round(self.target_delta_per_month, 4) if self.target_delta_per_month is not None else None,
            "peer_median_delta_per_month": round(self.peer_median_delta_per_month, 4) if self.peer_median_delta_per_month is not None else None,
            "trajectory_gap": round(self.trajectory_gap, 4) if self.trajectory_gap is not None else None,
            "direction": self.direction.value,
            "status": self.status,
            "summary": self.summary,
        }


@dataclass
class PeerTrajectoryResult:
    """Multi-snapshot trajectory comparison across target and peer cohort."""
    target_project_code: str
    snapshots_analyzed: int
    is_sufficient_history: bool
    comparisons: Dict[str, TrajectoryMetricComparison] = field(default_factory=dict)
    summary: str = ""
    source_lineage: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_project_code": self.target_project_code,
            "snapshots_analyzed": self.snapshots_analyzed,
            "is_sufficient_history": self.is_sufficient_history,
            "comparisons": {k: v.to_dict() for k, v in self.comparisons.items()},
            "summary": self.summary,
            "source_lineage": self.source_lineage,
        }


@dataclass
class OutlierMetricEvaluation:
    """Peer-relative anomaly evaluation for a single metric."""
    metric_name: str
    target_value: float
    peer_median: float
    peer_mad: float  # Median Absolute Deviation
    modified_z_score: float
    is_peer_outlier: bool
    severity: OutlierSeverity
    absolute_risk_level: str  # HIGH, MEDIUM, LOW
    peer_relative_risk_level: str  # HIGH_ANOMALY, MODERATE_ANOMALY, TYPICAL_FOR_PEERS
    distinction_explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "target_value": round(self.target_value, 4),
            "peer_median": round(self.peer_median, 4),
            "peer_mad": round(self.peer_mad, 4),
            "modified_z_score": round(self.modified_z_score, 4),
            "is_peer_outlier": self.is_peer_outlier,
            "severity": self.severity.value,
            "absolute_risk_level": self.absolute_risk_level,
            "peer_relative_risk_level": self.peer_relative_risk_level,
            "distinction_explanation": self.distinction_explanation,
        }


@dataclass
class PeerOutlierResult:
    """Peer-relative anomaly analysis distinguishing absolute risk from peer anomaly."""
    target_project_code: str
    cohort_size: int
    cohort_quality: CohortQuality
    is_sufficient: bool
    evaluations: Dict[str, OutlierMetricEvaluation] = field(default_factory=dict)
    is_overall_peer_outlier: bool = False
    highest_severity: OutlierSeverity = OutlierSeverity.NONE
    summary: str = ""
    source_lineage: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_project_code": self.target_project_code,
            "cohort_size": self.cohort_size,
            "cohort_quality": self.cohort_quality.value,
            "is_sufficient": self.is_sufficient,
            "evaluations": {k: v.to_dict() for k, v in self.evaluations.items()},
            "is_overall_peer_outlier": self.is_overall_peer_outlier,
            "highest_severity": self.highest_severity.value,
            "summary": self.summary,
            "source_lineage": self.source_lineage,
        }
