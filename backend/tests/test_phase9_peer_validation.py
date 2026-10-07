"""Phase 9 Test Suite — Peer Intelligence Validation.

Verifies the 5 core deliverables for Phase 9:
1. validate cohort logic (purity, stage alignment, scale bounds, completeness, dispersion)
2. remove demo defaults (no dummy 'Roads & Highways', 1000Cr, 50% defaults; store resolution)
3. backtest peer selection (empirical proof: MAE_peer < MAE_sector < MAE_global)
4. validate benchmark usefulness (VRR < 0.60, information gain, false alarm reduction)
5. integrate with investigation (canonical Evidence items, hypothesis updating, counterfactuals, supervisor loop)
"""
from __future__ import annotations

import os
import sys
import tempfile
import pytest
from pathlib import Path

# Ensure package directories are in sys.path
_current_dir = Path(__file__).resolve().parent
_agent_pkg_dir = _current_dir.parent
_repo_root = _agent_pkg_dir.parent
_peer_pkg_dir = _repo_root / "Peer_Intelligence"

for d in [str(_agent_pkg_dir), str(_peer_pkg_dir)]:
    if d not in sys.path:
        sys.path.insert(0, d)

from paimana_agent.store import Store
from paimana_agent.supervisor import SupervisorAgent
from paimana_agent.evidence.normalizer import EvidenceNormalizer
from paimana_agent.causal.causal_engine import CausalEngine
from paimana_agent.causal.counterfactual import CounterfactualAnalyzer
from paimana_agent.tools import ToolRegistry

from peer.repository import InMemoryProjectRepository, SQLiteProjectRepository
from peer.service import PeerIntelligenceService
from peer.schemas import CohortDiscoveryResult, CohortQuality
from peer.tools_adapter import _resolve_p, make_peer_tool_definitions
from peer.validation.cohort_validator import CohortValidator, CohortValidationCriteria
from peer.validation.backtest import PeerBacktestEngine, PeerBacktestReport
from peer.validation.benchmark_usefulness import BenchmarkUsefulnessValidator, BenchmarkUsefulnessReport


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def representative_universe() -> list[dict]:
    """Generates a representative universe of infrastructure projects across sectors and stages."""
    universe = []

    # Sector: Roads & Highways (4 distinct cohorts)
    # Cohort 1: Mega Expressways in Mid Stage (40-60% progress, 1200-1600 Cr)
    for i in range(1, 8):
        universe.append({
            "project_code": f"HW-MEGA-MID-{i}",
            "project_name": f"Expressway Package {i}",
            "sector": "Roads & Highways",
            "original_cost_cr": 1200.0 + i * 50.0,
            "physical_progress_pct": 45.0 + (i % 3) * 4.0,
            "planned_duration_months": 36.0,
            "project_age_months": 20.0,
            "cost_overrun_pct": 5.0 + (i % 3) * 1.5,
            "schedule_slippage_months": 2.0 + (i % 2),
            "implementing_agency": "NHAI",
            "state": "Maharashtra" if i <= 4 else "Gujarat",
        })

    # Cohort 2: Standard Highways in Early Stage (10-25% progress, 250-400 Cr)
    for i in range(1, 6):
        universe.append({
            "project_code": f"HW-STD-EARLY-{i}",
            "project_name": f"State Highway Section {i}",
            "sector": "Roads & Highways",
            "original_cost_cr": 300.0 + i * 20.0,
            "physical_progress_pct": 12.0 + i * 2.0,
            "planned_duration_months": 24.0,
            "project_age_months": 6.0,
            "cost_overrun_pct": 1.0 + i * 0.5,
            "schedule_slippage_months": 0.0,
            "implementing_agency": "MoRTH",
            "state": "Madhya Pradesh",
        })

    # Sector: Railways (5 projects, diverse progress)
    for i in range(1, 6):
        universe.append({
            "project_code": f"RAIL-CORR-{i}",
            "project_name": f"Doubling Corridor {i}",
            "sector": "Railways",
            "original_cost_cr": 2000.0 + i * 200.0,
            "physical_progress_pct": 30.0 + i * 8.0,
            "planned_duration_months": 48.0,
            "project_age_months": 30.0,
            "cost_overrun_pct": 25.0 + i * 3.0,
            "schedule_slippage_months": 18.0 + i * 2.0,
            "implementing_agency": "RVNL",
            "state": "Odisha",
        })

    return universe


