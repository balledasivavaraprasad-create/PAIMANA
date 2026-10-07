"""Comprehensive Test Suite for PAIMANA Domain-Specific Intelligence (DSI-01 to DSI-14).

Verifies:
- Infrastructure taxonomy & multi-attribute project profiling (DSI-01, DSI-02)
- Commercial procurement & contract variation tracking (DSI-03, DSI-04)
- Land acquisition bottlenecks, linear handover, and progress alignment (DSI-05)
- Statutory clearances (EC, FC Stage I/II, Wildlife) & workfront blocks (DSI-06)
- Utility shifting lifecycle, workfront obstructions & deposit tracking (DSI-07)
- Physical terrain difficulty & seasonal weather working windows (DSI-08, DSI-09)
- Contractor concentration & workfront fragmentation / island risk (DSI-10, DSI-11)
- Domain-specific peer normalizations (DSI-12)
- Execution dependency graph modeling & critical path bottlenecks (DSI-13)
- Hypothesis-conditioned investigation planning & CONTEXTUALIZES evidence (DSI-14)
- Full service & ToolRegistry adapter integration with caching
"""
from __future__ import annotations

import pytest
from typing import Any, Dict

from peer.domain import (
    ClearanceItem,
    ClearanceStatus,
    ClearanceType,
    ConstraintSeverity,
    ContractAnalyzer,
    ContractorWorkfrontAnalyzer,
    DependencyGraphBuilder,
    DependencyStatus,
    DomainIntelligenceService,
    DomainNormalizationEngine,
    EnvironmentalClearanceAnalyzer,
    EvidenceStatus,
    ExecutionModel,
    InfrastructureCategory,
    InfrastructureSector,
    InvestigationStrategyPlanner,
    LandAcquisitionAnalyzer,
    PhysicalContextAnalyzer,
    ProcurementAnalyzer,
    ProjectProfileBuilder,
    TerrainType,
    UtilityShiftingAnalyzer,
    UtilityStage,
    UtilityType,
    classify_sector,
    is_linear_infrastructure,
)
from peer.repository import InMemoryProjectRepository
from peer.service import PeerIntelligenceService
from peer.tools_adapter import make_peer_tool_definitions


# ==============================================================================
# 1. Taxonomy & Multi-Attribute Profiling (DSI-01, DSI-02)
# ==============================================================================

def test_taxonomy_classification():
    # Highway by keywords & agency
    sec, cat, sub = classify_sector(agency="NHAI", raw_sector="Roads")
    assert sec == InfrastructureSector.ROADS_HIGHWAYS
    assert cat == InfrastructureCategory.LINEAR_TRANSPORT
    assert is_linear_infrastructure(sec, cat) is True

    # Metro rail
    sec, cat, sub = classify_sector(project_name="Bangalore Metro Phase 2 Reach 5", agency="BMRCL")
    assert sec == InfrastructureSector.URBAN_METRO
    assert cat == InfrastructureCategory.URBAN_TRANSIT

    # Railway freight corridor
    sec, cat, sub = classify_sector(agency="DFCCIL", raw_sector="Railways")
    assert sec == InfrastructureSector.RAILWAYS
    assert is_linear_infrastructure(sec, cat) is True

    # Power Transmission vs Plant
    sec_tx, cat_tx, _ = classify_sector(project_name="765 kV Transmission Line Substation", agency="Powergrid")
    assert sec_tx == InfrastructureSector.POWER_ENERGY
    assert cat_tx == InfrastructureCategory.LINEAR_ENERGY

    sec_tp, cat_tp, _ = classify_sector(project_name="Super Thermal Power Station Unit 3", agency="NTPC")
    assert sec_tp == InfrastructureSector.POWER_ENERGY
    assert cat_tp == InfrastructureCategory.INDUSTRIAL_PLANT


