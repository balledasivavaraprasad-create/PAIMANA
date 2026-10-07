"""Interquartile Range (IQR) & Tukey Fences Outlier Detector (DO-03).

Identifies observations beyond conventional Tukey fences (1.5x IQR mild, 3.0x IQR extreme).
"""
from __future__ import annotations

import math
from typing import List, Optional
import numpy as np

from .schemas import AnomalyMethod, MethodDetectionDetail, MethodStatus


class IQRDetector:
    """Detects outliers using empirical quartiles and Tukey fences."""

    DEFAULT_MULTIPLIER = 1.5

    @classmethod
    def evaluate(
        cls,
        target_value: float,
        cohort_values: List[float],
        multiplier: float = DEFAULT_MULTIPLIER,
    ) -> MethodDetectionDetail:
        """Evaluate target value against IQR Tukey fences."""
        clean = [v for v in cohort_values if v is not None and not math.isnan(v)]
        if len(clean) < 3:
            return MethodDetectionDetail(
                method=AnomalyMethod.IQR_FENCE,
                score=None,
                threshold=multiplier,
                flagged=False,
                status=MethodStatus.INSUFFICIENT_DATA,
                reason=f"Insufficient peer observations (n={len(clean)}). Minimum 3 required.",
            )

        arr = np.array(clean, dtype=float)
        q25, q75 = np.percentile(arr, [25, 75])
        iqr = float(q75 - q25)

        if iqr <= 1e-6:
            diff = abs(target_value - float(np.median(arr)))
            if diff <= 1e-4:
                return MethodDetectionDetail(
                    method=AnomalyMethod.IQR_FENCE,
                    score=0.0,
                    threshold=multiplier,
                    flagged=False,
                    status=MethodStatus.NOT_FLAGGED,
                    reason="Target value identical to peer distribution with zero IQR.",
                )
            else:
                return MethodDetectionDetail(
                    method=AnomalyMethod.IQR_FENCE,
                    score=None,
                    threshold=multiplier,
                    flagged=False,
                    status=MethodStatus.INSUFFICIENT_DISPERSION,
                    reason="Zero IQR across peer cohort. Fences cannot be calculated.",
                )

        lower_fence = float(q25 - (multiplier * iqr))
        upper_fence = float(q75 + (multiplier * iqr))
        extreme_lower = float(q25 - (3.0 * iqr))
        extreme_upper = float(q75 + (3.0 * iqr))

        is_upper_outlier = target_value > upper_fence
        is_lower_outlier = target_value < lower_fence
        flagged = is_upper_outlier or is_lower_outlier

        status = MethodStatus.FLAGGED if flagged else MethodStatus.NOT_FLAGGED

        # Score indicates fence distance in IQR units
        if target_value > q75:
            score = float((target_value - q75) / iqr)
        elif target_value < q25:
            score = float((q25 - target_value) / iqr)
        else:
            score = 0.0

        is_extreme = target_value > extreme_upper or target_value < extreme_lower
        severity_label = "extreme" if is_extreme else ("mild" if flagged else "normal")

        if flagged:
            side = "above upper fence" if is_upper_outlier else "below lower fence"
            reason = f"Target ({target_value:.2f}) is a {severity_label} outlier {side} [{lower_fence:.2f}, {upper_fence:.2f}]."
        else:
            reason = f"Target ({target_value:.2f}) lies within Tukey fences [{lower_fence:.2f}, {upper_fence:.2f}]."

        return MethodDetectionDetail(
            method=AnomalyMethod.IQR_FENCE,
            score=round(score, 4),
            threshold=multiplier,
            flagged=flagged,
            status=status,
            lower_bound=round(lower_fence, 4),
            upper_bound=round(upper_fence, 4),
            reason=reason,
            notes=[
                f"Q25: {q25:.2f}, Q75: {q75:.2f}, IQR: {iqr:.2f}",
                f"Extreme fences (3.0x): [{extreme_lower:.2f}, {extreme_upper:.2f}]",
            ],
        )
