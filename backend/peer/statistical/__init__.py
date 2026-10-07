"""PAIMANA Statistical Benchmarking Subsystem.

Converts validated peer cohorts into reliable, non-parametric, outlier-resistant
statistical reference baselines for infrastructure monitoring.
"""
from __future__ import annotations

from .schemas import (
    MetricDirection,
    SmallSampleStatus,
    DistributionShape,
    ConfidenceInterval,
    PercentileBenchmark,
    BootstrapSummary,
    SensitivityReport,
    DistributionShiftReport,
    MetricBenchmarkDetail,
    StatisticalBenchmarkResult,
)
from .metric_registry import MetricDefinition, MetricRegistry
from .normalization import MetricNormalizer
from .small_sample import SmallSampleEvaluator
from .robust_statistics import RobustStatisticsEngine
from .bootstrap import BootstrapEngine
from .distributions import DistributionAnalyzer
from .shift_detection import DistributionShiftDetector
from .sensitivity import SensitivityEngine
from .reproducibility import AuditTrailEngine
from .service import StatisticalBenchmarkingService

__all__ = [
    "MetricDirection",
    "SmallSampleStatus",
    "DistributionShape",
    "ConfidenceInterval",
    "PercentileBenchmark",
    "BootstrapSummary",
    "SensitivityReport",
    "DistributionShiftReport",
    "MetricBenchmarkDetail",
    "StatisticalBenchmarkResult",
    "MetricDefinition",
    "MetricRegistry",
    "MetricNormalizer",
    "SmallSampleEvaluator",
    "RobustStatisticsEngine",
    "BootstrapEngine",
    "DistributionAnalyzer",
    "DistributionShiftDetector",
    "SensitivityEngine",
    "AuditTrailEngine",
    "StatisticalBenchmarkingService",
]
