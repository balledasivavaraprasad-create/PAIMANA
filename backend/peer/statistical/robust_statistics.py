"""Robust Statistics & Empirical Percentile Engine (SB-02, SB-03).

Provides robust central tendency, dispersion metrics, empirical percentiles,
and relative position benchmarks for infrastructure monitoring metrics.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple
import numpy as np

from .schemas import MetricDirection, PercentileBenchmark


class RobustStatisticsEngine:
    """Computes robust statistical estimators and relative percentile rankings."""

    @staticmethod
    def compute_central_tendency(values: List[float], alpha: float = 0.10) -> Dict[str, float]:
        """Compute mean, median, and trimmed mean."""
        arr = np.array(values, dtype=float)
        if len(arr) == 0:
            return {"mean": 0.0, "median": 0.0, "trimmed_mean": 0.0}

        mean_val = float(np.mean(arr))
        median_val = float(np.median(arr))

        n = len(arr)
        k = int(round(alpha * n))
        if alpha > 0 and k == 0 and n >= 5:
            k = 1

        if k > 0 and n > 2 * k:
            sorted_arr = np.sort(arr)
            trimmed_slice = sorted_arr[k : n - k]
            trimmed_val = float(np.mean(trimmed_slice))
        else:
            trimmed_val = mean_val

        return {
            "mean": round(mean_val, 4),
            "median": round(median_val, 4),
            "trimmed_mean": round(trimmed_val, 4),
        }

    @staticmethod
    def compute_dispersion(values: List[float]) -> Dict[str, float]:
        """Compute sample standard deviation, MAD (scale-adjusted), IQR, and CV."""
        arr = np.array(values, dtype=float)
        n = len(arr)
        if n <= 1:
            return {"std": 0.0, "mad": 0.0, "iqr": 0.0, "cv": 0.0}

        std_val = float(np.std(arr, ddof=1))
        median_val = float(np.median(arr))

        # MAD: scale factor 1.4826 makes MAD consistent with normal standard deviation
        abs_deviations = np.abs(arr - median_val)
        mad_val = float(1.4826 * np.median(abs_deviations))

        # Percentiles for IQR
        q75, q25 = np.percentile(arr, [75, 25])
        iqr_val = float(q75 - q25)

        # Coefficient of variation
        mean_val = float(np.mean(arr))
        cv_val = float(std_val / abs(mean_val)) if abs(mean_val) > 1e-6 else 0.0

        return {
            "std": round(std_val, 4),
            "mad": round(mad_val, 4),
            "iqr": round(iqr_val, 4),
            "cv": round(cv_val, 4),
        }

    @staticmethod
    def compute_percentiles(values: List[float]) -> Dict[str, float]:
        """Compute standard empirical percentiles (P10, P25, P50, P75, P90)."""
        arr = np.array(values, dtype=float)
        if len(arr) == 0:
            return {"p10": 0.0, "p25": 0.0, "p50": 0.0, "p75": 0.0, "p90": 0.0}

        p10, p25, p50, p75, p90 = np.percentile(arr, [10, 25, 50, 75, 90])
        return {
            "p10": round(float(p10), 4),
            "p25": round(float(p25), 4),
            "p50": round(float(p50), 4),
            "p75": round(float(p75), 4),
            "p90": round(float(p90), 4),
        }

    @classmethod
    def evaluate_target_percentile(
        cls,
        target_value: float,
        cohort_values: List[float],
        metric_name: str,
        direction: MetricDirection,
    ) -> PercentileBenchmark:
        """Compute target percentile rank and relative position interpretation."""
        arr = np.array(cohort_values, dtype=float)
        n = len(arr)
        if n == 0:
            return PercentileBenchmark(
                metric_name=metric_name,
                target_value=target_value,
                percentile_rank=50.0,
                interpretation="UNKNOWN",
                peers_below=0,
                peers_above=0,
                distance_from_median=0.0,
                distance_from_q75=0.0,
            )

        # Empirical percentile rank formula:
        # PR = (count(x_i < x) + 0.5 * count(x_i == x)) / n * 100
        count_less = int(np.sum(arr < target_value))
        count_equal = int(np.sum(arr == target_value))
        peers_below = count_less
        peers_above = int(np.sum(arr > target_value))

        percentile_rank = ((count_less + 0.5 * count_equal) / n) * 100.0
        percentile_rank = max(0.0, min(100.0, percentile_rank))

        median_val = float(np.median(arr))
        q75_val = float(np.percentile(arr, 75))

        distance_median = target_value - median_val
        distance_q75 = target_value - q75_val

        # Interpretation banding
        if percentile_rank >= 85.0:
            interpretation = "SIGNIFICANTLY_ABOVE"
        elif percentile_rank >= 60.0:
            interpretation = "ABOVE_MEDIAN"
        elif percentile_rank <= 15.0:
            interpretation = "SIGNIFICANTLY_BELOW"
        elif percentile_rank <= 40.0:
            interpretation = "BELOW_MEDIAN"
        else:
            interpretation = "TYPICAL_FOR_PEERS"

        return PercentileBenchmark(
            metric_name=metric_name,
            target_value=target_value,
            percentile_rank=round(percentile_rank, 2),
            interpretation=interpretation,
            peers_below=peers_below,
            peers_above=peers_above,
            distance_from_median=round(distance_median, 4),
            distance_from_q75=round(distance_q75, 4),
        )
