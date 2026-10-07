"""Comprehensive Test Suite for PAIMANA Peer Intelligence Foundation.

Verifies the 12 core engineering conditions:
1. Genuinely similar projects are selected.
2. Dissimilar projects are excluded.
3. Missing fields are handled safely.
4. Insufficient cohort is reported.
5. Cohort quality changes appropriately (HIGH, MEDIUM, LOW, INSUFFICIENT).
6. Similarity explanations are returned with dimension-level audit.
7. Benchmark calculations work (mean, median, IQR, percentiles).
8. Target-vs-peer deviation works with directionality and significance.
9. Trajectory comparison works when historical data exists.
10. Insufficient historical data is handled gracefully.
11. Peer outlier detection works (separating absolute risk from peer anomaly).
12. No peers are fabricated.
"""
from __future__ import annotations

import math
import pytest

from peer.schemas import (
    CohortQuality,
    DeviationDirection,
    OutlierSeverity,
)
from peer.repository import InMemoryProjectRepository
from peer.similarity import ExplainableSimilarityEngine, get_cost_band, get_progress_stage
from peer.cohort import PeerCohortEngine
from peer.benchmark import PeerBenchmarkEngine
from peer.deviation import PeerDeviationEngine
from peer.trajectory import PeerTrajectoryEngine
from peer.outlier import PeerOutlierEngine
from peer.service import PeerIntelligenceService
from peer.tools_adapter import make_peer_tool_definitions


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def target_highway_project():
    return {
        "project_code": "TARGET-HW-1",
        "project_name": "Four-Laning of National Highway Section 4",
        "sector": "Roads & Highways",
        "ministry": "Ministry of Road Transport & Highways",
        "implementing_agency": "National Highways Authority of India [NHAI]",
        "state": "Maharashtra",
        "original_cost_cr": 1200.0,
        "revised_cost_cr": 1400.0,
        "cumulative_expenditure_cr": 600.0,
        "physical_progress_pct": 45.0,
        "planned_duration_months": 36.0,
        "project_age_months": 24.0,
        "cost_overrun_pct": 16.67,
        "schedule_slippage_months": 6.0,
        "risk_score": 62.0,
        "report_month": "2026-03",
    }


@pytest.fixture
def candidate_projects():
    return [
        # Genuinely similar: Same sector, same agency, similar cost, mid stage
        {
            "project_code": "PEER-HW-1",
            "project_name": "Six-Laning of Bypass Expressway",
            "sector": "Roads & Highways",
            "implementing_agency": "National Highways Authority of India [NHAI]",
            "state": "Maharashtra",
            "original_cost_cr": 1150.0,
            "cumulative_expenditure_cr": 580.0,
            "physical_progress_pct": 48.0,
            "planned_duration_months": 36.0,
            "project_age_months": 22.0,
            "cost_overrun_pct": 5.0,
            "schedule_slippage_months": 2.0,
            "risk_score": 45.0,
        },
        # Similar: Same sector, same agency, different state, similar cost
        {
            "project_code": "PEER-HW-2",
            "project_name": "Eastern Peripheral Expressway Package B",
            "sector": "Roads & Highways",
            "implementing_agency": "National Highways Authority of India [NHAI]",
            "state": "Haryana",
            "original_cost_cr": 1300.0,
            "cumulative_expenditure_cr": 550.0,
            "physical_progress_pct": 42.0,
            "planned_duration_months": 36.0,
            "project_age_months": 24.0,
            "cost_overrun_pct": 8.0,
            "schedule_slippage_months": 4.0,
            "risk_score": 48.0,
        },
        # Similar: Same sector, state agency, similar cost, mid stage
        {
            "project_code": "PEER-HW-3",
            "project_name": "State Ring Road Package 1",
            "sector": "Roads & Highways",
            "implementing_agency": "Maharashtra State Road Development Corp [MSRDC]",
            "state": "Maharashtra",
            "original_cost_cr": 1050.0,
            "cumulative_expenditure_cr": 450.0,
            "physical_progress_pct": 40.0,
            "planned_duration_months": 30.0,
            "project_age_months": 20.0,
            "cost_overrun_pct": 6.0,
            "schedule_slippage_months": 3.0,
            "risk_score": 44.0,
        },
        # Dissimilar Sector: Railways
        {
            "project_code": "DIFF-SECTOR-1",
            "project_name": "New Broad Gauge Rail Line Doubling",
            "sector": "Railways",
            "implementing_agency": "Rail Vikas Nigam Limited [RVNL]",
            "state": "Maharashtra",
            "original_cost_cr": 1200.0,
            "physical_progress_pct": 45.0,
        },
        # Dissimilar Scale: Tiny cost (₹180 Cr) vs Mega (₹1200 Cr) and Late stage (92%)
        {
            "project_code": "DIFF-SCALE-1",
            "project_name": "City Grade Separator Flyover",
            "sector": "Roads & Highways",
            "implementing_agency": "State PWD",
            "state": "Assam",
            "original_cost_cr": 180.0,
            "physical_progress_pct": 92.0,
            "planned_duration_months": 18.0,
            "project_age_months": 28.0,
        },
    ]


