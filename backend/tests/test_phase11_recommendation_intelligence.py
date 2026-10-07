"""Phase 11 — Recommendation Intelligence Verification Suite.

Validates the canonical 7-stage decision layer lifecycle:
    supported hypotheses
    → candidate generation
    → validation
    → benefit/cost/risk/evidence/authority
    → Pareto
    → ranking
    → alternatives

Ensures rigorous pre-scoring validation gates, multi-criteria dimensional models,
decision-confidence adjustments, Pareto-frontier isolation, and deterministic
alternatives synthesis across all operational scenarios.
"""
from __future__ import annotations
import os
import json
import pytest
from unittest.mock import MagicMock

from paimana_agent.store import Store
from paimana_agent.state import InvestigationState, Fact
from paimana_agent.evidence.model import Evidence
from paimana_agent.hypotheses.model import Hypothesis
from paimana_agent.recommendations.candidate import RecommendationCandidate
from paimana_agent.recommendations.candidate_generator import CandidateGenerator
from paimana_agent.recommendations.candidate_deduplicator import CandidateDeduplicator
from paimana_agent.recommendations.candidate_validator import CandidateValidator
from paimana_agent.recommendations.benefit_model import BenefitModel
from paimana_agent.recommendations.cost_model import CostModel
from paimana_agent.recommendations.risk_model import RiskModel
from paimana_agent.recommendations.evidence_model import CandidateEvidenceModel
from paimana_agent.recommendations.authority_model import AuthorityModel
from paimana_agent.recommendations.ranking_policy import RankingPolicy
from paimana_agent.recommendations.candidate_scorer import CandidateScorer
from paimana_agent.recommendations.pareto import dominates, pareto_filter
from paimana_agent.recommendations.selector import RecommendationSelector, RecommendationDecision
from paimana_agent.supervisor import SupervisorAgent
from paimana_agent.tools import ToolRegistry


@pytest.fixture
def clean_store(tmp_path):
    db_path = str(tmp_path / "test_phase11.db")
    return Store(db_path)


@pytest.fixture
def sample_state():
    state = InvestigationState(
        objective="Investigate severe delay and contractor billing decoupling",
        project_code="NH-TEST-11",
        project_name="NH-11 Expansion Highway"
    )
    state.triggering_events = [{"type": "cost_progress_decoupling"}, {"type": "schedule_delay"}]
    
    # Active supported hypotheses
    h1 = Hypothesis(
        id="h_contractor_cashflow",
        statement="Contractor Liquidity Crisis",
        confidence=0.82,
        status="supported"
    )
    h2 = Hypothesis(
        id="h_regulatory_clearance",
        statement="Environmental Clearance Block",
        confidence=0.45,
        status="active"
    )
    h3 = Hypothesis(
        id="h_spec_dispute",
        statement="Specification Dispute",
        confidence=0.15,
        status="rejected"
    )
    state.hypotheses = [h1, h2, h3]

    # Grounded evidence
    e1 = Evidence(
        id="ev_01",
        claim="Disbursements outpace physical work by 34%",
        source_id="financial_velocity",
        evidence_type="direct_observation",
        reliability=0.92,
        authority_score=0.90,
        independence_group_id="finance_group",
        freshness=0.95
    )
    e2 = Evidence(
        id="ev_02",
        claim="Milestone 4 delayed by 180 days with zero physical mobilization",
        source_id="milestone_audit",
        evidence_type="direct_observation",
        reliability=0.88,
        authority_score=0.85,
        independence_group_id="milestone_group",
        freshness=0.90
    )
    state.evidence_items = [e1, e2]
    state.facts = [
        Fact(statement="Cost overrun is 42%", source="db", metric="cost_overrun", value=42.0)
    ]
    return state


