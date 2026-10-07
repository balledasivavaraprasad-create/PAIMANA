"""PAIMANA Trajectory Intelligence Subsystem.

Combines rolling velocity, acceleration, trend, volatility, stagnation/recovery,
change-point detection, execution regimes, and peer-relative comparative gap dynamics.
"""
from __future__ import annotations

from .legacy import PeerTrajectoryEngine
from .schemas import (
    AccelerationProfile,
    ChangePointReport,
    ExecutionRegime,
    ExpectedVsActualReport,
    HistoricalCoverageReport,
    MetricTrajectoryReport,
    PeerRelativeTrajectoryReport,
    RecoveryReport,
    RegimeShiftReport,
    StagnationReport,
    SuddenChangeReport,
    TrajectoryDirection,
    TrajectoryIntelligenceResult,
    TrajectoryReliability,
    TrendProfile,
    VelocityProfile,
    VolatilityProfile,
)
from .temporal_validation import TemporalValidator
from .velocity import VelocityCalculator
from .trend_volatility import TrendAndVolatilityAnalyzer
from .pattern_detection import PatternDetector
from .change_point_regime import ChangePointAndRegimeEngine
from .peer_relative import PeerRelativeTrajectoryEngine
from .reliability_explanation import TrajectoryExplainer
from .service import TrajectoryIntelligenceService

__all__ = [
    # Legacy engine for 100% backward compatibility
    "PeerTrajectoryEngine",
    # Data Contracts & Schemas
    "AccelerationProfile",
    "ChangePointReport",
    "ExecutionRegime",
    "ExpectedVsActualReport",
    "HistoricalCoverageReport",
    "MetricTrajectoryReport",
    "PeerRelativeTrajectoryReport",
    "RecoveryReport",
    "RegimeShiftReport",
    "StagnationReport",
    "SuddenChangeReport",
    "TrajectoryDirection",
    "TrajectoryIntelligenceResult",
    "TrajectoryReliability",
    "TrendProfile",
    "VelocityProfile",
    "VolatilityProfile",
    # Engines & Services
    "TemporalValidator",
    "VelocityCalculator",
    "TrendAndVolatilityAnalyzer",
    "PatternDetector",
    "ChangePointAndRegimeEngine",
    "PeerRelativeTrajectoryEngine",
    "TrajectoryExplainer",
    "TrajectoryIntelligenceService",
]
