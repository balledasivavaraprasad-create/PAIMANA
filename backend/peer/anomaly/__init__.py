"""PAIMANA Deviation & Outlier Detection Subsystem.

Consumes peer cohorts and statistical benchmarks to detect robust univariate,
contextual, multivariate, and temporal anomalies without conflating risk with outliers.
"""
from __future__ import annotations

from .schemas import (
    DeviationDirection,
    AnomalyMethod,
    MethodStatus,
    AnomalySeverity,
    PracticalSignificance,
    DeviationResult,
    MethodDetectionDetail,
    MetricAnomalyReport,
    MultivariateAnomalyReport,
    TemporalDeviationReport,
    ConsolidatedAnomalyResult,
)
from .deviation_metrics import DeviationCalculator
from .mad_detector import ModifiedZScoreDetector
from .zscore import OrdinaryZScoreDetector
from .iqr_detector import IQRDetector
from .percentile_detector import PercentileDetector
from .ensemble import EnsembleDetector
from .contextual import ContextualDetector
from .multivariate import MultivariateDetector
from .severity import SeverityEvaluator
from .temporal import TemporalAnomalyDetector
from .explanation import AnomalyExplainer
from .calibration import AnomalyCalibrator, AnomalyEvaluationMetrics
from .service import DeviationAndOutlierService

__all__ = [
    "DeviationDirection",
    "AnomalyMethod",
    "MethodStatus",
    "AnomalySeverity",
    "PracticalSignificance",
    "DeviationResult",
    "MethodDetectionDetail",
    "MetricAnomalyReport",
    "MultivariateAnomalyReport",
    "TemporalDeviationReport",
    "ConsolidatedAnomalyResult",
    "DeviationCalculator",
    "ModifiedZScoreDetector",
    "OrdinaryZScoreDetector",
    "IQRDetector",
    "PercentileDetector",
    "EnsembleDetector",
    "ContextualDetector",
    "MultivariateDetector",
    "SeverityEvaluator",
    "TemporalAnomalyDetector",
    "AnomalyExplainer",
    "AnomalyCalibrator",
    "AnomalyEvaluationMetrics",
    "DeviationAndOutlierService",
]