# ============================================================================
# Tests
# ============================================================================

def test_1_genuinely_similar_projects_selected(target_highway_project, candidate_projects):
    """Condition 1: Genuinely similar projects are identified and included."""
    repo = InMemoryProjectRepository(candidate_projects)
    cohort_engine = PeerCohortEngine(repository=repo, min_similarity_threshold=0.55)
    result = cohort_engine.discover_cohort(target_highway_project)

    assert result.cohort_size >= 3
    selected_codes = [p.peer_code for p in result.peers]
    assert "PEER-HW-1" in selected_codes
    assert "PEER-HW-2" in selected_codes
    assert "PEER-HW-3" in selected_codes


def test_2_dissimilar_projects_excluded(target_highway_project, candidate_projects):
    """Condition 2: Dissimilar projects (sector mismatch, extreme scale/stage gap) are excluded."""
    repo = InMemoryProjectRepository(candidate_projects)
    cohort_engine = PeerCohortEngine(repository=repo, min_similarity_threshold=0.60)
    result = cohort_engine.discover_cohort(target_highway_project)

    selected_codes = [p.peer_code for p in result.peers]
    # Sector mismatch must NEVER be included
    assert "DIFF-SECTOR-1" not in selected_codes
    # Tiny scale + late stage should fall below threshold
    assert "DIFF-SCALE-1" not in selected_codes
    assert result.excluded_count >= 1


def test_3_missing_fields_handled_safely(target_highway_project):
    """Condition 3: Candidate or target with missing fields does not crash and audits missing dimensions."""
    incomplete_candidate = {
        "project_code": "INCOMP-1",
        "project_name": "Highway Expansion with Missing Metadata",
        "sector": "Roads & Highways",
        "original_cost_cr": 1200.0,
        # Missing implementing_agency, state, planned_duration, project_age
    }
    sim_engine = ExplainableSimilarityEngine()
    breakdown = sim_engine.compute_similarity(target_highway_project, incomplete_candidate)

    assert breakdown.overall_similarity > 0.0
    assert "implementing_agency" in breakdown.missing_dimensions
    assert "state" in breakdown.missing_dimensions
    assert "planned_duration" in breakdown.missing_dimensions


def test_4_insufficient_cohort_reported(target_highway_project):
    """Condition 4: When candidate pool is too small or below threshold, report INSUFFICIENT cohort."""
    # Only 1 candidate available (below min_cohort_size of 3)
    repo = InMemoryProjectRepository([
        {
            "project_code": "LONE-PEER",
            "project_name": "Solo Highway",
            "sector": "Roads & Highways",
            "original_cost_cr": 1200.0,
            "physical_progress_pct": 45.0,
        }
    ])
    cohort_engine = PeerCohortEngine(repository=repo, min_cohort_size=3)
    result = cohort_engine.discover_cohort(target_highway_project)

    assert result.is_sufficient is False
    assert result.quality == CohortQuality.INSUFFICIENT
    assert any("below minimum requirement" in r for r in result.quality_reasons)


