"""Tests for Phase 7 — Resource Governance.

Validates the canonical resource-governance lifecycle underneath the investigation:
budget → reserve → execute → settle → resource-aware selection → graceful degradation → expansion when justified

And verifies:
1. Multi-Dimensional Investigation Budget: Explicit ledgers across calls, tokens, latency, cost, and emergency reserves.
2. Resource Reservation: Pre-execution holds preventing over-allocation and protecting emergency reserves.
3. Execution & Settlement: Post-execution settlement reconciling actuals vs estimates with ledger variance.
4. Resource-Aware Tool Selection: Net utility discounts based on resource pressure, financial cost, and quotas.
5. Graceful Degradation & Confidence Coupling: Enforces degraded tiers (LEVEL_1 to LEVEL_4) and confidence caps/caveats.
6. Justified Budget Escalation: Strict expansion gating (denies low severity or low gain; approves high-severity uncertainty).
7. End-to-End Supervisor Integration: Audit traces, governance dashboard, and graceful resource management.
"""
import pytest
import time
from paimana_agent.state import InvestigationState
from paimana_agent.evidence.model import Evidence
from paimana_agent.hypotheses.model import Hypothesis
from paimana_agent.investigation.evidence_need import EvidenceNeed
from paimana_agent.investigation.candidate import ToolCandidate
from paimana_agent.governance.budget.models import (
    InvestigationBudget,
    ResourceConsumption,
    ResourceClass,
)
from paimana_agent.governance.budget.budget_policy import BudgetPolicy
from paimana_agent.governance.budget.budget_reservation import ReservationManager, BudgetReservation
from paimana_agent.governance.budget.budget_manager import BudgetManager
from paimana_agent.governance.budget.degradation import (
    GracefulDegradationManager,
    DegradationLevel,
)
from paimana_agent.governance.budget.escalation import (
    BudgetEscalator,
    BudgetExpansionRequest,
)
from paimana_agent.governance.budget.resource_cost import (
    ToolCostProfile,
    get_tool_cost_profile,
)
from paimana_agent.governance.budget.resource_estimator import ResourceEstimator
from paimana_agent.supervisor import SupervisorAgent
from paimana_agent.store import Store


def test_phase7_1_multidimensional_budget_ledger_and_pressure():
    """Stage 1: Multi-resource tracking across calls, tokens, cost, latency, and pressure."""
    budget = InvestigationBudget(
        investigation_id="inv_test_ledger",
        max_tool_calls=5,
        max_iterations=7,
        max_llm_tokens=10000,
        max_execution_seconds=30.0,
        max_latency_ms=30000.0,
        max_estimated_cost=2.00,
        reserved_emergency_budget=0.20,
    )
    
    # Initial state
    assert budget.resource_pressure == 0.0
    assert not budget.is_exhausted()
    assert budget.remaining_calls == 5
    assert budget.remaining_tokens == 10000
    
    # Record realistic consumption across multiple dimensions
    budget.record_call(
        latency_ms=15000.0,
        cost=1.20,
        input_tokens=4000,
        output_tokens=2000,
    )
    
    # Check updated consumption ledger
    assert budget.consumed.tool_calls == 1
    assert budget.consumed.total_tokens == 6000
    assert budget.consumed.execution_seconds == 15.0
    assert budget.consumed.estimated_cost == pytest.approx(1.20, abs=0.01)
    
    # Resource pressure: cost ratio = 1.20/2.00 = 0.60, time ratio = 15/30 = 0.50, token ratio = 6000/10000 = 0.60
    assert budget.resource_pressure == pytest.approx(0.60, abs=0.05)
    assert not budget.is_exhausted()
    
    # Simulate hitting hard limit on tool calls
    budget.consumed.tool_calls = 5
    budget.tool_calls_used = 5
    assert budget.is_exhausted() is True
    assert budget.remaining_calls == 0