# ============================================================================
# 1. Candidate Generation Across 5 Sources
# ============================================================================
def test_hypothesis_driven_candidate_generation(sample_state):
    """Verifies that candidates are generated across distinct sources from supported hypotheses."""
    generator = CandidateGenerator()
    project = {"project_code": "NH-TEST-11", "original_cost_cr": 1200.0} # Mega project
    feats = {"is_mega_project": True}
    precedents = {
        "successful_precedents": [
            {
                "project_code": "HIST-09",
                "action": "Escrow account restructuring with conditional milestone disbursement",
                "outcome": "Project recovered 65 days schedule slippage",
            }
        ]
    }

    candidates = generator.generate_candidates(
        leading_hypotheses=sample_state.hypotheses,
        investigation_outcome="DIAGNOSIS_CONVERGED",
        project=project,
        feats=feats,
        precedents=precedents,
        investigation_state=sample_state
    )

    assert len(candidates) >= 4, f"Expected at least 4 candidates across sources, got {len(candidates)}"
    
    gen_sources = {c.generated_by for c in candidates}
    assert "precedent_memory" in gen_sources, "Expected candidate generated from precedent memory"
    assert "playbook" in gen_sources, "Expected candidate generated from domain playbooks"
    assert "hypothesis_action" in gen_sources, "Expected candidate generated from hypothesis actions"

    # Precedent candidate inspection
    prec_cand = next(c for c in candidates if c.generated_by == "precedent_memory")
    assert "HIST-09" in prec_cand.description or "HIST-09" in prec_cand.rationale
    assert prec_cand.precedent_outcome is not None
    assert prec_cand.approval_class == "executive"  # Mega-project escalation

    # Hypothesis alignment inspection
    hyp_cands = [c for c in candidates if c.hypothesis_ids]
    assert any("h_contractor_cashflow" in c.hypothesis_ids for c in hyp_cands)

    # Ensure all candidates have required structural attributes
    for c in candidates:
        assert c.id.startswith("REC-")
        assert len(c.title) > 10
        assert c.responsible_stakeholder
        assert c.urgency in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert 0.0 <= c.expected_benefit <= 1.0
        assert 0.0 <= c.expected_cost <= 1.0
        assert 0.0 <= c.implementation_risk <= 1.0


def test_candidate_generation_under_insufficient_evidence():
    """Verifies that INSUFFICIENT_EVIDENCE outcome generates forensic audit and targeted inspections."""
    generator = CandidateGenerator()
    state = InvestigationState(
        objective="Determine why progress stalled",
        project_code="RR-INSUF-1",
        project_name="Railway Gauge Conversion Section 1"
    )
    state.investigation_outcome = "INSUFFICIENT_EVIDENCE"
    state.hypotheses = [
        Hypothesis(id="h_tentative", name="Suspected Soil Instability", confidence=0.25, status="exploring")
    ]
    project = {"original_cost_cr": 250.0}

    candidates = generator.generate_candidates(
        leading_hypotheses=state.hypotheses,
        investigation_outcome="INSUFFICIENT_EVIDENCE",
        project=project,
        feats={},
        precedents={},
        investigation_state=state
    )

    audit_cands = [c for c in candidates if c.action_type == "FORENSIC_AUDIT" or "inspection" in c.title.lower()]
    assert len(audit_cands) >= 1
    assert any("audit" in c.title.lower() or "inspection" in c.title.lower() for c in audit_cands)


# ============================================================================
# 2. Candidate Deduplication
# ============================================================================
def test_candidate_deduplication():
    """Verifies that near-identical candidates are deduplicated and their evidence/hypothesis citations merged."""
    deduplicator = CandidateDeduplicator()

    c1 = RecommendationCandidate(
        id="REC-01",
        title="Establish Joint Financial Audit Taskforce to reconcile contractor invoices",
        rationale="Disbursements outpace certified physical progress on critical sections",
        evidence_ids=["ev_01"],
        hypothesis_ids=["h_finance"]
    )
    c2 = RecommendationCandidate(
        id="REC-02",
        title="Deploy Joint Financial Audit Taskforce to reconcile contractor invoice disbursements",
        rationale="Disbursements outpace certified progress on sections",
        evidence_ids=["ev_02", "ev_03"],
        hypothesis_ids=["h_billing"]
    )
    c3 = RecommendationCandidate(
        id="REC-03",
        title="Issue statutory environment clearance escalation to State Chief Secretary",
        rationale="Forest clearances holding up site possession",
        evidence_ids=["ev_04"],
        hypothesis_ids=["h_statutory"]
    )

    deduped = deduplicator.deduplicate([c1, c2, c3], similarity_threshold=0.60)
    assert len(deduped) == 2, f"Expected 2 unique candidates after deduplication, got {len(deduped)}"
    
    # C1 should have merged evidence and hypothesis citations from C2
    survivor = next(c for c in deduped if c.id == "REC-01")
    assert "ev_01" in survivor.evidence_ids
    assert "ev_02" in survivor.evidence_ids
    assert "ev_03" in survivor.evidence_ids
    assert "h_finance" in survivor.hypothesis_ids
    assert "h_billing" in survivor.hypothesis_ids


