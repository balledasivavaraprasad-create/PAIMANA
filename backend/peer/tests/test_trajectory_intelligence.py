"""Unit and Integration Tests for Trajectory Intelligence Subsystem (TI-01 to TI-14).

Tests:
1. Historical Snapshot Temporal Validation (TI-01)
2. Rolling Velocity & Acceleration (TI-02, TI-03)
3. Trend & Volatility Analysis (TI-04, TI-05)
4. Stagnation Detection with Expenditure Divergence (TI-06)
5. Recovery Detection & Post-Stagnation Rebound (TI-07)
6. Sudden Change Detection (TI-08)
7. Change-Point Detection via Binary Segmentation (TI-09)
8. Execution Regime Shift Classification (TI-10)
9. Peer-Relative Trajectory Gap Dynamics (TI-11)
10. Expected vs Actual Trajectory Analysis (TI-12)
11. Trajectory Reliability & Evidence Attribution (TI-13, TI-14)
12. End-to-End Service & ToolRegistry Integration (TI-14)
"""
from __future__ import annotations

import pytest

from peer.trajectory import (
    ChangePointAndRegimeEngine,
    ExecutionRegime,
    PatternDetector,
    PeerRelativeTrajectoryEngine,
    TemporalValidator,
    TrajectoryDirection,
    TrajectoryExplainer,
    TrajectoryIntelligenceService,
    TrajectoryReliability,
    TrendAndVolatilityAnalyzer,
    VelocityCalculator,
)
from peer.service import PeerIntelligenceService
from peer.repository import InMemoryProjectRepository
from peer.tools_adapter import make_peer_tool_definitions


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def stagnant_snapshots():
    """8 monthly snapshots showing early progress followed by 4 months of stagnation with expenditure."""
    return [
        {"report_month": "2025-01", "physical_progress_pct": 10.0, "cumulative_expenditure_cr": 100.0},
        {"report_month": "2025-02", "physical_progress_pct": 15.0, "cumulative_expenditure_cr": 150.0},
        {"report_month": "2025-03", "physical_progress_pct": 19.0, "cumulative_expenditure_cr": 200.0},
        {"report_month": "2025-04", "physical_progress_pct": 21.0, "cumulative_expenditure_cr": 260.0},
        # Stagnation begins: progress stalls near 21-22%, expenditure continues rising
        {"report_month": "2025-05", "physical_progress_pct": 21.2, "cumulative_expenditure_cr": 320.0},
        {"report_month": "2025-06", "physical_progress_pct": 21.3, "cumulative_expenditure_cr": 380.0},
        {"report_month": "2025-07", "physical_progress_pct": 21.5, "cumulative_expenditure_cr": 440.0},
        {"report_month": "2025-08", "physical_progress_pct": 21.6, "cumulative_expenditure_cr": 500.0},
    ]


@pytest.fixture
def steady_growth_snapshots():
    """6 monthly snapshots showing steady, consistent growth."""
    return [
        {"report_month": f"2025-{i:02d}", "physical_progress_pct": float(10.0 + (i * 5.0)), "cumulative_expenditure_cr": float(100.0 + (i * 40.0))}
        for i in range(1, 7)
    ]


# ============================================================================
# 1. Historical Snapshot Temporal Validation (TI-01)
# ============================================================================

def test_temporal_validation_chronology_and_coverage():
    # Out of order with one duplicate
    raw_snapshots = [
        {"report_month": "2025-03", "physical_progress_pct": 20.0},
        {"report_month": "2025-01", "physical_progress_pct": 10.0},
        {"report_month": "2025-02", "physical_progress_pct": 15.0},
        {"report_month": "2025-02", "physical_progress_pct": 15.0},  # duplicate
    ]

    sorted_snaps, cov = TemporalValidator.validate_snapshots(raw_snapshots)
    assert cov.is_chronological is False  # raw was disordered
    assert cov.has_duplicates is True
    assert sorted_snaps[0]["report_month"] == "2025-01"
    assert sorted_snaps[-1]["report_month"] == "2025-03"
    assert cov.available_snapshots == 4
    assert cov.coverage_ratio > 0.0


# ============================================================================
# 2. Rolling Velocity & Acceleration (TI-02, TI-03)
# ============================================================================

def test_velocity_and_sustained_deceleration():
    # Progress: 10, 15, 19, 21, 22 (velocities: +5, +4, +2, +1; accelerations: -1, -2, -1)
    progress_series = [10.0, 15.0, 19.0, 21.0, 22.0]
    vel, acc = VelocityCalculator.compute_velocity_and_acceleration(
        progress_series, metric_name="physical_progress_pct"
    )

    assert vel.latest_velocity == 1.0
    assert vel.previous_velocity == 2.0
    assert vel.rolling_3_velocity < vel.rolling_6_velocity or vel.rolling_3_velocity <= 2.5
    assert acc.current_acceleration < 0
    assert acc.is_sustained_deceleration is True
    assert vel.direction == TrajectoryDirection.DECELERATING