def test_phase7_2_pre_execution_reservation_and_emergency_protection():
    """Stage 2: Pre-execution reservation prevents over-allocation and guards emergency reserve."""
    budget = InvestigationBudget(
        investigation_id="inv_reserve_test",
        max_tool_calls=4,
        max_estimated_cost=1.00,
        reserved_emergency_budget=0.25,  # 25% reserved for emergency/contradiction resolution
    )
    mgr = ReservationManager(budget)
    
    # Usable limit for standard tools is 75% of 4 calls = 3 calls (or 0.75 cost)
    # 1. Standard reservation 1
    r1 = mgr.reserve(tool_name="financial_velocity", estimated_cost=0.20, estimated_latency_ms=500.0)
    assert r1 is not None
    assert r1.status == "PENDING"
    assert mgr.reserved_calls == 1
    assert mgr.reserved_cost == pytest.approx(0.20, abs=0.01)
    
    # 2. Standard reservation 2
    r2 = mgr.reserve(tool_name="milestone_audit", estimated_cost=0.20, estimated_latency_ms=500.0)
    assert r2 is not None
    
    # 3. Standard reservation 3
    r3 = mgr.reserve(tool_name="peer_intelligence", estimated_cost=0.20, estimated_latency_ms=500.0)
    assert r3 is not None
    
    # 4. Standard reservation 4 should be REJECTED because it breaches the 25% emergency reserve threshold
    r4_standard = mgr.reserve(tool_name="shap_attribution", estimated_cost=0.20, is_emergency=False)
    assert r4_standard is None, "Standard tool should not be permitted into emergency reserve!"
    
    # 5. Emergency reservation (e.g. resolving contradiction) is GRANTED access to the reserve
    r4_emergency = mgr.reserve(tool_name="shap_attribution", estimated_cost=0.20, is_emergency=True)
    assert r4_emergency is not None
    assert r4_emergency.is_emergency is True


def test_phase7_3_execution_settlement_and_ledger_variance():
    """Stage 3: Settlement applies actual consumption and records variance in ledger."""
    budget_mgr = BudgetManager(investigation_id="inv_settle_test")
    
    # 1. Pre-execution reservation
    res = budget_mgr.reserve("financial_velocity")
    assert res is not None
    res_id = res.reservation_id
    
    # 2. Settle with actual measurements (execution was faster and slightly cheaper)
    settled = budget_mgr.settle(
        reservation_id=res_id,
        actual_latency_ms=180.0,
        actual_cost=0.015,
        tool_name="financial_velocity"
    )
    assert settled is True
    assert res.status == "SETTLED"
    assert budget_mgr.budget.consumed.tool_calls == 1
    assert budget_mgr.budget.consumed.estimated_cost == pytest.approx(0.015, abs=0.005)
    
    # 3. Verify ledger variance recorded
    entries = budget_mgr.ledger.entries
    assert len(entries) == 1
    entry = entries[0]
    assert entry.operation_id == res_id
    assert entry.resource_name == "financial_velocity"
    assert entry.actual_cost == pytest.approx(0.015, abs=0.005)
    
    # 4. Cancelling a reservation frees held capacity
    res_cancel = budget_mgr.reserve("milestone_audit")
    assert res_cancel is not None
    cancelled = budget_mgr.reservations.cancel(res_cancel.reservation_id)
    assert cancelled is True
    assert res_cancel.status == "CANCELLED"
    assert budget_mgr.reservations.reserved_calls == 0


def test_phase7_4_resource_aware_tool_selection():
    """Stage 4: Resource-adjusted value and cost profiles discount candidates under pressure."""
    budget = InvestigationBudget(max_tool_calls=5, max_estimated_cost=1.00)
    
    # Under low pressure, value is unconstrained
    val_low = ResourceEstimator.calculate_resource_adjusted_value(
        tool_name="financial_velocity",
        expected_information_gain=0.40,
        decision_relevance=0.90,
        evidence_quality=0.90,
        budget=budget,
    )
    assert val_low >= 0.30
    
    # Under high resource pressure (85% consumed), expensive tools are heavily discounted
    budget.consumed.tool_calls = 4
    budget.consumed.estimated_cost = 0.85
    val_high = ResourceEstimator.calculate_resource_adjusted_value(
        tool_name="financial_velocity",
        expected_information_gain=0.40,
        decision_relevance=0.90,
        evidence_quality=0.90,
        budget=budget,
    )
    assert val_high < val_low, "Resource-adjusted value must decrease under heavy resource pressure!"
    
    # Affordability check flags unaffordable candidates
    can_afford = budget.can_afford(estimated_cost=0.25)  # Remaining cost is only 0.15
    assert can_afford is False