def test_project_profile_inference():
    raw_project = {
        "project_code": "NHAI-DL-04",
        "project_name": "Four Laning of Shimla Bypass NH-5 (45 km)",
        "agency": "NHAI",
        "state": "Himachal Pradesh",
        "mode": "HAM",
        "tunnels_km": 6.5,
        "major_bridges_count": 8,
    }
    profile = ProjectProfileBuilder.build_profile(raw_project)
    assert profile.project_code == "NHAI-DL-04"
    assert profile.sector == InfrastructureSector.ROADS_HIGHWAYS
    assert profile.execution_model == ExecutionModel.HAM
    assert profile.terrain in (TerrainType.HILLY, TerrainType.MOUNTAINOUS)
    assert profile.length_km == 45.0
    assert profile.structural_intensity in ("HIGH", "VERY_HIGH")
    assert profile.seasonal_vulnerability in ("HIGH", "SEVERE")
    assert profile.is_linear is True


# ==============================================================================
# 2. Land Acquisition Bottleneck & Linear Handover (DSI-05)
# ==============================================================================

def test_land_acquisition_analyzer_severe_bottleneck():
    analyzer = LandAcquisitionAnalyzer()
    project = {
        "project_code": "EXP-101",
        "land_acquisition": {
            "required_ha": 500.0,
            "acquired_ha": 350.0,
            "handed_over_ha": 250.0,
            "acquisition_velocity_ha_per_month": 10.0,
            "disputed_patches_count": 4,
        },
        "physical_progress_pct": 55.0,
    }
    res = analyzer.analyze(project, is_linear=True, physical_progress_pct=55.0)

    assert res.required_ha == 500.0
    assert res.handover_pct == 50.0
    assert res.pending_ha == 250.0
    assert res.is_critical_bottleneck is True
    assert res.bottleneck_severity == ConstraintSeverity.CRITICAL
    assert res.is_island_working_risk is True
    assert res.estimated_months_to_complete == 25.0
    assert res.progress_vs_land_gap_pct == 5.0  # 55% physical > 50% land handover
    assert res.evidence_status == EvidenceStatus.VERIFIED


def test_land_acquisition_missing_data_gap():
    analyzer = LandAcquisitionAnalyzer()
    res = analyzer.analyze({}, is_linear=True)
    assert res.evidence_status == EvidenceStatus.UNVERIFIED_GAP
    assert res.is_critical_bottleneck is False
    assert "No land acquisition" in res.findings[0]


# ==============================================================================
# 3. Environmental & Statutory Clearances (DSI-06)
# ==============================================================================

def test_environmental_clearances_critical_path():
    analyzer = EnvironmentalClearanceAnalyzer()
    project = {
        "clearances": [
            {"type": "ENVIRONMENTAL", "name": "MoEF Environmental Clearance", "status": "FINAL_APPROVED", "critical_path": False},
            {"type": "FOREST_STAGE_1", "name": "Forest Clearance Stage-I", "status": "IN_PRINCIPLE_APPROVED", "critical_path": True},
            {"type": "FOREST_STAGE_2", "name": "Forest Clearance Stage-II (Final)", "status": "SUBMITTED", "critical_path": True},
            {"type": "WILDLIFE", "name": "NBWL Eco-Sensitive Zone Approval", "status": "SUBMITTED", "critical_path": True},
        ],
        "forest_land_ha": 42.5,
        "pending_tree_felling_count": 1200,
    }
    res = analyzer.analyze(project)
    assert res.total_clearances_required == 4
    assert res.approved_count == 1
    assert res.pending_critical_count == 3
    assert res.is_clearance_bottleneck is True
    assert res.bottleneck_severity == ConstraintSeverity.CRITICAL
    assert res.forest_land_diverted_ha == 42.5
    assert res.tree_felling_pending_count == 1200
    assert res.evidence_status == EvidenceStatus.VERIFIED


# ==============================================================================
# 4. Utility Shifting & Workfront Obstruction (DSI-07)
# ==============================================================================

