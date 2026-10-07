"""Domain Schemas & Data Contracts for PAIMANA Statistical Benchmarking.

Defines formal contracts for:
- Normalized metric descriptions and interpretation directions
- Robust statistics, percentiles, and dispersion summaries
- Analytical and bootstrap-based confidence intervals
- Small-sample status and statistical safeguards
- Distribution shape, skewness, and tail characteristics
- Distribution-shift detection (PSI, Kolmogorov-Smirnov)
- Leave-one-out sensitivity and audit metadata
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class MetricDirection(str, Enum):
    """Directional interpretation of metric values."""
    HIGHER_IS_WORSE = "HIGHER_IS_WORSE"  # e.g. cost overrun, schedule delay
    HIGHER_IS_BETTER = "HIGHER_IS_BETTER"  # e.g. physical progress, progress velocity
    NEUTRAL = "NEUTRAL"                    # e.g. expenditure level, project duration


class SmallSampleStatus(str, Enum):
    """Operational reliability classification based on effective sample size."""
    INSUFFICIENT = "INSUFFICIENT"            # n <= 2: cannot infer cohort distribution
    HIGHLY_LIMITED = "HIGHLY_LIMITED"        # n in [3, 4]: descriptive only
    CAUTIOUS_EXPLORATORY = "CAUTIOUS_EXPLORATORY"  # n in [5, 9]: preliminary signals
    PRELIMINARY = "PRELIMINARY"              # n in [10, 19]: emerging distribution
    SUBSTANTIAL = "SUBSTANTIAL"              # n >= 20: solid statistical baseline


class DistributionShape(str, Enum):
    """Shape and skewness profile of the empirical distribution."""
    APPROXIMATELY_SYMMETRIC = "APPROXIMATELY_SYMMETRIC"
    RIGHT_SKEWED = "RIGHT_SKEWED"
    LEFT_SKEWED = "LEFT_SKEWED"
    HEAVY_TAILED = "HEAVY_TAILED"
    UNIFORM = "UNIFORM"
    UNKNOWN = "UNKNOWN"


@dataclass
class ConfidenceInterval:
    """Interval estimate representing parameter uncertainty."""
    statistic: str
    point_estimate: float
    confidence_level: float  # e.g. 0.95
    lower_bound: float
    upper_bound: float
    method: str  # BOOTSTRAP_PERCENTILE, T_DISTRIBUTION, ORDER_STATISTIC
    margin_of_error: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "statistic": self.statistic,
            "point_estimate": round(self.point_estimate, 4),
            "confidence_level": self.confidence_level,
            "lower_bound": round(self.lower_bound, 4),
            "upper_bound": round(self.upper_bound, 4),
            "method": self.method,
            "margin_of_error": round(self.margin_of_error, 4),
        }


@dataclass
class PercentileBenchmark:
    """Relative position and empirical ranking of target within the peer cohort."""
    metric_name: str
    target_value: float
    percentile_rank: float  # 0.0 to 100.0
    interpretation: str     # SIGNIFICANTLY_BELOW, BELOW_MEDIAN, ABOVE_MEDIAN, SIGNIFICANTLY_ABOVE
    peers_below: int
    peers_above: int
    distance_from_median: float
    distance_from_q75: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "target_value": round(self.target_value, 4),
            "percentile_rank": round(self.percentile_rank, 2),
            "interpretation": self.interpretation,
            "peers_below": self.peers_below,
            "peers_above": self.peers_above,
            "distance_from_median": round(self.distance_from_median, 4),
            "distance_from_q75": round(self.distance_from_q75, 4),
        }


@dataclass
class BootstrapSummary:
    """Summary of non-parametric bootstrap resampling evaluation."""
    statistic: str
    resample_count: int
    bootstrap_mean: float
    bootstrap_se: float
    confidence_interval: ConfidenceInterval
    random_seed: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "statistic": self.statistic,
            "resample_count": self.resample_count,
            "bootstrap_mean": round(self.bootstrap_mean, 4),
            "bootstrap_se": round(self.bootstrap_se, 4),
            "confidence_interval": self.confidence_interval.to_dict(),
            "random_seed": self.random_seed,
        }


@dataclass
class SensitivityReport:
    """Leave-one-out sensitivity testing identifying influential peers."""
    metric_name: str
    base_median: float
    leave_one_out_min: float
    leave_one_out_max: float
    sensitivity_level: str  # LOW, MEDIUM, HIGH
    influential_peers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "base_median": round(self.base_median, 4),
            "leave_one_out_min": round(self.leave_one_out_min, 4),
            "leave_one_out_max": round(self.leave_one_out_max, 4),
            "sensitivity_level": self.sensitivity_level,
            "influential_peers": self.influential_peers,
        }


@dataclass
class DistributionShiftReport:
    """Statistical shift detection between current cohort and reference baseline."""
    metric_name: str
    current_period_median: float
    reference_period_median: float
    psi_score: float
    ks_statistic: float
    p_value: float
    shift_detected: bool
    shift_severity: str  # NONE, MODERATE, SEVERE
    interpretation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "current_period_median": round(self.current_period_median, 4),
            "reference_period_median": round(self.reference_period_median, 4),
            "psi_score": round(self.psi_score, 4),
            "ks_statistic": round(self.ks_statistic, 4),
            "p_value": round(self.p_value, 4),
            "shift_detected": self.shift_detected,
            "shift_severity": self.shift_severity,
            "interpretation": self.interpretation,
        }


@dataclass
class MetricBenchmarkDetail:
    """In-depth statistical reference profile for a single metric."""
    metric_name: str
    unit: str
    direction: MetricDirection
    count: int
    effective_sample_size: int
    missing_count: int
    mean: float
    median: float
    trimmed_mean: float
    std: float
    mad: float
    iqr: float
    cv: float
    skewness: float
    kurtosis: float
    distribution_shape: DistributionShape
    percentiles: Dict[str, float]
    confidence_interval: Optional[ConfidenceInterval] = None
    bootstrap: Optional[BootstrapSummary] = None
    target_percentile: Optional[PercentileBenchmark] = None
    sensitivity: Optional[SensitivityReport] = None
    small_sample_status: SmallSampleStatus = SmallSampleStatus.SUBSTANTIAL
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "unit": self.unit,
            "direction": self.direction.value,
            "count": self.count,
            "effective_sample_size": self.effective_sample_size,
            "missing_count": self.missing_count,
            "mean": round(self.mean, 4),
            "median": round(self.median, 4),
            "trimmed_mean": round(self.trimmed_mean, 4),
            "std": round(self.std, 4),
            "mad": round(self.mad, 4),
            "iqr": round(self.iqr, 4),
            "cv": round(self.cv, 4),
            "skewness": round(self.skewness, 4),
            "kurtosis": round(self.kurtosis, 4),
            "distribution_shape": self.distribution_shape.value,
            "percentiles": {k: round(v, 4) for k, v in self.percentiles.items()},
            "confidence_interval": self.confidence_interval.to_dict() if self.confidence_interval else None,
            "bootstrap": self.bootstrap.to_dict() if self.bootstrap else None,
            "target_percentile": self.target_percentile.to_dict() if self.target_percentile else None,
            "sensitivity": self.sensitivity.to_dict() if self.sensitivity else None,
            "small_sample_status": self.small_sample_status.value,
            "warnings": self.warnings,
        }


@dataclass
class StatisticalBenchmarkResult:
    """Complete consolidated outcome of statistical benchmarking across all metrics."""
    target_project_code: str
    cohort_id: str
    cohort_size: int
    as_of_date: Optional[str]
    metrics_analyzed: List[str]
    benchmarks: Dict[str, MetricBenchmarkDetail]
    audit_metadata: Dict[str, Any] = field(default_factory=dict)
    evidence_items: List[Dict[str, Any]] = field(default_factory=list)
    computed_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_project_code": self.target_project_code,
            "cohort_id": self.cohort_id,
            "cohort_size": self.cohort_size,
            "as_of_date": self.as_of_date,
            "metrics_analyzed": self.metrics_analyzed,
            "benchmarks": {k: v.to_dict() for k, v in self.benchmarks.items()},
            "audit_metadata": self.audit_metadata,
            "evidence_items": self.evidence_items,
            "computed_at": self.computed_at,
        }
