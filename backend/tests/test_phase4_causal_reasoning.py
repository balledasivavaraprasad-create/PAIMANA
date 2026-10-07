"""Tests for Phase 4 — Causal Reasoning.

Validates the canonical 7-stage causal pipeline:
hypothesis → mechanism → temporal reasoning → confounders → alternatives → falsification → causal support

And enforces the three fundamental epistemological invariants:
1. SHAP ≠ causality (model-derived sensitivity cannot establish ground-truth physical causality)
2. historical precedent ≠ current intervention evidence (cross-project memory cannot substitute for current project verification)
3. heuristic score ≠ probability (causal claim levels and evidential support are distinct from heuristic numbers)
"""
import pytest
import time
from paimana_agent.causal import (
    CausalEngine,
    CausalOntology,
    TemporalReasoner,
    ConfounderDetector,
    CounterfactualAnalyzer,
    CausalTraceBuilder,
)
from paimana_agent.causal.models import (
    CausalClaim,
    CausalMechanism,
    TemporalRelation,
    Confounder,
)
from paimana_agent.evidence.model import Evidence
from paimana_agent.hypotheses.model import Hypothesis
from paimana_agent.state import InvestigationState
from paimana_agent.supervisor import SupervisorAgent


def test_phase4_1_hypothesis_to_mechanism_verification():
    """Stage 1 & 2: Validates mechanism lookup and intermediate transmission chain verification."""
    # Match canonical mechanism from ontology
    mech = CausalOntology.match_mechanism_for_cause("Contractor Resource Shortage")
    assert mech is not None
    assert mech.id == "M_CONTRACTOR_EXECUTION"
    assert "machinery_equipment_deployment" in mech.intermediate_variables
    assert "physical_progress" in mech.intermediate_variables

    # Case A: Intermediate transmission chain is missing from observed evidence
    score_unsupported = CausalEngine.evaluate_mechanism_links(
        mechanism=mech,
        observations={},
        facts_text="General progress delay observed across work packages."
    )
    assert score_unsupported <= 0.30
    assert mech.is_validated is False

    # Case B: Intermediate transmission variables are observationally verified
    facts_rich = (
        "Subcontractor machinery equipment deployment is 40% below sanctioned plan. "
        "Skilled labor density on active workfronts dropped to 2 workers per km. "
        "Workfront execution rate and site productivity rate stalled."
    )
    score_supported = CausalEngine.evaluate_mechanism_links(
        mechanism=mech,
        observations={},
        facts_text=facts_rich
    )
    assert score_supported >= 0.60
    assert mech.is_validated is True


def test_phase4_2_temporal_reasoning_and_inversion_detection():
    """Stage 3: Validates temporal precedence and temporal inversion penalty."""
    now = time.time()
    day = 86400.0

    # 1. Valid chronological ordering: Cause precedes effect
    cause_t = now - (60.0 * day)
    effect_t = now - (10.0 * day)
    rel_valid = TemporalReasoner.evaluate_temporal_order(
        cause_event="Environmental Stay Order",
        effect_event="Physical Progress Stoppage",
        cause_timestamp=cause_t,
        effect_timestamp=effect_t
    )
    assert rel_valid.temporal_consistency is True
    assert rel_valid.lag_days > 0
    assert TemporalReasoner.calculate_temporal_support(rel_valid) >= 0.70

    # 2. Temporal Inversion: Effect occurred before candidate cause
    # Progress stalled 50 days ago, but environmental clearance hurdle only arose 10 days ago!
    rel_inverted = TemporalReasoner.evaluate_temporal_order(
        cause_event="Environmental Clearance Hurdle",
        effect_event="Physical Progress Stoppage",
        cause_timestamp=effect_t,
        effect_timestamp=cause_t
    )
    assert rel_inverted.temporal_consistency is False
    assert rel_inverted.lag_days < 0
    assert "temporal inversion" in rel_inverted.inconsistency_reason.lower()
    
    # Claim evaluation must collapse temporal support and severely penalize
    claim = CausalEngine.evaluate_causal_claim(
        claim_id="CC-INVERT-TEST",
        proposed_cause="Environmental Clearance Hurdle",
        observed_effect="Physical Progress Stoppage",
        observations={},
        evidence_items=[],
        cause_timestamp=effect_t,
        effect_timestamp=cause_t
    )
    assert claim.temporal_support <= 0.10
    assert claim.contradiction_penalty >= 0.50
    assert claim.causal_level == "LEVEL_1_ASSOCIATION"
    assert claim.status in ["REJECTED", "WEAKENED"]


