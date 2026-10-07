"""Phase 2 Evidence + Confidence Tests.

Validates the complete canonical pipeline:
  Evidence → Lineage → Authority → Timestamps → Freshness → Independence → Contradiction → Confidence
"""
import math
import time
import pytest

from paimana_agent.evidence import (
    Evidence,
    EvidenceGroup,
    SourceLineage,
    ConfidenceUpdate,
    SOURCE_AUTHORITY,
    ContradictionDetector,
    EvidenceConfidenceEngine,
    GroundedConfidenceResult
)
from paimana_agent.state import InvestigationState, Fact, Inference, Contradiction


# ============================================================================
# 1. Evidence Model & Provenance
# ============================================================================

def test_evidence_model_and_provenance():
    """Validates evidence model captures complete provenance, attributes, and schemas."""
    ev = Evidence(
        id="E101",
        claim="Physical progress certified at 42.5%",
        source_id="cuf_monthly_progress_report",
        source_type="official_project_record",
        source_system="PAIMANA",
        source_record_id="snap_2026_01",
        source_field="physical_progress_pct",
        raw_value=42.5,
        derived_value=42.5,
        independence_group_id="CUF_REPORT_01"
    )

    assert ev.id == "E101"
    assert ev.authority_score == 1.00  # official_project_record default
    assert ev.reliability == 1.00
    assert ev.independence_group == "CUF_REPORT_01"
    assert ev.retrieved_at is not None
    assert ev.observed_at is not None
    assert ev.recorded_at is not None

    d = ev.to_dict()
    assert d["id"] == "E101"
    assert d["source_system"] == "PAIMANA"
    assert d["source_record_id"] == "snap_2026_01"
    assert d["effective_strength"] == 1.00


# ============================================================================
# 2. Lineage Tracking & Quality Factor
# ============================================================================

def test_evidence_lineage_and_quality_discount():
    """Validates that transformed/derived evidence tracks parent lineage and applies discount."""
    # Raw fact
    ev_raw = Evidence(
        id="E_raw",
        claim="Raw certified physical progress 25%",
        source_type="official_project_record",
        authority_score=1.00
    )
    assert ev_raw.calculate_effective_strength() == pytest.approx(1.00, abs=1e-3)

    # Derived analytical signal with parents
    ev_derived = Evidence(
        id="E_derived",
        claim="Spend-progress gap 15%",
        source_type="tool_result",
        authority_score=0.80,
        parent_evidence_ids=["E_raw", "E_fin"],
        transformation_chain=["expenditure_pct - progress_pct"]
    )
    # Lineage factor 0.85 applies to parented evidence
    strength = ev_derived.calculate_effective_strength()
    assert strength == pytest.approx(0.80 * 0.85, 0.01)

    lineage = SourceLineage(
        evidence_id="E_derived",
        source_system="PAIMANA_ANALYTICS",
        source_record_id="calc_1",
        source_field="gap_pct",
        parent_evidence_ids=["E_raw", "E_fin"],
        transformation_chain=["expenditure_pct - progress_pct"],
        lineage_quality=0.85
    )
    assert len(lineage.parent_evidence_ids) == 2
    assert lineage.lineage_quality == 0.85


# ============================================================================
# 3. Source Authority Hierarchy
# ============================================================================

def test_source_authority_hierarchy():
    """Validates the canonical authority hierarchy across source types."""
    assert SOURCE_AUTHORITY["official_project_record"] == 1.00
    assert SOURCE_AUTHORITY["verified_financial_record"] == 0.95
    assert SOURCE_AUTHORITY["official_milestone_record"] == 0.95
    assert SOURCE_AUTHORITY["approved_external_api"] == 0.90
    assert SOURCE_AUTHORITY["gis_derived_measurement"] == 0.85
    assert SOURCE_AUTHORITY["tool_result"] == 0.80
    assert SOURCE_AUTHORITY["historical_precedent"] == 0.70
    assert SOURCE_AUTHORITY["model_inference"] == 0.60
    assert SOURCE_AUTHORITY["llm_generated_claim"] == 0.10

    # Test auto-assignment of authority based on source_type
    e_fin = Evidence(id="E_f", claim="Audited ledger", source_type="verified_financial_record")
    assert e_fin.authority_score == 0.95

    e_llm = Evidence(id="E_l", claim="LLM thought", source_type="llm_generated_claim")
    assert e_llm.authority_score == 0.10


