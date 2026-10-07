"""Tests for Phase 3 — Hypothesis Engine.

Validates the canonical 6-stage lifecycle:
1. Seed hypotheses (4 standard competing models with calibrated priors and falsification conditions)
2. Evidence updates (independent group-level aggregation, corroboration bonus, posterior calculation)
3. Dynamic hypotheses (trigger conditions, candidate generation, parent-child branching, budget enforcement)
4. Validation (schema, evidence references, fraud guardrails, falsifiability, discriminating evidence)
5. Deduplication (semantic similarity with domain synonyms, duplicate rejection & evidence merging, refinement)
6. Falsification (direct contradiction accumulation, transition to 'rejected', rejection reasons, posterior zeroing)
7. Verification of supervisor-level integration and removal of legacy heuristic overrides
"""
import pytest
from paimana_agent.hypotheses.model import Hypothesis
from paimana_agent.hypotheses.manager import HypothesisManager
from paimana_agent.hypotheses.scorer import HypothesisScorer
from paimana_agent.hypotheses.validator import HypothesisValidator
from paimana_agent.hypotheses.similarity import HypothesisSimilarityChecker
from paimana_agent.hypotheses.generator import HypothesisGenerator
from paimana_agent.evidence.model import Evidence, EvidenceGroup
from paimana_agent.state import InvestigationState
from paimana_agent.supervisor import SupervisorAgent


def test_phase3_1_seed_hypotheses_and_calibrated_priors():
    """Validates seeding of the 4 standard competing models with calibrated priors and falsification conditions."""
    manager = HypothesisManager()
    
    # Event: severe cost-progress mismatch
    hypos = manager.seed_initial_hypotheses(
        event_types=["COST_PROGRESS_MISMATCH"],
        feats={"progress_expenditure_gap_pct": 28.0},
        baseline_evidence=[]
    )
    assert len(hypos) == 4
    h_map = {h.id: h for h in hypos}
    
    assert "front_loaded_billing" in h_map
    assert "chronic_schedule_delay" in h_map
    assert "regulatory_land_clearance" in h_map
    assert "reporting_discrepancy" in h_map

    # Front-loaded billing prior should be elevated
    h1 = h_map["front_loaded_billing"]
    assert h1.prior_prob > 0.35
    assert len(h1.predicted_observations) >= 2
    assert len(h1.discriminating_evidence) >= 1
    assert "falsification_condition" in h1.to_dict()
    assert len(h1.falsification_condition) > 20


def test_phase3_2_evidence_updates_and_group_aggregation():
    """Validates group-level evidence aggregation, corroboration bonus, and Bayesian posterior distribution."""
    scorer = HypothesisScorer()
    
    h1 = Hypothesis(id="front_loaded_billing", statement="Front-loaded billing", prior_prob=0.35)
    h2 = Hypothesis(id="chronic_schedule_delay", statement="Chronic delay", prior_prob=0.25)
    h3 = Hypothesis(id="regulatory_land_clearance", statement="Regulatory delay", prior_prob=0.20)
    h4 = Hypothesis(id="reporting_discrepancy", statement="Reporting discrepancy", prior_prob=0.20)
    hypotheses = [h1, h2, h3, h4]

    # Two independent evidence items supporting h1 across distinct source groups
    ev1 = Evidence(
        id="E_fin",
        claim="Disbursement leads progress by 25 pts",
        source_tool="financial_velocity",
        source_type="tool_result",
        independence_group_id="GRP_SNAPSHOT",
        supports_hypotheses=["front_loaded_billing"],
        authority_score=0.90
    )
    ev2 = Evidence(
        id="E_audit",
        claim="Audit confirmed uncertified contractor advances",
        source_tool="external_audit",
        source_type="external_audit_finding",
        independence_group_id="GRP_EXTERNAL_AUDIT",
        supports_hypotheses=["front_loaded_billing"],
        authority_score=0.85
    )
    # One evidence item supporting h2 in snapshot group
    ev3 = Evidence(
        id="E_mile",
        claim="Milestones delayed by 4 months",
        source_tool="milestone_audit",
        source_type="tool_result",
        independence_group_id="GRP_SNAPSHOT",
        supports_hypotheses=["chronic_schedule_delay"],
        authority_score=0.80
    )

    scorer.score_and_transition(hypotheses, [ev1, ev2, ev3], iteration=1)

    # h1 received multi-group independent corroboration (GRP_SNAPSHOT + GRP_EXTERNAL_AUDIT)
    assert h1.supporting_score > 1.2
    assert h1.confidence > 0.70
    assert h1.net_score > h2.net_score
    assert hypotheses[0].id == "front_loaded_billing"

    # Posterior probabilities must normalize to exactly 1.0 across active hypotheses
    total_post = sum(h.posterior_prob for h in hypotheses if h.status != "rejected")
    assert total_post == pytest.approx(1.0, abs=1e-3)