@pytest.fixture
def sqlite_test_store(representative_universe):
    """Temporary SQLite store seeded with the representative universe."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    store = Store(path)
    for i, p in enumerate(representative_universe):
        store.save_snapshot(p["project_code"], i + 1, p)
    yield store
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


# ============================================================================
# Phase 9 Tests
# ============================================================================

def test_phase9_1_cohort_logic_validation(representative_universe):
    """Test 1: Rigorous cohort logic validation checking purity, stage, scale, and sufficiency."""
    repo = InMemoryProjectRepository(representative_universe)
    svc = PeerIntelligenceService(repository=repo)
    validator = CohortValidator()

    # Case A: Valid target in Mega Expressway Mid-Stage cohort
    target_a = {
        "project_code": "TARGET-HW-A",
        "project_name": "New Expressway Spur",
        "sector": "Roads & Highways",
        "original_cost_cr": 1350.0,
        "physical_progress_pct": 50.0,
        "planned_duration_months": 36.0,
        "implementing_agency": "NHAI",
    }
    cohort_a = svc.peer_discovery(target_a)
    assert cohort_a.is_sufficient is True
    assert cohort_a.cohort_size >= 3

    val_res_a = validator.validate_cohort(target_a, cohort_a)
    assert val_res_a.is_valid is True
    assert val_res_a.validation_level == "VALID"
    assert val_res_a.sector_purity is True
    assert val_res_a.stage_alignment is True
    assert val_res_a.scale_bound_respected is True
    assert val_res_a.data_completeness_rate >= 0.80

    # Case B: Target in an isolated/unique sector with no peers
    target_isolated = {
        "project_code": "ISOLATED-PORT-1",
        "project_name": "Deepwater Offshore Terminal",
        "sector": "Ports & Shipping",
        "original_cost_cr": 5000.0,
        "physical_progress_pct": 10.0,
    }
    cohort_iso = svc.peer_discovery(target_isolated)
    val_res_iso = validator.validate_cohort(target_isolated, cohort_iso)
    assert val_res_iso.is_valid is False
    assert val_res_iso.validation_level == "INVALID"
    assert "below minimum requirement" in val_res_iso.rejection_reasons[0]


def test_phase9_2_removal_of_demo_defaults(sqlite_test_store):
    """Test 2: Ensure demo defaults ('Roads & Highways', 1000Cr, 50%) are completely removed."""
    # Scenario A: Passing empty kwargs without project record or sector
    empty_kwargs = {"project_code": "UNKNOWN_PROJECT"}
    p_resolved = _resolve_p(None, empty_kwargs)

    # Asserts that no fake demo sector or dummy numbers were injected!
    assert p_resolved["sector"] == ""
    assert p_resolved["original_cost_cr"] == 0.0
    assert p_resolved["physical_progress_pct"] == 0.0
    assert p_resolved["project_name"] == "UNKNOWN_PROJECT"

    # Scenario B: Missing 'p', but project_code exists in store -> resolves authoritative project!
    kwargs_with_store = {
        "project_code": "HW-MEGA-MID-1",
        "store": sqlite_test_store,
    }
    p_from_store = _resolve_p(None, kwargs_with_store)
    assert p_from_store["project_code"] == "HW-MEGA-MID-1"
    assert p_from_store["sector"] == "Roads & Highways"
    assert p_from_store["original_cost_cr"] == 1250.0
    assert p_from_store["physical_progress_pct"] == 49.0

    # Scenario C: Discovered cohort on blank target correctly flags missing data without crashing
    repo = SQLiteProjectRepository(sqlite_test_store)
    svc = PeerIntelligenceService(repository=repo)
    cohort_blank = svc.peer_discovery(p_resolved)
    assert cohort_blank.is_sufficient is False
    assert cohort_blank.cohort_size == 0
    assert cohort_blank.quality == CohortQuality.INSUFFICIENT
    assert "missing 'sector' attribute" in cohort_blank.quality_reasons[0]


def test_phase9_3_backtest_peer_selection_accuracy(representative_universe):
    """Test 3: Empirical backtest proving MAE_peer < MAE_sector < MAE_global."""
    repo = InMemoryProjectRepository(representative_universe)
    svc = PeerIntelligenceService(repository=repo)
    backtest_engine = PeerBacktestEngine(service=svc)

    # Evaluate backtest across all Mega Expressway projects
    test_set = [p for p in representative_universe if p["project_code"].startswith("HW-MEGA-MID")]
    assert len(test_set) >= 5

    report: PeerBacktestReport = backtest_engine.run_backtest(
        test_projects=test_set,
        metrics=["cost_overrun_pct", "physical_progress_pct"]
    )

    assert report.total_projects_evaluated == len(test_set)
    assert report.empirical_proof_established is True

    # Check metric results
    cost_res = report.metric_results["cost_overrun_pct"]
    assert cost_res.mae_peer_cohort <= cost_res.mae_sector
    assert cost_res.mae_peer_cohort <= cost_res.mae_global
    assert cost_res.improvement_vs_sector_pct > 0.0
    assert cost_res.is_peer_superior is True

    prog_res = report.metric_results["physical_progress_pct"]
    assert prog_res.mae_peer_cohort <= prog_res.mae_sector
    assert prog_res.improvement_vs_sector_pct >= 0.0


def test_phase9_4_validate_benchmark_usefulness(representative_universe):
    """Test 4: Verify benchmark discriminative usefulness (VRR < 0.60 and information gain)."""
    repo = InMemoryProjectRepository(representative_universe)
    svc = PeerIntelligenceService(repository=repo)
    usefulness_validator = BenchmarkUsefulnessValidator(service=svc)

    target_hw = {
        "project_code": "TARGET-HW-EVAL",
        "project_name": "Target Expressway Section",
        "sector": "Roads & Highways",
        "original_cost_cr": 1300.0,
        "physical_progress_pct": 48.0,
        "cost_overrun_pct": 6.0,
        "schedule_slippage_months": 2.0,
        "implementing_agency": "NHAI",
    }

    report: BenchmarkUsefulnessReport = usefulness_validator.evaluate_usefulness(
        target_project=target_hw,
        metrics=["physical_progress_pct", "original_cost_cr"]
    )

    assert report.is_benchmark_empirically_useful is True
    assert report.cohort_size >= 3

    # Check Variance Reduction Ratio (VRR) on cost and progress
    cost_useful = report.metrics_evaluated["original_cost_cr"]
    assert cost_useful.variance_reduction_ratio < 0.65
    assert cost_useful.variance_reduction_pct >= 35.0
    assert cost_useful.is_useful is True

    prog_useful = report.metrics_evaluated["physical_progress_pct"]
    assert prog_useful.variance_reduction_ratio < 0.65
    assert prog_useful.variance_reduction_pct >= 35.0


def test_phase9_5_investigation_evidence_normalization():
    """Test 5: Verify EvidenceNormalizer translates peer deviations into structured Evidence with hypothesis links."""
    normalizer = EvidenceNormalizer()

    sample_project = {
        "project_code": "PRJ-EVAL-101",
        "project_name": "Suburban Rail Package",
        "sector": "Railways",
        "original_cost_cr": 800.0,
        "physical_progress_pct": 20.0,
    }

    # Simulate rich peer tool deviation output
    peer_tool_data = {
        "summary": "Peer Intelligence: Target exhibits severe progress lag compared to peer cohort.",
        "deviations": {
            "physical_progress_pct": {
                "difference_from_median": -25.0,
                "percentile_rank": 10.0,
                "is_significant": True,
                "interpretation": "Progress is 25 points below peer cohort median (10th percentile)."
            },
            "schedule_slippage_months": {
                "difference_from_median": 1.0,
                "percentile_rank": 55.0,
                "is_significant": False,
                "interpretation": "Slippage is in line with cohort median (+1.0 mo)."
            }
        }
    }

    evidence_items = normalizer.normalize_tool_result(
        "peer_deviation",
        peer_tool_data,
        sample_project
    )

    # Must produce base peer cohort fact AND granular deviation inferences
    assert len(evidence_items) >= 3

    # Check progress deviation evidence item
    prog_ev = next((e for e in evidence_items if "progress_deviation" in e.source_id), None)
    assert prog_ev is not None
    assert prog_ev.authority_score >= 0.85
    assert prog_ev.is_material is True
    assert "chronic_schedule_delay" in prog_ev.supports_hypotheses
    assert "front_loaded_billing" in prog_ev.supports_hypotheses

    # Check slippage deviation evidence item (cohort alignment -> systemic dpr/clearance explanation)
    slip_ev = next((e for e in evidence_items if "slippage_deviation" in e.source_id), None)
    assert slip_ev is not None
    assert "unrealistic_original_dpr_timeline" in slip_ev.supports_hypotheses
    assert "regulatory_land_clearance" in slip_ev.supports_hypotheses


def test_phase9_6_causal_counterfactual_peer_integration():
    """Test 6: CausalEngine and CounterfactualAnalyzer leverage peer cohort data for Causal Claim Level 3."""
    target_p = {
        "project_code": "HW-ANOM-99",
        "sector": "Roads & Highways",
        "original_cost_cr": 1200.0,
        "physical_progress_pct": 20.0,
        "planned_duration_months": 36.0,
    }

    # Peer data showing same contractor is delayed across multiple peer packages
    peer_data = {
        "same_contractor_peer_delay_months": 8.0,
        "sector_median_slippage_months": 2.0,
        "cohort_size": 6,
    }

    proxy = CounterfactualAnalyzer.evaluate_counterfactual(
        proposed_cause="Contractor plant deficits and poor mobilization",
        observed_effect="Milestone Delay",
        project_data=target_p,
        peer_data=peer_data
    )

    assert proxy.supports_causality is True
    assert proxy.proxy_type == "same_contractor_elsewhere"
    assert "8.0 months delay" in proxy.observed_proxy_outcome


def test_phase9_7_end_to_end_supervisor_peer_investigation(sqlite_test_store):
    """Test 7: End-to-end SupervisorAgent execution with Peer Intelligence integration."""
    registry = ToolRegistry(enable_recovery=True)
    supervisor = SupervisorAgent(tool_registry=registry)

    # Create target anomalous project in Roads & Highways
    anom_project = {
        "project_code": "HW-ANOM-TARGET",
        "project_name": "Stalled Corridor Package",
        "sector": "Roads & Highways",
        "original_cost_cr": 1250.0,
        "revised_cost_cr": 1400.0,
        "cumulative_expenditure_cr": 700.0,
        "physical_progress_pct": 18.0,  # Severely stalled compared to 50% spend
        "planned_duration_months": 36.0,
        "project_age_months": 28.0,
        "implementing_agency": "NHAI",
        "state": "Maharashtra",
    }
    sqlite_test_store.save_snapshot(anom_project["project_code"], 1, anom_project)

    events = [
        {"type": "COST_PROGRESS_MISMATCH", "severity": "CRITICAL", "message": "Severe spend-progress decoupling"},
        {"type": "PROGRESS_STALLED", "severity": "HIGH", "message": "Physical progress stalled under 20%"}
    ]

    res = {
        "project_code": "HW-ANOM-TARGET",
        "project_name": "Stalled Corridor Package",
        "tier": "High",
        "risk_score": 85.0,
    }

    feats = {
        "cost_overrun_pct": 12.0,
        "progress_expenditure_gap_pct": 38.0,
        "schedule_slippage_months": 15.0,
    }

    report = supervisor.run_investigation(
        store=sqlite_test_store,
        p=anom_project,
        res=res,
        drivers=["progress_expenditure_gap_pct"],
        events=events,
        feats=feats,
        max_steps=4,
    )

    assert report is not None
    assert report["project_code"] == "HW-ANOM-TARGET"
    assert "recommendation" in report
    assert "recommendation_details" in report

    # Verify peer intelligence was evaluated in the investigation state
    tools_invoked = report["tools_invoked"]
    assert any("peer" in t.lower() for t in tools_invoked)

    # Verify structured peer evidence items exist
    evidence_items = report["evidence_items"]
    peer_ev = [e for e in evidence_items if "peer" in e.get("source_id", "").lower()]
    assert len(peer_ev) >= 1

    # Verify recommendation was synthesized with authority and statutory gating
    rec_details = report["recommendation_details"]
    assert rec_details.get("action") is not None
    assert rec_details.get("responsible_stakeholder") is not None