# ============================================================================
# 3. Pre-Scoring Validation Gates (Gates 1 to 6)
# ============================================================================
def test_pre_scoring_validation_gates(sample_state):
    """Validates pre-scoring gates: evidence existence, hypothesis alignment, precedent failure, authority, risk cap, causal support."""
    validator = CandidateValidator()
    unsuccessful_precedents = [
        {
            "project_code": "HIST-FAIL-04",
            "action": "Immediate unilateral penalty and forfeiture of bank guarantee",
            "outcome": "Contractor abandoned site and entered 3-year litigation",
            "attribution_class": "FAILED"
        }
    ]

    # Gate 1 Test: Hallucinated / Non-existent evidence ID
    c_bad_ev = RecommendationCandidate(
        id="REC-GATE1",
        title="Valid action title with missing evidence",
        evidence_ids=["E999_NON_EXISTENT"],
        hypothesis_ids=["h_contractor_cashflow"]
    )
    assert not validator.validate_candidate(c_bad_ev, sample_state, unsuccessful_precedents)
    assert c_bad_ev.validation_status == "REJECTED"
    assert any("non-existent or hallucinated" in r for r in c_bad_ev.validation_reasons)

    # Gate 2 Test: Aligned ONLY with rejected hypothesis
    c_bad_hyp = RecommendationCandidate(
        id="REC-GATE2",
        title="Revise technical specifications for foundation piers",
        action_type="ENGINEERING_CHANGE",
        evidence_ids=["ev_01"],
        hypothesis_ids=["h_spec_dispute"]  # Rejected in sample_state
    )
    assert not validator.validate_candidate(c_bad_hyp, sample_state, unsuccessful_precedents)
    assert c_bad_hyp.validation_status == "REJECTED"
    assert any("rejected or inactive" in r for r in c_bad_hyp.validation_reasons)

    # Gate 3 Test: Matches known precedent failure
    c_bad_prec = RecommendationCandidate(
        id="REC-GATE3",
        title="Issue immediate unilateral penalty and forfeiture of bank guarantee to recover advances",
        evidence_ids=["ev_01"],
        hypothesis_ids=["h_contractor_cashflow"]
    )
    assert not validator.validate_candidate(c_bad_prec, sample_state, unsuccessful_precedents)
    assert c_bad_prec.validation_status == "POLICY_VIOLATION"
    assert any("previously failed on project HIST-FAIL-04" in r for r in c_bad_prec.validation_reasons)

    # Gate 4 Test: Mega-project authority mismatch
    c_bad_auth = RecommendationCandidate(
        id="REC-GATE4",
        title="Shut down contractor camp on critical national highway corridor",
        urgency="CRITICAL",
        responsible_stakeholder="Junior Site Assistant",
        evidence_ids=["ev_01"],
        hypothesis_ids=["h_contractor_cashflow"]
    )
    assert not validator.validate_candidate(c_bad_auth, sample_state, unsuccessful_precedents, is_mega_project=True)
    assert c_bad_auth.validation_status == "REQUIRES_HIGHER_AUTHORITY"

    # Gate 5 Test: Implementation risk ceiling (> 0.85)
    c_bad_risk = RecommendationCandidate(
        id="REC-GATE5",
        title="Immediate replacement of EPC concessionaire mid-monsoon",
        implementation_risk=0.92,
        evidence_ids=["ev_01"],
        hypothesis_ids=["h_contractor_cashflow"]
    )
    assert not validator.validate_candidate(c_bad_risk, sample_state, unsuccessful_precedents)
    assert c_bad_risk.validation_status == "HIGH_RISK_ACTION"

    # Gate 6 Test: Causal Support Calibration (Punitive action without Level 4 support)
    sample_state.leading_causal_claim = {
        "causal_level": "LEVEL_2_TEMPORAL_ASSOCIATION",
        "causal_support_score": 0.45
    }
    c_punitive = RecommendationCandidate(
        id="REC-GATE6",
        title="Invoke liquidated damages and initiate contractor termination",
        evidence_ids=["ev_01"],
        hypothesis_ids=["h_contractor_cashflow"]
    )
    assert not validator.validate_candidate(c_punitive, sample_state, unsuccessful_precedents)
    assert c_punitive.validation_status == "PREMATURE_ESCALATION"
    assert any("Level 4 Strong Causal Support" in r for r in c_punitive.validation_reasons)

    # Valid candidate passes all gates
    c_valid = RecommendationCandidate(
        id="REC-VALID",
        title="Convene structured physical-financial reconciliation review with escrow controls",
        action_type="FORENSIC_AUDIT",
        responsible_stakeholder="Chief Engineer & Ministry Financial Advisor",
        urgency="HIGH",
        implementation_risk=0.25,
        evidence_ids=["ev_01", "ev_02"],
        hypothesis_ids=["h_contractor_cashflow"]
    )
    assert validator.validate_candidate(c_valid, sample_state, unsuccessful_precedents, is_mega_project=True)
    assert c_valid.validation_status == "VALID"
    assert c_valid.validated is True