def test_phase4_3_confounder_detection_and_gating():
    """Stage 4: Validates confounder detection, penalty calculation, and Level 4 gating."""
    # Observations containing signs of systemic funding/liquidity shortage
    obs = {
        "budget": "State escrow allocation delayed",
        "bills pending": "Running account bills unpaid for 90 days",
        "disbursement": "Only 10% released"
    }
    evidence_claims = ["Contractor running bills pending unpaid beyond statutory SLA"]

    confounders = ConfounderDetector.detect_confounders(
        proposed_cause="Contractor Execution Bottleneck",
        observed_effect="Schedule Slippage",
        observations=obs,
        evidence_claims=evidence_claims
    )
    assert len(confounders) >= 1
    conf_fund = next((c for c in confounders if "Funding" in c.variable or "Liquidity" in c.variable), None)
    assert conf_fund is not None
    assert conf_fund.resolved is False
    assert conf_fund.resolution_evidence_needed is not None

    penalty = ConfounderDetector.calculate_confounder_penalty(confounders)
    assert penalty >= 0.10

    # Unresolved confounder must prevent elevation to Level 4 Strong Causal Support
    claim = CausalEngine.evaluate_causal_claim(
        claim_id="CC-CONF-TEST",
        proposed_cause="Contractor Execution Bottleneck",
        observed_effect="Schedule Slippage",
        observations=obs,
        evidence_items=[{"id": "E1", "claim": "Running bills pending", "independence_group_id": "GRP_1"}],
        cause_timestamp=time.time() - 86400 * 30,
        effect_timestamp=time.time() - 86400 * 5
    )
    assert "Funding / Liquidity Shortage" in claim.unresolved_confounders
    assert claim.causal_level != "LEVEL_4_STRONG_CAUSAL_SUPPORT"


def test_phase4_4_alternative_explanations_and_conflict_status():
    """Stage 5: Validates that competing alternatives are retained when evidence is insufficiently separated."""
    # Two competing explanations with closely matched scores
    c1 = CausalClaim(
        id="C1",
        effect="Delay",
        proposed_cause="Contractor Resource Shortage",
        causal_support_score=0.62,
        causal_level="LEVEL_3_MECHANISTIC_SUPPORT",
        status="PLAUSIBLE"
    )
    c2 = CausalClaim(
        id="C2",
        effect="Delay",
        proposed_cause="Inter-Agency Clearance Delay",
        causal_support_score=0.58,
        causal_level="LEVEL_3_MECHANISTIC_SUPPORT",
        status="PLAUSIBLE"
    )

    top, alts, status, summary = CausalEngine.compare_competing_explanations([c1, c2])
    assert top.id == "C1"
    assert len(alts) == 1
    assert alts[0].id == "C2"
    # Close margin (0.04 < 0.15) must result in UNRESOLVED_CAUSAL_CONFLICT
    assert status == "UNRESOLVED_CAUSAL_CONFLICT"
    assert "Unresolved Causal Conflict" in summary
    assert "Both must be retained" in summary


def test_phase4_5_falsification_conditions_and_demotion():
    """Stage 6: Validates that observing explicit falsifying conditions demotes the causal claim."""
    mech = CausalOntology.match_mechanism_for_cause("Contractor Resource Shortage")
    assert mech is not None

    # Facts contain explicit falsifiers: contractor resource deployment is normal/high on site
    facts_falsifying = (
        "Independent site inspection confirms resource deployment at or above contract baseline. "
        "Heavy earthmoving plant and machinery fully mobilized."
    )
    has_falsified, falsifiers = CausalEngine.check_falsification_criteria(
        mechanism=mech,
        facts_text=facts_falsifying,
        observations={}
    )
    assert has_falsified is True
    assert len(falsifiers) >= 1

    claim = CausalEngine.evaluate_causal_claim(
        claim_id="CC-FALSIFIED",
        proposed_cause="Contractor Resource Shortage",
        observed_effect="Schedule Delay",
        observations={},
        evidence_items=[{"id": "E_audit", "claim": facts_falsifying, "independence_group_id": "AUDIT_1"}]
    )
    assert claim.contradiction_penalty >= 0.50
    assert claim.causal_level in ["LEVEL_0_OBSERVATION", "LEVEL_1_ASSOCIATION"]
    assert claim.status in ["WEAKENED", "REJECTED"]
    assert len(claim.falsification_notes) >= 1


def test_phase4_6_invariant_shap_does_not_equal_causality():
    """Invariant 1: Enforces that SHAP / model-derived attribution alone can NEVER claim causality."""
    ev_shap_only = [
        {
            "id": "E_shap_1",
            "claim": "SHAP feature importance permutation: progress_expenditure_gap +0.42",
            "source_tool": "shap_attribution",
            "evidence_type": "MODEL_DERIVED",
            "independence_group_id": "ML_PIPELINE"
        },
        {
            "id": "E_shap_2",
            "claim": "Model tree split attribution: original_cost_cr +0.28",
            "source_tool": "shap_attribution",
            "evidence_type": "MODEL_DERIVED",
            "independence_group_id": "ML_PIPELINE"
        }
    ]

    claim = CausalEngine.evaluate_causal_claim(
        claim_id="CC-SHAP-INVARIANT",
        proposed_cause="Front-Loaded Billing Decoupling",
        observed_effect="Cost Overrun Escalation",
        observations={"shap_attribution": {"shap_lines": ["gap +0.42", "cost +0.28"]}},
        evidence_items=ev_shap_only
    )

    # Invariant assertion: Capped at Level 1, cannot be Level 3, 4, or 5
    assert claim.causal_level == "LEVEL_1_ASSOCIATION"
    assert claim.causal_level != "LEVEL_3_MECHANISTIC_SUPPORT"
    assert claim.causal_level != "LEVEL_4_STRONG_CAUSAL_SUPPORT"
    assert claim.causal_level != "LEVEL_5_INTERVENTION_SUPPORTED"
    assert claim.status == "CANDIDATE"
    assert any("shap attribution reflects ml model" in note.lower() for note in claim.falsification_notes)


