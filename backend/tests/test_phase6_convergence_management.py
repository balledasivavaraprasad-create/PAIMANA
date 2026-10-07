"""Tests for Phase 6 — Convergence Management.

Validates the canonical convergence architecture:
evidence coverage + hypothesis separation + stability + contradictions + causal support + expected information gain

And verifies:
1. Evidence Coverage: Empirical coverage across declared needs with independent source corroboration.
2. Hypothesis Separation: Margin discrimination between leading hypothesis and runner-up.
3. Hypothesis Stability & Oscillation: Trajectory stability across consecutive steps and oscillation suppression.
4. Contradiction Resolution: Blocking behavior of unresolved high/critical contradictions vs resolution.
5. Causal Support: Coupling with verified causal claim levels (Level 3/4/5) vs unverified associations.
6. Expected Information Gain & Diminishing Returns: Scientific stopping criteria replacing fixed iteration loops.
7. Reopen Policy & Hysteresis: Controlled reopening upon authoritative ground truth or material risk changes.
8. End-to-End Supervisor Integration: Stopping on convergence well before maximum iteration limits.
"""
import pytest
import time
from paimana_agent.state import InvestigationState
from paimana_agent.evidence.model import Evidence
from paimana_agent.hypotheses.model import Hypothesis
from paimana_agent.causal.models import CausalClaim
from paimana_agent.investigation.evidence_need import EvidenceNeed
from paimana_agent.investigation.candidate import ToolCandidate
from paimana_agent.investigation.budget import InvestigationBudget
from paimana_agent.investigation.convergence.models import (
    ConvergenceState,
    ConvergenceStatus,
    TerminationRecord,
    ReopenTrigger,
)
from paimana_agent.investigation.convergence.convergence_policy import ConvergencePolicy
from paimana_agent.investigation.convergence.convergence_engine import ConvergenceEngine
from paimana_agent.investigation.convergence.evidence_coverage import EvidenceCoverageEvaluator
from paimana_agent.investigation.convergence.hypothesis_separation import HypothesisSeparationEvaluator
from paimana_agent.investigation.convergence.hypothesis_stability import HypothesisStabilityEvaluator
from paimana_agent.investigation.convergence.contradiction_resolution import ContradictionResolutionEvaluator
from paimana_agent.investigation.convergence.causal_convergence import CausalConvergenceEvaluator
from paimana_agent.investigation.convergence.decision_readiness import DecisionReadinessEvaluator
from paimana_agent.investigation.convergence.diminishing_returns import DiminishingReturnsDetector
from paimana_agent.investigation.convergence.oscillation import HypothesisOscillationDetector
from paimana_agent.investigation.convergence.reopen_policy import ReopenPolicyManager
from paimana_agent.investigation.convergence.termination_trace import TerminationTraceBuilder
from paimana_agent.supervisor import SupervisorAgent
from paimana_agent.store import Store