# ============================================================================
# 4. Multi-Criteria Dimensional Models & Scorer
# ============================================================================
def test_multi_criteria_dimensional_models(sample_state):
    """Verifies Benefit, Cost, Risk, Evidence, and Authority dimensional evaluations."""
    # 1. Benefit Model
    b_model = BenefitModel()
    b_score, b_break = b_model.compute_benefit_score(
        candidate_benefit=0.85,
        risk_reduction=0.80,
        schedule_improvement=0.60,
        cost_avoidance=0.70,
        problem_resolution=0.90
    )
    assert 0.70 <= b_score <= 0.90
    assert "risk_reduction_contrib" in b_break["components"]

    # 2. Cost Model (Lower burden = Higher score)
    c_model = CostModel()
    c_low_burden, _ = c_model.compute_cost_score(candidate_cost=0.15, direct_monetary_burden=0.10)
    c_high_burden, _ = c_model.compute_cost_score(candidate_cost=0.90, direct_monetary_burden=0.85)
    assert c_low_burden > c_high_burden, "Lower operational burden must yield higher cost utility"

    # 3. Risk Model (Balances risk reduction against implementation risk)
    r_model = RiskModel()
    r_safe, _ = r_model.compute_risk_score(risk_reduction=0.80, implementation_risk=0.15)
    r_risky, _ = r_model.compute_risk_score(risk_reduction=0.80, implementation_risk=0.85)
    assert r_safe > r_risky, "High implementation risk must sharply penalize risk utility"

    # 4. Evidence Model (Lineage-aware & independence groups)
    e_model = CandidateEvidenceModel()
    e_score_multi, e_break_multi = e_model.compute_evidence_strength(
        candidate_evidence_ids=["ev_01", "ev_02"],
        state_evidence_items=sample_state.evidence_items,
        contradictions_count=0
    )
    assert e_break_multi["independence_groups"] == 2
    assert e_break_multi["corroboration_boost"] > 0.0
    assert e_score_multi >= 0.80, "Corroboration across 2 independent groups must yield high evidence score"

    # With contradiction penalty
    e_score_contra, e_break_contra = e_model.compute_evidence_strength(
        candidate_evidence_ids=["ev_01", "ev_02"],
        state_evidence_items=sample_state.evidence_items,
        contradictions_count=2
    )
    assert e_score_contra < e_score_multi, "Contradictions must reduce evidence strength"

    # 5. Authority Model
    a_model = AuthorityModel()
    a_score_exec, _ = a_model.compute_authority_score(
        cited_evidence_authority=0.90,
        approval_class="executive",
        responsible_stakeholder="Ministry Chief Engineer",
        is_mega_project=True
    )
    a_score_mismatch, _ = a_model.compute_authority_score(
        cited_evidence_authority=0.90,
        approval_class="executive",
        responsible_stakeholder="Junior Field Officer",
        is_mega_project=True
    )
    assert a_score_exec > a_score_mismatch