def test_utility_shifting_workfront_blocks():
    analyzer = UtilityShiftingAnalyzer()
    project = {
        "utilities": [
            {"utility_type": "ELECTRICAL_HT_EHT", "identifier": "400kV Power Tower Line", "stage": "IDENTIFIED", "blocks_workfront": True, "deposit_paid": False},
            {"utility_type": "WATER_SUPPLY_PIPELINE", "identifier": "800mm Feeder Main", "stage": "SHIFTING_IN_PROGRESS", "blocks_workfront": True, "deposit_paid": True},
            {"utility_type": "TELECOM_OFC", "identifier": "BSNL OFC Cable", "stage": "SHIFTING_COMPLETED", "blocks_workfront": False, "deposit_paid": True},
        ]
    }
    res = analyzer.analyze(project)
    assert res.total_utilities == 3
    assert res.completed_count == 1
    assert res.pending_count == 2
    assert res.blocking_workfront_count == 2
    assert res.is_utility_bottleneck is True
    assert res.bottleneck_severity == ConstraintSeverity.CRITICAL
    assert res.completion_pct == pytest.approx(33.33, rel=1e-2)
    assert res.evidence_status == EvidenceStatus.VERIFIED


# ==============================================================================
# 5. Procurement & Contract Variation Intelligence (DSI-03, DSI-04)
# ==============================================================================

def test_procurement_intelligence_retendering():
    analyzer = ProcurementAnalyzer()
    project = {
        "procurement": {
            "tender_notice_date": "2022-01-10",
            "award_date": "2023-08-15",
            "retender_count": 2,
            "awarded_cost_cr": 720.0,
            "sanctioned_cost_cr": 950.0,
        },
        "mode": "EPC",
    }
    res = analyzer.analyze(project)
    assert res.execution_model == ExecutionModel.EPC
    assert res.retender_count == 2
    assert res.is_procurement_risk is True
    assert res.risk_severity == ConstraintSeverity.HIGH
    assert res.tender_duration_months > 18.0
    assert res.bid_premium_discount_pct < -20.0  # ~ -24.2% discount


def test_contract_analyzer_variations_and_eot():
    analyzer = ContractAnalyzer()
    project = {
        "contract": {
            "original_completion_date": "2024-03-31",
            "current_completion_date": "2025-12-31",
            "eot_granted_months": 15.0,
            "eot_pending_months": 8.0,
            "scope_changes_count": 4,
            "cost_revision_cr": 85.5,
            "penalty_invoked": True,
        }
    }
    res = analyzer.analyze(project)
    assert res.eot_granted_months == 15.0
    assert res.eot_pending_months == 8.0
    assert res.scope_changes_count == 4
    assert res.penalty_liquidated_damages_invoked is True
    assert res.is_contractual_risk is True
    assert res.risk_severity == ConstraintSeverity.CRITICAL
    assert res.evidence_status == EvidenceStatus.VERIFIED


# ==============================================================================
# 6. Physical Context, Terrain & Workfront Continuity (DSI-08 to DSI-11)
# ==============================================================================

def test_physical_context_mountainous_and_season():
    analyzer = PhysicalContextAnalyzer()
    project = {
        "state": "Uttarakhand",
        "terrain": "MOUNTAINOUS",
        "physical_context": {
            "tunnels_km": 8.2,
            "complex_structures_count": 6,
            "seasonal_monsoon_downtime_months": 3.0,
            "winter_downtime_months": 3.5,
        }
    }
    res = analyzer.analyze(project, terrain=TerrainType.MOUNTAINOUS)
    assert res.terrain == TerrainType.MOUNTAINOUS
    assert res.terrain_difficulty_factor > 2.0
    assert res.working_window_months_per_year == 5.5  # 12 - 6.5
    assert res.tunnels_km == 8.2