def test_phase4_7_invariant_historical_precedent_does_not_equal_current_intervention():
    """Invariant 2: Enforces that cross-project historical precedents cannot elevate current claims to Level 5."""
    # An ongoing anomaly with retrieved memory precedents from OTHER projects
    obs_with_memory = {
        "memory_retrieval": {
            "successful_precedents": [
                {"project_code": "OTHER-PROJ-99", "action": "Joint Financial Audit Taskforce", "outcome": "Overbilling stopped"}
            ]
        },
        "project_history": {"interventions": []}  # No verified intervention on THIS project yet
    }
    ev_empirical = [
        {"id": "E1", "claim": "Disbursement leads progress by 25 pts", "independence_group_id": "FIN_1"},
        {"id": "E2", "claim": "Milestone delivery stalled at 10%", "independence_group_id": "MILE_1"}
    ]

    claim = CausalEngine.evaluate_causal_claim(
        claim_id="CC-PRECEDENT-INVARIANT",
        proposed_cause="Front-Loaded Billing",
        observed_effect="Cost-Progress Mismatch",
        observations=obs_with_memory,
        evidence_items=ev_empirical,
        is_intervention_verified=False  # Must be False for current un-intervened project
    )

    # Invariant assertion: Cannot be Level 5 Intervention Supported
    assert claim.causal_level != "LEVEL_5_INTERVENTION_SUPPORTED"
    assert any("does not substitute for empirical site verification" in note for note in claim.counterfactual_notes)


def test_phase4_8_invariant_heuristic_score_does_not_equal_probability_and_supervisor_integration():
    """Invariant 3 & Supervisor Integration: Verifies disciplined causal claim tracking and separation from raw heuristic scores."""
    agent = SupervisorAgent()
    state = InvestigationState(objective="Causal Verification", project_code="CAUSAL-INT-1", project_name="Expressway Package 4")
    
    # Initialize hypotheses
    agent._init_competing_hypotheses(state, event_types=["COST_PROGRESS_MISMATCH"], feats={"progress_expenditure_gap_pct": 25.0})
    
    # Add empirical evidence items
    ev_fin = Evidence(
        id="E_fin",
        claim="Disbursement leads progress by 25 percentage points with uncertified advance",
        source_tool="financial_velocity",
        source_type="tool_result",
        independence_group_id="SNAP_FIN",
        supports_hypotheses=["front_loaded_billing"],
        authority_score=0.90
    )
    ev_audit = Evidence(
        id="E_audit",
        claim="Independent site verification confirms uncertified contractor advances pending",
        source_tool="external_audit",
        source_type="external_audit_finding",
        independence_group_id="GRP_AUDIT",
        supports_hypotheses=["front_loaded_billing"],
        authority_score=0.85
    )
    state.evidence_items.extend([ev_fin, ev_audit])
    state.observations["financial_velocity"] = {"progress_expenditure_gap_pct": 25.0}

    # Run hypothesis update to score canonical hypotheses with evidence
    agent._update_hypotheses_and_confidence(state, p={"original_cost_cr": 1200.0}, feats={"progress_expenditure_gap_pct": 25.0}, ref_stats=None)

    # Run causal evaluation
    agent._run_causal_evaluation(state, p={"original_cost_cr": 1200.0}, feats={"progress_expenditure_gap_pct": 25.0}, ref_stats=None)

    assert len(state.causal_claims) == 4
    top_claim = state.leading_causal_claim
    assert top_claim is not None
    assert "front_loaded_billing" in top_claim["proposed_cause"].lower() or "billing" in top_claim["proposed_cause"].lower()
    
    # Epistemic claim level is categorical, not a raw heuristic number
    assert top_claim["causal_level"] in [
        "LEVEL_1_ASSOCIATION",
        "LEVEL_2_TEMPORAL_ASSOCIATION",
        "LEVEL_3_MECHANISTIC_SUPPORT",
        "LEVEL_4_STRONG_CAUSAL_SUPPORT"
    ]
    # Invariant: Causal support score is bounded in [0.05, 1.0], not raw '25.0' gap
    assert 0.05 <= top_claim["causal_support_score"] <= 1.0
    assert state.causal_decision_trace is not None
