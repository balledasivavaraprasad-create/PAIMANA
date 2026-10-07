"""Peer-Relative Trajectory & Expected-vs-Actual Comparison Engine (TI-11, TI-12).

Compares target velocity against peer cohort median velocity and measures
progress gaps against planned schedule milestones or peer-derived expectations.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
import numpy as np

from .schemas import (
    ExpectedVsActualReport,
    PeerRelativeTrajectoryReport,
)


class PeerRelativeTrajectoryEngine:
    """Evaluates comparative trajectory gaps against peer cohorts and expected baselines."""

    @classmethod
    def evaluate_peer_relative_trajectory(
        cls,
        target_velocity: float,
        peer_velocities: List[float],
        metric_name: str,
        previous_target_velocity: Optional[float] = None,
        previous_peer_median: Optional[float] = None,
    ) -> PeerRelativeTrajectoryReport:
        """Compare target velocity against peer cohort median velocity."""
        clean_peers = [v for v in peer_velocities if v is not None and not math.isnan(v)]
        if not clean_peers:
            return PeerRelativeTrajectoryReport(
                metric_name=metric_name,
                target_velocity=target_velocity,
                peer_median_velocity=0.0,
                velocity_gap=0.0,
                trajectory_direction="ALIGNED_WITH_PEERS",
                is_gap_widening=False,
            )

        peer_med = float(np.median(clean_peers))
        gap = target_velocity - peer_med

        if gap > 0.5:
            direction = "AHEAD_OF_PEERS"
        elif gap < -0.5:
            direction = "LAGGING_PEERS"
        else:
            direction = "ALIGNED_WITH_PEERS"

        # Check if the gap is widening in an adverse direction
        is_widening = False
        if previous_target_velocity is not None and previous_peer_median is not None:
            prev_gap = previous_target_velocity - previous_peer_median
            if direction == "LAGGING_PEERS" and gap < prev_gap:
                is_widening = True
            elif direction == "AHEAD_OF_PEERS" and gap > prev_gap:
                is_widening = True

        return PeerRelativeTrajectoryReport(
            metric_name=metric_name,
            target_velocity=round(target_velocity, 4),
            peer_median_velocity=round(peer_med, 4),
            velocity_gap=round(gap, 4),
            trajectory_direction=direction,
            is_gap_widening=is_widening,
        )

    @classmethod
    def evaluate_expected_vs_actual(
        cls,
        actual_progress: float,
        planned_duration_months: Optional[float],
        project_age_months: Optional[float],
        metric_name: str = "physical_progress_pct",
        peer_median_progress: Optional[float] = None,
    ) -> ExpectedVsActualReport:
        """Evaluate actual progress against planned schedule curve or peer-derived baseline."""
        # Baseline 1: Linear or S-curve schedule expectation if durations available
        if planned_duration_months and planned_duration_months > 0 and project_age_months is not None:
            time_elapsed_ratio = min(1.0, max(0.0, project_age_months / planned_duration_months))
            # Standard S-curve logistic approximation: 1 / (1 + exp(-6 * (t - 0.5)))
            expected_val = float(100.0 / (1.0 + math.exp(-6.0 * (time_elapsed_ratio - 0.5))))
            baseline_type = "SCHEDULE"
        elif peer_median_progress is not None:
            expected_val = peer_median_progress
            baseline_type = "PEER_DERIVED"
        else:
            expected_val = actual_progress
            baseline_type = "HISTORICAL_TREND"

        gap = actual_progress - expected_val

        if gap >= 5.0:
            status = "AHEAD_OF_EXPECTED"
        elif gap >= -5.0:
            status = "ON_TRACK"
        elif gap >= -15.0:
            status = "BELOW_EXPECTED"
        else:
            status = "CRITICALLY_BELOW"

        return ExpectedVsActualReport(
            metric_name=metric_name,
            actual_value=round(actual_progress, 4),
            expected_value=round(expected_val, 4),
            gap=round(gap, 4),
            baseline_type=baseline_type,
            status=status,
        )
