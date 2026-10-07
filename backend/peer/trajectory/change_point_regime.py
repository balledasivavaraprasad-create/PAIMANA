"""Change-Point & Execution Regime Shift Detection Engine (TI-09, TI-10).

Identifies structural inflection points where underlying velocity shifted,
and infers persistent execution regimes (e.g. STAGNATING, RECOVERING, DECELERATING).
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from .schemas import (
    ChangePointReport,
    ExecutionRegime,
    RegimeShiftReport,
)


class ChangePointAndRegimeEngine:
    """Detects trajectory structural change-points and classifies operational execution regimes."""

    @classmethod
    def detect_change_point(
        cls,
        values: List[float],
        metric_name: str,
        dates: Optional[List[str]] = None,
    ) -> ChangePointReport:
        """Find the inflection index that best splits the trajectory using sum-of-squares partitioning."""
        n = len(values)
        if n < 6:
            return ChangePointReport(
                metric_name=metric_name,
                change_point_detected=False,
                estimated_change_index=None,
                estimated_change_date=None,
                pre_change_mean_velocity=0.0,
                post_change_mean_velocity=0.0,
                method="INSUFFICIENT_HISTORY",
                confidence="LOW",
            )

        deltas = np.diff(np.array(values, dtype=float))
        m = len(deltas)

        # Baseline variance with single mean
        total_ss = float(np.sum((deltas - np.mean(deltas)) ** 2))
        best_k = None
        min_sse = total_ss
        best_pre_mean = float(np.mean(deltas))
        best_post_mean = float(np.mean(deltas))

        # Search for split point k leaving at least 2 observations on each side
        for k in range(2, m - 2):
            pre = deltas[:k]
            post = deltas[k:]

            pre_mean = float(np.mean(pre))
            post_mean = float(np.mean(post))

            sse = float(np.sum((pre - pre_mean) ** 2) + np.sum((post - post_mean) ** 2))
            if sse < min_sse:
                min_sse = sse
                best_k = k
                best_pre_mean = pre_mean
                best_post_mean = post_mean

        # Significance criteria: SSE reduction >= 35% and velocity shift >= 0.75 pp/mo
        sse_reduction = (total_ss - min_sse) / total_ss if total_ss > 1e-4 else 0.0
        velocity_shift = abs(best_post_mean - best_pre_mean)

        change_detected = sse_reduction >= 0.35 and velocity_shift >= 0.75 and best_k is not None

        change_date = None
        if change_detected and dates and best_k is not None and best_k < len(dates):
            change_date = str(dates[best_k])

        confidence = "HIGH" if sse_reduction >= 0.50 else "MODERATE"

        return ChangePointReport(
            metric_name=metric_name,
            change_point_detected=change_detected,
            estimated_change_index=best_k if change_detected else None,
            estimated_change_date=change_date,
            pre_change_mean_velocity=round(best_pre_mean, 4),
            post_change_mean_velocity=round(best_post_mean, 4),
            method="BINARY_SEGMENTATION_SSE",
            confidence=confidence if change_detected else "LOW",
        )

    @classmethod
    def infer_execution_regime(
        cls,
        physical_progress_pct: Optional[float],
        latest_velocity: float,
        is_stagnant: bool,
        is_recovering: bool,
        is_sustained_decel: bool,
        is_accelerating: bool,
        volatility_category: str,
        dates: Optional[List[str]] = None,
    ) -> RegimeShiftReport:
        """Classify the current operational execution regime from consolidated signals."""
        signals: List[str] = []

        if physical_progress_pct is not None and physical_progress_pct >= 98.0:
            regime = ExecutionRegime.COMPLETED
            signals.append("Cumulative physical progress exceeds 98% (project substantially completed).")
        elif is_stagnant:
            regime = ExecutionRegime.STAGNATING
            signals.append("Sustained zero/near-zero progress over multiple consecutive reporting periods.")
        elif is_recovering:
            regime = ExecutionRegime.RECOVERING
            signals.append("Execution rebound: sustained positive velocity following prior stall.")
        elif is_sustained_decel:
            regime = ExecutionRegime.DECELERATING
            signals.append("Consecutive periods of declining progress velocity (negative acceleration).")
        elif is_accelerating:
            regime = ExecutionRegime.ACCELERATING
            signals.append("Monthly progress realization rate is increasing with positive acceleration.")
        elif volatility_category == "HIGHLY_VOLATILE":
            regime = ExecutionRegime.VOLATILE
            signals.append("High period-to-period change variance and uneven execution milestones.")
        else:
            regime = ExecutionRegime.NORMAL_EXECUTION
            signals.append(f"Steady progress velocity (+{latest_velocity:.2f} pp/month) within typical bounds.")

        latest_date = dates[-1] if dates else None

        return RegimeShiftReport(
            current_regime=regime,
            previous_regime=None,
            transition_index=len(dates) - 1 if dates else None,
            transition_date=latest_date,
            signals_supporting=signals,
            confidence="HIGH" if len(signals) >= 1 else "MODERATE",
        )