# ============================================================================
# 3. Trend & Volatility Analysis (TI-04, TI-05)
# ============================================================================

def test_trend_and_volatility_steady_progress():
    progress_series = [10.0, 14.0, 18.0, 22.0, 26.0, 30.0]
    trend = TrendAndVolatilityAnalyzer.analyze_trend(
        progress_series, metric_name="physical_progress_pct", direction_rule="HIGHER_IS_BETTER"
    )
    vol = TrendAndVolatilityAnalyzer.analyze_volatility(
        progress_series, metric_name="physical_progress_pct"
    )

    assert trend.trend_direction == "IMPROVING"
    assert trend.slope_ols > 3.5
    assert trend.r_squared >= 0.99
    assert vol.stability_category == "STABLE"
    assert vol.rolling_std < 1.0


# ============================================================================
# 4. Stagnation Detection with Expenditure Divergence (TI-06)
# ============================================================================

def test_stagnation_detection_with_continued_expenditure(stagnant_snapshots):
    prog_vals = [s["physical_progress_pct"] for s in stagnant_snapshots]
    exp_vals = [s["cumulative_expenditure_cr"] for s in stagnant_snapshots]

    stag = PatternDetector.detect_stagnation(
        progress_values=prog_vals,
        expenditure_values=exp_vals,
        metric_name="physical_progress_pct",
    )

    assert stag.stagnation_detected is True
    assert stag.duration_months >= 3
    assert stag.is_stagnation_with_expenditure is True
    assert stag.severity in ("HIGH", "CRITICAL")
    assert stag.expenditure_change > 100.0  # expenditure grew significantly while progress stalled


# ============================================================================
# 5. Recovery Detection & Post-Stagnation Rebound (TI-07)
# ============================================================================

def test_recovery_detection_post_stagnation():
    # Stalled for 3 months, then rebounded: 10, 10.2, 10.4, 10.5, 14.0, 18.0
    series = [10.0, 10.2, 10.4, 10.5, 14.0, 18.0]
    rec = PatternDetector.detect_recovery(series, metric_name="physical_progress_pct")

    assert rec.recovery_detected is True
    assert rec.prior_stagnation_duration_months >= 2
    assert rec.consecutive_positive_periods >= 2
    assert rec.latest_velocity >= 3.0


# ============================================================================
# 6. Sudden Change Detection (TI-08)
# ============================================================================

def test_sudden_change_detection():
    # Steady monthly expenditure (+20 Cr/mo), then sudden massive jump (+120 Cr in one month)
    expenditures = [100.0, 120.0, 140.0, 160.0, 180.0, 300.0]
    sudden = PatternDetector.detect_sudden_change(
        expenditures, metric_name="cumulative_expenditure_cr"
    )

    assert sudden.sudden_change_detected is True
    assert sudden.change_magnitude >= 50.0
    assert sudden.severity in ("MODERATE", "HIGH")


# ============================================================================
# 7. Change-Point Detection via Binary Segmentation (TI-09)
# ============================================================================

def test_change_point_detection():
    # Fast initial growth (+5 pp/mo), then abrupt drop to slow growth (+1 pp/mo)
    # Series: 10, 15, 20, 25, 26, 27, 28, 29
    dates = [f"2025-0{i}" for i in range(1, 9)]
    progress = [10.0, 15.0, 20.0, 25.0, 26.0, 27.0, 28.0, 29.0]

    cp = ChangePointAndRegimeEngine.detect_change_point(
        values=progress, metric_name="physical_progress_pct", dates=dates
    )

    assert cp.change_point_detected is True
    assert cp.pre_change_mean_velocity > 3.0
    assert cp.post_change_mean_velocity <= 1.5
    assert cp.estimated_change_index is not None


# ============================================================================
# 8. Execution Regime Shift Classification (TI-10)
# ============================================================================

def test_execution_regime_shift_inference():
    # Stagnant regime
    reg_stag = ChangePointAndRegimeEngine.infer_execution_regime(
        physical_progress_pct=25.0,
        latest_velocity=0.1,
        is_stagnant=True,
        is_recovering=False,
        is_sustained_decel=False,
        is_accelerating=False,
        volatility_category="STABLE",
    )
    assert reg_stag.current_regime == ExecutionRegime.STAGNATING

    # Decelerating regime
    reg_decel = ChangePointAndRegimeEngine.infer_execution_regime(
        physical_progress_pct=40.0,
        latest_velocity=1.0,
        is_stagnant=False,
        is_recovering=False,
        is_sustained_decel=True,
        is_accelerating=False,
        volatility_category="STABLE",
    )
    assert reg_decel.current_regime == ExecutionRegime.DECELERATING


# ============================================================================
# 9. Peer-Relative Trajectory Gap Dynamics (TI-11)
# ============================================================================

