"""Tests for Phase 5 — Dynamic Tool Selection.

Validates the canonical 8-stage dynamic tool selection pipeline:
hypotheses → evidence gaps → evidence needs → tool candidates → information value → reliability → cost → best next tool

And verifies:
1. Dynamic derivation of evidence needs from hypotheses, unverified mechanisms, confounders, and gaps.
2. Tool candidate prerequisite and eligibility gating (authorization, stores, circuit breakers).
3. Information Value (IV) and Hypothesis Discrimination Power (DP) scaling with epistemic uncertainty.
4. First-class separation of Execution Reliability from Evidence Reliability.
5. Multi-criteria cost accounting, redundancy discounting, and budget affordability governance.
6. Optimal best-next-tool selection, convergence stopping, and auditable selection history.
7. Full end-to-end SupervisorAgent dynamic investigation loop.
"""
import pytest
import time
from paimana_agent.state import InvestigationState
from paimana_agent.supervisor import SupervisorAgent
from paimana_agent.evidence.model import Evidence
from paimana_agent.hypotheses.model import Hypothesis
from paimana_agent.causal.models import CausalMechanism
from paimana_agent.investigation.evidence_need import EvidenceNeed
from paimana_agent.investigation.candidate import ToolCandidate, ToolSelectionRecord
from paimana_agent.investigation.gap_analyzer import EvidenceGapAnalyzer
from paimana_agent.investigation.utility import ToolUtilityEvaluator
from paimana_agent.investigation.selector import DynamicInformationSeekingSelector
from paimana_agent.investigation.discriminator import HypothesisDiscriminator
from paimana_agent.investigation.budget import InvestigationBudget, InvestigationPhase
from paimana_agent.tools import ToolRegistry, ToolDefinition
from paimana_agent.store import Store
from paimana_agent.reliability.models import ToolResult, ToolResultStatus, ToolReliabilityProfile


def test_phase5_1_hypotheses_and_evidence_gaps_to_evidence_needs():
    """Stage 1-3: Derives prioritized EvidenceNeed objects from active hypotheses, missing mechanisms, and confounders."""
    analyzer = EvidenceGapAnalyzer()
    state = InvestigationState(objective="Triage", project_code="P-DYNA-1", project_name="Highway 1")
    
    # Active competing hypotheses
    h1 = Hypothesis(id="front_loaded_billing", statement="Front-Loaded Billing", confidence=0.52)
    h2 = Hypothesis(id="reporting_discrepancy", statement="Reporting Discrepancy", confidence=0.48)
    state.hypotheses = [h1, h2]
    state.tools_used = ["financial_velocity"]

    # Stage 2: Missing causal mechanism transmission links
    state.causal_claims = [
        {
            "id": "CC-1",
            "hypothesis_id": "front_loaded_billing",
            "proposed_cause": "Front-Loaded Billing",
            "status": "PLAUSIBLE",
            "mechanism": {
                "id": "M_FRONT_LOADED_BILLING",
                "links_verified": {
                    "disbursement_velocity": True,
                    "milestone_certification_gap": False,
                    "contractor_cashflow_frontloading": False
                }
            }
        }
    ]

    # Stage 2: Unresolved confounder
    state.confounders = [
        {"variable": "monsoon_heavy_rainfall", "affects_claim": "Front-Loaded Billing", "resolved": False}
    ]

    # Stage 2: Unexplained material evidence
    state.unexplained_evidence = [
        Evidence(id="E_unexp_1", claim="Unusual payment voucher spike in month 4 without MPR entry", source_tool="audit_log")
    ]

    # Stage 3: Analyze needs
    needs = analyzer.analyze_needs(
        state=state,
        p={"physical_progress_pct": 20.0, "original_cost_cr": 800.0},
        feats={"progress_expenditure_gap_pct": 22.0},
        event_types=["COST_PROGRESS_MISMATCH"]
    )

    need_ids = {n.id for n in needs}
    assert "need_financial_velocity" in need_ids
    assert "need_discriminate_front_loaded_billing_reporting_discrepancy" in need_ids
    assert "need_mech_transmission_front_loaded_billing" in need_ids
    assert "need_confounder_monsoon_heavy_rainfall" in need_ids
    assert "need_unexplained_evidence_resolution" in need_ids

    # Verify priority and discrimination power are correctly calibrated
    mech_need = next(n for n in needs if n.id == "need_mech_transmission_front_loaded_billing")
    assert mech_need.discrimination_power >= 0.85
    assert mech_need.priority >= 0.85
    assert "financial_audit" in mech_need.required_evidence_types