def test_contractor_workfront_fragmentation():
    analyzer = ContractorWorkfrontAnalyzer()
    project = {
        "contractor": "Apex Infra Ltd",
        "contractor_active_packages": 5,
        "contractor_workfront": {
            "linear_continuity_ratio": 0.55,
            "broken_workfronts_count": 5,
        }
    }
    res = analyzer.analyze(project, is_linear=True, length_km=60.0, handover_pct=70.0)
    assert res.contractor_name == "Apex Infra Ltd"
    assert res.concentration_risk == "HIGH"
    assert res.is_fragmented_workfront is True
    assert res.linear_continuity_ratio == 0.55
    assert res.broken_workfronts_count == 5


# ==============================================================================
# 7. Peer Normalization (DSI-12)
# ==============================================================================

def test_domain_peer_normalization():
    norm_engine = DomainNormalizationEngine()
    profile = ProjectProfileBuilder.build_profile({
        "project_code": "TUNNEL-EXP",
        "project_name": "High Altitude Expressway",
        "terrain": "MOUNTAINOUS",
        "state": "Jammu & Kashmir",
        "sector": "Roads & Highways",
    })
    target_metrics = {
        "time_overrun_pct": 80.0,
        "cost_per_km_cr": 45.0,
    }
    adjustments = norm_engine.compute_normalizations(profile, target_metrics)
    assert len(adjustments) >= 2
    time_adj = next(a for a in adjustments if a.metric_name == "time_overrun_pct")
    assert time_adj.normalized_target_value < time_adj.raw_target_value
    assert "Normalized for MOUNTAINOUS" in time_adj.adjustment_rationale


# ==============================================================================
# 8. Dependency Graph Modeling (DSI-13)
# ==============================================================================

def test_dependency_graph_modeling():
    builder = DependencyGraphBuilder()
    land_analyzer = LandAcquisitionAnalyzer()
    clr_analyzer = EnvironmentalClearanceAnalyzer()
    utl_analyzer = UtilityShiftingAnalyzer()

    land = land_analyzer.analyze({
        "land_acquisition": {"required_ha": 300.0, "handed_over_ha": 150.0}
    }, is_linear=True)

    clr = clr_analyzer.analyze({
        "clearances": [
            {"type": "FOREST_STAGE_2", "name": "Forest Clearance", "status": "SUBMITTED", "critical_path": True}
        ]
    })

    utl = utl_analyzer.analyze({
        "utilities": [
            {"utility_type": "ELECTRICAL_HT_EHT", "identifier": "Tower 44", "stage": "IDENTIFIED", "blocks_workfront": True}
        ]
    })

    graph = builder.build_graph(
        project_code="TEST-CORRIDOR",
        land_analysis=land,
        clearance_analysis=clr,
        utility_analysis=utl,
    )

    assert graph.total_nodes > 3
    assert graph.total_edges > 2
    assert len(graph.blocking_nodes) >= 2
    assert len(graph.blocked_milestones) >= 1
    assert "COD" in graph.blocked_milestones[0]
    assert "active upstream blockage" in graph.bottleneck_summary


# ==============================================================================
# 9. Investigation Planning & Evidence Semantics (DSI-14)
# ==============================================================================

def test_investigation_strategy_planning():
    planner = InvestigationStrategyPlanner()
    profile = ProjectProfileBuilder.build_profile({"project_name": "Test Bypass"})
    land_analyzer = LandAcquisitionAnalyzer()
    land = land_analyzer.analyze({"land_acquisition": {"required_ha": 200.0, "handed_over_ha": 80.0}}, is_linear=True)

    recommendations = planner.plan_strategy(
        profile=profile,
        question="Why is the project experiencing critical schedule delay?",
        land_analysis=land,
    )
    assert len(recommendations) >= 1
    land_rec = next(r for r in recommendations if r.target_domain == "LAND_ACQUISITION")
    assert land_rec.suggested_tool == "investigate_land_records"
    assert land_rec.priority == "CRITICAL"
    assert len(land_rec.specific_questions) >= 2
    assert len(land_rec.evidence_gaps_to_fill) >= 1


