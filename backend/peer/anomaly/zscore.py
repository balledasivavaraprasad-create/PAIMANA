"""Standard Z-Score Anomaly Detector (DO-02).

Evaluates target distance from peer arithmetic mean in units of sample standard deviation.
"""
from __future__ import annotations

import math
from typing import List, Optional
import numpy as np

from .schemas import AnomalyMethod, MethodDetectionDetail, MethodStatus


class OrdinaryZScoreDetector:
    """Parametric Z-score anomaly detector."""

    DEFAULT_THRESHOLD = 2.5

    @classmethod
    def evaluate(
        cls,
        target_value: float,
        cohort_values: List[float],
        threshold: float = DEFAULT_THRESHOLD,
    ) -> MethodDetectionDetail:
        """Evaluate target value using Ordinary Z-score."""
        clean = [v for v in cohort_values if v is not None and not math.isnan(v)]
        if len(clean) < 3:
            return MethodDetectionDetail(
                method=AnomalyMethod.ORDINARY_Z_SCORE,
                score=None,
                threshold=threshold,
                flagged=False,
                status=MethodStatus.INSUFFICIENT_DATA,
                reason=f"Insufficient peer observations (n={len(clean)}). Minimum 3 required.",
            )

        arr = np.array(clean, dtype=float)
        mean_val = float(np.mean(arr))
        std_val = float(np.std(arr, ddof=1))

        if std_val <= 1e-6:
            diff = abs(target_value - mean_val)
            if diff <= 1e-4:
                return MethodDetectionDetail(
                    method=AnomalyMethod.ORDINARY_Z_SCORE,
                    score=0.0,
                    threshold=threshold,
                    flagged=False,
                    status=MethodStatus.NOT_FLAGGED,
                    reason="Target value identical to constant peer mean (zero variance).",
                )
            else:
                return MethodDetectionDetail(
                    method=AnomalyMethod.ORDINARY_Z_SCORE,
                    score=None,
                    threshold=threshold,
                    flagged=False,
                    status=MethodStatus.INSUFFICIENT_DISPERSION,
                    reason="Zero standard deviation across peer cohort. Parametric Z-score cannot be calculated.",
                )

        z_score = float((target_value - mean_val) / std_val)
        abs_z = abs(z_score)
        flagged = abs_z >= threshold

        status = MethodStatus.FLAGGED if flagged else MethodStatus.NOT_FLAGGED
        reason = (
            f"Z-Score ({abs_z:.2f}) {'exceeds' if flagged else 'within'} threshold ({threshold:.1f})."
        )

        return MethodDetectionDetail(
            method=AnomalyMethod.ORDINARY_Z_SCORE,
            score=round(z_score, 4),
            threshold=threshold,
            flagged=flagged,
            status=status,
            lower_bound=round(mean_val - (threshold * std_val), 4),
            upper_bound=round(mean_val + (threshold * std_val), 4),
            reason=reason,
            notes=[f"Peer mean: {mean_val:.4f}, Peer std: {std_val:.4f}"],
        )
