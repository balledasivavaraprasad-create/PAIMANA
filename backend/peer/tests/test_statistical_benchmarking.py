"""Unit and Integration Tests for Statistical Benchmarking Subsystem (SB-01 to SB-12).

Tests:
1. Metric Registry & Specification
2. Metric Normalization & Derivations
3. Robust Central Tendency & Dispersion
4. Small-Sample Guardrails & Operational Statuses
5. Bootstrap Resampling & Analytical Confidence Intervals
6. Distribution-Shape, Skewness & Tail Classification
7. Distribution-Shift & Temporal Drift Detection (PSI, KS-test)
8. Leave-One-Out Sensitivity Analysis
9. Cryptographic Reproducibility & Audit Trail
10. End-to-End Master Service & ToolRegistry Integration
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from peer.statistical import (
    BootstrapEngine,
    DistributionAnalyzer,
    DistributionShape,
    DistributionShiftDetector,
    MetricDefinition,
    MetricDirection,
    MetricNormalizer,
    MetricRegistry,
    RobustStatisticsEngine,
    SensitivityEngine,
    SmallSampleEvaluator,
    SmallSampleStatus,
    StatisticalBenchmarkingService,
    AuditTrailEngine,
)
from peer.service import PeerIntelligenceService
from peer.repository import InMemoryProjectRepository
from peer.tools_adapter import make_peer_tool_definitions


# ============================================================================
# Test Fixtures & Data
# ============================================================================

@pytest.fixture
def registry():
    return MetricRegistry()


@pytest.fixture
def normalizer(registry):
    return MetricNormalizer(registry)


@pytest.fixture
def sample_projects():
    """10 representative highway projects with diverse metrics."""
    return [
        {
            "project_code": f"P-{i:02d}",
            "project_name": f"Highway Section {i}",
            "sector": "Roads & Highways",
            "original_cost_cr": 1000.0,
            "revised_cost_cr": 1000.0 + (i * 20.0),  # 0% to 18% overrun
            "cumulative_expenditure_cr": 400.0 + (i * 30.0),
            "physical_progress_pct": 35.0 + (i * 4.0),
            "planned_duration_months": 36.0,
            "project_age_months": 24.0,
            "schedule_slippage_months": float(i),
        }
        for i in range(1, 11)
    ]


# ============================================================================
# 1. Metric Registry Tests
# ============================================================================

def test_metric_registry_standard_definitions(registry):
    metrics = registry.list_metrics()
    assert len(metrics) >= 6
    metric_ids = {m.metric_id for m in metrics}
    assert "cost_overrun_pct" in metric_ids
    assert "time_slippage_months" in metric_ids
    assert "physical_progress_pct" in metric_ids
    assert "expenditure_pct" in metric_ids
    assert "progress_expenditure_gap_pct" in metric_ids
    assert "progress_velocity_pct_per_month" in metric_ids

    cost_m = registry.get_metric("cost_overrun_pct")
    assert cost_m.direction == MetricDirection.HIGHER_IS_WORSE
    assert cost_m.allowed_range == (-50.0, 500.0)

    prog_m = registry.get_metric("physical_progress_pct")
    assert prog_m.direction == MetricDirection.HIGHER_IS_BETTER
    assert prog_m.allowed_range == (0.0, 100.0)


def test_metric_registry_custom_registration(registry):
    custom = MetricDefinition(
        metric_id="contractor_attrition_rate",
        unit="ratio",
        direction=MetricDirection.HIGHER_IS_WORSE,
        description="Contractor turnover frequency per quarter",
        source_fields=["contractor_attrition"],
        allowed_range=(0.0, 1.0),
    )
    registry.register_metric(custom)
    retrieved = registry.get_metric("contractor_attrition_rate")
    assert retrieved is not None
    assert retrieved.unit == "ratio"


# ============================================================================
# 2. Metric Normalization & Derivations
# ============================================================================

def test_normalization_direct_and_derived(normalizer):
    # Direct field
    p1 = {"cost_overrun_pct": 14.5}
    assert normalizer.extract_metric(p1, "cost_overrun_pct") == 14.5

    # Derived from original and revised cost
    p2 = {"original_cost_cr": 1000.0, "revised_cost_cr": 1250.0}
    assert normalizer.extract_metric(p2, "cost_overrun_pct") == 25.0

    # Derived expenditure pct
    p3 = {"original_cost_cr": 500.0, "cumulative_expenditure_cr": 250.0}
    assert normalizer.extract_metric(p3, "expenditure_pct") == 50.0

    # Derived progress expenditure gap
    p4 = {
        "original_cost_cr": 500.0,
        "cumulative_expenditure_cr": 350.0,  # 70%
        "physical_progress_pct": 40.0,
    }
    assert normalizer.extract_metric(p4, "progress_expenditure_gap_pct") == 30.0

    # Derived progress velocity
    p5 = {"physical_progress_pct": 48.0, "project_age_months": 24.0}
    assert normalizer.extract_metric(p5, "progress_velocity_pct_per_month") == 2.0


def test_normalization_bounds_and_invalid_data(normalizer):
    # Out of allowed range (-50 to 500 for cost overrun)
    p_invalid = {"cost_overrun_pct": 9999.0}
    assert normalizer.extract_metric(p_invalid, "cost_overrun_pct") is None

    # NaN / Inf rejection
    p_nan = {"cost_overrun_pct": float("nan")}
    assert normalizer.extract_metric(p_nan, "cost_overrun_pct") is None

    p_inf = {"cost_overrun_pct": float("inf")}
    assert normalizer.extract_metric(p_inf, "cost_overrun_pct") is None


def test_normalization_cohort_series_extraction(normalizer, sample_projects):
    vals, stats = normalizer.extract_cohort_series(sample_projects, "cost_overrun_pct")
    assert stats["total_candidates"] == 10
    assert stats["valid_count"] == 10
    assert stats["missing_count"] == 0
    assert len(vals) == 10
    # Overruns: 2%, 4%, 6%, 8%, 10%, 12%, 14%, 16%, 18%, 20%
    assert vals[0] == 2.0
    assert vals[-1] == 20.0


# ============================================================================
# 3. Robust Statistics Engine Tests
# ============================================================================

def test_robust_central_tendency_outlier_resistance():
    # Symmetric data with one massive outlier: 10, 11, 12, 12, 13, 14, 1000
    values = [10.0, 11.0, 12.0, 12.0, 13.0, 14.0, 1000.0]
    ct = RobustStatisticsEngine.compute_central_tendency(values, alpha=0.14)

    assert ct["median"] == 12.0
    # Mean is distorted by 1000
    assert ct["mean"] > 100.0
    # Trimmed mean removes 1000 and remains close to median
    assert ct["trimmed_mean"] < 20.0


def test_robust_dispersion_estimators():
    # Normal-like sample
    values = [10.0, 12.0, 14.0, 16.0, 18.0]
    disp = RobustStatisticsEngine.compute_dispersion(values)

    assert disp["std"] > 0
    assert disp["mad"] > 0
    assert disp["iqr"] == 4.0
    assert disp["cv"] > 0


def test_percentile_ranking_and_banding():
    cohort_vals = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0]

    # Target at median (11.0)
    p_med = RobustStatisticsEngine.evaluate_target_percentile(
        target_value=11.0,
        cohort_values=cohort_vals,
        metric_name="cost_overrun_pct",
        direction=MetricDirection.HIGHER_IS_WORSE,
    )
    assert p_med.percentile_rank == 50.0
    assert p_med.interpretation == "TYPICAL_FOR_PEERS"
    assert p_med.peers_below == 5
    assert p_med.peers_above == 5

    # Target with extreme overrun (25.0) -> above all peers
    p_high = RobustStatisticsEngine.evaluate_target_percentile(
        target_value=25.0,
        cohort_values=cohort_vals,
        metric_name="cost_overrun_pct",
        direction=MetricDirection.HIGHER_IS_WORSE,
    )
    assert p_high.percentile_rank == 100.0
    assert p_high.interpretation == "SIGNIFICANTLY_ABOVE"
    assert p_high.peers_below == 10
    assert p_high.peers_above == 0

    # Target with low overrun (1.0) -> below all peers
    p_low = RobustStatisticsEngine.evaluate_target_percentile(
        target_value=1.0,
        cohort_values=cohort_vals,
        metric_name="cost_overrun_pct",
        direction=MetricDirection.HIGHER_IS_WORSE,
    )
    assert p_low.percentile_rank == 0.0
    assert p_low.interpretation == "SIGNIFICANTLY_BELOW"


# ============================================================================
# 4. Small-Sample Guardrails Tests
# ============================================================================

def test_small_sample_evaluator_statuses():
    # n <= 2: INSUFFICIENT
    status, n, warnings = SmallSampleEvaluator.evaluate_sample_size([5.0, 6.0])
    assert status == SmallSampleStatus.INSUFFICIENT
    assert not SmallSampleEvaluator.can_compute_benchmarks(status)
    assert len(warnings) > 0

    # n in (3, 4): HIGHLY_LIMITED
    status, n, warnings = SmallSampleEvaluator.evaluate_sample_size([5.0, 6.0, 7.0])
    assert status == SmallSampleStatus.HIGHLY_LIMITED
    assert SmallSampleEvaluator.can_compute_benchmarks(status)
    assert not SmallSampleEvaluator.can_compute_bootstrap(status)
    assert not SmallSampleEvaluator.can_fit_distribution_shape(status)

    # n in (5..9): CAUTIOUS_EXPLORATORY
    status, n, warnings = SmallSampleEvaluator.evaluate_sample_size([1.0, 2.0, 3.0, 4.0, 5.0])
    assert status == SmallSampleStatus.CAUTIOUS_EXPLORATORY
    assert SmallSampleEvaluator.can_compute_bootstrap(status)

    # n >= 20: SUBSTANTIAL
    vals = list(range(25))
    status, n, warnings = SmallSampleEvaluator.evaluate_sample_size(vals)
    assert status == SmallSampleStatus.SUBSTANTIAL
    assert len(warnings) == 0


def test_small_sample_degenerate_zero_variance():
    vals = [10.0, 10.0, 10.0, 10.0]
    status, n, warnings = SmallSampleEvaluator.evaluate_sample_size(vals)
    assert any("zero dispersion" in w for w in warnings)


# ============================================================================
# 5. Bootstrap Resampling & Analytical Confidence Intervals
# ============================================================================

def test_bootstrap_median_confidence_interval():
    np.random.seed(42)
    # Generate 30 values from lognormal (skewed)
    values = list(np.random.lognormal(mean=2.0, sigma=0.5, size=30))
    summary = BootstrapEngine.compute_bootstrap_interval(
        values=values,
        statistic="median",
        resample_count=1000,
        confidence_level=0.95,
        random_seed=42,
    )

    ci = summary.confidence_interval
    assert ci.lower_bound <= ci.point_estimate <= ci.upper_bound
    assert ci.method == "BOOTSTRAP_PERCENTILE"
    assert summary.resample_count == 1000
    assert summary.bootstrap_se > 0


def test_analytical_mean_ci():
    values = [10.0, 12.0, 14.0, 16.0, 18.0, 20.0]
    ci = BootstrapEngine.compute_analytical_mean_ci(values, confidence_level=0.95)
    assert ci.statistic == "mean"
    assert ci.method == "T_DISTRIBUTION"
    assert ci.lower_bound < ci.point_estimate < ci.upper_bound


# ============================================================================
# 6. Distribution Shape & Tail Analysis
# ============================================================================

def test_distribution_analyzer_skewed_and_symmetric():
    # Heavily right-skewed data
    right_skew = [1.0, 2.0, 2.1, 2.2, 2.5, 3.0, 3.5, 4.0, 15.0, 30.0]
    skew, kurt, shape, _ = DistributionAnalyzer.analyze_distribution(right_skew)
    assert skew > 0.75
    assert shape == DistributionShape.RIGHT_SKEWED

    # Symmetric data
    symmetric = [10.0, 12.0, 14.0, 15.0, 16.0, 18.0, 20.0]
    skew_s, kurt_s, shape_s, _ = DistributionAnalyzer.analyze_distribution(symmetric)
    assert abs(skew_s) < 0.5
    assert shape_s == DistributionShape.APPROXIMATELY_SYMMETRIC


# ============================================================================
# 7. Distribution Shift & Drift Detection
# ============================================================================

def test_distribution_shift_stable_vs_shifted():
    # Stable: two samples from identical distribution
    np.random.seed(42)
    ref = list(np.random.normal(loc=10.0, scale=2.0, size=50))
    curr_stable = list(np.random.normal(loc=10.1, scale=2.0, size=50))

    rep_stable = DistributionShiftDetector.evaluate_shift(
        current_values=curr_stable,
        reference_values=ref,
        metric_name="cost_overrun_pct",
    )
    assert not rep_stable.shift_detected
    assert rep_stable.shift_severity == "NONE"

    # Shifted: current cohort exhibits significant upward cost escalations
    curr_shifted = list(np.random.normal(loc=25.0, scale=4.0, size=50))
    rep_shifted = DistributionShiftDetector.evaluate_shift(
        current_values=curr_shifted,
        reference_values=ref,
        metric_name="cost_overrun_pct",
    )
    assert rep_shifted.shift_detected
    assert rep_shifted.shift_severity in ("MODERATE", "SEVERE")
    assert rep_shifted.psi_score > 0.10


# ============================================================================
# 8. Leave-One-Out Sensitivity Analysis
# ============================================================================

def test_sensitivity_engine_influential_peer():
    # Peer P-99 is an extreme outlier
    pids = [f"P-{i}" for i in range(1, 10)] + ["P-99"]
    values = [10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 150.0]

    rep = SensitivityEngine.evaluate_sensitivity(
        project_ids=pids,
        values=values,
        metric_name="cost_overrun_pct",
        relative_threshold=0.05,
    )
    assert rep.sensitivity_level in ("LOW", "MEDIUM", "HIGH")
    assert rep.base_median > 0
    assert rep.leave_one_out_min <= rep.base_median <= rep.leave_one_out_max


# ============================================================================
# 9. Reproducibility & Audit Trail
# ============================================================================

def test_audit_trail_reproducibility():
    checksum1 = AuditTrailEngine.generate_input_checksum(
        target_project_code="T-100",
        peer_codes=["P-1", "P-2", "P-3"],
        metric_names=["cost_overrun_pct"],
        random_seed=42,
    )
    checksum2 = AuditTrailEngine.generate_input_checksum(
        target_project_code="T-100",
        peer_codes=["P-3", "P-1", "P-2"],  # out of order
        metric_names=["cost_overrun_pct"],
        random_seed=42,
    )
    assert checksum1 == checksum2

    meta = AuditTrailEngine.build_audit_metadata(
        target_project_code="T-100",
        peer_codes=["P-1", "P-2"],
        metric_names=["cost_overrun_pct"],
        random_seed=42,
        resample_count=2000,
        start_time=1000.0,
    )
    assert meta["engine_version"] == "1.0.0"
    assert meta["random_seed"] == 42
    assert "input_checksum" in meta


# ============================================================================
# 10. End-to-End Master Service & ToolRegistry Integration
# ============================================================================

def test_end_to_end_statistical_benchmarking_service(sample_projects):
    service = StatisticalBenchmarkingService()
    target = {
        "project_code": "TARGET-01",
        "project_name": "Target Corridor Expressway",
        "sector": "Roads & Highways",
        "original_cost_cr": 1000.0,
        "revised_cost_cr": 1300.0,  # 30% overrun (higher than all peers)
        "cumulative_expenditure_cr": 800.0,
        "physical_progress_pct": 40.0,
        "schedule_slippage_months": 15.0,
        "project_age_months": 24.0,
    }

    result = service.benchmark_cohort(
        target_project=target,
        cohort=sample_projects,
        metrics=["cost_overrun_pct", "time_slippage_months", "physical_progress_pct"],
        random_seed=42,
        resample_count=1000,
    )

    assert result.target_project_code == "TARGET-01"
    assert result.cohort_size == 10
    assert len(result.benchmarks) == 3

    # Cost overrun checks
    cost_detail = result.benchmarks["cost_overrun_pct"]
    assert cost_detail.count == 10
    assert cost_detail.median > 0
    assert cost_detail.target_percentile is not None
    assert cost_detail.target_percentile.percentile_rank == 100.0
    assert cost_detail.target_percentile.interpretation == "SIGNIFICANTLY_ABOVE"
    assert cost_detail.bootstrap is not None
    assert cost_detail.bootstrap.confidence_interval.lower_bound <= cost_detail.median <= cost_detail.bootstrap.confidence_interval.upper_bound

    # Evidence items check
    assert len(result.evidence_items) == 3
    cost_ev = next(ev for ev in result.evidence_items if ev["metric_name"] == "cost_overrun_pct")
    assert cost_ev["is_peer_outlier"] is True
    assert cost_ev["peer_relative_risk_level"] == "SIGNIFICANTLY_ABOVE_PEERS"

    # Audit metadata check
    assert "input_checksum" in result.audit_metadata
    assert result.audit_metadata["random_seed"] == 42


def test_tool_registry_statistical_benchmark_execution(sample_projects):
    repo = InMemoryProjectRepository()
    for p in sample_projects:
        repo.add_project(p)

    target = {
        "project_code": "T-TEST",
        "project_name": "Target Bypass",
        "sector": "Roads & Highways",
        "original_cost_cr": 1000.0,
        "revised_cost_cr": 1100.0,
        "physical_progress_pct": 50.0,
        "cumulative_expenditure_cr": 550.0,
        "schedule_slippage_months": 2.0,
    }
    repo.add_project(target)

    intel_service = PeerIntelligenceService(repository=repo)
    tools = make_peer_tool_definitions(intel_service)

    stat_tool = next((t for t in tools if t.name == "statistical_benchmark"), None)
    assert stat_tool is not None

    tool_res = stat_tool.execute(p=target)
    assert tool_res.status == "SUCCESS"
    assert "benchmarks" in tool_res.data
    assert len(tool_res.evidence_items) > 0
    assert "Statistical Benchmarking" in tool_res.summary
