"""Empirical Percentile-Based Anomaly Detector (DO-04).

Evaluates target position across empirical percentile bands with metric direction awareness
and effective sample size confidence weighting.
"""
from __future__ import annotations

import math
from typing import List, Optional
import numpy as np

from .schemas import AnomalyMethod, MethodDetectionDetail, MethodStatus


class PercentileDetector:
    """Evaluates relative peer position using empirical percentile thresholds."""

    @classmethod
    def evaluate(
        cls,
        target_value: float,
        cohort_values: List[float],
        direction_rule: str = "HIGHER_IS_WORSE",
        upper_threshold: float = 90.0,
        lower_threshold: float = 10.0,
    ) -> MethodDetectionDetail:
        """Evaluate empirical percentile rank against tail bands."""
        clean = [v for v in cohort_values if v is not None and not math.isnan(v)]
        n = len(clean)
        if n < 3:
            return MethodDetectionDetail(
                method=AnomalyMethod.PERCENTILE_BAND,
                score=None,
                threshold=upper_threshold,
                flagged=False,
                status=MethodStatus.INSUFFICIENT_DATA,
                reason=f"Insufficient peer observations (n={n}). Minimum 3 required.",
            )

        arr = np.array(clean, dtype=float)
        # Empirical percentile rank: PR = (count(x_i < x) + 0.5 * count(x_i == x)) / n * 100
        count_less = int(np.sum(arr < target_value))
        count_equal = int(np.sum(arr == target_value))
        pct_rank = ((count_less + 0.5 * count_equal) / n) * 100.0
        pct_rank = max(0.0, min(100.0, pct_rank))

        notes: List[str] = [f"Effective peer sample size: n={n}"]
        if n < 10:
            notes.append(f"Small peer cohort (n={n}); percentile estimates carry sampling uncertainty.")

        flagged = False
        reason = ""

        if direction_rule == "HIGHER_IS_WORSE":
            if pct_rank >= upper_threshold:
                flagged = True
                reason = f"Target percentile rank ({pct_rank:.1f}%) is in extreme adverse upper tail (>= {upper_threshold}%)."
            elif pct_rank <= lower_threshold:
                flagged = False  # Favorable performance
                reason = f"Target percentile rank ({pct_rank:.1f}%) is in favorable lower tail (<= {lower_threshold}%)."
            else:
                reason = f"Target percentile rank ({pct_rank:.1f}%) lies within normal peer variation."
        elif direction_rule == "HIGHER_IS_BETTER":
            if pct_rank <= lower_threshold:
                flagged = True
                reason = f"Target percentile rank ({pct_rank:.1f}%) is in critical adverse lower tail (<= {lower_threshold}%)."
            elif pct_rank >= upper_threshold:
                flagged = False  # Favorable performance
                reason = f"Target percentile rank ({pct_rank:.1f}%) is in leading upper tail (>= {upper_threshold}%)."
            else:
                reason = f"Target percentile rank ({pct_rank:.1f}%) lies within normal peer variation."
        else:
            # Neutral: both extremes may indicate unusual divergence
            if pct_rank >= upper_threshold or pct_rank <= lower_threshold:
                flagged = True
                reason = f"Target percentile rank ({pct_rank:.1f}%) diverges significantly from peer body."
            else:
                reason = f"Target percentile rank ({pct_rank:.1f}%) is aligned with peers."

        status = MethodStatus.FLAGGED if flagged else MethodStatus.NOT_FLAGGED

        return MethodDetectionDetail(
            method=AnomalyMethod.PERCENTILE_BAND,
            score=round(pct_rank, 2),
            threshold=upper_threshold if direction_rule != "HIGHER_IS_BETTER" else lower_threshold,
            flagged=flagged,
            status=status,
            lower_bound=float(np.percentile(arr, lower_threshold)),
            upper_bound=float(np.percentile(arr, upper_threshold)),
            reason=reason,
            notes=notes,
        )