def test_phase5_2_tool_candidates_evaluation_and_gating():
    """Stage 4: Evaluates tool candidates and validates prerequisite, authorization, and circuit breaker gating."""
    evaluator = ToolUtilityEvaluator()
    state = InvestigationState(objective="Triage", project_code="P-DYNA-2", project_name="Highway 2")
    open_needs = [
        EvidenceNeed(
            id="need_fin",
            question="Audit billing velocity",
            required_evidence_types=["financial_audit", "disbursement_velocity"],
            target_hypothesis_ids=["front_loaded_billing"],
            priority=0.90,
            status="OPEN"
        )
    ]

    # Tool A: Standard eligible tool
    t_normal = ToolDefinition(
        name="tool_normal",
        purpose="Normal tool",
        evidence_types_generated=["financial_audit"],
        prerequisites=[],
        authorization_required="read_only"
    )
    cand_normal = evaluator.evaluate_candidate(t_normal, state, open_needs)
    assert cand_normal.eligible is True
    assert len(cand_normal.ineligibility_reasons) == 0

    # Tool B: Missing database store prerequisite
    t_store = ToolDefinition(
        name="tool_store",
        purpose="Store tool",
        evidence_types_generated=["financial_audit"],
        prerequisites=["store"]
    )
    cand_store = evaluator.evaluate_candidate(t_store, state, open_needs, store_available=False)
    assert cand_store.eligible is False
    assert any("store is unavailable" in r for r in cand_store.ineligibility_reasons)

    # Tool C: Unauthorized privileged tool
    t_priv = ToolDefinition(
        name="tool_priv",
        purpose="Privileged tool",
        evidence_types_generated=["financial_audit"],
        authorization_required="privileged"
    )
    cand_priv = evaluator.evaluate_candidate(t_priv, state, open_needs, caller_authorization="read_only")
    assert cand_priv.eligible is False
    assert any("elevated authorization" in r for r in cand_priv.ineligibility_reasons)

    # Tool D: Open Circuit Breaker
    class DummyBreaker:
        def can_execute(self):
            return False
    t_breaker = ToolDefinition(
        name="tool_broken",
        purpose="Failing tool with open circuit breaker",
        evidence_types_generated=["financial_audit"]
    )
    t_breaker.circuit_breaker = DummyBreaker()
    cand_breaker = evaluator.evaluate_candidate(t_breaker, state, open_needs)
    assert cand_breaker.eligible is False
    assert any("Circuit breaker is OPEN" in r for r in cand_breaker.ineligibility_reasons)


def test_phase5_3_information_value_and_uncertainty_scaling():
    """Stage 5: Verifies that Information Value and Discrimination Power scale dynamically with hypothesis uncertainty."""
    discriminator = HypothesisDiscriminator()
    open_needs = [
        EvidenceNeed(
            id="need_disc",
            question="Discriminate causes",
            required_evidence_types=["financial_audit"],
            target_hypothesis_ids=["h1", "h2"],
            priority=0.90,
            discrimination_power=0.90,
            status="OPEN"
        )
    ]
    t_def = ToolDefinition(
        name="financial_auditor",
        purpose="Financial audit",
        evidence_types_generated=["financial_audit"],
        hypothesis_domains=["h1", "h2"],
        discrimination_targets=[("h1", "h2")]
    )

    # Case A: High uncertainty (top hypotheses closely contested 0.51 vs 0.49)
    state_ambiguous = InvestigationState(objective="Triage", project_code="P-DYNA-3A", project_name="Highway 3A")
    state_ambiguous.hypotheses = [
        Hypothesis(id="h1", confidence=0.51, status="active"),
        Hypothesis(id="h2", confidence=0.49, status="active")
    ]
    gain_high_unc, disc_high_unc, _ = discriminator.evaluate_tool_information_gain(
        t_def, open_needs, state_ambiguous.hypotheses, state_ambiguous
    )

    # Case B: Low uncertainty (hypothesis 1 is already clear winner 0.85 vs 0.15)
    state_resolved = InvestigationState(objective="Triage", project_code="P-DYNA-3B", project_name="Highway 3B")
    state_resolved.hypotheses = [
        Hypothesis(id="h1", confidence=0.85, status="active"),
        Hypothesis(id="h2", confidence=0.15, status="active")
    ]
    gain_low_unc, disc_low_unc, _ = discriminator.evaluate_tool_information_gain(
        t_def, open_needs, state_resolved.hypotheses, state_resolved
    )

    # Information gain must be strictly higher under epistemic ambiguity
    assert gain_high_unc > gain_low_unc
    assert disc_high_unc >= 0.90


