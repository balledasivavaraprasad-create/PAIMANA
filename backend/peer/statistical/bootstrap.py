"""Bootstrap Resampling & Confidence Interval Engine (SB-04, SB-05).

Provides non-parametric bootstrap estimation for median and mean with
reproducible random seeds and analytical fallback intervals.
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple
import numpy as np

from .schemas import ConfidenceInterval, BootstrapSummary


class BootstrapEngine:
    """Computes bootstrap and analytical confidence intervals."""

    DEFAULT_RESAMPLES = 2000
    DEFAULT_SEED = 42

    @classmethod
    def compute_bootstrap_interval(
        cls,
        values: List[float],
        statistic: str = "median",
        resample_count: int = DEFAULT_RESAMPLES,
        confidence_level: float = 0.95,
        random_seed: int = DEFAULT_SEED,
    ) -> BootstrapSummary:
        """Compute non-parametric bootstrap confidence interval for median or mean."""
        arr = np.array(values, dtype=float)
        n = len(arr)
        if n == 0:
            ci = ConfidenceInterval(
                statistic=statistic,
                point_estimate=0.0,
                confidence_level=confidence_level,
                lower_bound=0.0,
                upper_bound=0.0,
                method="BOOTSTRAP_PERCENTILE",
                margin_of_error=0.0,
            )
            return BootstrapSummary(
                statistic=statistic,
                resample_count=0,
                bootstrap_mean=0.0,
                bootstrap_se=0.0,
                confidence_interval=ci,
                random_seed=random_seed,
            )

        rng = np.random.RandomState(random_seed)
        # Resample with replacement: shape (resample_count, n)
        resamples = rng.choice(arr, size=(resample_count, n), replace=True)

        if statistic == "mean":
            point_est = float(np.mean(arr))
            boot_estimates = np.mean(resamples, axis=1)
        else:
            # Default to robust median
            point_est = float(np.median(arr))
            boot_estimates = np.median(resamples, axis=1)

        boot_mean = float(np.mean(boot_estimates))
        boot_se = float(np.std(boot_estimates, ddof=1)) if resample_count > 1 else 0.0

        # Percentile method confidence interval
        alpha = 1.0 - confidence_level
        lower_pct = 100.0 * (alpha / 2.0)
        upper_pct = 100.0 * (1.0 - alpha / 2.0)

        lower_bound = float(np.percentile(boot_estimates, lower_pct))
        upper_bound = float(np.percentile(boot_estimates, upper_pct))
        margin_of_error = max(abs(point_est - lower_bound), abs(upper_bound - point_est))

        ci = ConfidenceInterval(
            statistic=statistic,
            point_estimate=round(point_est, 4),
            confidence_level=confidence_level,
            lower_bound=round(lower_bound, 4),
            upper_bound=round(upper_bound, 4),
            method="BOOTSTRAP_PERCENTILE",
            margin_of_error=round(margin_of_error, 4),
        )

        return BootstrapSummary(
            statistic=statistic,
            resample_count=resample_count,
            bootstrap_mean=round(boot_mean, 4),
            bootstrap_se=round(boot_se, 4),
            confidence_interval=ci,
            random_seed=random_seed,
        )

    @classmethod
    def compute_analytical_mean_ci(
        cls,
        values: List[float],
        confidence_level: float = 0.95
    ) -> ConfidenceInterval:
        """Compute analytical confidence interval for the mean using Student's t distribution."""
        arr = np.array(values, dtype=float)
        n = len(arr)
        if n <= 1:
            val = float(arr[0]) if n == 1 else 0.0
            return ConfidenceInterval(
                statistic="mean",
                point_estimate=val,
                confidence_level=confidence_level,
                lower_bound=val,
                upper_bound=val,
                method="T_DISTRIBUTION",
                margin_of_error=0.0,
            )

        from scipy import stats

        mean_val = float(np.mean(arr))
        se = float(stats.sem(arr))
        t_crit = float(stats.t.ppf((1.0 + confidence_level) / 2.0, df=n - 1))
        margin = t_crit * se

        return ConfidenceInterval(
            statistic="mean",
            point_estimate=round(mean_val, 4),
            confidence_level=confidence_level,
            lower_bound=round(mean_val - margin, 4),
            upper_bound=round(mean_val + margin, 4),
            method="T_DISTRIBUTION",
            margin_of_error=round(margin, 4),
        )
