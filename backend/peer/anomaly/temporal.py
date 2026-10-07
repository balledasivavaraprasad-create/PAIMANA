"""Temporal Deviation Velocity, Acceleration & Persistence Engine (DO-10).

Analyzes chronological deviation trajectories across snapshot histories to detect
accelerating deterioration and sustained anomaly patterns.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from .schemas import TemporalDeviationReport


class TemporalAnomalyDetector:
    """Evaluates rates of change and sustained patterns across historical deviations."""

    @classmethod
    def evaluate_temporal_deviation(
        cls,
        target_project_code: str,
        metric_name: str,
        historical_deviations: List[Dict[str, Any]],
        anomaly_threshold: float = 10.0,
    ) -> TemporalDeviationReport:
        """Calculate deviation velocity, acceleration, and persistence over time.

        `historical_deviations` should be a chronologically ordered list of dicts,
        each containing 'report_month' or 'snapshot_index', and 'absolute_deviation'.
        """
        n = len(historical_deviations)
        if n < 2:
            return TemporalDeviationReport(
                metric_name=metric_name,
                target_project_code=target_project_code,
                snapshot_count=n,
                deviation_velocity=0.0,
                deviation_acceleration=0.0,
                is_accelerating=False,
                is_sustained=False,
                consecutive_anomalous_snapshots=1 if n == 1 and abs(historical_deviations[0].get("absolute_deviation", 0.0)) >= anomaly_threshold else 0,
                trend_description="Insufficient historical snapshots to calculate temporal velocity (minimum 2 required).",
            )

        devs = [float(h.get("absolute_deviation", 0.0)) for h in historical_deviations]

        # 1. Velocities (change per step)
        velocities = [devs[i] - devs[i - 1] for i in range(1, n)]
        current_velocity = float(velocities[-1])

        # 2. Acceleration (change in velocity per step)
        if len(velocities) >= 2:
            current_accel = float(velocities[-1] - velocities[-2])
        else:
            current_accel = 0.0

        is_accelerating = current_velocity > 0.5 and current_accel > 0.0

        # 3. Sustained anomaly detection (consecutive snapshots exceeding threshold)
        consecutive_count = 0
        for d in reversed(devs):
            if abs(d) >= anomaly_threshold:
                consecutive_count += 1
            else:
                break

        is_sustained = consecutive_count >= 3

        # 4. Trend narrative
        if is_accelerating:
            trend_desc = (
                f"Accelerating deviation: velocity is +{current_velocity:.2f} per snapshot with positive acceleration (+{current_accel:.2f}). "
                "Gap between target and peer benchmark is widening."
            )
        elif current_velocity > 0:
            trend_desc = f"Expanding deviation: velocity is +{current_velocity:.2f} per snapshot."
        elif current_velocity < 0:
            trend_desc = f"Converging deviation: velocity is {current_velocity:.2f} per snapshot. Project is realigning toward peer baseline."
        else:
            trend_desc = "Stable deviation: relative distance from peer baseline remains constant."

        if is_sustained:
            trend_desc += f" Sustained anomaly for {consecutive_count} consecutive periods."

        return TemporalDeviationReport(
            metric_name=metric_name,
            target_project_code=target_project_code,
            snapshot_count=n,
            deviation_velocity=round(current_velocity, 4),
            deviation_acceleration=round(current_accel, 4),
            is_accelerating=is_accelerating,
            is_sustained=is_sustained,
            consecutive_anomalous_snapshots=consecutive_count,
            trend_description=trend_desc,
        )