def test_phase5_4_reliability_separation_execution_vs_evidence():
    """Stage 6: Verifies first-class separation of execution reliability from evidence reliability."""
    evaluator = ToolUtilityEvaluator()
    state = InvestigationState(objective="Triage", project_code="P-DYNA-4", project_name="Highway 4")
    open_needs = [
        EvidenceNeed(
            id="need_test",
            question="Audit physical site",
            required_evidence_types=["site_inspection"],
            priority=0.85,
            status="OPEN"
        )
    ]

    # Tool 1: Clean high reliability
    t_clean = ToolDefinition(
        name="tool_clean",
        purpose="Reliable sensor",
        evidence_types_generated=["site_inspection"],
        source_authority=0.90
    )
    prof_clean = ToolReliabilityProfile(
        tool_name="tool_clean",
        successful_calls=100,
        total_calls=100,
        data_completeness=0.95,
        data_freshness=0.95,
        useful_evidence_rate=0.98,
        false_success_rate=0.01
    )
    t_clean.reliability_profile = prof_clean

    # Tool 2: High execution uptime (0.99) but poor evidence reliability (0.45 due to high false success and empty payloads)
    t_noisy = ToolDefinition(
        name="tool_noisy",
        purpose="Unreliable sensor",
        evidence_types_generated=["site_inspection"],
        source_authority=0.90
    )
    prof_noisy = ToolReliabilityProfile(
        tool_name="tool_noisy",
        successful_calls=99,
        total_calls=100,
        data_completeness=0.40,
        data_freshness=0.50,
        useful_evidence_rate=0.40,
        false_success_rate=0.25
    )
    t_noisy.reliability_profile = prof_noisy

    cand_clean = evaluator.evaluate_candidate(t_clean, state, open_needs)
    cand_noisy = evaluator.evaluate_candidate(t_noisy, state, open_needs)

    # Assert separated reliability metrics are tracked
    assert cand_clean.execution_reliability >= 0.95
    assert cand_clean.evidence_reliability >= 0.85
    assert cand_noisy.execution_reliability >= 0.95
    assert cand_noisy.evidence_reliability <= 0.60

    # Net utility of the clean tool must be significantly higher
    assert cand_clean.net_utility > cand_noisy.net_utility
    assert cand_clean.net_utility - cand_noisy.net_utility >= 0.05


def test_phase5_5_cost_latency_redundancy_and_budget_governance():
    """Stage 7: Verifies multi-criteria cost accounting, redundancy discounting, and budget affordability gating."""
    evaluator = ToolUtilityEvaluator()
    state = InvestigationState(objective="Triage", project_code="P-DYNA-5", project_name="Highway 5")
    open_needs = [
        EvidenceNeed(
            id="need_fin",
            question="Audit bills",
            required_evidence_types=["financial_audit"],
            priority=0.85,
            status="OPEN"
        )
    ]

    t_def = ToolDefinition(
        name="heavy_audit_tool",
        purpose="Audit",
        evidence_types_generated=["financial_audit"],
        execution_cost=0.15,
        typical_latency_ms=150.0
    )

    # Fresh run on unvisited tool: no redundancy penalty
    cand_fresh = evaluator.evaluate_candidate(t_def, state, open_needs)
    assert cand_fresh.redundancy_penalty == 0.0

    # Second run after tool already executed on static data: severe redundancy penalty
    state.tools_used.append("heavy_audit_tool")
    cand_redundant = evaluator.evaluate_candidate(t_def, state, open_needs)
    assert cand_redundant.redundancy_penalty >= 0.60
    assert cand_redundant.net_utility < cand_fresh.net_utility

    # Budget affordability test via selector
    registry = ToolRegistry()
    registry.register(t_def)
    selector = DynamicInformationSeekingSelector()
    
    # Depleted budget cannot afford heavy tool
    depleted_budget = InvestigationBudget(
        investigation_id="INV-DEPLETED",
        max_estimated_cost=0.01
    )
    depleted_budget.consumed.estimated_cost = 0.01
    
    _, evaluated_candidates, _, _, _, _ = selector.select_next_step(
        state=state, p={"original_cost_cr": 500.0}, feats={}, event_types=[],
        registry=registry, budget=depleted_budget
    )
    heavy_cand = next((c for c in evaluated_candidates if c.tool_name == "heavy_audit_tool"), None)
    if heavy_cand:
        assert heavy_cand.is_affordable is False