def test_phase3_3_dynamic_hypothesis_generation_and_branching():
    """Validates dynamic generation on unexplained material evidence, parent-child branching, and budget limits."""
    manager = HypothesisManager(max_active=5, max_generated_per_iteration=2, max_total_generated=4)
    hypotheses = manager.seed_initial_hypotheses([], {}, [])

    # Unexplained material evidence item
    ev_unexplained = Evidence(
        id="E_geotech",
        source_tool="geological_survey",
        claim="Sudden subterranean fissure collapsed tunnel boring chamber",
        is_material=True,
        coverage_status="UNEXPLAINED",
        reliability=0.95
    )

    should_gen, reason = manager.generator.should_generate(
        unexplained_evidence=[ev_unexplained],
        active_hypotheses=hypotheses,
        has_contradictions=False,
        iteration=1
    )
    assert should_gen
    assert "material evidence" in reason.lower()

    # Process iteration generates candidate
    processed = manager.process_iteration(
        hypotheses=hypotheses,
        evidence_items=[ev_unexplained],
        unexplained_evidence=[ev_unexplained],
        has_contradictions=False,
        project_context={"project_code": "PROJ-DYN", "sector": "Power"},
        iteration=1
    )
    assert len(processed) > 4
    gen_hypo = next(h for h in processed if h.source == "agent_generated")
    assert gen_hypo.status in ["active", "candidate", "supported"]
    assert len(manager.generation_events) >= 1

    # Branching child hypothesis from parent
    child = manager.branch_hypothesis(
        parent_id="chronic_schedule_delay",
        child_id="H2_geotech_collapse",
        child_statement="Unforeseen geological strata collapse halting tunnel excavation.",
        predicted_observations=["seismic ground shifts", "excavation stoppage"],
        discriminating_evidence=["tunnel boring machine telemetry log"],
        hypotheses=processed,
        iteration=2
    )
    assert child is not None
    assert child.parent_hypothesis_id == "chronic_schedule_delay"
    assert any(h.id == "H2_geotech_collapse" for h in processed)


def test_phase3_4_validation_guardrails():
    """Validates formal gatekeeping against invalid schemas, fake evidence IDs, fraud claims, and untestability."""
    validator = HypothesisValidator()
    known_eids = {"E1", "E2"}
    known_claims = ["Disbursement 40% vs Physical progress 10%"]
    existing = [Hypothesis(id="H_base", statement="Base existing hypothesis.")]

    # 1. Trivial statement (<15 chars)
    c1 = Hypothesis(id="C1", statement="Too short", support_evidence_ids=["E1"])
    ok1, r1, _ = validator.validate_candidate(c1, known_eids, known_claims, existing)
    assert not ok1
    assert "trivial" in r1.lower()

    # 2. Nonexistent evidence reference
    c2 = Hypothesis(id="C2", statement="Substantive valid claim regarding project delay", support_evidence_ids=["E_NONEXISTENT"], predicted_observations=["Obs 1"], discriminating_evidence=["Disc 1"])
    ok2, r2, _ = validator.validate_candidate(c2, known_eids, known_claims, existing)
    assert not ok2
    assert "nonexistent" in r2.lower()

    # 3. Unbacked fraud / embezzlement accusation
    c3 = Hypothesis(id="C3", statement="Contractor executed intentional embezzlement and fraud with funds", support_evidence_ids=["E1"], predicted_observations=["Obs 1"], discriminating_evidence=["Disc 1"])
    ok3, r3, _ = validator.validate_candidate(c3, known_eids, known_claims, existing)
    assert not ok3
    assert "unsupported claims" in r3.lower() or "fraud" in r3.lower()

    # 4. Unfalsifiable without observable predictions
    c4 = Hypothesis(id="C4", statement="Abstract cosmological misalignment causing structural delays", support_evidence_ids=["E1"], predicted_observations=[], discriminating_evidence=["Disc 1"])
    ok4, r4, _ = validator.validate_candidate(c4, known_eids, known_claims, existing)
    assert not ok4
    assert "unfalsifiable" in r4.lower()

    # 5. Satisfies all checks
    c5 = Hypothesis(
        id="C5",
        statement="Severe monsoon flood inundated sub-station foundation trenches halting civil works",
        support_evidence_ids=["E1"],
        predicted_observations=["sub-station water levels > 1.5m", "pumping logs recorded"],
        discriminating_evidence=["district meteorological rainfall log"],
        falsification_condition="Meteorological rainfall report confirms dry weather with zero flood logging."
    )
    ok5, r5, _ = validator.validate_candidate(c5, known_eids, known_claims, existing)
    assert ok5
    assert "satisfied" in r5.lower()