def test_candidate_scorer_confidence_adjustment(sample_state):
    """Verifies that CandidateScorer computes weighted utility and scales by decision confidence."""
    scorer = CandidateScorer()
    policy = RankingPolicy.get_policy("standard")

    cand = RecommendationCandidate(
        id="REC-SCORE-1",
        title="Structured milestone-linked disbursements",
        expected_benefit=0.85,
        expected_cost=0.25,
        expected_risk_reduction=0.80,
        implementation_risk=0.20,
        authority_score=0.90,
        evidence_ids=["ev_01", "ev_02"],
        responsible_stakeholder="Project Director & Chief Engineer"
    )

    scored_cand = scorer.score_candidate(cand, sample_state, policy)
    
    assert scored_cand.utility_score > 0.60
    assert scored_cand.confidence > 0.60
    assert scored_cand.confidence_adjusted_score <= scored_cand.utility_score
    # Formula: utility * (0.50 + 0.50 * decision_conf)
    expected_conf_adj = round(scored_cand.utility_score * (0.50 + 0.50 * scored_cand.confidence), 3)
    assert abs(scored_cand.confidence_adjusted_score - expected_conf_adj) <= 0.002
    assert "weights" in scored_cand.score_breakdown


# ============================================================================
# 5. Pareto Dominance and Frontier Filtering
# ============================================================================
def test_pareto_frontier_isolation():
    """Verifies that Pareto filtering separates strictly dominated candidates from the optimal frontier."""
    # A dominates B across all 5 dimensions
    cand_a = RecommendationCandidate(
        id="CAND_A",
        expected_benefit=0.90,
        expected_cost=0.20,             # Better cost (lower burden)
        expected_risk_reduction=0.85,
        implementation_risk=0.10,       # Better risk
        evidence_strength=0.88,
        authority_score=0.90
    )
    cand_b = RecommendationCandidate(
        id="CAND_B",
        expected_benefit=0.70,
        expected_cost=0.50,             # Worse cost
        expected_risk_reduction=0.60,
        implementation_risk=0.35,       # Worse risk
        evidence_strength=0.65,
        authority_score=0.75
    )
    # C has higher benefit than A but higher cost (trade-off, not dominated by A)
    cand_c = RecommendationCandidate(
        id="CAND_C",
        expected_benefit=0.98,
        expected_cost=0.45,
        expected_risk_reduction=0.90,
        implementation_risk=0.20,
        evidence_strength=0.85,
        authority_score=0.88
    )

    assert dominates(cand_a, cand_b) is True
    assert dominates(cand_b, cand_a) is False
    assert dominates(cand_a, cand_c) is False
    assert dominates(cand_c, cand_a) is False

    frontier, dominated = pareto_filter([cand_a, cand_b, cand_c])
    frontier_ids = {c.id for c in frontier}
    dominated_ids = {c.id for c in dominated}

    assert "CAND_A" in frontier_ids
    assert "CAND_C" in frontier_ids
    assert "CAND_B" in dominated_ids
    assert len(dominated) == 1
    assert len(frontier) == 2


