"""Comprehensive Test Suite for Evidence & Semantic Safety Subsystem (ESS-01 to ESS-10).

Covers:
- ESS-01: Canonical Evidence Object Standardization & Ingestion
- ESS-02: Provenance & Cryptographic Lineage (SHA-256)
- ESS-03: Multi-Dimensional Reliability Profiling & Tiers
- ESS-04: Semantic Relation Graph & Edge Semantics
- ESS-05: 5-Level Cognitive Claim Hierarchy
- ESS-06: Semantic Claim Validation & Downgrade Gates
- ESS-07: Causal-Claim Guard, 8 Safety Rules & Sanitization
- ESS-08: Contradiction Detection & Empirical Invalidation
- ESS-09: Pre-Report Unsupported-Claim Audit
- ESS-10: Semantic-Safe Report Synthesis & Human Approval Boundary
"""
import pytest
from peer.evidence import (
    Claim,
    ClaimLevel,
    ClaimStatus,
    Evidence,
    EvidenceAndSemanticSafetyService,
    EvidenceProvenance,
    EvidenceRelationType,
    EvidenceReliability,
    ReliabilityTier,
    SemanticRelationGraph,
    SemanticSafeReport,
)
from peer.evidence.causal_guard import CausalClaimGuard, RULES_CATALOG
from peer.evidence.claims import ClaimManager, ClaimValidator
from peer.evidence.contradiction import ContradictionDetector
from peer.evidence.extraction import EvidenceExtractor
from peer.evidence.provenance import ProvenanceTracker
from peer.evidence.registry import EvidenceRegistry
from peer.evidence.reliability import ReliabilityEvaluator
from peer.evidence.synthesis import SemanticReportSynthesizer
from peer.evidence.unsupported_claims import UnsupportedClaimAuditor
from peer.repository import InMemoryProjectRepository
from peer.service import PeerIntelligenceService


@pytest.fixture
def evidence_service():
    return EvidenceAndSemanticSafetyService()


# ==============================================================================
# 1. ESS-01 & ESS-02: Standardization, Extraction & Provenance
# ==============================================================================

def test_evidence_extraction_and_provenance():
    extractor = EvidenceExtractor()
    
    # Financial velocity extraction
    financial_data = {
        "cost_progress_mismatch": True,
        "cost_progress_gap_pct": 32.5,
        "cost_consumed_pct": 78.5,
        "physical_progress_pct": 46.0,
        "burn_rate_cr_pm": 12.4,
    }
    fin_ev_list = extractor.extract_from_financial_velocity("PRJ_101", financial_data)
    assert len(fin_ev_list) >= 2
    
    mismatch_ev = next(e for e in fin_ev_list if e.evidence_type == "COST_PROGRESS_MISMATCH")
    assert mismatch_ev.project_id == "PRJ_101"
    assert mismatch_ev.value == 32.5
    assert mismatch_ev.unit == "percentage_points"
    assert mismatch_ev.provenance is not None
    assert len(mismatch_ev.provenance.input_hash) == 64  # Valid SHA-256
    assert mismatch_ev.provenance.tool_name == "financial_velocity"
    assert mismatch_ev.reliability is not None
    assert mismatch_ev.semantic_status in (ReliabilityTier.SUPPORTED, ReliabilityTier.CONFIRMED)


def test_provenance_hash_reproducibility():
    tracker = ProvenanceTracker()
    payload = {"spend": 100, "progress": 50}
    prov1 = tracker.create_provenance("PRJ_1", "tool_a", "source_a", payload)
    prov2 = tracker.create_provenance("PRJ_1", "tool_a", "source_a", payload)
    
    assert prov1.input_hash == prov2.input_hash
    
    payload_diff = {"spend": 101, "progress": 50}
    prov3 = tracker.create_provenance("PRJ_1", "tool_a", "source_a", payload_diff)
    assert prov1.input_hash != prov3.input_hash


# ==============================================================================
# 2. ESS-03: Multi-Dimensional Reliability Evaluation
# ==============================================================================

