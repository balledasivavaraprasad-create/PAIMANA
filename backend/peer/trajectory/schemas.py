"""Domain Schemas & Data Contracts for PAIMANA Trajectory Intelligence (TI-01 to TI-14).

Defines formal contracts for:
- Historical snapshot coverage & temporal validation
- Rolling velocity, acceleration & deceleration
- Statistical & robust trend analysis
- Execution volatility & stability
- Stagnation & recovery detection
- Sudden change & change-point detection (PELT/CUSUM)
- Operational execution regimes & regime transitions
- Peer-relative trajectory gap dynamics
- Expected vs actual trajectory analysis
- Trajectory reliability & supervisor evidence attribution
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TrajectoryDirection(str, Enum):
    """Directional velocity profile."""
    ACCELERATING = "ACCELERATING"
    STEADY_GROWTH = "STEADY_GROWTH"
    STABLE = "STABLE"
    DECELERATING = "DECELERATING"
    STAGNATING = "STAGNATING"
    REVERSING = "REVERSING"


class ExecutionRegime(str, Enum):
    """Categorical persistent execution regime."""
    NORMAL_EXECUTION = "NORMAL_EXECUTION"
    ACCELERATING = "ACCELERATING"
    DECELERATING = "DECELERATING"
    STAGNATING = "STAGNATING"
    VOLATILE = "VOLATILE"
    RECOVERING = "RECOVERING"
    COMPLETED = "COMPLETED"


class TrajectoryReliability(str, Enum):
    """Operational reliability classification based on snapshot depth and quality."""
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    INSUFFICIENT = "INSUFFICIENT"


@dataclass
class HistoricalCoverageReport:
    """Historical snapshot depth and temporal continuity."""
    available_snapshots: int
    expected_snapshots: int
    coverage_ratio: float
    missing_periods: int
    temporal_quality: str  # FULL, PARTIAL, INSUFFICIENT
    is_chronological: bool
    has_duplicates: bool
    date_range: tuple[Optional[str], Optional[str]] = (None, None)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "available_snapshots": self.available_snapshots,
            "expected_snapshots": self.expected_snapshots,
            "coverage_ratio": round(self.coverage_ratio, 4),
            "missing_periods": self.missing_periods,
            "temporal_quality": self.temporal_quality,
            "is_chronological": self.is_chronological,
            "has_duplicates": self.has_duplicates,
            "date_range": list(self.date_range),
        }


@dataclass
class VelocityProfile:
    """Rolling velocity metrics."""
    metric_name: str
    latest_velocity: float  # change per month
    previous_velocity: Optional[float]
    rolling_3_velocity: float
    rolling_6_velocity: float
    unit: str
    direction: TrajectoryDirection
    confidence: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "latest_velocity": round(self.latest_velocity, 4),
            "previous_velocity": (
                round(self.previous_velocity, 4) if self.previous_velocity is not None else None
            ),
            "rolling_3_velocity": round(self.rolling_3_velocity, 4),
            "rolling_6_velocity": round(self.rolling_6_velocity, 4),
            "unit": self.unit,
            "direction": self.direction.value,
            "confidence": self.confidence,
        }


@dataclass
class AccelerationProfile:
    """Acceleration and deceleration characteristics."""
    metric_name: str
    current_acceleration: float  # velocity delta per month
    previous_acceleration: Optional[float]
    is_sustained_deceleration: bool
    is_accelerating: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "current_acceleration": round(self.current_acceleration, 4),
            "previous_acceleration": (
                round(self.previous_acceleration, 4) if self.previous_acceleration is not None else None
            ),
            "is_sustained_deceleration": self.is_sustained_deceleration,
            "is_accelerating": self.is_accelerating,
        }


@dataclass
class TrendProfile:
    """Parametric and robust trajectory trend."""
    metric_name: str
    slope_ols: float
    slope_theil_sen: float
    trend_direction: str  # IMPROVING, STABLE, DETERIORATING, REVERSING
    r_squared: float
    method: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "slope_ols": round(self.slope_ols, 4),
            "slope_theil_sen": round(self.slope_theil_sen, 4),
            "trend_direction": self.trend_direction,
            "r_squared": round(self.r_squared, 4),
            "method": self.method,
        }


@dataclass
class VolatilityProfile:
    """Variability and execution stability."""
    metric_name: str
    rolling_std: float
    mad_change: float
    cv: float
    stability_category: str  # STABLE, MODERATE_VARIABILITY, HIGHLY_VOLATILE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "rolling_std": round(self.rolling_std, 4),
            "mad_change": round(self.mad_change, 4),
            "cv": round(self.cv, 4),
            "stability_category": self.stability_category,
        }


@dataclass
class StagnationReport:
    """Stagnation and stall detection."""
    metric_name: str
    stagnation_detected: bool
    duration_months: int
    progress_change: float
    expenditure_change: float
    is_stagnation_with_expenditure: bool
    severity: str  # NONE, MODERATE, HIGH, CRITICAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "stagnation_detected": self.stagnation_detected,
            "duration_months": self.duration_months,
            "progress_change": round(self.progress_change, 4),
            "expenditure_change": round(self.expenditure_change, 4),
            "is_stagnation_with_expenditure": self.is_stagnation_with_expenditure,
            "severity": self.severity,
        }


@dataclass
class RecoveryReport:
    """Recovery from prolonged stagnation or stall."""
    metric_name: str
    recovery_detected: bool
    prior_stagnation_duration_months: int
    consecutive_positive_periods: int
    latest_velocity: float
    is_sustained: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "recovery_detected": self.recovery_detected,
            "prior_stagnation_duration_months": self.prior_stagnation_duration_months,
            "consecutive_positive_periods": self.consecutive_positive_periods,
            "latest_velocity": round(self.latest_velocity, 4),
            "is_sustained": self.is_sustained,
        }


@dataclass
class SuddenChangeReport:
    """Sudden jump or drop detection."""
    metric_name: str
    sudden_change_detected: bool
    change_magnitude: float
    change_type: str  # VELOCITY_SPIKE, PROGRESS_DROP, EXPENDITURE_JUMP, SLIPPAGE_SURGE, NONE
    snapshot_index: Optional[int]
    severity: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "sudden_change_detected": self.sudden_change_detected,
            "change_magnitude": round(self.change_magnitude, 4),
            "change_type": self.change_type,
            "snapshot_index": self.snapshot_index,
            "severity": self.severity,
        }


@dataclass
class ChangePointReport:
    """Statistical change point detection across trajectory."""
    metric_name: str
    change_point_detected: bool
    estimated_change_index: Optional[int]
    estimated_change_date: Optional[str]
    pre_change_mean_velocity: float
    post_change_mean_velocity: float
    method: str
    confidence: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "change_point_detected": self.change_point_detected,
            "estimated_change_index": self.estimated_change_index,
            "estimated_change_date": self.estimated_change_date,
            "pre_change_mean_velocity": round(self.pre_change_mean_velocity, 4),
            "post_change_mean_velocity": round(self.post_change_mean_velocity, 4),
            "method": self.method,
            "confidence": self.confidence,
        }


@dataclass
class RegimeShiftReport:
    """Operational execution regime identification."""
    current_regime: ExecutionRegime
    previous_regime: Optional[ExecutionRegime]
    transition_index: Optional[int]
    transition_date: Optional[str]
    signals_supporting: List[str]
    confidence: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_regime": self.current_regime.value,
            "previous_regime": self.previous_regime.value if self.previous_regime else None,
            "transition_index": self.transition_index,
            "transition_date": self.transition_date,
            "signals_supporting": self.signals_supporting,
            "confidence": self.confidence,
        }


@dataclass
class PeerRelativeTrajectoryReport:
    """Target trajectory vs comparable peer cohort velocity."""
    metric_name: str
    target_velocity: float
    peer_median_velocity: float
    velocity_gap: float
    trajectory_direction: str  # AHEAD_OF_PEERS, LAGGING_PEERS, ALIGNED_WITH_PEERS
    is_gap_widening: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "target_velocity": round(self.target_velocity, 4),
            "peer_median_velocity": round(self.peer_median_velocity, 4),
            "velocity_gap": round(self.velocity_gap, 4),
            "trajectory_direction": self.trajectory_direction,
            "is_gap_widening": self.is_gap_widening,
        }


@dataclass
class ExpectedVsActualReport:
    """Actual performance vs expected progression baseline."""
    metric_name: str
    actual_value: float
    expected_value: float
    gap: float
    baseline_type: str  # SCHEDULE, PEER_DERIVED, HISTORICAL_TREND
    status: str  # AHEAD_OF_EXPECTED, ON_TRACK, BELOW_EXPECTED, CRITICALLY_BELOW

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "actual_value": round(self.actual_value, 4),
            "expected_value": round(self.expected_value, 4),
            "gap": round(self.gap, 4),
            "baseline_type": self.baseline_type,
            "status": self.status,
        }


@dataclass
class MetricTrajectoryReport:
    """Consolidated trajectory profile for a single infrastructure metric."""
    metric_name: str
    coverage: HistoricalCoverageReport
    velocity: VelocityProfile
    acceleration: AccelerationProfile
    trend: TrendProfile
    volatility: VolatilityProfile
    stagnation: StagnationReport
    recovery: RecoveryReport
    sudden_change: SuddenChangeReport
    change_point: Optional[ChangePointReport] = None
    peer_relative: Optional[PeerRelativeTrajectoryReport] = None
    expected_vs_actual: Optional[ExpectedVsActualReport] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "coverage": self.coverage.to_dict(),
            "velocity": self.velocity.to_dict(),
            "acceleration": self.acceleration.to_dict(),
            "trend": self.trend.to_dict(),
            "volatility": self.volatility.to_dict(),
            "stagnation": self.stagnation.to_dict(),
            "recovery": self.recovery.to_dict(),
            "sudden_change": self.sudden_change.to_dict(),
            "change_point": self.change_point.to_dict() if self.change_point else None,
            "peer_relative": self.peer_relative.to_dict() if self.peer_relative else None,
            "expected_vs_actual": self.expected_vs_actual.to_dict() if self.expected_vs_actual else None,
        }


@dataclass
class TrajectoryIntelligenceResult:
    """Master analytical outcome of trajectory intelligence."""
    target_project_code: str
    cohort_id: str
    cohort_size: int
    snapshots_analyzed: int
    metrics_evaluated: List[str]
    historical_coverage: HistoricalCoverageReport
    metric_trajectories: Dict[str, MetricTrajectoryReport]
    execution_regime: RegimeShiftReport
    overall_reliability: TrajectoryReliability
    findings: List[str] = field(default_factory=list)
    evidence_items: List[Dict[str, Any]] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    computed_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_project_code": self.target_project_code,
            "cohort_id": self.cohort_id,
            "cohort_size": self.cohort_size,
            "snapshots_analyzed": self.snapshots_analyzed,
            "metrics_evaluated": self.metrics_evaluated,
            "historical_coverage": self.historical_coverage.to_dict(),
            "metric_trajectories": {k: v.to_dict() for k, v in self.metric_trajectories.items()},
            "execution_regime": self.execution_regime.to_dict(),
            "overall_reliability": self.overall_reliability.value,
            "findings": self.findings,
            "evidence_items": self.evidence_items,
            "limitations": self.limitations,
            "computed_at": self.computed_at,
        }
