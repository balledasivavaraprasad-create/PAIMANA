"""Master Trajectory Intelligence Service (TI-14).

Orchestrates snapshot validation, velocity/acceleration, trend/volatility,
stagnation/recovery, change-point/regime detection, and peer trajectory benchmarking.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Union
import numpy as np

from .schemas import (
    MetricTrajectoryReport,
    TrajectoryIntelligenceResult,
    TrajectoryReliability,
)
from .temporal_validation import TemporalValidator
from .velocity import VelocityCalculator
from .trend_volatility import TrendAndVolatilityAnalyzer
from .pattern_detection import PatternDetector
from .change_point_regime import ChangePointAndRegimeEngine
from .peer_relative import PeerRelativeTrajectoryEngine
from .reliability_explanation import TrajectoryExplainer
from peer.statistical.normalization import MetricNormalizer


DEFAULT_TRAJECTORY_METRICS = [
    "physical_progress_pct",
    "cumulative_expenditure_cr",
    "schedule_slippage_months",
    "cost_overrun_pct",
]


class TrajectoryIntelligenceService:
    """Master service providing comprehensive temporal and trajectory intelligence."""

    def __init__(self, normalizer: Optional[MetricNormalizer] = None):
        self.normalizer = normalizer or MetricNormalizer()

    def analyze_project_trajectory(
        self,
        target_project_code: str,
        target_snapshots: List[Dict[str, Any]],
        peer_cohort_snapshots: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        metrics: Optional[List[str]] = None,
        target_project: Optional[Dict[str, Any]] = None,
        cohort_id: str = "COHORT",
    ) -> TrajectoryIntelligenceResult:
        """Run complete end-to-end trajectory intelligence across historical snapshots."""
        start_time = time.time()
        eval_metrics = metrics or DEFAULT_TRAJECTORY_METRICS

        # 1. Temporal Validation of Target Snapshots
        clean_snapshots, coverage = TemporalValidator.validate_snapshots(target_snapshots)

        if len(clean_snapshots) < 2:
            reliability = TrajectoryReliability.INSUFFICIENT
            regime = ChangePointAndRegimeEngine.infer_execution_regime(
                physical_progress_pct=None,
                latest_velocity=0.0,
                is_stagnant=False,
                is_recovering=False,
                is_sustained_decel=False,
                is_accelerating=False,
                volatility_category="STABLE",
            )
            return TrajectoryIntelligenceResult(
                target_project_code=target_project_code,
                cohort_id=cohort_id,
                cohort_size=len(peer_cohort_snapshots) if peer_cohort_snapshots else 0,
                snapshots_analyzed=len(clean_snapshots),
                metrics_evaluated=eval_metrics,
                historical_coverage=coverage,
                metric_trajectories={},
                execution_regime=regime,
                overall_reliability=reliability,
                findings=[f"Insufficient snapshot history ({len(clean_snapshots)} available). Minimum 2 required."],
                evidence_items=[],
                limitations=["INSUFFICIENT_HISTORICAL_SNAPSHOTS"],
            )

        metric_reports: Dict[str, MetricTrajectoryReport] = {}
        findings: List[str] = []
        evidence_items: List[Dict[str, Any]] = []

        # Extract dates for change-point labeling
        dates = [
            str(s.get("report_month") or s.get("report_date") or f"T{i}")
            for i, s in enumerate(clean_snapshots)
        ]

        # Extract progress and expenditure arrays for cross-metric checks
        prog_vals: List[float] = []
        exp_vals: List[float] = []
        for s in clean_snapshots:
            pv = self.normalizer.extract_metric(s, "physical_progress_pct")
            ev = self.normalizer.extract_metric(s, "cumulative_expenditure_cr")
            if pv is not None:
                prog_vals.append(pv)
            if ev is not None:
                exp_vals.append(ev)

        # 2. Iterate through each requested metric
        for m in eval_metrics:
            vals: List[float] = []
            for s in clean_snapshots:
                v = self.normalizer.extract_metric(s, m)
                if v is not None:
                    vals.append(v)

            if len(vals) < 2:
                continue

            # A. Velocity & Acceleration
            vel_prof, acc_prof = VelocityCalculator.compute_velocity_and_acceleration(
                values=vals, metric_name=m
            )

            # B. Trend & Volatility
            trend_prof = TrendAndVolatilityAnalyzer.analyze_trend(
                values=vals, metric_name=m
            )
            vol_prof = TrendAndVolatilityAnalyzer.analyze_volatility(
                values=vals, metric_name=m
            )

            # C. Stagnation & Recovery
            if "progress" in m:
                stag_rep = PatternDetector.detect_stagnation(
                    progress_values=vals,
                    expenditure_values=exp_vals if len(exp_vals) == len(vals) else None,
                    metric_name=m,
                )
                rec_rep = PatternDetector.detect_recovery(progress_values=vals, metric_name=m)
            else:
                stag_rep = PatternDetector.detect_stagnation(
                    progress_values=vals, expenditure_values=None, metric_name=m
                )
                rec_rep = PatternDetector.detect_recovery(progress_values=vals, metric_name=m)

            # D. Sudden Change
            sudden_rep = PatternDetector.detect_sudden_change(values=vals, metric_name=m)

            # E. Change-Point Detection
            cp_rep = ChangePointAndRegimeEngine.detect_change_point(
                values=vals, metric_name=m, dates=dates
            )

            # F. Peer-Relative Trajectory
            peer_rel_rep = None
            if peer_cohort_snapshots:
                peer_velocities = []
                for p_code, p_snaps in peer_cohort_snapshots.items():
                    p_vals = [
                        self.normalizer.extract_metric(ps, m)
                        for ps in p_snaps
                        if self.normalizer.extract_metric(ps, m) is not None
                    ]
                    if len(p_vals) >= 2:
                        p_v, _ = VelocityCalculator.compute_velocity_and_acceleration(
                            values=p_vals, metric_name=m
                        )
                        peer_velocities.append(p_v.latest_velocity)

                if peer_velocities:
                    peer_rel_rep = PeerRelativeTrajectoryEngine.evaluate_peer_relative_trajectory(
                        target_velocity=vel_prof.latest_velocity,
                        peer_velocities=peer_velocities,
                        metric_name=m,
                        previous_target_velocity=vel_prof.previous_velocity,
                    )

            # G. Expected vs Actual Trajectory
            exp_actual_rep = None
            if target_project and "progress" in m:
                planned_dur = target_project.get("planned_duration_months")
                age_dur = target_project.get("project_age_months")
                exp_actual_rep = PeerRelativeTrajectoryEngine.evaluate_expected_vs_actual(
                    actual_progress=vals[-1],
                    planned_duration_months=planned_dur,
                    project_age_months=age_dur,
                    metric_name=m,
                )

            m_report = MetricTrajectoryReport(
                metric_name=m,
                coverage=coverage,
                velocity=vel_prof,
                acceleration=acc_prof,
                trend=trend_prof,
                volatility=vol_prof,
                stagnation=stag_rep,
                recovery=rec_rep,
                sudden_change=sudden_rep,
                change_point=cp_rep,
                peer_relative=peer_rel_rep,
                expected_vs_actual=exp_actual_rep,
            )
            metric_reports[m] = m_report

            if stag_rep.stagnation_detected:
                findings.append(
                    f"{m}: Stagnation detected ({stag_rep.duration_months} consecutive months stalled)."
                )
            if acc_prof.is_sustained_deceleration:
                findings.append(f"{m}: Sustained progress deceleration over recent reporting periods.")
            if sudden_rep.sudden_change_detected:
                findings.append(f"{m}: Sudden velocity shock detected ({sudden_rep.change_type}).")

        # 3. Overall Execution Regime
        prog_rep = metric_reports.get("physical_progress_pct")
        latest_prog = prog_vals[-1] if prog_vals else None
        latest_v = prog_rep.velocity.latest_velocity if prog_rep else 0.0
        is_stag = prog_rep.stagnation.stagnation_detected if prog_rep else False
        is_rec = prog_rep.recovery.recovery_detected if prog_rep else False
        is_decel = prog_rep.acceleration.is_sustained_deceleration if prog_rep else False
        is_acc = prog_rep.acceleration.is_accelerating if prog_rep else False
        vol_cat = prog_rep.volatility.stability_category if prog_rep else "STABLE"

        regime = ChangePointAndRegimeEngine.infer_execution_regime(
            physical_progress_pct=latest_prog,
            latest_velocity=latest_v,
            is_stagnant=is_stag,
            is_recovering=is_rec,
            is_sustained_decel=is_decel,
            is_accelerating=is_acc,
            volatility_category=vol_cat,
            dates=dates,
        )

        # 4. Overall Reliability
        overall_reliability = TrajectoryExplainer.evaluate_reliability(coverage)

        # 5. Build Supervisor Evidence Items
        for m, rep in metric_reports.items():
            ev = TrajectoryExplainer.build_supervisor_evidence_item(
                target_project_code=target_project_code,
                metric_report=rep,
                regime=regime,
            )
            evidence_items.append(ev)

        return TrajectoryIntelligenceResult(
            target_project_code=target_project_code,
            cohort_id=cohort_id,
            cohort_size=len(peer_cohort_snapshots) if peer_cohort_snapshots else 0,
            snapshots_analyzed=len(clean_snapshots),
            metrics_evaluated=list(metric_reports.keys()),
            historical_coverage=coverage,
            metric_trajectories=metric_reports,
            execution_regime=regime,
            overall_reliability=overall_reliability,
            findings=findings,
            evidence_items=evidence_items,
            limitations=[],
        )
