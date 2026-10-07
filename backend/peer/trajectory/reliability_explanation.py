"""Trajectory Reliability & Structured Supervisor Evidence Engine (TI-13, TI-14).

Evaluates historical data reliability and constructs structured evidence items
conforming to CONTEXTUALIZES semantics without causal overreach.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .schemas import (
    HistoricalCoverageReport,
    MetricTrajectoryReport,
    RegimeShiftReport,
    TrajectoryReliability,
)


class TrajectoryExplainer:
    """Evaluates trajectory data reliability and formats explainable Supervisor evidence."""

    @classmethod
    def evaluate_reliability(
        cls,
        coverage: HistoricalCoverageReport,
    ) -> TrajectoryReliability:
        """Assign an operational reliability grade based on snapshot depth and completeness."""
        n = coverage.available_snapshots
        ratio = coverage.coverage_ratio

        if n < 2 or coverage.temporal_quality == "INSUFFICIENT":
            return TrajectoryReliability.INSUFFICIENT
        elif n >= 6 and ratio >= 0.85 and coverage.missing_periods <= 1:
            return TrajectoryReliability.HIGH
        elif n >= 3 and ratio >= 0.60:
            return TrajectoryReliability.MODERATE
        else:
            return TrajectoryReliability.LOW

    @classmethod
    def build_supervisor_evidence_item(
        cls,
        target_project_code: str,
        metric_report: MetricTrajectoryReport,
        regime: RegimeShiftReport,
    ) -> Dict[str, Any]:
        """Convert metric trajectory findings into structured Supervisor evidence items."""
        m_name = metric_report.metric_name
        vel = metric_report.velocity
        acc = metric_report.acceleration
        stag = metric_report.stagnation

        # Formulate non-conflating statement
        statement_parts = []
        if stag.stagnation_detected:
            statement_parts.append(
                f"{m_name}: Stagnation detected over past {stag.duration_months} months (progress change: +{stag.progress_change:.1f} pp)"
            )
            if stag.is_stagnation_with_expenditure:
                statement_parts.append(f"with continued financial expenditure (+Rs. {stag.expenditure_change:.1f} Cr)")
        elif acc.is_sustained_deceleration:
            statement_parts.append(
                f"{m_name}: Sustained progress deceleration (latest velocity: +{vel.latest_velocity:.1f} pp/mo, acceleration: {acc.current_acceleration:.2f})"
            )
        elif vel.direction.value == "ACCELERATING":
            statement_parts.append(
                f"{m_name}: Progress accelerating (+{vel.latest_velocity:.1f} pp/mo, acceleration: +{acc.current_acceleration:.2f})"
            )
        else:
            statement_parts.append(
                f"{m_name}: Velocity is +{vel.latest_velocity:.1f} pp/mo (trend: {metric_report.trend.trend_direction})"
            )

        if metric_report.peer_relative:
            pr = metric_report.peer_relative
            statement_parts.append(f"| Peer relative: {pr.trajectory_direction} (gap: {pr.velocity_gap:+.1f} pp/mo)")

        statement = " ".join(statement_parts)

        # Map to risk level
        if stag.severity in ("CRITICAL", "HIGH") or acc.is_sustained_deceleration:
            risk_level = "SIGNIFICANTLY_ABOVE_PEERS" if "expenditure" in m_name else "LAGGING_PEERS"
        elif vel.direction.value == "STEADY_GROWTH":
            risk_level = "TYPICAL_FOR_PEERS"
        else:
            risk_level = "MODERATE_DEVIATION"

        return {
            "source": "peer_trajectory_intelligence",
            "type": "PEER_TRAJECTORY_EVALUATION",
            "metric_name": m_name,
            "target_project_code": target_project_code,
            "latest_velocity": vel.latest_velocity,
            "velocity_direction": vel.direction.value,
            "current_acceleration": acc.current_acceleration,
            "is_sustained_deceleration": acc.is_sustained_deceleration,
            "stagnation_detected": stag.stagnation_detected,
            "execution_regime": regime.current_regime.value,
            "peer_relative_direction": (
                metric_report.peer_relative.trajectory_direction
                if metric_report.peer_relative
                else "ALIGNED_WITH_PEERS"
            ),
            "relation": "CONTEXTUALIZES",
            "statement": statement,
            "limitations": [
                f"Historical coverage ratio: {metric_report.coverage.coverage_ratio:.2f}",
                f"Snapshots analyzed: {metric_report.coverage.available_snapshots}",
            ],
        }