def test_phase7_5_graceful_degradation_tiers_and_confidence_coupling():
    """Stage 5: Degradation tiers qualify reported confidence and enforce explicit caveats."""
    budget = InvestigationBudget(max_tool_calls=5, max_execution_seconds=30.0, max_estimated_cost=1.50)
    
    # Tier 1: Normal (pressure <= 0.50)
    budget.consumed.tool_calls = 1
    tier1 = GracefulDegradationManager.evaluate_tier(budget)
    assert tier1 == DegradationLevel.LEVEL_1_NORMAL
    coup1 = GracefulDegradationManager.apply_confidence_coupling(tier1, raw_confidence=0.88, evidence_coverage=0.90)
    assert coup1["adjusted_confidence"] == 0.88
    assert coup1["is_resource_constrained"] is False
    assert len(coup1["caveats"]) == 0
    
    # Tier 2: Cost-Aware (pressure 0.50 - 0.75)
    budget.consumed.tool_calls = 3  # 3/5 = 0.60
    tier2 = GracefulDegradationManager.evaluate_tier(budget)
    assert tier2 == DegradationLevel.LEVEL_2_COST_AWARE
    coup2 = GracefulDegradationManager.apply_confidence_coupling(tier2, raw_confidence=0.90, evidence_coverage=0.85)
    assert coup2["adjusted_confidence"] <= 0.85
    assert coup2["is_resource_constrained"] is True
    
    # Tier 3: Constrained (pressure 0.75 - 0.90)
    budget.consumed.tool_calls = 4  # 4/5 = 0.80
    tier3 = GracefulDegradationManager.evaluate_tier(budget)
    assert tier3 == DegradationLevel.LEVEL_3_CONSTRAINED
    coup3 = GracefulDegradationManager.apply_confidence_coupling(tier3, raw_confidence=0.85, evidence_coverage=0.60)
    assert coup3["adjusted_confidence"] <= 0.65
    assert "constrained local evidence" in coup3["caveats"][0].lower()
    
    # Tier 4: Safe Termination (exhausted / pressure > 0.90)
    budget.consumed.tool_calls = 5
    tier4 = GracefulDegradationManager.evaluate_tier(budget)
    assert tier4 == DegradationLevel.LEVEL_4_SAFE_TERMINATION
    coup4 = GracefulDegradationManager.apply_confidence_coupling(tier4, raw_confidence=0.80, evidence_coverage=0.40)
    assert coup4["adjusted_confidence"] <= 0.45
    assert "terminated early" in coup4["caveats"][0].lower()