# ============================================================================
# 6. Constrained Ranking and Winner Selection
# ============================================================================
def test_constrained_ranking_and_winner_selection(sample_state):
    """Verifies policy constraint threshold gating, ranking order, and winner determination."""
    selector = RecommendationSelector()
    policy = RankingPolicy(
        min_evidence_strength=0.30,
        max_implementation_risk=0.60,
        min_authority_score=0.40
    )

    c1 = RecommendationCandidate(
        id="C1",
        title="High scoring balanced intervention",
        expected_benefit=0.88,
        expected_cost=0.20,
        expected_risk_reduction=0.85,
        implementation_risk=0.15,
        evidence_strength=0.80,
        authority_score=0.85,
        utility_score=0.84,
        confidence=0.85,
        confidence_adjusted_score=0.78,
        validation_status="VALID",
        score_breakdown={"evidence": {"independence_groups": 2}}
    )
    c2 = RecommendationCandidate(
        id="C2",
        title="Viable runner-up with lower evidence",
        expected_benefit=0.80,
        expected_cost=0.30,
        expected_risk_reduction=0.75,
        implementation_risk=0.25,
        evidence_strength=0.70,
        authority_score=0.80,
        utility_score=0.76,
        confidence=0.75,
        confidence_adjusted_score=0.66,
        validation_status="VALID",
        score_breakdown={"evidence": {"independence_groups": 1}}
    )
    c3_violator = RecommendationCandidate(
        id="C3",
        title="Intervention with excessive risk",
        implementation_risk=0.75,  # Exceeds max_implementation_risk (0.60)
        evidence_strength=0.50,
        authority_score=0.50,
        confidence_adjusted_score=0.55,
        validation_status="VALID"
    )

    decision = selector.select(
        frontier_candidates=[c1, c2, c3_violator],
        all_candidates=[c1, c2, c3_violator],
        state=sample_state,
        policy=policy
    )

    assert decision.selected_candidate is not None
    assert decision.selected_candidate.id == "C1"
    assert decision.selected_candidate.rank == 1
    assert decision.outcome_status == "RECOMMENDATION_SELECTED"
    
    # C2 should be an alternative
    assert len(decision.alternatives) == 1
    assert decision.alternatives[0].id == "C2"

    # C3 should be rejected due to runtime policy constraints
    assert any(c.id == "C3" for c in decision.rejected_candidates)


def test_ranking_tie_break_multiple_candidates_review(sample_state):
    """Verifies that close scores trigger MULTIPLE_CANDIDATES_REQUIRE_REVIEW status."""
    selector = RecommendationSelector()
    c1 = RecommendationCandidate(
        id="C1",
        title="Action Option A",
        implementation_risk=0.20,
        evidence_strength=0.80,
        authority_score=0.85,
        confidence_adjusted_score=0.780,
        validation_status="VALID",
        score_breakdown={"evidence": {"independence_groups": 2}}
    )
    c2 = RecommendationCandidate(
        id="C2",
        title="Action Option B",
        implementation_risk=0.20,
        evidence_strength=0.80,
        authority_score=0.85,
        confidence_adjusted_score=0.770,  # Delta = 0.010 < 0.025
        validation_status="VALID",
        score_breakdown={"evidence": {"independence_groups": 2}}
    )

    decision = selector.select(
        frontier_candidates=[c1, c2],
        all_candidates=[c1, c2],
        state=sample_state
    )

    assert decision.outcome_status == "MULTIPLE_CANDIDATES_REQUIRE_REVIEW"
    assert decision.selected_candidate.id == "C1"
    assert len(decision.alternatives) == 1


