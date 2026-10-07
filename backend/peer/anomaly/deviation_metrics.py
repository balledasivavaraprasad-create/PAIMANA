"""Absolute & Relative Deviation Engine (DO-01).

Calculates exact absolute and relative deviations, enforces direction awareness,
distinguishes percentage points from relative percentages, and prevents near-zero
division instability.
"""
from __future__ import annotations

import math
from typing import Optional

from .schemas import DeviationDirection, DeviationResult


PERCENTAGE_POINT_METRICS = {
    "cost_overrun_pct",
    "physical_progress_pct",
    "expenditure_pct",
    "progress_expenditure_gap_pct",
    "time_overrun_pct",
}


class DeviationCalculator:
    """Computes rigorous absolute and relative deviation measurements."""

    @classmethod
    def compute_deviation(
        cls,
        target_value: float,
        peer_reference: float,
        metric_name: str,
        direction_rule: str = "HIGHER_IS_WORSE",
        unit: Optional[str] = None,
        near_zero_epsilon: float = 1e-4,
    ) -> DeviationResult:
        """Calculate absolute and relative deviation with safeguards."""
        # 1. Absolute deviation
        abs_dev = target_value - peer_reference

        # 2. Relative deviation with near-zero safeguard
        if abs(peer_reference) <= near_zero_epsilon:
            rel_dev: Optional[float] = None
            is_near_zero = True
        else:
            rel_dev = (abs_dev / abs(peer_reference)) * 100.0
            is_near_zero = False

        # 3. Unit and percentage points flag
        resolved_unit = unit or ("percentage" if metric_name in PERCENTAGE_POINT_METRICS else "value")
        is_pct_points = resolved_unit == "percentage" or metric_name in PERCENTAGE_POINT_METRICS

        # 4. Directional orientation
        if abs(abs_dev) <= near_zero_epsilon:
            dev_direction = DeviationDirection.ALIGNED_WITH_PEERS
        elif abs_dev > 0:
            dev_direction = DeviationDirection.ABOVE_PEERS
        else:
            dev_direction = DeviationDirection.BELOW_PEERS

        return DeviationResult(
            metric_name=metric_name,
            target_value=round(target_value, 4),
            peer_reference=round(peer_reference, 4),
            absolute_deviation=round(abs_dev, 4),
            relative_deviation_pct=round(rel_dev, 2) if rel_dev is not None else None,
            unit=resolved_unit,
            is_unit_percentage_points=is_pct_points,
            direction_rule=direction_rule,
            deviation_direction=dev_direction,
            is_near_zero_reference=is_near_zero,
        )