def test_phase5_6_best_next_tool_selection_and_audit_history():
    """Stage 8: Verifies optimal best-next-tool selection, candidate ranking, and audit logging."""
    selector = DynamicInformationSeekingSelector()
    state = InvestigationState(objective="Triage", project_code="P-DYNA-6", project_name="Highway 6")
    registry = ToolRegistry()

    # Initial state with cost-progress anomaly
    feats = {"progress_expenditure_gap_pct": 24.0, "completion_delay_months": 2.0}
    event_types = ["COST_PROGRESS_MISMATCH"]
    p = {"original_cost_cr": 1000.0, "physical_progress_pct": 15.0}

    h1 = Hypothesis(id="front_loaded_billing", statement="Front-Loaded Billing", confidence=0.55)
    h2 = Hypothesis(id="chronic_schedule_delay", statement="Chronic Delay", confidence=0.45)
    state.hypotheses = [h1, h2]

    selected_tool, candidates, is_terminated, stop_reason, thought, goal = selector.select_next_step(
        state=state, p=p, feats=feats, event_types=event_types, registry=registry
    )

    # 1. Verification of candidates ranking
    assert len(candidates) >= 5
    assert candidates[0].eligible is True
    # Verify sorted descending by net utility
    for i in range(len(candidates) - 1):
        if candidates[i].eligible and candidates[i+1].eligible:
            assert candidates[i].net_utility >= candidates[i+1].net_utility

    # 2. Financial velocity should be top tool for COST_PROGRESS_MISMATCH
    assert selected_tool == "financial_velocity"
    assert is_terminated is False
    assert stop_reason is None
    assert "Phase" in thought
    assert "Financial Velocity" in goal

    # 3. Verification of audit record
    assert len(state.tool_selection_history) == 1
    record: ToolSelectionRecord = state.tool_selection_history[0]
    assert record.step == 1
    assert record.selected_tool == "financial_velocity"
    assert record.net_utility > 0.0
    assert len(record.candidates_evaluated) == len(candidates)
    assert any("financial" in need.lower() for need in record.evidence_needs_addressed)


def test_phase5_7_supervisor_end_to_end_dynamic_selection_loop():
    """Full Pipeline: Verifies that SupervisorAgent executes a coherent multi-step dynamic investigation using selector."""
    agent = SupervisorAgent()
    p = {
        "project_code": "P-DYNA-E2E",
        "project_name": "Dynamic National Highway 8",
        "original_cost_cr": 1500.0,
        "physical_progress_pct": 18.0,
        "original_completion_date": "2024-06",
        "revised_completion_date": "2026-12",
        "project_age_months": 36.0,
        "planned_duration_months": 30.0,
    }
    feats = {
        "progress_expenditure_gap_pct": 28.0,
        "completion_delay_months": 30.0,
        "cost_overrun_pct": 12.0,
        "is_mega_project": True
    }
    event_types = ["COST_PROGRESS_MISMATCH", "MILESTONE_DELAYED"]

    store = Store(":memory:")
    res = {
        "project_code": p["project_code"],
        "project_name": p["project_name"],
        "tier": "High",
        "risk_score": 85.0
    }
    drivers = ["Cost-progress mismatch: spending is ahead of physical progress", "Milestone delayed by 30 months"]
    events = [
        {"type": "COST_PROGRESS_MISMATCH", "severity": "HIGH", "message": "Disbursement leading progress"},
        {"type": "MILESTONE_DELAYED", "severity": "HIGH", "message": "Milestone delayed"}
    ]

    report = agent.run_investigation(
        store=store, p=p, res=res, drivers=drivers, events=events, feats=feats, event_id=999
    )

    # Investigation executed dynamic multi-step loop
    assert len(report["tools_invoked"]) >= 3
    assert len(report["tool_executions"]) >= 3
    assert "tool_financial_velocity" in report["tools_invoked"]
    assert "tool_milestone_audit" in report["tools_invoked"]

    # Dynamic selection history logged
    assert "tool_candidates" in report or len(report["supervisor_steps"]) >= 3
    for step in report["supervisor_steps"]:
        assert "tool_selected" in step
        assert "goal" in step
        assert "thought" in step

    # Final report contains structured evidence, hypotheses, and recommendations
    assert report["structured_evidence"]["hypotheses"]
    assert report["confidence"] in ["High", "Medium", "HIGH", "MEDIUM"]
    assert report["recommendation_confidence"] > 0.0
