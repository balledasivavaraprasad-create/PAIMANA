"""Small-Sample Safeguards & Effective Sample Size Evaluator (SB-05).

Enforces operational sample-size guardrails based on effective sample size:
- n <= 2: INSUFFICIENT (benchmarking suppressed)
- n in [3, 4]: HIGHLY_LIMITED (descriptive median/IQR only, suppress bootstrap/shape)
- n in [5, 9]: CAUTIOUS_EXPLORATORY (preliminary percentiles, cautious warnings)
- n in [10, 19]: PRELIMINARY (emerging empirical distribution)
- n >= 20: SUBSTANTIAL (robust parametric and non-parametric reference)
"""
from __future__ import annotations

import math
from typing import List, Tuple

from .schemas import SmallSampleStatus


class SmallSampleEvaluator:
    """Evaluates sample size sufficiency and enforces analytical guardrails."""

    @staticmethod
    def evaluate_sample_size(values: List[float]) -> Tuple[SmallSampleStatus, int, List[str]]:
        """Determine small sample status, effective count, and operational warnings."""
        clean = [v for v in values if v is not None and not math.isnan(v) and not math.isinf(v)]
        n = len(clean)
        warnings: List[str] = []

        if n <= 2:
            status = SmallSampleStatus.INSUFFICIENT
            warnings.append(
                f"Cohort sample size (n={n}) is strictly insufficient for statistical benchmarking. Minimum n=3 required."
            )
        elif n in (3, 4):
            status = SmallSampleStatus.HIGHLY_LIMITED
            warnings.append(
                f"Cohort sample size (n={n}) is highly limited. Resampling, distribution fitting, and extreme percentiles are suppressed."
            )
        elif 5 <= n <= 9:
            status = SmallSampleStatus.CAUTIOUS_EXPLORATORY
            warnings.append(
                f"Cohort sample size (n={n}) is small. Percentile estimates and confidence intervals should be interpreted cautiously."
            )
        elif 10 <= n <= 19:
            status = SmallSampleStatus.PRELIMINARY
        else:
            status = SmallSampleStatus.SUBSTANTIAL

        # Check for zero variance / identical values
        if n >= 3 and len(set(clean)) == 1:
            warnings.append("Degenerate distribution: All peer observations have identical values (zero dispersion).")

        return status, n, warnings

    @staticmethod
    def can_compute_benchmarks(status: SmallSampleStatus) -> bool:
        """Indicates whether basic descriptive benchmarking is permissible."""
        return status != SmallSampleStatus.INSUFFICIENT

    @staticmethod
    def can_compute_bootstrap(status: SmallSampleStatus) -> bool:
        """Indicates whether bootstrap resampling confidence intervals are statistically sound."""
        return status not in (SmallSampleStatus.INSUFFICIENT, SmallSampleStatus.HIGHLY_LIMITED)

    @staticmethod
    def can_fit_distribution_shape(status: SmallSampleStatus) -> bool:
        """Indicates whether skewness/kurtosis shape classification is reliable."""
        return status not in (SmallSampleStatus.INSUFFICIENT, SmallSampleStatus.HIGHLY_LIMITED)