def test_5_cohort_quality_changes_appropriately(target_highway_project):
    """Condition 5: Cohort quality scales logically across HIGH, MEDIUM, LOW, INSUFFICIENT."""
    # Generate 12 highly similar projects
    high_pool = []
    for i in range(12):
        high_pool.append({
            "project_code": f"HIGH-PEER-{i}",
            "project_name": f"NHAI Mega Highway Package {i}",
            "sector": "Roads & Highways",
            "implementing_agency": "National Highways Authority of India [NHAI]",
            "state": "Maharashtra",
            "original_cost_cr": 1200.0 + (i * 10),
            "physical_progress_pct": 45.0 + (i % 5),
            "planned_duration_months": 36.0,
            "project_age_months": 24.0,
        })
    repo_high = InMemoryProjectRepository(high_pool)
    engine = PeerCohortEngine(repository=repo_high)
    res_high = engine.discover_cohort(target_highway_project)
    assert res_high.quality == CohortQuality.HIGH
    assert res_high.cohort_size >= 10

    # 6 peers -> MEDIUM
    repo_med = InMemoryProjectRepository(high_pool[:6])
    engine_med = PeerCohortEngine(repository=repo_med)
    res_med = engine_med.discover_cohort(target_highway_project)
    assert res_med.quality == CohortQuality.MEDIUM

    # 3 peers -> LOW
    repo_low = InMemoryProjectRepository(high_pool[:3])
    engine_low = PeerCohortEngine(repository=repo_low)
    res_low = engine_low.discover_cohort(target_highway_project)
    assert res_low.quality == CohortQuality.LOW


def test_6_similarity_explanations_returned(target_highway_project, candidate_projects):
    """Condition 6: Explainable breakdown is returned with dimensions, scores, and reasons."""
    sim_engine = ExplainableSimilarityEngine()
    breakdown = sim_engine.compute_similarity(target_highway_project, candidate_projects[0])

    d = breakdown.to_dict()
    assert "overall_similarity" in d
    assert "dimension_scores" in d
    assert "matching_dimensions" in d
    assert "differing_dimensions" in d
    assert "inclusion_reasons" in d
    assert "sector" in breakdown.matching_dimensions
    assert "implementing_agency" in breakdown.matching_dimensions
    assert len(breakdown.inclusion_reasons) >= 2


def test_7_benchmark_calculations_work(target_highway_project, candidate_projects):
    """Condition 7: Statistical benchmark distributions (median, mean, IQR, percentiles) are verified."""
    repo = InMemoryProjectRepository(candidate_projects)
    cohort_engine = PeerCohortEngine(repository=repo, min_similarity_threshold=0.50)
    cohort = cohort_engine.discover_cohort(target_highway_project)

    bench_engine = PeerBenchmarkEngine()
    benchmarks = bench_engine.compute_benchmarks(cohort, metrics=["risk_score", "cost_overrun_pct"])

    assert benchmarks.is_sufficient is True
    assert "risk_score" in benchmarks.distributions
    dist = benchmarks.distributions["risk_score"]
    assert dist.median > 0
    assert dist.p25 <= dist.median <= dist.p75
    assert math.isclose(dist.iqr, dist.p75 - dist.p25)
    assert dist.count >= 3