def test_reliability_profiling_and_tiers():
    evaluator = ReliabilityEvaluator()
    
    # Audited primary source
    audited_rel = evaluator.evaluate(
        source_quality="HIGH",
        freshness="CURRENT",
        provenance_completeness="COMPLETE",
        methodological_quality="HIGH",
        corroboration="MULTI_SOURCE",
    )
    assert audited_rel.overall_tier == ReliabilityTier.CONFIRMED
    assert audited_rel.reliability_score >= 0.90
    
    # Contextual peer signal
    peer_rel = evaluator.evaluate(
        source_quality="MEDIUM",
        freshness="RECENT",
        provenance_completeness="COMPLETE",
        methodological_quality="HIGH",
        corroboration="SINGLE_SOURCE",
        source_category="PEER_INTELLIGENCE",
    )
    assert peer_rel.overall_tier == ReliabilityTier.CONTEXTUAL
    
    # Unverified proxy
    unverified_rel = evaluator.evaluate(
        source_quality="UNVERIFIED",
        freshness="STALE",
        provenance_completeness="PARTIAL",
        methodological_quality="HEURISTIC",
        corroboration="UNCORROBORATED",
    )
    assert unverified_rel.overall_tier == ReliabilityTier.UNVERIFIED
    assert unverified_rel.reliability_score < 0.50


# ==============================================================================
# 3. ESS-04: Semantic Relation Graph & Edge Semantics
# ==============================================================================

def test_semantic_relation_graph():
    graph = SemanticRelationGraph()
    
    rel1 = graph.add_relation(
        source_id="EV_FIN_01",
        target_id="CLAIM_GAP",
        relation_type=EvidenceRelationType.OBSERVES,
        confidence=0.95,
    )
    assert rel1.relation_type == EvidenceRelationType.OBSERVES
    assert "EV_FIN_01" in graph.get_supporting_evidence_ids("CLAIM_GAP")
    
    # Add contextual edge
    graph.add_relation(
        source_id="EV_PEER_01",
        target_id="HYP_01",
        relation_type=EvidenceRelationType.CONTEXTUALIZES,
    )
    assert graph.is_only_contextual("HYP_01") is True
    
    # Add contradictory edge
    graph.add_relation(
        source_id="EV_SITE_02",
        target_id="HYP_01",
        relation_type=EvidenceRelationType.CONTRADICTS,
    )
    assert graph.has_contradiction("HYP_01") is True
    assert graph.is_only_contextual("HYP_01") is False


# ==============================================================================
# 4. ESS-05 & ESS-06: 5-Level Claim Hierarchy & Safety Gates
# ==============================================================================

def test_claim_hierarchy_and_downgrade_gate(evidence_service):
    # 1. Register primary evidence
    ev1 = Evidence(
        evidence_id="EV_SPEND_01",
        project_id="PRJ_200",
        evidence_type="FINANCIAL_EXPENDITURE",
        source_type="FINANCIAL_TOOL",
        source_id="fin_velocity",
        observation="Sanctioned cost consumed is 78%",
        value=78.0,
        semantic_status=ReliabilityTier.SUPPORTED,
    )
    evidence_service.register_evidence(ev1)
    
    # Register peer contextual evidence
    ev_ctx = Evidence(
        evidence_id="EV_PEER_CTX",
        project_id="PRJ_200",
        evidence_type="PEER_BENCHMARK",
        source_type="PEER_INTELLIGENCE",
        source_id="peer_benchmark",
        observation="Peer cohort average spend is 52%",
        value=52.0,
        semantic_status=ReliabilityTier.CONTEXTUAL,
    )
    evidence_service.register_evidence(ev_ctx)
    
    # Link contextual relation
    evidence_service.link_evidence_to_claim(
        evidence_id="EV_PEER_CTX",
        claim_id="CLAIM_CORRUPT_01",
        relation_type=EvidenceRelationType.CONTEXTUALIZES,
    )
    
    # Attempt to propose a Level 5 CAUSAL claim based only on contextual evidence
    causal_claim = evidence_service.propose_claim(
        project_id="PRJ_200",
        statement="Peer divergence proves front-loaded billing manipulation",
        claim_level=ClaimLevel.CAUSAL,
        evidence_ids=["EV_PEER_CTX"],
        claim_id="CLAIM_CORRUPT_01",
    )
    
    # Safety gate MUST downgrade claim from CAUSAL to HYPOTHESIS
    assert causal_claim.claim_level == ClaimLevel.HYPOTHESIS
    assert causal_claim.status in (ClaimStatus.CONTEXTUAL, ClaimStatus.PARTIALLY_SUPPORTED)
    assert "Downgrade" in causal_claim.audit_note or "downgraded" in causal_claim.audit_note.lower()