def test_phase6_1_evidence_coverage_dimension():
    """Dimension 1: Evidence Coverage evaluates satisfied needs and source independence."""
    state = InvestigationState(objective="Coverage test", project_code="P-COV-1", project_name="Water Project")
    
    # Needs declared
    n1 = EvidenceNeed(id="N1", question="Check spend", target_hypothesis_ids=["H1"], priority=1.0, status="OPEN")
    n2 = EvidenceNeed(id="N2", question="Check delay", target_hypothesis_ids=["H1"], priority=1.0, status="OPEN")
    
    # 0 tools used, open needs remain
    cov_empty = EvidenceCoverageEvaluator.evaluate_coverage(state, open_needs=[n1, n2], total_needs=[n1, n2])
    assert cov_empty["evidence_coverage"] == 0.0
    assert not cov_empty["is_sufficient"]

    # Now add evidence with distinct independence groups
    ev1 = Evidence(
        id="EV-1",
        claim="Disbursement lead confirmed",
        source_tool="financial_velocity",
        source_system="cuf_financial",
        independence_group_id="GRP_FIN",
        authority_score=0.90,
    )
    ev2 = Evidence(
        id="EV-2",
        claim="Civil timeline slipped 8 months",
        source_tool="milestone_audit",
        source_system="cuf_mpr",
        independence_group_id="GRP_MPR",
        authority_score=0.88,
    )
    ev3 = Evidence(
        id="EV-3",
        claim="Peer agency has 2x higher delays",
        source_tool="peer_intelligence",
        source_system="peer_intel",
        independence_group_id="GRP_PEER",
        authority_score=0.85,
    )
    state.evidence_items = [ev1, ev2, ev3]
    state.evidence_groups = {"GRP_FIN": [ev1], "GRP_MPR": [ev2], "GRP_PEER": [ev3]}
    state.tools_used = ["financial_velocity", "milestone_audit", "peer_intelligence"]

    # All needs satisfied
    cov_full = EvidenceCoverageEvaluator.evaluate_coverage(state, open_needs=[], total_needs=[n1, n2])
    assert cov_full["evidence_coverage"] >= 0.85
    assert cov_full["is_sufficient"]
    assert cov_full["independent_groups_count"] == 3


def test_phase6_2_hypothesis_separation_dimension():
    """Dimension 2: Hypothesis Separation evaluates discrimination margin between competing explanations."""
    # Case A: Tightly competitive hypotheses
    h1 = Hypothesis(id="H_frontload", statement="Front-Loaded Billing", confidence=0.52)
    h2 = Hypothesis(id="H_reporting", statement="Reporting Discrepancy", confidence=0.48)
    sep_close = HypothesisSeparationEvaluator.evaluate_separation([h1, h2])
    assert sep_close["classification"] == "HIGHLY_COMPETITIVE"
    assert sep_close["is_clearly_separated"] is False
    assert sep_close["margin"] == pytest.approx(0.04, abs=0.01)
    assert sep_close["hypothesis_separation"] < 0.20

    # Case B: Clear winner with wide margin
    h1.confidence = 0.85
    h2.confidence = 0.30
    sep_clear = HypothesisSeparationEvaluator.evaluate_separation([h1, h2])
    assert sep_clear["classification"] == "CLEARLY_SEPARATED"
    assert sep_clear["is_clearly_separated"] is True
    assert sep_clear["margin"] >= 0.50
    assert sep_clear["hypothesis_separation"] >= 0.80


def test_phase6_3_hypothesis_stability_and_oscillation_dimension():
    """Dimension 3: Hypothesis Stability verifies trajectory stabilization and detects flip-flop oscillations."""
    # Step A: Trajectory stabilization across consecutive iterations
    history = [
        {"H1": 0.50, "H2": 0.45},
        {"H1": 0.78, "H2": 0.35},
        {"H1": 0.79, "H2": 0.34},
        {"H1": 0.80, "H2": 0.34},
        {"H1": 0.80, "H2": 0.33},
    ]
    stab = HypothesisStabilityEvaluator.evaluate_stability(history, stability_threshold=0.05, required_stable_steps=2)
    assert stab["is_stable"] is True
    assert stab["hypothesis_stability"] >= 0.85
    assert stab["consecutive_stable_steps"] >= 2

    # Step B: Oscillation detection (alternating leaders with tight margins)
    leader_flips = ["H1", "H2", "H1", "H2"]
    margin_history = [0.03, 0.04, 0.02, 0.03]
    osc = HypothesisOscillationDetector.detect_oscillation(leader_flips, margin_history, min_flips=2, narrow_margin_threshold=0.15)
    assert osc["is_oscillating"] is True
    assert osc["flip_count"] == 3
    assert osc["action_required"] == "DISCRIMINATING_EVIDENCE_NEEDED"