def test_phase7_6_justified_budget_expansion_and_rejection_gating():
    """Stage 6: Expansion gating strictly permits justified requests and denies frivolous drift."""
    budget = InvestigationBudget(severity="MEDIUM", max_tool_calls=4, max_estimated_cost=1.00)
    
    # Case A: Low severity request -> strictly DENIED
    req_low = BudgetExpansionRequest(
        investigation_id="inv_low",
        reason="Seek extra data",
        requested_resources={"tool_calls": 2, "cost": 0.50},
        current_uncertainty=0.60,
        expected_information_gain=0.25,
        severity="LOW"
    )
    eval_low = BudgetEscalator.evaluate_request(req_low, budget)
    assert eval_low.status == "DENIED"
    assert "LOW severity" in eval_low.audit_notes
    assert budget.max_tool_calls == 4  # Unchanged
    
    # Case B: Trivial expected information gain (< 0.08) -> DENIED
    req_trivial = BudgetExpansionRequest(
        investigation_id="inv_triv",
        reason="Run redundant tool",
        requested_resources={"tool_calls": 1},
        current_uncertainty=0.40,
        expected_information_gain=0.03,
        severity="HIGH"
    )
    eval_triv = BudgetEscalator.evaluate_request(req_trivial, budget)
    assert eval_triv.status == "DENIED"
    assert "Expected information gain" in eval_triv.audit_notes
    assert budget.max_tool_calls == 4
    
    # Case C: High severity with material uncertainty and strong gain -> APPROVED
    budget_high = InvestigationBudget(severity="HIGH", max_tool_calls=5, max_estimated_cost=1.50)
    req_high = BudgetExpansionRequest(
        investigation_id="inv_high",
        reason="Disambiguate critical progress contradiction",
        requested_resources={"tool_calls": 2, "cost": 0.40, "latency_ms": 3000.0},
        current_uncertainty=0.45,
        expected_information_gain=0.22,
        severity="HIGH"
    )
    eval_high = BudgetEscalator.evaluate_request(req_high, budget_high)
    assert eval_high.status == "APPROVED"
    assert budget_high.max_tool_calls == 7  # Expanded by +2
    assert budget_high.max_estimated_cost == pytest.approx(1.90, abs=0.01)


def test_phase7_7_end_to_end_supervisor_resource_governance():
    """Stage 7: Full Supervisor investigation executes complete reserve-settle governance lifecycle."""
    supervisor = SupervisorAgent()
    store = Store()
    
    project_data = {
        "project_code": "P-GOV-E2E",
        "project_name": "Hydroelectric Dam Package A",
        "sector": "Power & Energy",
        "implementing_agency": "NHPC",
        "original_cost_cr": 1200.0,
        "revised_cost_cr": 1450.0,
        "cumulative_expenditure_cr": 1100.0,
        "physical_progress_pct": 42.0,
        "original_completion_date": "2023-12-31",
        "revised_completion_date": "2026-06-30",
    }
    
    res = {
        "project_code": "P-GOV-E2E",
        "project_name": "Hydroelectric Dam Package A",
        "composite_risk_score": 82.0,
        "risk_level": "CRITICAL",
    }
    
    events = [
        {"type": "COST_PROGRESS_MISMATCH", "severity": "CRITICAL", "project_code": "P-GOV-E2E"}
    ]
    
    feats = {
        "cost_overrun_pct": 20.8,
        "progress_expenditure_gap_pct": 49.7,
        "schedule_slippage_months": 30.0,
        "composite_risk_score": 82.0,
    }
    
    report = supervisor.run_investigation(
        store=store,
        p=project_data,
        res=res,
        drivers=["progress_expenditure_gap_pct"],
        events=events,
        feats=feats,
        max_steps=5
    )
    
    # 1. Governance Trace & Dashboard are emitted
    assert "governance_trace" in report
    assert report["governance_trace"] is not None
    assert "governance_dashboard" in report
    dash = report["governance_dashboard"]
    assert "resource_pressure" in dash
    assert "tool_calls_progress" in dash
    
    # 2. Degradation Level & Quality Tier reported
    assert report["degradation_level"] in [
        "LEVEL_1_NORMAL",
        "LEVEL_2_COST_AWARE",
        "LEVEL_3_CONSTRAINED",
        "LEVEL_4_SAFE_TERMINATION",
    ]
    assert report["quality_tier"] in [
        "TIER_1_FULL",
        "TIER_2_STANDARD",
        "TIER_3_MINIMAL",
    ]
    
    # 3. Investigation Budget serialized
    assert "investigation_budget" in report
    inv_b = report["investigation_budget"]
    assert inv_b["tool_calls_used"] > 0
    assert inv_b["consumed"]["tool_calls"] == inv_b["tool_calls_used"]
    assert inv_b["consumed"]["execution_seconds"] > 0.0