# ============================================================================
# 7. Distinct Viable Alternatives Synthesis
# ============================================================================
def test_distinct_viable_alternatives_synthesis(sample_state):
    """Verifies that non-winning Pareto-optimal candidates are formatted with trade-off rationale."""
    selector = RecommendationSelector()
    
    winner = RecommendationCandidate(
        id="REC-WIN",
        title="Institute escrow disbursements linked to third-party engineering audits",
        confidence_adjusted_score=0.82,
        expected_risk_reduction=0.85,
        implementation_risk=0.18,
        evidence_strength=0.88,
        authority_score=0.92,
        tradeoffs="Requires dedicated monitoring overhead from PMU.",
        validation_status="VALID",
        score_breakdown={"evidence": {"independence_groups": 2}}
    )
    runner_up = RecommendationCandidate(
        id="REC-ALT-1",
        title="Deploy multi-agency taskforce to re-baseline project milestones",
        confidence_adjusted_score=0.71,
        expected_risk_reduction=0.70,
        implementation_risk=0.28,
        evidence_strength=0.75,
        authority_score=0.85,
        validation_status="VALID",
        score_breakdown={"evidence": {"independence_groups": 1}}
    )

    decision = selector.select(
        frontier_candidates=[winner, runner_up],
        all_candidates=[winner, runner_up],
        state=sample_state
    )

    assert decision.selected_candidate.id == "REC-WIN"
    assert len(decision.alternatives) == 1
    
    sel_reason = decision.selection_reason
    assert "dominant_factors" in sel_reason
    assert len(sel_reason["dominant_factors"]) >= 1
    assert "why_alternatives_not_selected" in sel_reason
    
    alt_eval = sel_reason["why_alternatives_not_selected"][0]
    assert alt_eval["candidate_id"] == "REC-ALT-1"
    assert len(alt_eval["reasons"]) >= 1
    assert any("Lower confidence-adjusted utility score" in r for r in alt_eval["reasons"])


# ============================================================================
# 8. End-to-End Supervisor Recommendation Loop
# ============================================================================
def test_end_to_end_supervisor_recommendation_intelligence(clean_store):
    """Executes a full supervisor investigation verifying the complete recommendation intelligence pipeline."""
    # Seed project in store
    proj_code = "NH-E2E-REC-99"
    p_proj = {
        "project_code": proj_code,
        "project_name": "Golden Quadrilateral Expansion Section 9",
        "sector": "Roads & Highways",
        "original_cost_cr": 1450.0,
        "revised_cost_cr": 1950.0,
        "cumulative_expenditure_cr": 920.0,
        "physical_progress_pct": 38.0,
        "financial_progress_pct": 63.4,
        "original_completion_date": "2024-12-31",
        "revised_completion_date": "2026-06-30",
        "agency": "NHAI",
        "state": "Maharashtra",
        "contract_type": "EPC",
        "is_mega_project": True,
        "status": "Delayed"
    }
    clean_store.save_snapshot(proj_code, 1, p_proj)

    events = [{
        "type": "PROGRESS_STALLED",
        "message": "Physical progress stalled at 38% with severe financial decoupling",
        "event_id": "EV-NH-REC-01",
        "timestamp": 1700000000.0
    }]

    registry = ToolRegistry(enable_recovery=True)
    supervisor = SupervisorAgent(tool_registry=registry)
    report = supervisor.run_investigation(
        store=clean_store,
        p=p_proj,
        res={"project_code": proj_code, "tier": "High", "risk_score": 82.0},
        drivers=["progress_expenditure_gap_pct", "schedule_delay_months"],
        events=events,
        max_steps=4
    )

    # 1. Verify candidate recommendations generated and populated
    candidates = report.get("candidate_recommendations", [])
    assert len(candidates) >= 3, f"Expected at least 3 candidates in final report, got {len(candidates)}"

    # 2. Verify winner selection
    selected_rec = report.get("selected_recommendation")
    assert selected_rec is not None, "Selected recommendation must not be None"
    assert selected_rec.get("rank") == 1
    assert selected_rec.get("validation_status") == "VALID"
    assert selected_rec.get("utility_score", 0.0) > 0.0
    assert selected_rec.get("confidence_adjusted_score", 0.0) > 0.0
    assert "responsible_stakeholder" in selected_rec

    # 3. Verify alternatives
    alternatives = report.get("recommendation_alternatives", [])
    assert isinstance(alternatives, list)

    # 4. Verify recommendation decision trace
    rec_decision = report.get("recommendation_decision")
    assert rec_decision is not None
    assert "outcome_status" in rec_decision
    assert "selection_reason" in rec_decision
    assert "policy_version" in rec_decision

    # 5. Verify top-level report recommendation fields
    assert report.get("recommendation")
    assert report.get("recommendation_justification")
    assert report.get("recommendation_confidence", 0.0) > 0.0
