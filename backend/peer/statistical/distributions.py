"""Distribution-Shape, Skewness & Tail Analysis Engine (SB-07).

Analyzes skewness, kurtosis, and empirical distributional characteristics
of infrastructure benchmark metrics without assuming normality.
"""
from __future__ import annotations

import math
from typing import Dict, List, Tuple
import numpy as np
from scipy import stats

from .schemas import DistributionShape


class DistributionAnalyzer:
    """Evaluates distribution shape, skewness, and tail behavior."""

    @classmethod
    def analyze_distribution(
        cls,
        values: List[float]
    ) -> Tuple[float, float, DistributionShape, Dict[str, float]]:
        """Compute skewness, kurtosis, shape classification, and normality metrics."""
        arr = np.array(values, dtype=float)
        n = len(arr)

        if n < 3:
            return 0.0, 0.0, DistributionShape.UNKNOWN, {}

        # Skewness
        try:
            skew_val = float(stats.skew(arr, bias=False)) if n >= 3 else 0.0
            if math.isnan(skew_val):
                skew_val = 0.0
        except Exception:
            skew_val = 0.0

        # Kurtosis (excess kurtosis, normal = 0.0)
        try:
            kurt_val = float(stats.kurtosis(arr, bias=False)) if n >= 4 else 0.0
            if math.isnan(kurt_val):
                kurt_val = 0.0
        except Exception:
            kurt_val = 0.0

        normality_metrics: Dict[str, float] = {}
        # Shapiro-Wilk test if sample size is between 5 and 5000
        if 5 <= n <= 5000 and len(set(arr)) > 1:
            try:
                stat, p_val = stats.shapiro(arr)
                normality_metrics["shapiro_statistic"] = round(float(stat), 4)
                normality_metrics["shapiro_p_value"] = round(float(p_val), 4)
            except Exception:
                pass

        # Shape classification: skewness takes precedence for asymmetry;
        # kurtosis distinguishes heavy-tailed profiles for approximately symmetric distributions.
        if n < 5:
            shape = DistributionShape.UNKNOWN
        elif skew_val > 0.75:
            shape = DistributionShape.RIGHT_SKEWED
        elif skew_val < -0.75:
            shape = DistributionShape.LEFT_SKEWED
        elif kurt_val > 3.0:
            shape = DistributionShape.HEAVY_TAILED
        else:
            shape = DistributionShape.APPROXIMATELY_SYMMETRIC

        return round(skew_val, 4), round(kurt_val, 4), shape, normality_metrics