# ============================================================================
# 4. Timestamps & Freshness Exponential Decay
# ============================================================================

def test_timestamps_and_freshness_decay():
    """Validates exponential freshness decay based on domain half-life."""
    t_now = time.time()
    # 45 days ago
    t_45_days_ago = t_now - (45 * 86400)

    # Financial record (half-life = 45 days)
    ev_fin = Evidence(
        id="E_fin_old",
        claim="Disbursement ledger from 45 days ago",
        source_type="verified_financial_record",
        observed_at=t_45_days_ago,
        retrieved_at=t_now
    )
    freshness = ev_fin.calculate_freshness(current_time=t_now)
    # At exactly one half-life, freshness should be ~0.50
    assert freshness == pytest.approx(0.50, 0.05)

    # 90 days ago = 2 half-lives -> freshness ~0.25
    t_90_days_ago = t_now - (90 * 86400)
    ev_fin_older = Evidence(
        id="E_fin_older",
        claim="Disbursement ledger from 90 days ago",
        source_type="verified_financial_record",
        observed_at=t_90_days_ago,
        retrieved_at=t_now
    )
    assert ev_fin_older.calculate_freshness(current_time=t_now) == pytest.approx(0.25, 0.05)

    # Historical precedent decays much slower (half-life = 365 days)
    ev_prec = Evidence(
        id="E_prec",
        claim="Historical precedent from 45 days ago",
        source_type="historical_precedent",
        observed_at=t_45_days_ago,
        retrieved_at=t_now
    )
    assert ev_prec.calculate_freshness(current_time=t_now) > 0.90


# ============================================================================
# 5. Independence Groups & Aggregation
# ============================================================================

def test_independence_group_aggregation():
    """Validates that evidence from the same underlying snapshot does not inflate independence."""
    state = InvestigationState(objective="Independence Test", project_code="IND-1", project_name="Indep Proj")

    # Three tools all querying the same CUF snapshot
    e1 = Evidence(id="E1", claim="Financial spend", independence_group_id="CUF_SNAPSHOT_2026_01")
    e2 = Evidence(id="E2", claim="Milestone slip", independence_group_id="CUF_SNAPSHOT_2026_01")
    e3 = Evidence(id="E3", claim="Physical progress", independence_group_id="CUF_SNAPSHOT_2026_01")

    state.add_evidence(e1)
    state.add_evidence(e2)
    state.add_evidence(e3)

    # All 3 evidence items must collapse into ONE independence group
    assert len(state.evidence_groups) == 1
    assert "CUF_SNAPSHOT_2026_01" in state.evidence_groups

    # Independent external corroboration from GIS satellite inspection
    e_gis = Evidence(id="E_gis", claim="Satellite site earthwork volume", independence_group_id="GIS_SATELLITE_SURVEY")
    state.add_evidence(e_gis)

    assert len(state.evidence_groups) == 2
    dash = state.get_evidence_quality_dashboard()
    assert len(dash["independent_corroborating_groups"]) == 2
    assert dash["independence"] > 60.0


# ============================================================================
# 6. Contradiction Detection & Penalty
# ============================================================================

