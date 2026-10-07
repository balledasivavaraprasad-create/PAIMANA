"""Validation and Empirical Efficacy Framework for Peer Intelligence.

Exposes:
- CohortValidator & CohortValidationResult (cohort logic and purity verification)
- PeerBacktestEngine & PeerBacktestReport (forecasting accuracy vs baselines)
- BenchmarkUsefulnessValidator & BenchmarkUsefulnessReport (variance reduction & discriminative power)
"""
from .cohort_validator import (
    CohortValidationCriteria,
    CohortValidationResult,
    CohortValidator,
)
from .backtest import (
    BacktestMetricResult,
    PeerBacktestEngine,
    PeerBacktestReport,
)
from .benchmark_usefulness import (
    BenchmarkUsefulnessReport,
    BenchmarkUsefulnessValidator,
    MetricUsefulnessResult,
)

__all__ = [
    "CohortValidationCriteria",
    "CohortValidationResult",
    "CohortValidator",
    "BacktestMetricResult",
    "PeerBacktestEngine",
    "PeerBacktestReport",
    "BenchmarkUsefulnessReport",
    "BenchmarkUsefulnessValidator",
    "MetricUsefulnessResult",
]
