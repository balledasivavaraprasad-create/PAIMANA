"""Pattern Detection Engine: Stagnation, Recovery & Sudden Change (TI-06, TI-07, TI-08).

Identifies operational milestones:
- Sustained progress stagnation and stall, including stagnation with continued expenditure
- Post-stagnation recovery and execution rebounds
- Sudden velocity shocks and structural trend disruptions
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
import numpy as np

from .schemas import (
    RecoveryReport,
    StagnationReport,
    SuddenChangeReport,
)


class PatternDetector:
    """Detects operational execution patterns across historical snapshots."""

    @classmethod
    def detect_stagnation(
        cls,
        progress_values: List[float],
        expenditure_values: Optional[List[float]] = None,
        metric_name: str = "physical_progress_pct",
        stagnation_threshold_pp: float = 0.5,
        min_consecutive_periods: int = 3,
    ) -> StagnationReport:
        """Detect sustained periods of zero or negligible physical progress."""
        n = len(progress_values)
        if n < min_consecutive_periods:
            return StagnationReport(
                metric_name=metric_name,
                stagnation_detected=False,
                duration_months=0,
                progress_change=0.0,
                expenditure_change=0.0,
                is_stagnation_with_expenditure=False,
                severity="NONE",
            )

        # Count consecutive periods from the latest snapshot backward where progress delta <= threshold
        consecutive_stagnant = 0
        deltas = []
        for i in range(n - 1, 0, -1):
            d = progress_values[i] - progress_values[i - 1]
            deltas.append(d)
            if abs(d) <= stagnation_threshold_pp:
                consecutive_stagnant += 1
            else:
                break

        stagnation_detected = consecutive_stagnant >= min_consecutive_periods
        duration_months = consecutive_stagnant if stagnation_detected else 0

        # Progress change during stagnation period
        if stagnation_detected:
            start_idx = max(0, n - 1 - duration_months)
            prog_change = float(progress_values[-1] - progress_values[start_idx])
            if expenditure_values and len(expenditure_values) == n:
                exp_change = float(expenditure_values[-1] - expenditure_values[start_idx])
            else:
                exp_change = 0.0
        else:
            prog_change = float(progress_values[-1] - progress_values[-2]) if n >= 2 else 0.0
            exp_change = 0.0

        # Front-loaded billing / leakage risk: progress stalled but money spent
        stagnation_with_exp = stagnation_detected and exp_change >= 5.0

        if stagnation_with_exp and duration_months >= 4:
            severity = "CRITICAL"
        elif stagnation_with_exp or duration_months >= 4:
            severity = "HIGH"
        elif stagnation_detected:
            severity = "MODERATE"
        else:
            severity = "NONE"

        return StagnationReport(
            metric_name=metric_name,
            stagnation_detected=stagnation_detected,
            duration_months=duration_months,
            progress_change=round(prog_change, 4),
            expenditure_change=round(exp_change, 4),
            is_stagnation_with_expenditure=stagnation_with_exp,
            severity=severity,
        )

    @classmethod
    def detect_recovery(
        cls,
        progress_values: List[float],
        metric_name: str = "physical_progress_pct",
        min_recovery_periods: int = 2,
        velocity_threshold_pp: float = 1.0,
    ) -> RecoveryReport:
        """Detect recovery after an earlier period of stagnation or deceleration."""
        n = len(progress_values)
        if n < 4:
            return RecoveryReport(
                metric_name=metric_name,
                recovery_detected=False,
                prior_stagnation_duration_months=0,
                consecutive_positive_periods=0,
                latest_velocity=0.0,
                is_sustained=False,
            )

        deltas = [progress_values[i] - progress_values[i - 1] for i in range(1, n)]

        # Check latest periods for sustained positive progress
        consecutive_positive = 0
        for d in reversed(deltas):
            if d >= velocity_threshold_pp:
                consecutive_positive += 1
            else:
                break

        latest_v = float(deltas[-1]) if deltas else 0.0

        # Look for prior stagnation immediately preceding this recovery
        prior_stagnation_count = 0
        if consecutive_positive >= min_recovery_periods:
            rem_idx = len(deltas) - consecutive_positive - 1
            while rem_idx >= 0:
                if deltas[rem_idx] <= 0.5:
                    prior_stagnation_count += 1
                    rem_idx -= 1
                else:
                    break

        recovery_detected = (
            consecutive_positive >= min_recovery_periods and prior_stagnation_count >= 2
        )
        is_sustained = consecutive_positive >= 3

        return RecoveryReport(
            metric_name=metric_name,
            recovery_detected=recovery_detected,
            prior_stagnation_duration_months=prior_stagnation_count,
            consecutive_positive_periods=consecutive_positive,
            latest_velocity=round(latest_v, 4),
            is_sustained=is_sustained,
        )

    @classmethod
    def detect_sudden_change(
        cls,
        values: List[float],
        metric_name: str,
    ) -> SuddenChangeReport:
        """Detect abrupt jumps or drops in value or velocity using robust residual screening."""
        n = len(values)
        if n < 3:
            return SuddenChangeReport(
                metric_name=metric_name,
                sudden_change_detected=False,
                change_magnitude=0.0,
                change_type="NONE",
                snapshot_index=None,
                severity="NONE",
            )

        deltas = np.diff(np.array(values, dtype=float))
        med_delta = float(np.median(deltas[:-1])) if len(deltas) > 1 else float(deltas[0])
        mad_delta = float(np.median(np.abs(deltas[:-1] - med_delta))) if len(deltas) > 1 else 1.0
        mad_delta = max(mad_delta, 0.5)

        latest_delta = float(deltas[-1])
        diff_from_baseline = abs(latest_delta - med_delta)

        # Check if latest change is > 3 * MAD
        sudden_detected = diff_from_baseline >= (3.0 * mad_delta) and diff_from_baseline >= 5.0

        change_type = "NONE"
        severity = "NONE"

        if sudden_detected:
            if latest_delta > med_delta:
                change_type = "VELOCITY_SPIKE" if "progress" in metric_name else "EXPENDITURE_JUMP"
            else:
                change_type = "PROGRESS_DROP"

            severity = "HIGH" if diff_from_baseline >= (5.0 * mad_delta) else "MODERATE"

        return SuddenChangeReport(
            metric_name=metric_name,
            sudden_change_detected=sudden_detected,
            change_magnitude=round(float(diff_from_baseline), 4),
            change_type=change_type,
            snapshot_index=n - 1 if sudden_detected else None,
            severity=severity,
        )