def test_8_target_vs_peer_deviation_works(target_highway_project, candidate_projects):
    """Condition 8: Target-vs-peer deviation computes differences, directionality, and significance."""
    repo = InMemoryProjectRepository(candidate_projects)
    cohort_engine = PeerCohortEngine(repository=repo, min_similarity_threshold=0.50)
    cohort = cohort_engine.discover_cohort(target_highway_project)

    bench_engine = PeerBenchmarkEngine()
    benchmarks = bench_engine.compute_benchmarks(cohort, metrics=["cost_overrun_pct", "physical_progress_pct", "risk_score"])

    dev_engine = PeerDeviationEngine()
    dev_result = dev_engine.analyze_deviations(target_highway_project, benchmarks)

    assert dev_result.is_sufficient is True
    assert "cost_overrun_pct" in dev_result.deviations
    cost_dev = dev_result.deviations["cost_overrun_pct"]
    assert cost_dev.target_value == 16.67
    assert cost_dev.absolute_difference > 0  # 16.67% > peer median (~6%)
    assert cost_dev.direction in (DeviationDirection.HIGHER_THAN_PEERS, DeviationDirection.SIGNIFICANTLY_ABOVE_PEERS)
    assert cost_dev.is_significant is True


def test_9_trajectory_comparison_works_with_history(target_highway_project, candidate_projects):
    """Condition 9: Trajectory comparison computes velocity rates across chronological snapshots."""
    repo = InMemoryProjectRepository(candidate_projects)
    # Add 3 snapshots for target (month 1 -> 3)
    repo.add_snapshot("TARGET-HW-1", {"report_index": 1, "physical_progress_pct": 35.0, "cumulative_expenditure_cr": 400.0, "risk_score": 50.0})
    repo.add_snapshot("TARGET-HW-1", {"report_index": 2, "physical_progress_pct": 40.0, "cumulative_expenditure_cr": 500.0, "risk_score": 55.0})
    repo.add_snapshot("TARGET-HW-1", {"report_index": 3, "physical_progress_pct": 45.0, "cumulative_expenditure_cr": 600.0, "risk_score": 62.0})

    # Add snapshots for peers (advancing faster at +5% per month)
    for p in ["PEER-HW-1", "PEER-HW-2", "PEER-HW-3"]:
        repo.add_snapshot(p, {"report_index": 1, "physical_progress_pct": 30.0, "cumulative_expenditure_cr": 300.0, "risk_score": 40.0})
        repo.add_snapshot(p, {"report_index": 3, "physical_progress_pct": 50.0, "cumulative_expenditure_cr": 550.0, "risk_score": 45.0})

    cohort_engine = PeerCohortEngine(repository=repo, min_similarity_threshold=0.50)
    cohort = cohort_engine.discover_cohort(target_highway_project)

    traj_engine = PeerTrajectoryEngine(repository=repo)
    traj_res = traj_engine.analyze_trajectory("TARGET-HW-1", cohort)

    assert traj_res.is_sufficient_history is True
    assert "physical_progress_pct" in traj_res.comparisons
    prog_comp = traj_res.comparisons["physical_progress_pct"]
    assert prog_comp.target_delta_per_month == 5.0  # (45 - 35) / 2 = 5.0%/mo
    assert prog_comp.peer_median_delta_per_month == 10.0  # (50 - 30) / 2 = 10.0%/mo
    assert prog_comp.direction == DeviationDirection.LAGGING_PEERS


def test_10_insufficient_historical_data_handled():
    """Condition 10: Projects with < 2 snapshots return DATA_INSUFFICIENT cleanly without error."""
    repo = InMemoryProjectRepository([])
    # Only 1 snapshot
    repo.add_snapshot("SOLO-1", {"report_index": 1, "physical_progress_pct": 20.0})
    traj_engine = PeerTrajectoryEngine(repository=repo)
    empty_cohort = PeerCohortEngine(repository=repo).discover_cohort({"project_code": "SOLO-1", "sector": "Power"})
    traj_res = traj_engine.analyze_trajectory("SOLO-1", empty_cohort)

    assert traj_res.is_sufficient_history is False
    assert "at least 2 chronological snapshots are required" in traj_res.summary


