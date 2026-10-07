"""Trend & Volatility Analysis Engine (TI-04, TI-05).

Estimates statistical and robust (Theil-Sen) trajectory slopes, determinacy (R^2),
and evaluates execution volatility and stability.
"""
from __future__ import annotations

import math
from typing import List, Tuple
import numpy as np

from .schemas import TrendProfile, VolatilityProfile


class TrendAndVolatilityAnalyzer:
    """Computes parametric/robust trajectory trends and variability profiles."""

    @classmethod
    def analyze_trend(
        cls,
        values: List[float],
        metric_name: str,
        direction_rule: str = "HIGHER_IS_BETTER",
    ) -> TrendProfile:
        """Estimate parametric OLS and non-parametric Theil-Sen trend slopes."""
        n = len(values)
        if n < 2:
            return TrendProfile(
                metric_name=metric_name,
                slope_ols=0.0,
                slope_theil_sen=0.0,
                trend_direction="STABLE",
                r_squared=0.0,
                method="INSUFFICIENT_DATA",
            )

        x = np.arange(n, dtype=float)
        y = np.array(values, dtype=float)

        # 1. OLS Linear Regression
        try:
            poly, residuals, _, _, _ = np.polyfit(x, y, 1, full=True)
            slope_ols = float(poly[0])
            y_pred = np.polyval(poly, x)
            ss_tot = float(np.sum((y - np.mean(y)) ** 2))
            ss_res = float(np.sum((y - y_pred) ** 2))
            r_sq = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-6 else 1.0
            r_sq = max(0.0, min(1.0, r_sq))
        except Exception:
            slope_ols = 0.0
            r_sq = 0.0

        # 2. Theil-Sen Robust Estimator (median of pairwise slopes)
        pairwise_slopes = []
        for i in range(n):
            for j in range(i + 1, n):
                if j > i:
                    s = (y[j] - y[i]) / (j - i)
                    pairwise_slopes.append(float(s))

        slope_ts = float(np.median(pairwise_slopes)) if pairwise_slopes else slope_ols

        # 3. Trend Direction Classification
        eff_slope = slope_ts
        if direction_rule == "HIGHER_IS_BETTER":
            if eff_slope > 0.5:
                trend_dir = "IMPROVING"
            elif eff_slope < -0.2:
                trend_dir = "DETERIORATING"
            else:
                trend_dir = "STABLE"
        elif direction_rule == "HIGHER_IS_WORSE":
            if eff_slope > 0.5:
                trend_dir = "DETERIORATING"
            elif eff_slope < -0.2:
                trend_dir = "IMPROVING"
            else:
                trend_dir = "STABLE"
        else:
            trend_dir = "GROWING" if eff_slope > 0.5 else ("DECLINING" if eff_slope < -0.5 else "STABLE")

        return TrendProfile(
            metric_name=metric_name,
            slope_ols=round(slope_ols, 4),
            slope_theil_sen=round(slope_ts, 4),
            trend_direction=trend_dir,
            r_squared=round(r_sq, 4),
            method="OLS_THEIL_SEN",
        )

    @classmethod
    def analyze_volatility(
        cls,
        values: List[float],
        metric_name: str,
    ) -> VolatilityProfile:
        """Measure period-to-period change variance and execution stability."""
        n = len(values)
        if n < 3:
            return VolatilityProfile(
                metric_name=metric_name,
                rolling_std=0.0,
                mad_change=0.0,
                cv=0.0,
                stability_category="STABLE",
            )

        y = np.array(values, dtype=float)
        deltas = np.diff(y)

        # Standard deviation of period deltas
        std_delta = float(np.std(deltas, ddof=1)) if len(deltas) > 1 else 0.0

        # MAD of deltas
        med_delta = float(np.median(deltas))
        mad_delta = float(np.median(np.abs(deltas - med_delta)))

        # Coefficient of variation
        mean_delta = float(np.mean(np.abs(deltas)))
        cv = float(std_delta / mean_delta) if mean_delta > 1e-4 else 0.0

        # Stability categorization
        if cv >= 1.5 or std_delta >= 5.0:
            category = "HIGHLY_VOLATILE"
        elif cv >= 0.75 or std_delta >= 2.0:
            category = "MODERATE_VARIABILITY"
        else:
            category = "STABLE"

        return VolatilityProfile(
            metric_name=metric_name,
            rolling_std=round(std_delta, 4),
            mad_change=round(mad_delta, 4),
            cv=round(cv, 4),
            stability_category=category,
        )