def test_peer_relative_trajectory_comparison():
    target_vel = 1.0  # target progress advancing at 1.0 pp/mo
    peer_velocities = [3.0, 3.5, 4.0, 4.2, 4.5]  # peer median = 4.0 pp/mo

    comp = PeerRelativeTrajectoryEngine.evaluate_peer_relative_trajectory(
        target_velocity=target_vel,
        peer_velocities=peer_velocities,
        metric_name="physical_progress_pct",
        previous_target_velocity=2.0,
        previous_peer_median=3.8,
    )

    assert comp.trajectory_direction == "LAGGING_PEERS"
    assert comp.velocity_gap == -3.0
    assert comp.is_gap_widening is True


# ============================================================================
# 10. Expected vs Actual Trajectory Analysis (TI-12)
# ============================================================================

def test_expected_vs_actual_schedule_evaluation():
    # Target is at month 24 of planned 36 month schedule (66% elapsed time)
    # Expected progress along S-curve is ~73%, but actual progress is only 40%
    exp_rep = PeerRelativeTrajectoryEngine.evaluate_expected_vs_actual(
        actual_progress=40.0,
        planned_duration_months=36.0,
        project_age_months=24.0,
    )

    assert exp_rep.baseline_type == "SCHEDULE"
    assert exp_rep.gap < -15.0
    assert exp_rep.status == "CRITICALLY_BELOW"


# ============================================================================
# 11. Trajectory Reliability & Evidence Attribution (TI-13, TI-14)
# ============================================================================

def test_trajectory_reliability_evaluation():
    # High coverage (8 snapshots, no missing)
    cov_high = TemporalValidator.validate_snapshots([
        {"report_month": f"2025-{i:02d}", "physical_progress_pct": float(i * 5)} for i in range(1, 9)
    ])[1]
    rel_high = TrajectoryExplainer.evaluate_reliability(cov_high)
    assert rel_high == TrajectoryReliability.HIGH

    # Insufficient coverage (1 snapshot)
    cov_single = TemporalValidator.validate_snapshots([
        {"report_month": "2025-01", "physical_progress_pct": 10.0}
    ])[1]
    rel_insuf = TrajectoryExplainer.evaluate_reliability(cov_single)
    assert rel_insuf == TrajectoryReliability.INSUFFICIENT


# ============================================================================
# 12. End-to-End Service & ToolRegistry Integration (TI-14)
# ============================================================================

def test_end_to_end_trajectory_service(stagnant_snapshots):
    service = TrajectoryIntelligenceService()

    # Peer snapshots for comparative trajectory
    peer_snaps = {
        "P-01": [{"report_month": f"2025-{i:02d}", "physical_progress_pct": float(10 + i * 4)} for i in range(1, 9)],
        "P-02": [{"report_month": f"2025-{i:02d}", "physical_progress_pct": float(10 + i * 5)} for i in range(1, 9)],
        "P-03": [{"report_month": f"2025-{i:02d}", "physical_progress_pct": float(10 + i * 4.5)} for i in range(1, 9)],
    }

    target_info = {"project_code": "T-STAG-HIGHWAY", "planned_duration_months": 24.0, "project_age_months": 12.0}

    result = service.analyze_project_trajectory(
        target_project_code="T-STAG-HIGHWAY",
        target_snapshots=stagnant_snapshots,
        peer_cohort_snapshots=peer_snaps,
        target_project=target_info,
    )

    assert result.target_project_code == "T-STAG-HIGHWAY"
    assert result.snapshots_analyzed == 8
    assert result.overall_reliability == TrajectoryReliability.HIGH
    assert result.execution_regime.current_regime == ExecutionRegime.STAGNATING

    # Check evidence items conforming to CONTEXTUALIZES semantics
    assert len(result.evidence_items) > 0
    prog_ev = next(ev for ev in result.evidence_items if ev["metric_name"] == "physical_progress_pct")
    assert prog_ev["stagnation_detected"] is True
    assert prog_ev["relation"] == "CONTEXTUALIZES"
    assert "Stagnation detected" in prog_ev["statement"]


def test_tool_registry_trajectory_intelligence_execution(stagnant_snapshots):
    repo = InMemoryProjectRepository()
    target = {
        "project_code": "T-TRAJ-TOOL",
        "project_name": "Tollway Package C",
        "sector": "Roads & Highways",
        "original_cost_cr": 1000.0,
        "revised_cost_cr": 1200.0,
        "physical_progress_pct": 21.6,
        "planned_duration_months": 36.0,
        "project_age_months": 18.0,
    }
    repo.add_project(target)
    for s in stagnant_snapshots:
        repo.add_snapshot("T-TRAJ-TOOL", s)

    intel_service = PeerIntelligenceService(repository=repo)
    tools = make_peer_tool_definitions(intel_service)

    traj_tool = next((t for t in tools if t.name == "analyze_trajectory_intelligence"), None)
    assert traj_tool is not None

    tool_res = traj_tool.execute(p=target)
    assert tool_res.status == "SUCCESS"
    assert "execution_regime" in tool_res.data
    assert len(tool_res.evidence_items) > 0
    assert "Trajectory Intelligence" in tool_res.summary
