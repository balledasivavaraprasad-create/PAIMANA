"""Domain Schemas & Data Contracts for PAIMANA Deviation and Outlier Detection (DO-01).

Defines formal contracts for:
- Absolute and relative metric deviations
- Direction-aware deviations (higher/lower is worse/better)
- Univariate anomaly method results (Z-score, Modified Z, IQR, Percentile)
- Multi-method consensus and agreement
- Contextual vs global anomaly profiles
- Multivariate anomaly detection (Mahalanobis distance)
- Temporal deviation velocity, acceleration, and sustained anomalies
- Statistical unusualness vs practical significance and overall severity
- Supervisor evidence items conforming to CONTEXTUALIZES semantics
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class DeviationDirection(str, Enum):
    """Directional classification of target relative to peer baseline."""
    ABOVE_PEERS = "ABOVE_PEERS"
    BELOW_PEERS = "BELOW_PEERS"
    ALIGNED_WITH_PEERS = "ALIGNED_WITH_PEERS"
    INCONCLUSIVE = "INCONCLUSIVE"


class AnomalyMethod(str, Enum):
    """Statistical and empirical detection methods."""
    ORDINARY_Z_SCORE = "ORDINARY_Z_SCORE"
    MODIFIED_Z_SCORE = "MODIFIED_Z_SCORE"
    IQR_FENCE = "IQR_FENCE"
    PERCENTILE_BAND = "PERCENTILE_BAND"
    MAHALANOBIS = "MAHALANOBIS"
    MULTIVARIATE_COMPOSITE = "MULTIVARIATE_COMPOSITE"


class MethodStatus(str, Enum):
    """Operational status of an anomaly detection method."""
    FLAGGED = "FLAGGED"
    NOT_FLAGGED = "NOT_FLAGGED"
    INSUFFICIENT_DISPERSION = "INSUFFICIENT_DISPERSION"
    METHOD_NOT_APPLICABLE = "METHOD_NOT_APPLICABLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class AnomalySeverity(str, Enum):
    """Operational severity classification."""
    INFO = "INFO"            # Minor or negligible deviation
    LOW = "LOW"              # Noticeable but limited
    MODERATE = "MODERATE"    # Meaningful deviation warranting observation
    HIGH = "HIGH"            # Strong deviation requiring review
    CRITICAL = "CRITICAL"    # Extreme deviation with substantial practical implications


class PracticalSignificance(str, Enum):
    """Real-world practical impact of the observed deviation."""
    NEGLIGIBLE = "NEGLIGIBLE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class DeviationResult:
    """Absolute and relative deviation measurements for a single metric."""
    metric_name: str
    target_value: float
    peer_reference: float  # typically peer median
    absolute_deviation: float  # target - peer (in native units, e.g. percentage points or months)
    relative_deviation_pct: Optional[float]  # ((target - peer) / |peer|) * 100, None if peer ~ 0
    unit: str
    is_unit_percentage_points: bool
    direction_rule: str  # HIGHER_IS_WORSE, HIGHER_IS_BETTER, NEUTRAL
    deviation_direction: DeviationDirection
    is_near_zero_reference: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "target_value": round(self.target_value, 4),
            "peer_reference": round(self.peer_reference, 4),
            "absolute_deviation": round(self.absolute_deviation, 4),
            "relative_deviation_pct": (
                round(self.relative_deviation_pct, 2)
                if self.relative_deviation_pct is not None
                else None
            ),
            "unit": self.unit,
            "is_unit_percentage_points": self.is_unit_percentage_points,
            "direction_rule": self.direction_rule,
            "deviation_direction": self.deviation_direction.value,
            "is_near_zero_reference": self.is_near_zero_reference,
        }


@dataclass
class MethodDetectionDetail:
    """Outcome of a single anomaly detection algorithm."""
    method: AnomalyMethod
    score: Optional[float]
    threshold: float
    flagged: bool
    status: MethodStatus
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    reason: str = ""
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method": self.method.value,
            "score": round(self.score, 4) if self.score is not None else None,
            "threshold": self.threshold,
            "flagged": self.flagged,
            "status": self.status.value,
            "lower_bound": round(self.lower_bound, 4) if self.lower_bound is not None else None,
            "upper_bound": round(self.upper_bound, 4) if self.upper_bound is not None else None,
            "reason": self.reason,
            "notes": self.notes,
        }


@dataclass
class MetricAnomalyReport:
    """Comprehensive anomaly assessment for an individual metric across multiple methods."""
    metric_name: str
    deviation: DeviationResult
    method_results: Dict[str, MethodDetectionDetail]
    agreement_ratio: float  # flagged_methods / applicable_methods
    consensus_flagged: bool
    statistical_status: str  # NORMAL, MODERATE_DEVIATION, STATISTICAL_OUTLIER
    practical_significance: PracticalSignificance
    severity: AnomalySeverity
    confidence: str  # HIGH, MEDIUM, LOW
    explanation: str
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "deviation": self.deviation.to_dict(),
            "method_results": {k: v.to_dict() for k, v in self.method_results.items()},
            "agreement_ratio": round(self.agreement_ratio, 2),
            "consensus_flagged": self.consensus_flagged,
            "statistical_status": self.statistical_status,
            "practical_significance": self.practical_significance.value,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "limitations": self.limitations,
        }


@dataclass
class MultivariateAnomalyReport:
    """Multi-metric joint anomaly detection outcome (e.g. Mahalanobis distance)."""
    target_project_code: str
    method: AnomalyMethod
    distance_or_score: float
    threshold: float
    anomaly_detected: bool
    contributing_metrics: List[str]
    severity: AnomalySeverity
    interpretation: str
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_project_code": self.target_project_code,
            "method": self.method.value,
            "distance_or_score": round(self.distance_or_score, 4),
            "threshold": round(self.threshold, 4),
            "anomaly_detected": self.anomaly_detected,
            "contributing_metrics": self.contributing_metrics,
            "severity": self.severity.value,
            "interpretation": self.interpretation,
            "limitations": self.limitations,
        }


@dataclass
class TemporalDeviationReport:
    """Rate of change, acceleration, and persistence of deviations across snapshots."""
    metric_name: str
    target_project_code: str
    snapshot_count: int
    deviation_velocity: float  # change in deviation per month
    deviation_acceleration: float  # rate of change of velocity
    is_accelerating: bool
    is_sustained: bool
    consecutive_anomalous_snapshots: int
    trend_description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "target_project_code": self.target_project_code,
            "snapshot_count": self.snapshot_count,
            "deviation_velocity": round(self.deviation_velocity, 4),
            "deviation_acceleration": round(self.deviation_acceleration, 4),
            "is_accelerating": self.is_accelerating,
            "is_sustained": self.is_sustained,
            "consecutive_anomalous_snapshots": self.consecutive_anomalous_snapshots,
            "trend_description": self.trend_description,
        }


@dataclass
class ConsolidatedAnomalyResult:
    """Master consolidated anomaly analysis across all metrics, context, multivariate & temporal signals."""
    target_project_code: str
    cohort_id: str
    cohort_size: int
    metrics_evaluated: List[str]
    univariate_anomalies: Dict[str, MetricAnomalyReport]
    multivariate_anomaly: Optional[MultivariateAnomalyReport] = None
    temporal_anomalies: Dict[str, TemporalDeviationReport] = field(default_factory=dict)
    overall_severity: AnomalySeverity = AnomalySeverity.INFO
    overall_is_outlier: bool = False
    executive_summary: str = ""
    evidence_items: List[Dict[str, Any]] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    computed_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_project_code": self.target_project_code,
            "cohort_id": self.cohort_id,
            "cohort_size": self.cohort_size,
            "metrics_evaluated": self.metrics_evaluated,
            "univariate_anomalies": {k: v.to_dict() for k, v in self.univariate_anomalies.items()},
            "multivariate_anomaly": (
                self.multivariate_anomaly.to_dict() if self.multivariate_anomaly else None
            ),
            "temporal_anomalies": {k: v.to_dict() for k, v in self.temporal_anomalies.items()},
            "overall_severity": self.overall_severity.value,
            "overall_is_outlier": self.overall_is_outlier,
            "executive_summary": self.executive_summary,
            "evidence_items": self.evidence_items,
            "limitations": self.limitations,
            "computed_at": self.computed_at,
        }
