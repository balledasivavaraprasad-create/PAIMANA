"""Distribution-Shift & Temporal Drift Detection Engine (SB-09).

Detects empirical distribution shifts between cohort periods or baselines
using the Population Stability Index (PSI) and two-sample Kolmogorov-Smirnov test.
"""
from __future__ import annotations

import math
from typing import List, Tuple
import numpy as np
from scipy import stats

from .schemas import DistributionShiftReport


class DistributionShiftDetector:
    """Detects population shift and temporal drift across project distributions."""

    @classmethod
    def evaluate_shift(
        cls,
        current_values: List[float],
        reference_values: List[float],
        metric_name: str,
        bins: int = 5,
        alpha: float = 0.05,
    ) -> DistributionShiftReport:
        """Assess whether current metric values represent a distribution shift from reference."""
        curr = np.array([v for v in current_values if v is not None and not math.isnan(v)], dtype=float)
        ref = np.array([v for v in reference_values if v is not None and not math.isnan(v)], dtype=float)

        curr_median = float(np.median(curr)) if len(curr) > 0 else 0.0
        ref_median = float(np.median(ref)) if len(ref) > 0 else 0.0

        if len(curr) < 3 or len(ref) < 3:
            return DistributionShiftReport(
                metric_name=metric_name,
                current_period_median=curr_median,
                reference_period_median=ref_median,
                psi_score=0.0,
                ks_statistic=0.0,
                p_value=1.0,
                shift_detected=False,
                shift_severity="NONE",
                interpretation="Sample size insufficient to evaluate temporal shift.",
            )

        # 1. Kolmogorov-Smirnov 2-sample test
        try:
            ks_res = stats.ks_2samp(curr, ref)
            ks_stat = float(ks_res.statistic)
            p_val = float(ks_res.pvalue)
        except Exception:
            ks_stat = 0.0
            p_val = 1.0

        # 2. Population Stability Index (PSI)
        psi_score = cls._compute_psi(curr, ref, bins=bins)

        # Shift severity decision
        if (psi_score >= 0.25 and p_val < 0.10) or (p_val < 0.01 and ks_stat > 0.35):
            shift_detected = True
            shift_severity = "SEVERE"
            interpretation = (
                f"Significant distribution shift detected (PSI={psi_score:.3f}, KS p-value={p_val:.4f}). "
                "Historical reference baselines may not represent current execution dynamics."
            )
        elif (psi_score >= 0.15 and p_val < 0.10) or p_val < alpha:
            shift_detected = True
            shift_severity = "MODERATE"
            interpretation = (
                f"Moderate distribution shift detected (PSI={psi_score:.3f}, KS p-value={p_val:.4f}). "
                "Slight drift between reference and current cohort."
            )
        else:
            shift_detected = False
            shift_severity = "NONE"
            interpretation = f"Distribution is stable (PSI={psi_score:.3f}, KS p-value={p_val:.4f})."

        return DistributionShiftReport(
            metric_name=metric_name,
            current_period_median=round(curr_median, 4),
            reference_period_median=round(ref_median, 4),
            psi_score=round(psi_score, 4),
            ks_statistic=round(ks_stat, 4),
            p_value=round(p_val, 4),
            shift_detected=shift_detected,
            shift_severity=shift_severity,
            interpretation=interpretation,
        )

    @classmethod
    def _compute_psi(cls, curr: np.ndarray, ref: np.ndarray, bins: int = 5) -> float:
        """Compute Population Stability Index between reference and current arrays."""
        if len(curr) == 0 or len(ref) == 0:
            return 0.0

        # Create quantiles on reference data
        percentile_cuts = np.linspace(0, 100, bins + 1)
        bin_edges = np.percentile(ref, percentile_cuts)
        # Ensure distinct edges
        bin_edges = np.unique(bin_edges)
        if len(bin_edges) < 2:
            return 0.0

        # Ensure outer bounds cover both reference and current distributions
        bin_edges[0] = min(float(bin_edges[0]), float(np.min(curr)), float(np.min(ref))) - 1e-5
        bin_edges[-1] = max(float(bin_edges[-1]), float(np.max(curr)), float(np.max(ref))) + 1e-5

        # Counts
        ref_counts, _ = np.histogram(ref, bins=bin_edges)
        curr_counts, _ = np.histogram(curr, bins=bin_edges)

        eps = 1e-4
        ref_pct = (ref_counts + eps) / (np.sum(ref_counts) + eps * len(ref_counts))
        curr_pct = (curr_counts + eps) / (np.sum(curr_counts) + eps * len(curr_counts))

        psi = np.sum((curr_pct - ref_pct) * np.log(curr_pct / ref_pct))
        return float(max(0.0, psi))