def test_11_peer_outlier_detection_separates_absolute_from_peer_risk():
    """Condition 11: Decouples absolute risk from peer-relative anomaly using Modified Z-scores."""
    # Scenario A: High absolute risk (78), but peer median is ALSO high (75).
    # Expected: absolute_risk=HIGH, peer_relative=TYPICAL_FOR_PEERS, is_peer_outlier=False.
    high_norm_target = {
        "project_code": "TUNNEL-1", "sector": "Railways", "risk_score": 78.0,
    }
    high_peers = [
        {"project_code": f"T-PEER-{i}", "sector": "Railways", "risk_score": 74.0 + (i % 4)}
        for i in range(8)
    ]
    repo_a = InMemoryProjectRepository(high_peers)
    cohort_a = PeerCohortEngine(repository=repo_a, min_similarity_threshold=0.40).discover_cohort(high_norm_target)
    outlier_engine = PeerOutlierEngine()
    res_a = outlier_engine.evaluate_outliers(high_norm_target, cohort_a)

    eval_a = res_a.evaluations["risk_score"]
    assert eval_a.absolute_risk_level == "HIGH"
    assert eval_a.peer_relative_risk_level == "TYPICAL_FOR_PEERS"
    assert eval_a.is_peer_outlier is False
    assert "TYPICAL for peer cohort" in eval_a.distinction_explanation

    # Scenario B: Moderate absolute risk (55), but peers are all very low risk (15-20).
    # Expected: absolute_risk=MEDIUM, peer_relative=HIGH_ANOMALY, is_peer_outlier=True.
    mod_anom_target = {
        "project_code": "STALLED-1", "sector": "Power", "risk_score": 58.0,
    }
    low_peers = [
        {"project_code": f"P-PEER-{i}", "sector": "Power", "risk_score": 15.0 + (i % 3)}
        for i in range(8)
    ]
    repo_b = InMemoryProjectRepository(low_peers)
    cohort_b = PeerCohortEngine(repository=repo_b, min_similarity_threshold=0.40).discover_cohort(mod_anom_target)
    res_b = outlier_engine.evaluate_outliers(mod_anom_target, cohort_b)

    eval_b = res_b.evaluations["risk_score"]
    assert eval_b.absolute_risk_level == "MEDIUM"
    assert eval_b.peer_relative_risk_level == "HIGH_ANOMALY"
    assert eval_b.is_peer_outlier is True
    assert eval_b.severity in (OutlierSeverity.MILD, OutlierSeverity.EXTREME)


def test_12_no_peers_fabricated(target_highway_project):
    """Condition 12: Zero synthetic peers are invented if database is empty."""
    empty_repo = InMemoryProjectRepository([])
    cohort_engine = PeerCohortEngine(repository=empty_repo)
    result = cohort_engine.discover_cohort(target_highway_project)

    assert result.cohort_size == 0
    assert len(result.peers) == 0
    assert result.is_sufficient is False
    assert result.quality == CohortQuality.INSUFFICIENT


def test_service_and_tools_end_to_end(target_highway_project, candidate_projects):
    """Exercises full PeerIntelligenceService and standard ToolDefinition compatibility."""
    repo = InMemoryProjectRepository(candidate_projects)
    service = PeerIntelligenceService(repository=repo)

    # 1. Comprehensive Report
    report = service.get_comprehensive_peer_intelligence(target_highway_project)
    assert report["cohort_health"]["is_sufficient"] is True
    assert "benchmarks" in report
    assert "deviations" in report
    assert "outliers" in report

    # 2. Tool Definitions Execution
    tools = make_peer_tool_definitions(service)
    tool_map = {t.name: t for t in tools}
    assert "peer_discovery" in tool_map
    assert "peer_benchmark" in tool_map
    assert "peer_deviation" in tool_map
    assert "peer_outlier" in tool_map
    assert "peer_intelligence" in tool_map

    # Run peer_intelligence tool
    tool_res = tool_map["peer_intelligence"].execute(p=target_highway_project)
    assert tool_res.status == "SUCCESS"
    assert "Peer Intelligence for TARGET-HW-1" in tool_res.summary