def test_unsupported_claim_rejection(evidence_service):
    # Proposing a claim with no evidence
    naked_claim = evidence_service.propose_claim(
        project_id="PRJ_200",
        statement="Project will completely default in 30 days",
        claim_level=ClaimLevel.CAUSAL,
        evidence_ids=[],
        claim_id="CLAIM_NAKED",
    )
    assert naked_claim.status == ClaimStatus.UNSUPPORTED
    assert "zero registered evidence" in naked_claim.audit_note.lower()


# ==============================================================================
# 5. ESS-07: Causal-Claim Guard & 8 Safety Rules
# ==============================================================================

def test_causal_guard_rules_and_sanitization():
    guard = CausalClaimGuard()
    assert len(guard.rules) == 8
    
    # Test Rule 2 & Rule 3: Anomaly / spend ≠ fraud / manipulation
    bad_text = "The financial audit found front-loaded billing manipulation and fraudulent expenditure by contractor."
    is_safe, violations, sanitized = guard.check_statement(bad_text)
    
    assert is_safe is False
    assert "SSR-02" in violations or "SSR-03" in violations
    assert "fraud" not in sanitized.lower()
    assert "manipulation" not in sanitized.lower()
    assert "disproportionate expenditure" in sanitized
    
    # Test Rule 4: Delay ≠ contractor fault
    contractor_fault_text = "Severe schedule delay was because contractor is at fault."
    is_safe4, violations4, sanitized4 = guard.check_statement(contractor_fault_text)
    assert is_safe4 is False
    assert "SSR-04" in violations4
    assert "root-cause attribution pending" in sanitized4


# ==============================================================================
# 6. ESS-08: Contradiction Detection
# ==============================================================================

def test_contradiction_detection():
    registry = EvidenceRegistry()
    graph = SemanticRelationGraph()
    detector = ContradictionDetector(registry, graph)
    
    # Register physical progress evidence: 12% progress achieved
    ev_prog = Evidence(
        evidence_id="EV_PROG_12",
        project_id="PRJ_300",
        evidence_type="PHYSICAL_PROGRESS",
        source_type="FIELD_TELEMETRY",
        source_id="telemetry",
        observation="Physical progress advanced by 12% this quarter",
        value=0.12,
        semantic_status=ReliabilityTier.CONFIRMED,
    )
    registry.register(ev_prog)
    
    # Claim says site was completely idle
    idle_claim = Claim(
        claim_id="CLAIM_IDLE",
        project_id="PRJ_300",
        statement="Construction site was completely idle with no work during monsoon",
        claim_level=ClaimLevel.OBSERVATION,
        evidence_ids=[],
    )
    
    detected = detector.scan_for_contradictions([idle_claim], project_id="PRJ_300")
    assert len(detected) == 1
    assert detected[0].severity in ("CRITICAL", "HIGH")
    assert "EV_PROG_12" in detected[0].conflicting_evidence_ids
    assert graph.has_contradiction("CLAIM_IDLE") is True


# ==============================================================================
# 7. ESS-09: Pre-Report Unsupported-Claim Audit
# ==============================================================================

def test_pre_report_audit(evidence_service):
    # Setup valid evidence
    ev = Evidence(
        evidence_id="EV_FACT_01",
        project_id="PRJ_400",
        evidence_type="VELOCITY_ANALYSIS",
        source_type="FINANCIAL_TOOL",
        source_id="vel_tool",
        observation="Monthly expenditure burn rate is 5.2 Cr",
        value=5.2,
        semantic_status=ReliabilityTier.SUPPORTED,
    )
    evidence_service.register_evidence(ev)
    
    # 1 supported claim
    c1 = evidence_service.propose_claim(
        project_id="PRJ_400",
        statement="Monthly financial velocity is 5.2 Cr per month",
        claim_level=ClaimLevel.OBSERVATION,
        evidence_ids=["EV_FACT_01"],
    )
    
    # 1 unsupported claim
    c2 = Claim(
        claim_id="CLAIM_FAKE",
        project_id="PRJ_400",
        statement="Contractor committed fraud and absconded",
        claim_level=ClaimLevel.CAUSAL,
        evidence_ids=["NON_EXISTENT_EV"],
    )
    
    audit_report = evidence_service.audit_claims([c1, c2])
    assert audit_report.total_claims_evaluated == 2
    assert len(audit_report.supported_claims) >= 1
    assert len(audit_report.rejected_claims) >= 1
    assert audit_report.unsupported_claim_rate > 0.0