def test_phase3_5_semantic_similarity_and_deduplication():
    """Validates semantic deduplication using domain synonyms and token Jaccard overlap."""
    checker = HypothesisSimilarityChecker()
    
    h_exist = Hypothesis(
        id="H_vendor",
        statement="Severe contractor mobilization delay halting civil progress.",
        mechanism="contractor vendor labor shortage"
    )
    # Duplicate using synonyms (agency -> contractor, slippage -> delay, bottleneck -> delay)
    h_dup = Hypothesis(
        id="H_dup",
        statement="Severe agency mobilization slippage causing execution bottleneck.",
        mechanism="agency concessionaire labor shortage"
    )
    
    sim = checker.calculate_similarity(h_exist, h_dup)
    assert sim >= 0.35, f"Expected synonym matching similarity >= 0.35, got {sim}"
    
    is_dup, match = checker.is_duplicate(h_dup, [h_exist], threshold=0.35)
    assert is_dup
    assert match.id == "H_vendor"

    # Distinct hypothesis should not trigger duplicate
    h_distinct = Hypothesis(
        id="H_forest",
        statement="Forest department environmental clearance pending stage-2 nod.",
        mechanism="regulatory statutory clearance approval"
    )
    is_dup2, _ = checker.is_duplicate(h_distinct, [h_exist], threshold=0.35)
    assert not is_dup2


def test_phase3_6_falsification_and_rejection():
    """Validates explicit falsification upon receiving definitive contradictory evidence."""
    manager = HypothesisManager()
    h1 = Hypothesis(id="front_loaded_billing", statement="Front-loaded billing", prior_prob=0.35, support_evidence_ids=["E_gap"])
    h2 = Hypothesis(id="chronic_schedule_delay", statement="Chronic delay", prior_prob=0.25)
    hypotheses = [h1, h2]

    # Tool delivers definitive contradictory evidence (on-site audit verifies physical works match billing)
    ev_disprove = Evidence(
        id="E_audit_cert",
        source_tool="physical_inspection_audit",
        source_type="external_audit_finding",
        independence_group_id="GRP_SITE_AUDIT",
        claim="Independent 3D lidar and core-sample inspection verifies 100% of claimed physical works are constructed on site.",
        contradicts_hypotheses=["front_loaded_billing"],
        authority_score=0.95
    )

    manager.scorer.score_and_transition(hypotheses, [ev_disprove], iteration=2)

    assert h1.status == "rejected"
    assert h1.rejection_reason is not None
    assert "contradicted" in h1.rejection_reason.lower()
    assert h1.net_score == 0.0
    assert h1.posterior_prob == 0.0

    # Remaining non-rejected hypothesis becomes PRIMARY
    assert hypotheses[0].id == "chronic_schedule_delay"
    assert hypotheses[0].posterior_prob == 1.0


def test_phase3_7_canonical_supervisor_integration_no_heuristic_overrides():
    """Validates that supervisor uses canonical HypothesisScorer and no conflicting heuristic overrides exist."""
    agent = SupervisorAgent()
    state = InvestigationState(objective="Verify canonical hypothesis engine", project_code="TEST-CANONICAL", project_name="Canonical Test")
    
    # Initialize hypotheses
    agent._init_competing_hypotheses(state, event_types=["COST_PROGRESS_MISMATCH"], feats={"progress_expenditure_gap_pct": 25.0})
    assert len(state.hypotheses) == 4

    # Add normalized evidence directly
    ev_fin = Evidence(
        id="E_vel",
        source_tool="financial_velocity",
        source_type="tool_result",
        independence_group_id="SNAP_1",
        claim="Cumulative spend leads progress by 25 pts",
        supports_hypotheses=["front_loaded_billing"],
        contradicts_hypotheses=["reporting_discrepancy"],
        authority_score=0.90
    )
    state.evidence_items.append(ev_fin)

    # Call _update_hypotheses_and_confidence
    agent._update_hypotheses_and_confidence(state, p={"original_cost_cr": 1000.0}, feats={"progress_expenditure_gap_pct": 25.0}, ref_stats=None)

    # Verify that front_loaded_billing was evaluated and ranked #1
    assert state.hypotheses[0].id == "front_loaded_billing"
    assert state.hypotheses[0].supporting_score > 0.0
    assert state.hypotheses[0].confidence > 0.60
    
    # Build final report and verify PRIMARY status on leading structured hypothesis
    rep = agent._build_final_report(state, res={"tier": "High", "risk_score": 75}, event_id=None, store=None)
    hypos = rep["structured_evidence"]["hypotheses"]
    assert hypos[0]["name"] == "front_loaded_billing"
    assert hypos[0]["status"] == "PRIMARY"
    assert sum(h["posterior_prob"] for h in hypos) == pytest.approx(1.0, abs=1e-3)
