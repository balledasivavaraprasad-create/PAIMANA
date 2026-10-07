"""Rolling Velocity & Acceleration Analysis Engine (TI-02, TI-03).

Calculates period-over-period metric velocity, rolling 3-period and 6-period averages,
acceleration/deceleration rates, and direction classifications.
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple
import numpy as np

from .schemas import (
    AccelerationProfile,
    TrajectoryDirection,
    VelocityProfile,
)


class VelocityCalculator:
    """Calculates rolling velocity and acceleration profiles across time-series values."""

    @classmethod
    def compute_velocity_and_acceleration(
        cls,
        values: List[float],
        metric_name: str,
        unit: str = "percentage_points_per_month",
        time_deltas: Optional[List[float]] = None,
    ) -> Tuple[VelocityProfile, AccelerationProfile]:
        """Compute rolling velocity and acceleration from a sequence of observations."""
        n = len(values)
        if n < 2:
            vel = VelocityProfile(
                metric_name=metric_name,
                latest_velocity=0.0,
                previous_velocity=None,
                rolling_3_velocity=0.0,
                rolling_6_velocity=0.0,
                unit=unit,
                direction=TrajectoryDirection.STABLE,
                confidence="INSUFFICIENT",
            )
            acc = AccelerationProfile(
                metric_name=metric_name,
                current_acceleration=0.0,
                previous_acceleration=None,
                is_sustained_deceleration=False,
                is_accelerating=False,
            )
            return vel, acc

        # Default time delta = 1 month if not specified
        dts = time_deltas if time_deltas and len(time_deltas) == n - 1 else [1.0] * (n - 1)

        # 1. Period velocities: V_i = (X_i - X_{i-1}) / dt_i
        velocities = []
        for i in range(1, n):
            dt = max(float(dts[i - 1]), 0.1)
            v = (values[i] - values[i - 1]) / dt
            velocities.append(float(v))

        latest_v = velocities[-1]
        prev_v = velocities[-2] if len(velocities) >= 2 else None

        # 2. Rolling averages
        r3_slice = velocities[-3:] if len(velocities) >= 3 else velocities
        r6_slice = velocities[-6:] if len(velocities) >= 6 else velocities
        r3_v = float(np.mean(r3_slice))
        r6_v = float(np.mean(r6_slice))

        # 3. Accelerations: A_i = (V_i - V_{i-1}) / dt_i
        accelerations = []
        for i in range(1, len(velocities)):
            dt = max(float(dts[i]), 0.1)
            a = (velocities[i] - velocities[i - 1]) / dt
            accelerations.append(float(a))

        current_a = accelerations[-1] if accelerations else 0.0
        prev_a = accelerations[-2] if len(accelerations) >= 2 else None

        is_accelerating = current_a > 0.1
        # Sustained deceleration: at least 2 consecutive periods of negative acceleration
        is_sustained_decel = (
            len(accelerations) >= 2 and accelerations[-1] < -0.1 and accelerations[-2] < -0.1
        )

        # 4. Direction classification
        if latest_v < -0.1:
            direction = TrajectoryDirection.REVERSING
        elif abs(latest_v) <= 0.2:
            direction = TrajectoryDirection.STAGNATING
        elif is_sustained_decel:
            direction = TrajectoryDirection.DECELERATING
        elif is_accelerating:
            direction = TrajectoryDirection.ACCELERATING
        elif abs(latest_v - r3_v) <= 0.5:
            direction = TrajectoryDirection.STEADY_GROWTH
        else:
            direction = TrajectoryDirection.STABLE

        confidence = "HIGH" if n >= 6 else ("MODERATE" if n >= 3 else "LOW")

        vel_prof = VelocityProfile(
            metric_name=metric_name,
            latest_velocity=round(latest_v, 4),
            previous_velocity=round(prev_v, 4) if prev_v is not None else None,
            rolling_3_velocity=round(r3_v, 4),
            rolling_6_velocity=round(r6_v, 4),
            unit=unit,
            direction=direction,
            confidence=confidence,
        )

        acc_prof = AccelerationProfile(
            metric_name=metric_name,
            current_acceleration=round(current_a, 4),
            previous_acceleration=round(prev_a, 4) if prev_a is not None else None,
            is_sustained_deceleration=is_sustained_decel,
            is_accelerating=is_accelerating,
        )

        return vel_prof, acc_prof