# ==============================================================================
# 8. ESS-10: Semantic-Safe Report Synthesis & Human Approval Boundary
# ==============================================================================

def test_semantic_safe_report_synthesis(evidence_service):
    ev1 = Evidence(
        evidence_id="EV_REP_01",
        project_id="PRJ_500",
        evidence_type="COST_ANALYSIS",
        source_type="FINANCIAL_TOOL",
        source_id="cuf_ledger",
        observation="Cumulative expenditure stands at 450 Cr",
        value=450.0,
        semantic_status=ReliabilityTier.SUPPORTED,
    )
    evidence_service.register_evidence(ev1)
    
    valid_claim = evidence_service.propose_claim(
        project_id="PRJ_500",
        statement="Expenditure reaches 450 Cr as of Q2",
        claim_level=ClaimLevel.OBSERVATION,
        evidence_ids=["EV_REP_01"],
    )
    
    bad_claim = Claim(
        claim_id="BAD_ATTRIBUTION",
        project_id="PRJ_500",
        statement="Contractor corruption guaranteed to fail project",
        claim_level=ClaimLevel.ATTRIBUTION,
        evidence_ids=[],
    )
    
    report = evidence_service.generate_safe_report(
        project_id="PRJ_500",
        project_name="NH-44 Highway Expansion",
        candidate_claims=[valid_claim, bad_claim],
        evidence_gaps=["Telemetry logs for Section B pending"],
    )
    
    assert isinstance(report, SemanticSafeReport)
    assert report.project_id == "PRJ_500"
    assert report.human_approval_required is True
    assert "Human Approval Gate Active" in report.executive_narrative
    assert "corruption" not in report.executive_narrative.lower()
    assert any("Suppressed ungrounded claim" in note for note in report.semantic_safety_notes)


# ==============================================================================
# 9. Full Integration with PeerIntelligenceService
# ==============================================================================

def test_peer_intelligence_service_evidence_integration():
    candidates = [
        {
            "project_code": "PEER_METRO_1",
            "project_name": "Line 3 Underground Metro",
            "sector": "Urban Transport",
            "state": "Maharashtra",
            "original_cost_cr": 1300.0,
            "physical_progress_pct": 40.0,
            "expenditure_cr": 750.0,
            "report_month": "2026-03",
        },
        {
            "project_code": "PEER_METRO_2",
            "project_name": "Metro Extension Line 2A",
            "sector": "Urban Transport",
            "state": "Maharashtra",
            "original_cost_cr": 1100.0,
            "physical_progress_pct": 32.0,
            "expenditure_cr": 680.0,
            "report_month": "2026-03",
        },
    ]
    repo = InMemoryProjectRepository(projects=candidates)
    svc = PeerIntelligenceService(repository=repo)
    
    assert svc.evidence_service is not None
    
    target_project = {
        "project_code": "PRJ_TEST_99",
        "project_name": "Metro Rail Phase 2",
        "sector": "Urban Transport",
        "state": "Maharashtra",
        "original_cost_cr": 1200.0,
        "physical_progress_pct": 35.0,
        "expenditure_cr": 720.0,
        "report_month": "2026-03",
    }
    
    pipeline_res = svc.get_comprehensive_peer_intelligence(target_project)
    ingested = svc.normalize_evidence_from_pipeline(target_project, pipeline_res)
    assert len(ingested) > 0
    
    # Audit a candidate claim
    test_claim = svc.evidence_service.propose_claim(
        project_id="PRJ_TEST_99",
        statement="Urban Transport sector peer group benchmarks expenditure distribution",
        claim_level=ClaimLevel.OBSERVATION,
        evidence_ids=[ingested[0].evidence_id],
    )
    audit = svc.audit_investigation_claims([test_claim])
    assert audit.total_claims_evaluated == 1
    assert audit.passed_safety_gate is True
    
    # Generate bounded report
    safe_rep = svc.generate_semantic_safe_report(target_project, [test_claim])
    assert safe_rep.project_id == "PRJ_TEST_99"
    assert safe_rep.human_approval_required is True
