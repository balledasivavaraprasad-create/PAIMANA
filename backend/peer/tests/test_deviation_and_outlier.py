"""Unit and Integration Tests for Deviation & Outlier Detection Subsystem (DO-01 to DO-12).

Tests:
1. Absolute and Relative Deviation Measurement (DO-01)
2. Robust Modified Z-Score & Zero-MAD Handling (DO-02)
3. Ordinary Z-Score Detector (DO-02)
4. IQR Tukey Fences & Outlier Screening (DO-03)
5. Direction-Aware Percentile Anomaly Detection (DO-04)
6. Multi-Method Ensemble & Agreement Ratio (DO-05)
7. Context-Aware Detection & Stage Adaptation (DO-06)
8. Multivariate Mahalanobis Anomaly Detection (DO-07)
9. Statistical Unusualness vs Practical Significance (DO-08)
10. Temporal Velocity, Acceleration & Sustained Anomalies (DO-10)
11. Anomaly Calibration & Error Rate Evaluation (DO-12)
12. End-to-End Service & ToolRegistry Integration (DO-12)
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from peer.anomaly import (
    AnomalyCalibrator,
    AnomalyMethod,
    AnomalySeverity,
    ContextualDetector,
    DeviationCalculator,
    DeviationDirection,
    DeviationAndOutlierService,
    EnsembleDetector,
    IQRDetector,
    MethodStatus,
    ModifiedZScoreDetector,
    MultivariateDetector,
    OrdinaryZScoreDetector,
    PercentileDetector,
    PracticalSignificance,
    SeverityEvaluator,
    TemporalAnomalyDetector,
)
from peer.service import PeerIntelligenceService
from peer.repository import InMemoryProjectRepository
from peer.tools_adapter import make_peer_tool_definitions


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def highway_cohort():
    """12 representative highway projects with diverse performance."""
    return [
        {
            "project_code": f"HW-{i:02d}",
            "project_name": f"Highway Package {i}",
            "sector": "Roads & Highways",
            "original_cost_cr": 1000.0,
            "revised_cost_cr": 1000.0 + (i * 15.0),  # 1.5% to 18% overrun
            "cumulative_expenditure_cr": 400.0 + (i * 20.0),
            "physical_progress_pct": 30.0 + (i * 3.0),
            "planned_duration_months": 36.0,
            "project_age_months": 24.0,
            "schedule_slippage_months": float(i),
            "progress_expenditure_gap_pct": float(5.0 + (i * 0.5)),
        }
        for i in range(1, 13)
    ]


# ============================================================================
# 1. Absolute and Relative Deviation Tests (DO-01)
# ============================================================================

def test_deviation_calculator_standard_and_near_zero():
    # Standard deviation
    res1 = DeviationCalculator.compute_deviation(
        target_value=24.0,
        peer_reference=8.0,
        metric_name="cost_overrun_pct",
        direction_rule="HIGHER_IS_WORSE",
    )
    assert res1.absolute_deviation == 16.0
    assert res1.relative_deviation_pct == 200.0
    assert res1.deviation_direction == DeviationDirection.ABOVE_PEERS
    assert res1.is_unit_percentage_points is True
    assert not res1.is_near_zero_reference

    # Below peers
    res2 = DeviationCalculator.compute_deviation(
        target_value=4.0,
        peer_reference=8.0,
        metric_name="cost_overrun_pct",
        direction_rule="HIGHER_IS_WORSE",
    )
    assert res2.absolute_deviation == -4.0
    assert res2.relative_deviation_pct == -50.0
    assert res2.deviation_direction == DeviationDirection.BELOW_PEERS

    # Near-zero peer reference: relative deviation must be None (suppressed)
    res_zero = DeviationCalculator.compute_deviation(
        target_value=5.0,
        peer_reference=0.0,
        metric_name="schedule_slippage_months",
        direction_rule="HIGHER_IS_WORSE",
        near_zero_epsilon=1e-4,
    )
    assert res_zero.absolute_deviation == 5.0
    assert res_zero.relative_deviation_pct is None
    assert res_zero.is_near_zero_reference is True


# ============================================================================
# 2. Robust Modified Z-Score & Zero-MAD Handling (DO-02)
# ============================================================================

def test_modified_z_score_detector():
    cohort = [10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0]

    # Normal target
    res_norm = ModifiedZScoreDetector.evaluate(target_value=12.0, cohort_values=cohort)
    assert not res_norm.flagged
    assert res_norm.status == MethodStatus.NOT_FLAGGED
    assert res_norm.score is not None and abs(res_norm.score) < 3.5

    # Extreme target
    res_ext = ModifiedZScoreDetector.evaluate(target_value=35.0, cohort_values=cohort)
    assert res_ext.flagged
    assert res_ext.status == MethodStatus.FLAGGED
    assert res_ext.score is not None and res_ext.score > 3.5


def test_modified_z_score_zero_mad_handling():
    # Degenerate cohort: all peers identical
    cohort_identical = [15.0, 15.0, 15.0, 15.0, 15.0]

    # Target also identical -> NOT_FLAGGED with score 0.0
    res_same = ModifiedZScoreDetector.evaluate(target_value=15.0, cohort_values=cohort_identical)
    assert not res_same.flagged
    assert res_same.status == MethodStatus.NOT_FLAGGED
    assert res_same.score == 0.0

    # Target distinct -> INSUFFICIENT_DISPERSION without arbitrary unit-insensitive fallbacks
    res_diff = ModifiedZScoreDetector.evaluate(target_value=25.0, cohort_values=cohort_identical)
    assert not res_diff.flagged
    assert res_diff.status == MethodStatus.INSUFFICIENT_DISPERSION
    assert res_diff.score is None
    assert "Zero MAD" in res_diff.reason


# ============================================================================
# 3. Ordinary Z-Score Detector (DO-02)
# ============================================================================

def test_ordinary_z_score_detector():
    cohort = [10.0, 12.0, 14.0, 16.0, 18.0]

    res = OrdinaryZScoreDetector.evaluate(target_value=28.0, cohort_values=cohort, threshold=2.5)
    assert res.flagged
    assert res.score is not None and res.score >= 2.5
    assert res.status == MethodStatus.FLAGGED

    # Zero standard deviation
    res_zero_std = OrdinaryZScoreDetector.evaluate(target_value=20.0, cohort_values=[10.0, 10.0, 10.0])
    assert res_zero_std.status == MethodStatus.INSUFFICIENT_DISPERSION


# ============================================================================
# 4. IQR Tukey Fences & Outlier Screening (DO-03)
# ============================================================================

def test_iqr_detector_tukey_fences():
    cohort = [10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0]
    # Q25 = 12.5, Q75 = 19.5, IQR = 7.0
    # Upper fence (1.5x) = 19.5 + 10.5 = 30.0

    # Mild target within fence
    res_in = IQRDetector.evaluate(target_value=25.0, cohort_values=cohort, multiplier=1.5)
    assert not res_in.flagged

    # Outlier above fence
    res_out = IQRDetector.evaluate(target_value=35.0, cohort_values=cohort, multiplier=1.5)
    assert res_out.flagged
    assert res_out.status == MethodStatus.FLAGGED
    assert "above upper fence" in res_out.reason


# ============================================================================
# 5. Direction-Aware Percentile Anomaly Detection (DO-04)
# ============================================================================

def test_percentile_detector_direction_awareness():
    cohort = list(range(10, 30))  # 20 peers

    # HIGHER_IS_WORSE (e.g. cost overrun): high percentile is adverse anomaly
    res_high_cost = PercentileDetector.evaluate(
        target_value=35.0, cohort_values=cohort, direction_rule="HIGHER_IS_WORSE", upper_threshold=90.0
    )
    assert res_high_cost.flagged
    assert res_high_cost.score == 100.0

    # Low cost overrun is favorable, NOT an adverse anomaly
    res_low_cost = PercentileDetector.evaluate(
        target_value=5.0, cohort_values=cohort, direction_rule="HIGHER_IS_WORSE", lower_threshold=10.0
    )
    assert not res_low_cost.flagged
    assert "favorable lower tail" in res_low_cost.reason

    # HIGHER_IS_BETTER (e.g. physical progress): low percentile is adverse anomaly
    res_low_prog = PercentileDetector.evaluate(
        target_value=5.0, cohort_values=cohort, direction_rule="HIGHER_IS_BETTER", lower_threshold=10.0
    )
    assert res_low_prog.flagged
    assert "critical adverse lower tail" in res_low_prog.reason


# ============================================================================
# 6. Multi-Method Ensemble & Agreement Ratio (DO-05)
# ============================================================================

def test_ensemble_detector_consensus():
    cohort = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0]

    # Extreme target: should achieve high consensus agreement
    res, agree, consensus, stat_status = EnsembleDetector.evaluate_univariate_ensemble(
        target_value=35.0, cohort_values=cohort, direction_rule="HIGHER_IS_WORSE"
    )
    assert agree >= 0.75
    assert consensus is True
    assert stat_status == "STATISTICAL_OUTLIER"
    assert len(res) == 4

    # Normal target: no methods flag
    res_norm, agree_norm, consensus_norm, stat_status_norm = EnsembleDetector.evaluate_univariate_ensemble(
        target_value=13.0, cohort_values=cohort, direction_rule="HIGHER_IS_WORSE"
    )
    assert agree_norm == 0.0
    assert consensus_norm is False
    assert stat_status_norm == "NORMAL"


# ============================================================================
# 7. Context-Aware Detection & Stage Adaptation (DO-06)
# ============================================================================

def test_contextual_threshold_adaptation():
    # Early stage project (<25% progress)
    p_early = {"project_code": "EARLY-1", "sector": "Roads & Highways", "physical_progress_pct": 12.0}
    prof_early = ContextualDetector.get_contextual_profile("schedule_slippage_months", p_early)
    assert prof_early.stage_bracket == "EARLY"
    # Delay tolerance widened in early stage to accommodate initial mobilization
    assert prof_early.modified_z_threshold > 3.5

    # Late stage project (>75% progress)
    p_late = {"project_code": "LATE-1", "sector": "Roads & Highways", "physical_progress_pct": 85.0}
    prof_late = ContextualDetector.get_contextual_profile("cost_overrun_pct", p_late)
    assert prof_late.stage_bracket == "LATE"
    # Stricter thresholds for late stage
    assert prof_late.modified_z_threshold <= 3.0


# ============================================================================
# 8. Multivariate Mahalanobis Anomaly Detection (DO-07)
# ============================================================================

def test_multivariate_detector_mahalanobis(highway_cohort):
    # Target project with an extreme discordant combination across all 4 metrics
    extreme_target = {
        "project_code": "ANOM-MULTI",
        "cost_overrun_pct": 45.0,
        "schedule_slippage_months": 36.0,
        "physical_progress_pct": 15.0,
        "progress_expenditure_gap_pct": 35.0,
    }

    rep = MultivariateDetector.evaluate_multivariate(
        target_project=extreme_target,
        cohort_records=highway_cohort,
    )

    assert rep.method == AnomalyMethod.MAHALANOBIS
    assert rep.anomaly_detected is True
    assert rep.distance_or_score > rep.threshold
    assert len(rep.contributing_metrics) > 0
    assert rep.severity in (AnomalySeverity.HIGH, AnomalySeverity.CRITICAL)


def test_multivariate_small_sample_fallback():
    small_cohort = [
        {"cost_overrun_pct": 10.0, "schedule_slippage_months": 5.0, "physical_progress_pct": 40.0},
        {"cost_overrun_pct": 12.0, "schedule_slippage_months": 6.0, "physical_progress_pct": 42.0},
    ]
    target = {"cost_overrun_pct": 11.0, "schedule_slippage_months": 5.5, "physical_progress_pct": 41.0}

    rep = MultivariateDetector.evaluate_multivariate(
        target_project=target,
        cohort_records=small_cohort,
        metrics=["cost_overrun_pct", "schedule_slippage_months", "physical_progress_pct"],
    )
    # n=2 <= p=3 + 1 -> fallback to composite distance
    assert rep.method == AnomalyMethod.MULTIVARIATE_COMPOSITE
    assert any("too small" in w for w in rep.limitations)


# ============================================================================
# 9. Statistical Unusualness vs Practical Significance (DO-08)
# ============================================================================

def test_severity_evaluator_statistical_vs_practical():
    # Case A: Statistical outlier with massive financial impact -> CRITICAL
    dev_crit = DeviationCalculator.compute_deviation(
        target_value=40.0, peer_reference=8.0, metric_name="cost_overrun_pct"
    )
    target_big = {"original_cost_cr": 2000.0}
    prac_sig, sev, conf = SeverityEvaluator.evaluate_severity(
        metric_name="cost_overrun_pct",
        deviation=dev_crit,
        statistical_status="STATISTICAL_OUTLIER",
        agreement_ratio=1.0,
        target_project=target_big,
        sample_size=20,
    )
    assert prac_sig == PracticalSignificance.CRITICAL
    assert sev == AnomalySeverity.CRITICAL
    assert conf == "HIGH"

    # Case B: Statistically unusual in a very narrow peer distribution, but tiny impact (1 month delay) -> LOW
    dev_minor = DeviationCalculator.compute_deviation(
        target_value=2.0, peer_reference=1.0, metric_name="schedule_slippage_months"
    )
    prac_sig2, sev2, _ = SeverityEvaluator.evaluate_severity(
        metric_name="schedule_slippage_months",
        deviation=dev_minor,
        statistical_status="STATISTICAL_OUTLIER",
        agreement_ratio=0.75,
        target_project={},
        sample_size=20,
    )
    assert prac_sig2 in (PracticalSignificance.LOW, PracticalSignificance.NEGLIGIBLE)
    assert sev2 == AnomalySeverity.LOW


# ============================================================================
# 10. Temporal Velocity, Acceleration & Sustained Anomalies (DO-10)
# ============================================================================

def test_temporal_anomaly_detector_accelerating_and_sustained():
    # Deterioration history: 5, 8, 14, 25 (expanding gaps)
    history = [
        {"report_month": "2025-01", "absolute_deviation": 5.0},
        {"report_month": "2025-03", "absolute_deviation": 8.0},    # v = +3
        {"report_month": "2025-05", "absolute_deviation": 14.0},   # v = +6, a = +3
        {"report_month": "2025-07", "absolute_deviation": 25.0},   # v = +11, a = +5
    ]

    rep = TemporalAnomalyDetector.evaluate_temporal_deviation(
        target_project_code="T-TEMP",
        metric_name="cost_overrun_pct",
        historical_deviations=history,
        anomaly_threshold=7.0,
    )

    assert rep.is_accelerating is True
    assert rep.deviation_velocity > 0
    assert rep.deviation_acceleration > 0
    assert rep.is_sustained is True  # 8, 14, 25 >= 7.0 (3 consecutive periods)
    assert rep.consecutive_anomalous_snapshots == 3
    assert "Accelerating deviation" in rep.trend_description


# ============================================================================
# 11. Anomaly Calibration & Error Rate Evaluation (DO-12)
# ============================================================================

def test_anomaly_calibrator_metrics():
    predictions = [True, True, False, False, True]
    ground_truth = [True, False, False, True, True]

    metrics = AnomalyCalibrator.evaluate_predictions(predictions, ground_truth)
    assert metrics.total_cases == 5
    assert metrics.true_positives == 2
    assert metrics.false_positives == 1
    assert metrics.true_negatives == 1
    assert metrics.false_negatives == 1
    assert round(metrics.precision, 2) == 0.67
    assert round(metrics.recall, 2) == 0.67


# ============================================================================
# 12. End-to-End Service & ToolRegistry Integration (DO-12)
# ============================================================================

def test_end_to_end_anomaly_service(highway_cohort):
    service = DeviationAndOutlierService()

    target = {
        "project_code": "T-TARGET-HIGHWAY",
        "project_name": "Target Expressway Section",
        "sector": "Roads & Highways",
        "original_cost_cr": 1200.0,
        "revised_cost_cr": 1600.0,  # 33.3% overrun (well above peer max of 18%)
        "physical_progress_pct": 25.0,  # below peers
        "schedule_slippage_months": 20.0,  # above peers
        "progress_expenditure_gap_pct": 25.0,
    }

    result = service.detect_anomalies(
        target_project=target,
        cohort=highway_cohort,
        metrics=["cost_overrun_pct", "schedule_slippage_months", "physical_progress_pct"],
    )

    assert result.target_project_code == "T-TARGET-HIGHWAY"
    assert result.cohort_size == 12
    assert result.overall_is_outlier is True
    assert result.overall_severity in (AnomalySeverity.HIGH, AnomalySeverity.CRITICAL)

    # Check evidence items conforming to CONTEXTUALIZES semantics
    assert len(result.evidence_items) > 0
    cost_ev = next(ev for ev in result.evidence_items if ev["metric_name"] == "cost_overrun_pct")
    assert cost_ev["is_peer_outlier"] is True
    assert cost_ev["peer_relative_risk_level"] == "SIGNIFICANTLY_ABOVE_PEERS"
    assert cost_ev["relation"] == "CONTEXTUALIZES"
    assert "STATISTICAL ANOMALY" in cost_ev["statement"]


def test_tool_registry_detect_peer_anomalies_execution(highway_cohort):
    repo = InMemoryProjectRepository()
    for p in highway_cohort:
        repo.add_project(p)

    target = {
        "project_code": "T-ANOM-TOOL",
        "project_name": "Anomalous Tollway",
        "sector": "Roads & Highways",
        "original_cost_cr": 1000.0,
        "revised_cost_cr": 1400.0,
        "physical_progress_pct": 35.0,
        "schedule_slippage_months": 18.0,
    }
    repo.add_project(target)

    intel_service = PeerIntelligenceService(repository=repo)
    tools = make_peer_tool_definitions(intel_service)

    anom_tool = next((t for t in tools if t.name == "detect_peer_anomalies"), None)
    assert anom_tool is not None

    tool_res = anom_tool.execute(p=target)
    assert tool_res.status == "SUCCESS"
    assert "univariate_anomalies" in tool_res.data
    assert len(tool_res.evidence_items) > 0
    assert "Overall Severity" in tool_res.summary