# ==============================================================================
# 10. End-to-End Service & Tool Adapter Integration
# ==============================================================================

def test_domain_service_end_to_end():
    service = DomainIntelligenceService()
    project = {
        "project_code": "NH-66-KRL",
        "project_name": "Six Laning of NH-66 Coastal Corridor (80 km)",
        "agency": "NHAI",
        "state": "Kerala",
        "mode": "HAM",
        "land_acquisition": {
            "required_ha": 400.0,
            "acquired_ha": 340.0,
            "handed_over_ha": 300.0,
            "disputed_patches_count": 3,
        },
        "clearances": [
            {"type": "CRZ", "name": "Coastal Zone Clearance", "status": "FINAL_APPROVED"},
            {"type": "TREE_FELLING", "name": "Tree Cutting Permission", "status": "SUBMITTED", "critical_path": True},
        ],
        "utilities": [
            {"utility_type": "ELECTRICAL_HT_EHT", "identifier": "KSEB 110kV Line", "stage": "ESTIMATE_SANCTIONED", "blocks_workfront": True},
        ],
        "contract": {
            "eot_granted_months": 6.0,
            "eot_pending_months": 4.0,
        },
        "physical_progress_pct": 60.0,
    }

    report = service.analyze_domain_context(
        project_data=project,
        question="What operational constraints explain the execution delay?",
        target_metrics={"time_overrun_pct": 35.0},
    )

    assert report.project_code == "NH-66-KRL"
    assert report.profile.sector == InfrastructureSector.ROADS_HIGHWAYS
    assert report.profile.terrain == TerrainType.COASTAL
    assert report.profile.is_linear is True
    assert len(report.key_constraints) >= 2
    assert len(report.evidence_items) >= 2

    # Check CONTEXTUALIZES semantics strictly maintained
    for item in report.evidence_items:
        assert item["evidence_relation"] == "CONTEXTUALIZES"
        assert "contextualizes the operational execution environment" in item["cautionary_note"]

    # Verify Caching
    cached_report = service.analyze_domain_context(
        project_data=project,
        question="What operational constraints explain the execution delay?",
        target_metrics={"time_overrun_pct": 35.0},
    )
    assert cached_report is report


def test_peer_service_and_tool_adapter_integration():
    repo = InMemoryProjectRepository()
    peer_service = PeerIntelligenceService(repository=repo)

    target_project = {
        "project_code": "METRO-PH2",
        "project_name": "Urban Metro Reach 3 Underground",
        "sector": "Urban Transport",
        "agency": "DMRC",
        "original_cost_cr": 4500.0,
        "physical_progress_pct": 42.0,
        "underground_ratio": 0.65,
        "tunnels_km": 12.0,
    }
    repo.add_project(target_project)

    # 1. Test PeerIntelligenceService direct method
    domain_report = peer_service.analyze_domain_context(target_project)
    assert domain_report.project_code == "METRO-PH2"
    assert domain_report.profile.sector == InfrastructureSector.URBAN_METRO
    assert domain_report.profile.structural_intensity == "VERY_HIGH"

    # 2. Test comprehensive report includes domain_context
    comp_report = peer_service.get_comprehensive_peer_intelligence(target_project)
    assert "domain_context" in comp_report
    assert comp_report["domain_context"]["project_code"] == "METRO-PH2"

    # 3. Test ToolRegistry adapter
    tools = make_peer_tool_definitions(peer_service)
    tool_map = {t.name: t for t in tools}
    assert "analyze_domain_context" in tool_map

    tool_def = tool_map["analyze_domain_context"]
    tool_result = tool_def.execute(p=target_project, question="Assess structural complexity")
    assert tool_result.status == "SUCCESS"
    assert "Domain Context for METRO-PH2" in tool_result.summary
    assert tool_result.data["project_code"] == "METRO-PH2"
    assert len(tool_result.data["normalizations"]) >= 1  # Underground metro capex adjustment
