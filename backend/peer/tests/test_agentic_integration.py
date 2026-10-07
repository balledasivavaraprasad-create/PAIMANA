"""Integration Tests for Peer Intelligence in the Real PAIMANA Agentic System.

Verifies the 11 targeted scenarios required by Prompt 3:
- Test A: Tool registration in the REAL ToolRegistry
- Test B: Direct peer tool execution through the REAL ToolRegistry
- Test C: Peer repository integration with SQLite Store
- Test D: Peer benchmark execution and result distribution
- Test E: Peer deviation with directionality and percentile ranks
- Test F: Insufficient peers reporting explicit insufficient status without fabrication
- Test G: Insufficient history reporting DATA_INSUFFICIENT
- Test H: Real Supervisor discovering and invoking peer tools dynamically
- Test I: Evidence propagation into InvestigationState (inferences & decision trace)
- Test J: Hypothesis and confidence propagation from peer evidence
- Test K: End-to-end integration proving the full chain:
         Project -> Supervisor -> ToolRegistry -> Peer Tool -> Service -> Store -> Evidence -> Hypothesis -> Final Report
"""
from __future__ import annotations

import os
import sys
import tempfile
import pytest

# Ensure paimana_agent and peer packages are discoverable
from pathlib import Path
_tests_dir = Path(__file__).resolve().parent
_peer_pkg_dir = _tests_dir.parent.parent  # Peer_Intelligence directory
_agent_v3_dir = _peer_pkg_dir.parent       # paimana_agent_v3 directory
_paimana_agent_dir = _agent_v3_dir / "paimana_agent"

for d in [str(_paimana_agent_dir), str(_peer_pkg_dir)]:
    if d not in sys.path:
        sys.path.insert(0, d)

from paimana_agent.tools import ToolRegistry, ToolResult
from paimana_agent.supervisor import SupervisorAgent, DynamicEvidenceGapPlanner
from paimana_agent.store import Store
from paimana_agent.state import InvestigationState
from paimana_agent.tracer import AgentTracer