def test_phase6_4_contradiction_resolution_dimension():
    """Dimension 4: Contradiction Resolution ensures unresolved critical/high discrepancies block convergence."""
    # Subtest 4a: Active critical contradiction blocks termination
    class DummyContradiction:
        def __init__(self, sev, res=False):
            self.severity = sev
            self.resolved = res

    c_crit = DummyContradiction("CRITICAL", res=False)
    contra_eval = ContradictionResolutionEvaluator.evaluate_contradictions([c_crit])
    assert contra_eval["has_blocking_contradictions"] is True
    assert contra_eval["unresolved_critical"] == 1
    assert contra_eval["contradiction_resolution"] < 0.50

    # Subtest 4b: Resolving contradiction unblocks convergence
    c_crit.resolved = True
    contra_eval_resolved = ContradictionResolutionEvaluator.evaluate_contradictions([c_crit])
    assert contra_eval_resolved["has_blocking_contradictions"] is False
    assert contra_eval_resolved["unresolved_critical"] == 0
    assert contra_eval_resolved["contradiction_resolution"] == 1.0


def test_phase6_5_causal_support_dimension():
    """Dimension 5: Causal Support binds directly to verified causal claims (Level 3/4/5)."""
    state = InvestigationState(objective="Causal test", project_code="P-CAUSAL-1", project_name="Power Grid")
    
    # Level 1 Association (Insufficient for causal convergence)
    c1 = CausalClaim(
        id="CC-1",
        proposed_cause="Contractor Shortage",
        effect="Schedule Slippage",
        causal_level="LEVEL_1_ASSOCIATION",
        causal_support_score=0.30,
        status="ACTIVE"
    )
    state.causal_claims = [c1]
    res_l1 = CausalConvergenceEvaluator.evaluate_causal_convergence(state)
    assert res_l1["causal_status"] == "CAUSALLY_UNRESOLVED"
    assert res_l1["is_causally_supported"] is False
    assert res_l1["causal_support"] < 0.50

    # Level 4 Strong Causal Support (Verified mechanism + temporal precedence + non-spuriousness)
    c4 = CausalClaim(
        id="CC-4",
        proposed_cause="Uncertified Advance Disbursement",
        effect="Progress-Expenditure Decoupling",
        causal_level="LEVEL_4_STRONG_CAUSAL_SUPPORT",
        causal_support_score=0.92,
        status="SUPPORTED"
    )
    state.causal_claims = [c4]
    res_l4 = CausalConvergenceEvaluator.evaluate_causal_convergence(state)
    assert res_l4["causal_status"] == "CAUSALLY_SUPPORTED"
    assert res_l4["is_causally_supported"] is True
    assert res_l4["causal_support"] >= 0.85


def test_phase6_6_expected_information_gain_and_diminishing_returns():
    """Dimension 6: Expected Information Gain & Diminishing Returns replace fixed iteration logic."""
    engine = ConvergenceEngine(ConvergencePolicy.for_severity("MEDIUM"))
    state = InvestigationState(objective="EIG test", project_code="P-EIG-1", project_name="Metro Link")
    state.tools_used = ["financial_velocity", "milestone_audit", "peer_intelligence"]
    
    # Setup diminishing returns trajectory
    engine.gain_history = [0.35, 0.18, 0.02, 0.015, 0.01]
    
    # Candidates have negligible expected information gain (< policy threshold 0.04)
    cand_low = ToolCandidate(
        tool_name="shap_attribution",
        expected_information_gain=0.015,
        net_utility=0.01,
        eligible=True
    )
    
    conv_state, term_record = engine.evaluate(
        state=state,
        candidates=[cand_low],
        open_needs=[],
        iteration=3
    )
    
    # The agent terminates cleanly due to diminishing returns / low expected information gain
    assert conv_state.should_terminate is True
    assert conv_state.status == ConvergenceStatus.NO_HIGH_VALUE_EVIDENCE_AVAILABLE
    assert conv_state.termination_reason == "NO_HIGH_VALUE_TOOL_REMAINING"
    assert term_record is not None
    assert term_record.best_remaining_tool == "shap_attribution"