def test_contradiction_detection_and_penalty():
    """Validates contradiction detection between unrevised dates and stalled progress."""
    detector = ContradictionDetector()

    e_sched = Evidence(id="E_sch", claim="Milestone schedule", source_tool="cuf_milestone_schedule")
    e_mpr = Evidence(id="E_mpr", claim="Physical progress MPR", source_tool="cuf_monthly_progress_report")

    proj = {
        "project_code": "CONTRA-1",
        "original_completion_date": "06/2026",
        "revised_completion_date": "06/2026", # 0 slippage claimed
        "physical_progress_pct": 12.0,        # stalled at 12%
        "project_age_months": 40              # well aged project
    }

    contras = detector.detect_contradictions([e_sched, e_mpr], proj)
    assert len(contras) == 1
    assert contras[0]["metric_or_claim"] == "schedule_progress_alignment"
    assert "Milestone Schedule" in contras[0]["source_a"]
    assert "Physical Progress" in contras[0]["source_b"]


# ============================================================================
# 7. Canonical EvidenceConfidenceEngine Evaluation
# ============================================================================

def test_evidence_confidence_engine_complete_pipeline():
    """Validates the canonical EvidenceConfidenceEngine computes separated, grounded confidence."""
    e1 = Evidence(id="E1", claim="Verified financial record", source_type="verified_financial_record", authority_score=0.95, independence_group_id="GRP_FIN")
    e2 = Evidence(id="E2", claim="External GIS measurement", source_type="gis_derived_measurement", authority_score=0.85, independence_group_id="GRP_GIS")
    ev_items = [e1, e2]

    facts = [
        Fact(statement="Cost is 1000", source="Ledger", metric="cost", value=1000),
        Fact(statement="Physical progress is 25%", source="GIS", metric="progress", value=25)
    ]
    inferences = [Inference(statement="Decoupling observed", derived_from=["cost"], analytical_significance="high")]

    from paimana_agent.hypotheses.model import Hypothesis
    h1 = Hypothesis(id="H1", statement="Front-loaded billing", posterior_prob=0.75, net_score=15.0)
    h2 = Hypothesis(id="H2", statement="Schedule delay", posterior_prob=0.25, net_score=5.0)
    hypotheses = [h1, h2]

    evidence_groups = {
        "GRP_FIN": EvidenceGroup(group_id="GRP_FIN", source_system="FIN"),
        "GRP_GIS": EvidenceGroup(group_id="GRP_GIS", source_system="GIS"),
    }
    source_lineage = {
        "E1": SourceLineage(evidence_id="E1", source_system="FIN", source_record_id="r1", source_field="cost"),
        "E2": SourceLineage(evidence_id="E2", source_system="GIS", source_record_id="r2", source_field="geo"),
    }

    # Case A: Strong corroboration, positive precedent, no contradictions
    res_a = EvidenceConfidenceEngine.evaluate(
        evidence_items=ev_items,
        facts=facts,
        inferences=inferences,
        hypotheses=hypotheses,
        contradictions=[],
        evidence_groups=evidence_groups,
        source_lineage=source_lineage,
        precedent_data={"successful_precedents": [{"action": "Audit", "outcome": "Recovered"}]}
    )

    assert isinstance(res_a, GroundedConfidenceResult)
    assert res_a.total_confidence >= 0.70
    assert res_a.confidence_tier == "HIGH"
    assert res_a.root_cause_confidence > 0.40
    assert res_a.recommendation_confidence > 0.50
    assert "GRP_FIN" in res_a.evidence_quality_dashboard["independent_corroborating_groups"]
    assert "GRP_GIS" in res_a.evidence_quality_dashboard["independent_corroborating_groups"]

    # Case B: Unresolved contradiction penalizes confidence
    res_b = EvidenceConfidenceEngine.evaluate(
        evidence_items=ev_items,
        facts=facts,
        inferences=inferences,
        hypotheses=hypotheses,
        contradictions=[{"metric": "dates", "impact": "discrepancy"}],
        evidence_groups=evidence_groups,
        source_lineage=source_lineage,
        precedent_data={}
    )

    assert res_b.total_confidence < res_a.total_confidence
    assert res_b.confidence_breakdown["contradiction_penalty"] == 0.20
    assert any("contradiction" in r.lower() for r in res_b.confidence_reasons)