from peer.schemas import CohortQuality, DeviationDirection, OutlierSeverity
from peer.repository import SQLiteProjectRepository, InMemoryProjectRepository
from peer.service import PeerIntelligenceService


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sqlite_store():
    """Isolated temporary SQLite Store containing representative PAIMANA records."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    store = Store(db_path)

    # Seed 5 projects in Roads & Highways sector
    projects = [
        {
            "project_code": "SEED-HW-1", "project_name": "Expressway Corridor A",
            "sector": "Roads & Highways", "ministry": "MoRTH", "implementing_agency": "NHAI",
            "state": "Maharashtra", "original_cost_cr": 1200.0, "revised_cost_cr": 1300.0,
            "cumulative_expenditure_cr": 600.0, "physical_progress_pct": 50.0,
            "planned_duration_months": 36.0, "project_age_months": 24.0,
            "cost_overrun_pct": 8.33, "schedule_slippage_months": 3.0, "risk_score": 45.0,
        },
        {
            "project_code": "SEED-HW-2", "project_name": "Expressway Corridor B",
            "sector": "Roads & Highways", "ministry": "MoRTH", "implementing_agency": "NHAI",
            "state": "Maharashtra", "original_cost_cr": 1250.0, "revised_cost_cr": 1350.0,
            "cumulative_expenditure_cr": 620.0, "physical_progress_pct": 52.0,
            "planned_duration_months": 36.0, "project_age_months": 24.0,
            "cost_overrun_pct": 8.0, "schedule_slippage_months": 4.0, "risk_score": 48.0,
        },
        {
            "project_code": "SEED-HW-3", "project_name": "Ring Road Section C",
            "sector": "Roads & Highways", "ministry": "MoRTH", "implementing_agency": "NHAI",
            "state": "Gujarat", "original_cost_cr": 1100.0, "revised_cost_cr": 1150.0,
            "cumulative_expenditure_cr": 550.0, "physical_progress_pct": 48.0,
            "planned_duration_months": 36.0, "project_age_months": 22.0,
            "cost_overrun_pct": 4.5, "schedule_slippage_months": 2.0, "risk_score": 42.0,
        },
        {
            "project_code": "SEED-HW-4", "project_name": "Four-Lane Bypass D",
            "sector": "Roads & Highways", "ministry": "MoRTH", "implementing_agency": "MSRDC",
            "state": "Maharashtra", "original_cost_cr": 1050.0, "revised_cost_cr": 1100.0,
            "cumulative_expenditure_cr": 520.0, "physical_progress_pct": 46.0,
            "planned_duration_months": 30.0, "project_age_months": 20.0,
            "cost_overrun_pct": 4.76, "schedule_slippage_months": 2.0, "risk_score": 44.0,
        },
    ]

    for p in projects:
        code = p["project_code"]
        store.save_snapshot(code, report_index=1, record=p)

    yield store

    try:
        os.remove(db_path)
    except Exception:
        pass


@pytest.fixture
def target_project():
    return {
        "project_code": "TARGET-HW-NEW",
        "project_name": "Western Expressway Extension",
        "sector": "Roads & Highways",
        "ministry": "MoRTH",
        "implementing_agency": "NHAI",
        "state": "Maharashtra",
        "original_cost_cr": 1200.0,
        "revised_cost_cr": 1450.0,
        "cumulative_expenditure_cr": 750.0,
        "physical_progress_pct": 48.0,
        "planned_duration_months": 36.0,
        "project_age_months": 24.0,
        "cost_overrun_pct": 20.83,
        "schedule_slippage_months": 8.0,
        "risk_score": 68.0,
    }


# ============================================================================
# Scenario Tests
# ============================================================================

def test_a_peer_tools_registered_in_real_tool_registry():
    """Test A: Verify all peer tools are available in the actual PAIMANA ToolRegistry."""
    registry = ToolRegistry()
    available_tools = [t["name"] for t in registry.list_tools()]

    expected_peer_tools = [
        "peer_intelligence",
        "peer_discovery",
        "peer_benchmark",
        "peer_deviation",
        "peer_trajectory",
        "peer_outlier",
        "peer_cohort_health",
    ]

    for tool in expected_peer_tools:
        assert tool in available_tools, f"Tool '{tool}' was not registered in ToolRegistry"

    # Verify ToolDefinition properties
    for tool in expected_peer_tools:
        tool_def = registry.get(tool)
        assert tool_def is not None
        assert tool_def.name == tool
        assert tool_def.purpose != ""
        assert "type" in tool_def.input_schema


def test_b_direct_peer_tool_execution(sqlite_store, target_project):
    """Test B: Execute a registered peer tool through the real ToolRegistry."""
    registry = ToolRegistry()

    # Execute peer_discovery tool
    res_discovery = registry.execute("peer_discovery", p=target_project, store=sqlite_store)
    assert isinstance(res_discovery, ToolResult)
    assert res_discovery.status == "SUCCESS"
    assert "cohort_size" in res_discovery.data
    assert res_discovery.data["cohort_size"] >= 3
    assert len(res_discovery.evidence_items) > 0


def test_c_peer_repository_integration(sqlite_store, target_project):
    """Test C: Verify peer repository adapter reads real records from Store."""
    repo = SQLiteProjectRepository(sqlite_store)
    candidates = repo.get_candidates(sector="Roads & Highways", exclude_code="TARGET-HW-NEW")

    assert len(candidates) == 4
    candidate_codes = [c["project_code"] for c in candidates]
    assert "SEED-HW-1" in candidate_codes
    assert "SEED-HW-2" in candidate_codes
    assert "TARGET-HW-NEW" not in candidate_codes


def test_d_peer_benchmark(sqlite_store, target_project):
    """Test D: Verify peer benchmark returns robust statistical distributions."""
    registry = ToolRegistry()
    res = registry.execute("peer_benchmark", p=target_project, store=sqlite_store,
                           metrics=["cost_overrun_pct", "risk_score"])

    assert res.status == "SUCCESS"
    assert "distributions" in res.data
    dists = res.data["distributions"]
    assert "cost_overrun_pct" in dists
    cost_dist = dists["cost_overrun_pct"]
    assert cost_dist["median"] > 0
    assert cost_dist["p25"] <= cost_dist["median"] <= cost_dist["p75"]
    assert cost_dist["count"] >= 3


def test_e_peer_deviation(sqlite_store, target_project):
    """Test E: Verify target-vs-peer deviation computes differences and directionality."""
    registry = ToolRegistry()
    res = registry.execute("peer_deviation", p=target_project, store=sqlite_store,
                           metrics=["cost_overrun_pct"])

    assert res.status == "SUCCESS"
    devs = res.data["deviations"]
    assert "cost_overrun_pct" in devs
    dev = devs["cost_overrun_pct"]
    assert dev["target_value"] == 20.83
    # Target cost overrun (20.8%) is higher than peer median (~6%)
    assert dev["absolute_difference"] > 0
    assert dev["direction"] in (DeviationDirection.HIGHER_THAN_PEERS.value,
                                DeviationDirection.SIGNIFICANTLY_ABOVE_PEERS.value)
    assert dev["is_significant"] is True


def test_f_insufficient_peers_reported_cleanly(target_project):
    """Test F: When database has fewer than 3 peers, report INSUFFICIENT without fabrication."""
    empty_db = tempfile.mktemp(suffix=".db")
    empty_store = Store(empty_db)
    # Only 1 peer
    empty_store.save_snapshot("SOLO-PEER", 1, {"project_code": "SOLO-PEER", "sector": "Roads & Highways", "original_cost_cr": 1000.0})

    registry = ToolRegistry()
    res = registry.execute("peer_benchmark", p=target_project, store=empty_store)

    assert res.status == "PARTIAL"
    assert res.data["is_sufficient"] is False
    assert res.data["cohort_quality"] == CohortQuality.INSUFFICIENT.value
    assert any("insufficient" in note.lower() for note in res.data.get("notes", []))
    # Crucial: NO fabricated metric distributions
    assert len(res.data["distributions"]) == 0

    try:
        os.remove(empty_db)
    except Exception:
        pass


def test_g_insufficient_history_reported_cleanly(sqlite_store, target_project):
    """Test G: Projects with < 2 snapshots report DATA_INSUFFICIENT for trajectory."""
    registry = ToolRegistry()
    # Save exactly 1 snapshot for target (< 2 required)
    sqlite_store.save_snapshot("TARGET-HW-NEW", 1, target_project)
    res = registry.execute("peer_trajectory", p=target_project, store=sqlite_store)

    assert res.status == "PARTIAL"
    assert res.data["is_sufficient_history"] is False
    assert "at least 2 chronological snapshots are required" in res.summary


def test_h_supervisor_discovers_and_invokes_peer_tools(sqlite_store, target_project):
    """Test H: Verify real Supervisor discovers and invokes peer tools dynamically."""
    registry = ToolRegistry()
    tracer = AgentTracer()
    supervisor = SupervisorAgent(tool_registry=registry, tracer=tracer)

    manifest = supervisor.registry.export_tools_manifest()
    tool_names = [t["name"] for t in manifest]
    assert "peer_intelligence" in tool_names
    assert "peer_discovery" in tool_names
    assert "peer_deviation" in tool_names

    res_mock = {
        "project_code": "TARGET-HW-NEW", "project_name": "Western Expressway Extension",
        "tier": "High", "risk_score": 68.0, "cost_overrun_pct": 20.83, "slippage_months": 8.0
    }
    events = [{"type": "COST_PROGRESS_MISMATCH", "severity": "HIGH", "message": "Spend lead over progress"}]

    report = supervisor.run_investigation(
        store=sqlite_store, p=target_project, res=res_mock, drivers=["cost overrun"],
        events=events, feats={"progress_expenditure_gap_pct": 18.0}
    )

    assert report is not None
    # Supervisor must invoke peer_intelligence during dynamic investigation
    assert any("peer_intelligence" in t for t in report["tools_invoked"])
    assert "peers" in report["evidence"]
    assert report["evidence"]["peers"].get("sector") == "Roads & Highways"


def test_i_evidence_propagation_into_investigation_state(sqlite_store, target_project):
    """Test I: Verify peer ToolResult converts into structured inferences in InvestigationState."""
    registry = ToolRegistry()
    supervisor = SupervisorAgent(tool_registry=registry)

    res_mock = {
        "project_code": "TARGET-HW-NEW", "project_name": "Western Expressway Extension",
        "tier": "High", "risk_score": 68.0, "cost_overrun_pct": 20.83, "slippage_months": 8.0
    }
    events = [{"type": "COST_PROGRESS_MISMATCH", "severity": "HIGH", "message": "Spend lead"}]

    report = supervisor.run_investigation(
        store=sqlite_store, p=target_project, res=res_mock, drivers=["cost overrun"],
        events=events, feats={"progress_expenditure_gap_pct": 18.0}
    )

    # Check that structured evidence contains peer evidence
    inferences = report["structured_evidence"]["inferences"]
    assert len(inferences) > 0
    peer_inferences = [inf for inf in inferences if "peer" in str(inf.get("derived_from", [])).lower()
                       or "peer" in str(inf.get("statement", "")).lower()]
    assert len(peer_inferences) >= 1

    # Check decision trace contains Peer Evidence
    traces = report["decision_trace"]
    peer_traces = [tr for tr in traces if "peer" in str(tr.get("finding", "")).lower()
                   or "peer" in str(tr.get("evidence_source", "")).lower()]
    assert len(peer_traces) >= 1


def test_j_hypothesis_propagation_from_peer_evidence(sqlite_store, target_project):
    """Test J: Verify peer evidence is linked into the relational evidence graph and hypotheses."""
    registry = ToolRegistry()
    supervisor = SupervisorAgent(tool_registry=registry)

    res_mock = {
        "project_code": "TARGET-HW-NEW", "project_name": "Western Expressway Extension",
        "tier": "High", "risk_score": 68.0, "cost_overrun_pct": 20.83, "slippage_months": 8.0
    }
    events = [{"type": "COST_PROGRESS_MISMATCH", "severity": "HIGH", "message": "Spend lead"}]

    report = supervisor.run_investigation(
        store=sqlite_store, p=target_project, res=res_mock, drivers=["cost overrun"],
        events=events, feats={"progress_expenditure_gap_pct": 18.0}
    )

    # Verify relational evidence graph includes peer tool links
    evidence_graph = report["evidence_graph"]
    peer_edges = [edge for edge in evidence_graph if "peer" in edge.get("source", "")]
    assert len(peer_edges) >= 1
    assert any(edge["relation"] in ("CONTEXTUALIZES", "SUPPORTS", "WEAKENS") for edge in peer_edges)

    # Verify confidence reasons include peer validation
    assert any("peer cohort/baseline validated" in r for r in report["confidence_reasons"])


def test_k_complete_end_to_end_chain(sqlite_store, target_project):
    """Test K: Exercises the complete end-to-end chain from Target Project to Final Investigation Report."""
    # 1. Target Project Input
    assert target_project["project_code"] == "TARGET-HW-NEW"

    # 2. ToolRegistry with peer tools
    registry = ToolRegistry()
    assert registry.get("peer_intelligence") is not None
    assert registry.get("peer_deviation") is not None

    # 3. Direct execution via ToolRegistry
    direct_res = registry.execute("peer_deviation", p=target_project, store=sqlite_store)
    assert direct_res.status == "SUCCESS"

    # 4. Supervisor investigation
    supervisor = SupervisorAgent(tool_registry=registry)
    res_mock = {
        "project_code": "TARGET-HW-NEW", "project_name": "Western Expressway Extension",
        "tier": "High", "risk_score": 68.0, "cost_overrun_pct": 20.83, "slippage_months": 8.0
    }
    events = [{"type": "COST_PROGRESS_MISMATCH", "severity": "HIGH", "message": "Spend lead"}]

    final_report = supervisor.run_investigation(
        store=sqlite_store, p=target_project, res=res_mock, drivers=["cost overrun"],
        events=events, feats={"progress_expenditure_gap_pct": 18.0}
    )

    # 5. Assertions on final report
    assert final_report["project_code"] == "TARGET-HW-NEW"
    assert "peer_intelligence" in "".join(final_report["tools_invoked"])
    assert final_report["evidence"]["peers"] is not None
    assert "cohort_health" in final_report["evidence"]["peers"]
    assert final_report["evidence"]["peers"]["cohort_health"]["is_sufficient"] is True
    assert final_report["evidence"]["peers"]["cohort_health"]["cohort_size"] >= 3
    assert final_report["confidence"] in ("HIGH", "MEDIUM", "LOW")
    assert final_report["status"] == "pending_approval"  # Human approval boundary preserved!