def test_phase6_7_reopen_policy_hysteresis():
    """Verifies ReopenPolicyManager prevents noisy reopenings while honoring authoritative overrides."""
    prev_term = TerminationRecord(
        status=ConvergenceStatus.CONVERGED,
        evidence_coverage=0.90,
        hypothesis_separation=0.85,
        hypothesis_stability=0.92,
        contradictions_remaining=0,
        causal_support=0.88,
        decision_readiness=0.85,
        iterations=3,
        tool_calls=3,
    )

    # 1. Minor low-materiality addition -> suppressed by hysteresis
    trig_minor = ReopenTrigger(
        trigger_type="NEW_AUTHORITATIVE_EVIDENCE",
        severity="LOW",
        materiality=0.20,
        description="Minor typo correction in progress report"
    )
    can_reopen_minor, rat_minor = ReopenPolicyManager.should_reopen(prev_term, trig_minor)
    assert can_reopen_minor is False
    assert "Suppressed" in rat_minor

    # 2. Material risk escalation (+25 pts) -> cleanly reopens
    trig_risk = ReopenTrigger(
        trigger_type="MATERIAL_RISK_CHANGE",
        severity="HIGH",
        materiality=25.0,
        description="Abrupt 25-point spike in expenditure velocity anomaly"
    )
    can_reopen_risk, rat_risk = ReopenPolicyManager.should_reopen(prev_term, trig_risk)
    assert can_reopen_risk is True
    assert "Reopened" in rat_risk

    # 3. Direct causal contradiction -> cleanly reopens
    trig_contra = ReopenTrigger(
        trigger_type="CAUSAL_CONTRADICTION",
        severity="CRITICAL",
        materiality=1.0,
        description="Contractor audit shows zero frontloading; delay was purely statutory ROW clearance"
    )
    can_reopen_contra, rat_contra = ReopenPolicyManager.should_reopen(prev_term, trig_contra)
    assert can_reopen_contra is True
    assert "Reopened" in rat_contra


def test_phase6_8_full_supervisor_convergence_integration():
    """End-to-End: SupervisorAgent converges dynamically on scientific sufficiency, stopping early."""
    supervisor = SupervisorAgent()
    store = Store()
    
    project_data = {
        "project_code": "P-CONV-E2E",
        "project_name": "State Highway Expansion",
        "sector": "Roads & Highways",
        "implementing_agency": "NHAI",
        "original_cost_cr": 450.0,
        "revised_cost_cr": 580.0,
        "cumulative_expenditure_cr": 410.0,
        "physical_progress_pct": 38.0,
        "original_completion_date": "2024-03-31",
        "revised_completion_date": "2026-12-31",
    }
    
    res = {
        "project_code": "P-CONV-E2E",
        "project_name": "State Highway Expansion",
        "composite_risk_score": 78.5,
        "risk_level": "HIGH",
    }
    
    events = [
        {"type": "EXPENDITURE_VELOCITY_ANOMALY", "severity": "HIGH", "project_code": "P-CONV-E2E"}
    ]
    
    feats = {
        "cost_overrun_pct": 28.8,
        "progress_expenditure_gap_pct": 53.1,
        "schedule_slippage_months": 33.0,
        "composite_risk_score": 78.5,
    }
    
    # Request up to 10 steps; the dynamic convergence engine should stop gracefully well before 10 steps!
    report = supervisor.run_investigation(
        store=store,
        p=project_data,
        res=res,
        drivers=["progress_expenditure_gap_pct", "schedule_slippage_months"],
        events=events,
        feats=feats,
        max_steps=10
    )
    
    steps = report["supervisor_steps"]
    total_steps = len(steps)
    
    # Proves convergence stopped the loop early rather than blindly executing all 10 steps!
    assert total_steps < 10, f"Expected early convergence termination before 10 steps, but ran {total_steps} steps."
    assert report["termination_reason"] in ["SUFFICIENT_EVIDENCE", "NO_HIGH_VALUE_TOOL_REMAINING", "CONVERGED"]
    assert report.get("convergence_dashboard") is not None
    assert report.get("termination_record") is not None
