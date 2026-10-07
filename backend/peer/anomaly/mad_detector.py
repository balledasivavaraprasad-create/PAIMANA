"""Modified Z-Score & Robust MAD Anomaly Detector (DO-02).

Applies Median Absolute Deviation (MAD) to compute outlier-resistant Modified Z-scores
with explicit zero-dispersion safeguards.
"""
from __future__ import annotations

import math
from typing import List, Optional
import numpy as np

from .schemas import AnomalyMethod, MethodDetectionDetail, MethodStatus


class ModifiedZScoreDetector:
    """Robust anomaly detector based on Median Absolute Deviation (MAD)."""

    DEFAULT_THRESHOLD = 3.5

    @classmethod
    def evaluate(
        cls,
        target_value: float,
        cohort_values: List[float],
        threshold: float = DEFAULT_THRESHOLD,
    ) -> MethodDetectionDetail:
        """Evaluate target value using Modified Z-score."""
        clean = [v for v in cohort_values if v is not None and not math.isnan(v)]
        if len(clean) < 3:
            return MethodDetectionDetail(
                method=AnomalyMethod.MODIFIED_Z_SCORE,
                score=None,
                threshold=threshold,
                flagged=False,
                status=MethodStatus.INSUFFICIENT_DATA,
                reason=f"Insufficient peer observations (n={len(clean)}). Minimum 3 required.",
            )

        arr = np.array(clean, dtype=float)
        median_val = float(np.median(arr))
        abs_deviations = np.abs(arr - median_val)
        mad_val = float(np.median(abs_deviations))

        # Check for zero dispersion
        if mad_val <= 1e-6:
            diff = abs(target_value - median_val)
            if diff <= 1e-4:
                return MethodDetectionDetail(
                    method=AnomalyMethod.MODIFIED_Z_SCORE,
                    score=0.0,
                    threshold=threshold,
                    flagged=False,
                    status=MethodStatus.NOT_FLAGGED,
                    reason="Target value identical to constant peer cohort median (zero dispersion).",
                    notes=["Zero MAD: Peer cohort has zero dispersion across observations."],
                )
            else:
                return MethodDetectionDetail(
                    method=AnomalyMethod.MODIFIED_Z_SCORE,
                    score=None,
                    threshold=threshold,
                    flagged=False,
                    status=MethodStatus.INSUFFICIENT_DISPERSION,
                    reason="Zero MAD: All peer observations have identical values. Modified Z-score cannot be calculated without dispersion.",
                    notes=[f"Target differs by {diff:.4f} from constant peer value {median_val:.4f}."],
                )

        # Standard Modified Z-Score formula: MZ = 0.6745 * (x - median) / MAD
        mod_z = float(0.6745 * (target_value - median_val) / mad_val)
        abs_mod_z = abs(mod_z)
        flagged = abs_mod_z >= threshold

        status = MethodStatus.FLAGGED if flagged else MethodStatus.NOT_FLAGGED
        reason = (
            f"Modified Z-Score ({abs_mod_z:.2f}) {'exceeds' if flagged else 'within'} threshold ({threshold:.1f})."
        )

        return MethodDetectionDetail(
            method=AnomalyMethod.MODIFIED_Z_SCORE,
            score=round(mod_z, 4),
            threshold=threshold,
            flagged=flagged,
            status=status,
            lower_bound=round(median_val - (threshold * mad_val / 0.6745), 4),
            upper_bound=round(median_val + (threshold * mad_val / 0.6745), 4),
            reason=reason,
            notes=[f"Peer median: {median_val:.4f}, Peer MAD: {mad_val:.4f}"],
        )
