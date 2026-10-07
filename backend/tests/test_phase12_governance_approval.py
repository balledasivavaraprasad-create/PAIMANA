"""Phase 12 — Governance + Human Approval Verification Suite.

Validates the canonical lockdown:
    INVESTIGATE  ≠  RECOMMEND  ≠  APPROVE  ≠  EXECUTE

Tests real permissions, approval requirements, policy gates, cryptographic HMAC
signatures, execution guardrails, audit ledger chaining, and end-to-end HITL workflow.
"""
from __future__ import annotations
import time
import pytest

from paimana_agent.store import Store
from paimana_agent.state import InvestigationState, Fact
from paimana_agent.evidence.model import Evidence
from paimana_agent.hypotheses.model import Hypothesis
from paimana_agent.recommendations.candidate import RecommendationCandidate
from paimana_agent.governance.approval import (
    Stage,
    Role,
    Permission,
    Actor,
    ApprovalStatus,
    ExecutionStatus,
    ApprovalRequest,
    ApprovalDecision,
    ApprovalRecord,
    ExecutionRecord,
    StageBoundaryManager,
    PolicyGateEngine,
    ApprovalEngine,
    ExecutionEngine,
    GovernanceAuditLedger,
    GovernanceError,
    StageViolationError,
    PermissionDeniedError,
    PolicyGateViolationError,
    CausalGateViolationError,
    UnauthorizedExecutionError,
)
from paimana_agent.supervisor import SupervisorAgent
from paimana_agent.tools import ToolRegistry


@pytest.fixture
def clean_store(tmp_path):
    db_path = str(tmp_path / "test_phase12.db")
    return Store(db_path)


@pytest.fixture
def actors():
    """Provides a hierarchy of institutional human actors and AI system actors."""
    return {
        "ai_investigator": Actor(
            id="actor_ai_inv",
            name="PAIMANA AI Investigator",
            role=Role.AI_INVESTIGATOR,
        ),
        "ai_recommender": Actor(
            id="actor_ai_rec",
            name="PAIMANA AI Recommender",
            role=Role.AI_RECOMMENDER,
        ),
        "field_engineer": Actor(
            id="actor_fe_01",
            name="Er. Rajesh Sharma",
            role=Role.FIELD_ENGINEER,
            department="Regional Office Lucknow",
            max_financial_limit_cr=10.0,
            risk_tolerance_ceiling=0.25,
        ),
        "project_director": Actor(
            id="actor_pd_01",
            name="Dr. V. K. Malhotra",
            role=Role.PROJECT_DIRECTOR,
            department="PIU Varanasi",
            max_financial_limit_cr=100.0,
            risk_tolerance_ceiling=0.50,
        ),
        "chief_engineer": Actor(
            id="actor_ce_01",
            name="Shri A. P. Sengupta",
            role=Role.CHIEF_ENGINEER,
            department="HQ Technical Division",
            max_financial_limit_cr=500.0,
            risk_tolerance_ceiling=0.75,
        ),
        "ministry_secretary": Actor(
            id="actor_sec_01",
            name="Smt. Meenakshi Sundaram, IAS",
            role=Role.MINISTRY_SECRETARY,
            department="Ministry of Road Transport and Highways",
            max_financial_limit_cr=5000.0,
            risk_tolerance_ceiling=0.90,
        ),
        "apex_committee": Actor(
            id="actor_apex_01",
            name="Cabinet Apex Committee on Infrastructure",
            role=Role.APEX_COMMITTEE,
            department="Cabinet Secretariat",
            max_financial_limit_cr=50000.0,
            risk_tolerance_ceiling=0.95,
        ),
    }


# ============================================================================
# 1. Stage Boundary Decoupling
# ============================================================================
def test_stage_boundary_decoupling(actors):
    """Verifies that investigate ≠ recommend ≠ approve ≠ execute and invalid jumps are blocked."""
    mgr = StageBoundaryManager()
    human = actors["project_director"]

    # Allowed transitions
    assert mgr.validate_transition(Stage.INVESTIGATE, Stage.RECOMMEND, actor=human) is True
    assert mgr.validate_transition(Stage.RECOMMEND, Stage.APPROVE, actor=human) is True
    assert mgr.validate_transition(Stage.APPROVE, Stage.EXECUTE, actor=human) is True
    assert mgr.validate_transition(Stage.APPROVE, Stage.INVESTIGATE, actor=human) is True

    # Forbidden direct execution bypass: INVESTIGATE -> EXECUTE
    with pytest.raises(StageViolationError, match="Direct Execution Bypass Detected"):
        mgr.validate_transition(Stage.INVESTIGATE, Stage.EXECUTE, actor=human)

    # Forbidden autonomous execution: RECOMMEND -> EXECUTE
    with pytest.raises(StageViolationError, match="Autonomous Execution Bypass Detected"):
        mgr.validate_transition(Stage.RECOMMEND, Stage.EXECUTE, actor=human)

    # Forbidden bypass: INVESTIGATE -> APPROVE
    with pytest.raises(StageViolationError, match="Invalid Stage Transition"):
        mgr.validate_transition(Stage.INVESTIGATE, Stage.APPROVE, actor=human)


# ============================================================================
# 2. AI Agent Lockout from Human Approval & Execution
# ============================================================================
def test_ai_agent_lockout(actors):
    """Verifies that AI agents can NEVER approve or execute actions."""
    mgr = StageBoundaryManager()
    ai_inv = actors["ai_investigator"]
    ai_rec = actors["ai_recommender"]

    # AI can investigate or recommend
    mgr.assert_can_investigate(ai_inv)
    mgr.assert_can_recommend(ai_rec)

    # AI is blocked from entering APPROVE stage
    with pytest.raises(PermissionDeniedError, match="strictly prohibited from entering stage 'APPROVE'"):
        mgr.validate_transition(Stage.RECOMMEND, Stage.APPROVE, actor=ai_inv)

    # AI is blocked from entering EXECUTE stage
    with pytest.raises(PermissionDeniedError, match="strictly prohibited from entering stage 'EXECUTE'"):
        mgr.validate_transition(Stage.APPROVE, Stage.EXECUTE, actor=ai_rec)

    # AI assert checks fail
    with pytest.raises(PermissionDeniedError, match="AI agents cannot approve"):
        mgr.assert_can_approve(ai_inv)

    with pytest.raises(PermissionDeniedError, match="AI agents cannot execute"):
        mgr.assert_can_execute(ai_rec)


# ============================================================================
# 3. Separation of Duties Policy Gate
# ============================================================================
def test_separation_of_duties_policy_gate(actors):
    """Verifies that an actor who proposed an action cannot self-approve it."""
    engine = PolicyGateEngine()
    pd = actors["project_director"]

    # Request proposed by Project Director
    request = ApprovalRequest(
        request_id="REQ-001",
        project_code="NH-DUTY-1",
        candidate_id="CAND-01",
        action_title="Restructure contractor milestone escrow account",
        action_type="FINANCIAL_RESTRUCTURING",
        approval_class="managerial",
        urgency="HIGH",
        proposed_by=pd,  # Proposer is PD
        cost_cr=25.0,
        implementation_risk=0.30
    )

    # Project Director attempts to self-approve
    passed, gate_results, reasons = engine.evaluate_gates(request=request, approver=pd)
    assert passed is False
    assert gate_results["separation_of_duties_proposer"] is False
    assert any("Separation of Duties Violation" in r for r in reasons)

    # Chief Engineer approves -> Passes separation of duties
    ce = actors["chief_engineer"]
    passed_ce, gate_results_ce, _ = engine.evaluate_gates(request=request, approver=ce)
    assert passed_ce is True
    assert gate_results_ce["separation_of_duties_proposer"] is True


# ============================================================================
# 4. Approval Class & Role Permissions
# ============================================================================
def test_approval_class_and_role_permissions(actors):
    """Verifies that approval classes (routine, managerial, executive, statutory) require matching permissions."""
    engine = PolicyGateEngine()
    fe = actors["field_engineer"]
    pd = actors["project_director"]
    ce = actors["chief_engineer"]
    sec = actors["ministry_secretary"]
    proposer = actors["ai_recommender"]

    # 1. Routine Approval: Field Engineer can approve
    req_routine = ApprovalRequest(
        request_id="REQ-ROUTINE",
        project_code="NH-PERM-1",
        candidate_id="CAND-01",
        action_title="Issue statutory data reconciliation notice",
        action_type="DATA_REFRESH",
        approval_class="routine",
        urgency="MEDIUM",
        proposed_by=proposer,
        cost_cr=1.0,
        implementation_risk=0.10
    )
    passed_fe, _, _ = engine.evaluate_gates(request=req_routine, approver=fe)
    assert passed_fe is True

    # 2. Managerial Approval: Field Engineer FAILS, Project Director PASSES
    req_managerial = ApprovalRequest(
        request_id="REQ-MANAGERIAL",
        project_code="NH-PERM-2",
        candidate_id="CAND-02",
        action_title="Mandate resource-loaded catch-up schedule with fortnightly verification",
        action_type="RECOVERY_PLAN",
        approval_class="managerial",
        urgency="HIGH",
        proposed_by=proposer,
        cost_cr=15.0,
        implementation_risk=0.25
    )
    passed_fe_mgr, gates_fe, _ = engine.evaluate_gates(request=req_managerial, approver=fe)
    assert passed_fe_mgr is False
    assert gates_fe["role_authority"] is False

    passed_pd_mgr, _, _ = engine.evaluate_gates(request=req_managerial, approver=pd)
    assert passed_pd_mgr is True

    # 3. Executive Approval: Project Director FAILS, Chief Engineer PASSES
    req_exec = ApprovalRequest(
        request_id="REQ-EXECUTIVE",
        project_code="NH-PERM-3",
        candidate_id="CAND-03",
        action_title="Establish Joint Financial-Physical Audit Taskforce to freeze unverified disbursements",
        action_type="FORENSIC_AUDIT",
        approval_class="executive",
        urgency="HIGH",
        proposed_by=proposer,
        cost_cr=45.0,
        implementation_risk=0.35
    )
    passed_pd_exec, gates_pd, _ = engine.evaluate_gates(request=req_exec, approver=pd)
    assert passed_pd_exec is False
    assert gates_pd["role_authority"] is False

    passed_ce_exec, _, _ = engine.evaluate_gates(request=req_exec, approver=ce)
    assert passed_ce_exec is True

    # 4. Statutory Approval: Chief Engineer FAILS, Ministry Secretary PASSES
    req_stat = ApprovalRequest(
        request_id="REQ-STATUTORY",
        project_code="NH-PERM-4",
        candidate_id="CAND-04",
        action_title="Escalate Stage-2 forest clearance to State Chief Secretary Apex Committee",
        action_type="ESCALATION",
        approval_class="statutory",
        urgency="CRITICAL",
        proposed_by=proposer,
        cost_cr=80.0,
        implementation_risk=0.40
    )
    passed_ce_stat, gates_ce, _ = engine.evaluate_gates(request=req_stat, approver=ce)
    assert passed_ce_stat is False
    assert gates_ce["role_authority"] is False

    passed_sec_stat, _, _ = engine.evaluate_gates(request=req_stat, approver=sec)
    assert passed_sec_stat is True


# ============================================================================
# 5. Causal Support Invariant Gate (Punitive Actions)
# ============================================================================
def test_causal_support_governance_invariant(actors):
    """Verifies that punitive contractual actions strictly require Level 4 Causal Support."""
    engine = PolicyGateEngine()
    sec = actors["ministry_secretary"]
    proposer = actors["ai_recommender"]

    # Punitive action with only Level 2 Temporal Association
    req_punitive_low_causal = ApprovalRequest(
        request_id="REQ-CAUSAL-FAIL",
        project_code="NH-CAUSAL-1",
        candidate_id="CAND-PUN-01",
        action_title="Enforce liquidated damages penalty and forfeit contractor bank guarantee",
        action_type="PENALTY_ENFORCEMENT",
        approval_class="statutory",
        urgency="CRITICAL",
        proposed_by=proposer,
        causal_level="LEVEL_2_TEMPORAL_ASSOCIATION",
        causal_support_score=0.42,
        cost_cr=50.0,
        implementation_risk=0.45
    )

    with pytest.raises(CausalGateViolationError, match="Level 4 Strong Causal Support"):
        engine.assert_can_approve(request=req_punitive_low_causal, approver=sec)

    # Punitive action WITH Level 4 Strong Causal Support
    req_punitive_high_causal = ApprovalRequest(
        request_id="REQ-CAUSAL-PASS",
        project_code="NH-CAUSAL-1",
        candidate_id="CAND-PUN-02",
        action_title="Enforce liquidated damages penalty and forfeit contractor bank guarantee",
        action_type="PENALTY_ENFORCEMENT",
        approval_class="statutory",
        urgency="CRITICAL",
        proposed_by=proposer,
        causal_level="LEVEL_4_COUNTERFACTUAL",
        causal_support_score=0.88,
        cost_cr=50.0,
        implementation_risk=0.45
    )
    gates = engine.assert_can_approve(request=req_punitive_high_causal, approver=sec)
    assert gates["causal_support_calibration"] is True


# ============================================================================
# 6. Mega-Project Governance and Financial Limits
# ============================================================================
def test_mega_project_and_financial_authority_gates(actors):
    """Verifies mega-project scrutiny and financial authorization caps."""
    engine = PolicyGateEngine()
    proposer = actors["ai_recommender"]
    pd = actors["project_director"]  # Limit: 100 Cr
    ce = actors["chief_engineer"]    # Limit: 500 Cr

    # Mega-project action on 1,800 Cr corridor
    req_mega = ApprovalRequest(
        request_id="REQ-MEGA-01",
        project_code="NH-MEGA-01",
        candidate_id="CAND-MEGA",
        action_title="Deploy specialized technical ground inspection team across all 6 packages",
        action_type="FORENSIC_AUDIT",
        approval_class="managerial",
        urgency="HIGH",
        proposed_by=proposer,
        is_mega_project=True,
        cost_cr=120.0,  # Exceeds PD limit (100 Cr)
        implementation_risk=0.30
    )

    # PD fails on both mega-project high-urgency governance and financial limit
    passed_pd, gates_pd, reasons_pd = engine.evaluate_gates(request=req_mega, approver=pd)
    assert passed_pd is False
    assert gates_pd["mega_project_governance"] is False
    assert gates_pd["financial_authority"] is False

    # Chief Engineer has executive authority & 500 Cr limit -> PASSES
    passed_ce, gates_ce, _ = engine.evaluate_gates(request=req_mega, approver=ce)
    assert passed_ce is True


# ============================================================================
# 7. Approval Decision & Cryptographic Signatures
# ============================================================================
def test_approval_decision_and_cryptographic_signatures(actors):
    """Verifies that approval records contain authentic HMAC signatures that detect tampering."""
    app_engine = ApprovalEngine()
    ce = actors["chief_engineer"]
    proposer = actors["ai_recommender"]

    request = ApprovalRequest(
        request_id="REQ-APP-SIGN-01",
        project_code="NH-SIGN-1",
        candidate_id="CAND-SIGN-01",
        action_title="Mandate revised contractor recovery schedule with fortnightly reviews",
        action_type="RECOVERY_PLAN",
        approval_class="managerial",
        urgency="HIGH",
        proposed_by=proposer,
        cost_cr=20.0,
        implementation_risk=0.22
    )

    # 1. Process approval
    record = app_engine.process_decision(
        request=request,
        approver=ce,
        decision=ApprovalStatus.APPROVED,
        justification="Critical schedule recovery measure backed by verified milestone audit findings."
    )

    assert record.record_id.startswith("REC-APP-")
    assert record.decision.decision == ApprovalStatus.APPROVED
    assert record.is_valid() is True

    # 2. Verify signature tampering detection
    tampered_record = ApprovalRecord(
        record_id=record.record_id,
        request=record.request,
        decision=ApprovalDecision(
            decision=ApprovalStatus.APPROVED,
            approver=record.decision.approver,
            justification=record.decision.justification,
            timestamp=record.decision.timestamp + 100.0  # Tampered timestamp
        ),
        gate_evaluations=record.gate_evaluations,
        signature_token=record.signature_token
    )
    assert tampered_record.is_valid() is False, "Signature verification must fail on tampered payload"


def test_conditional_approval_and_escalation(actors):
    """Verifies conditional approvals and escalation workflows."""
    app_engine = ApprovalEngine()
    ce = actors["chief_engineer"]
    proposer = actors["ai_recommender"]

    request = ApprovalRequest(
        request_id="REQ-APP-COND-01",
        project_code="NH-COND-1",
        candidate_id="CAND-COND",
        action_title="Interim mobilization advance release tied to drone verification",
        action_type="FINANCIAL_DISBURSEMENT",
        approval_class="managerial",
        urgency="HIGH",
        proposed_by=proposer,
        cost_cr=30.0,
        implementation_risk=0.25
    )

    # Conditional approval
    cond_record = app_engine.process_decision(
        request=request,
        approver=ce,
        decision=ApprovalStatus.CONDITIONAL_APPROVAL,
        justification="Approved subject to field physical verification.",
        conditions=["Drone aerial survey confirms 100% equipment mobilization", "PMC issues zero-defect certificate"]
    )
    assert cond_record.decision.decision == ApprovalStatus.CONDITIONAL_APPROVAL
    assert len(cond_record.decision.conditions) == 2
    assert cond_record.is_valid() is True


# ============================================================================
# 8. Execution Engine Pre-Execution Guardrails
# ============================================================================
def test_execution_engine_pre_execution_guardrails(actors, clean_store):
    """Verifies that APPROVE ≠ EXECUTE and unapproved/tampered/expired executions are rejected."""
    exec_engine = ExecutionEngine()
    app_engine = ApprovalEngine()
    ce = actors["chief_engineer"]
    pd = actors["project_director"]
    proposer = actors["ai_recommender"]

    request = ApprovalRequest(
        request_id="REQ-EXEC-GUARD",
        project_code="NH-EXEC-GUARD-01",
        candidate_id="CAND-01",
        action_title="Mandate revised contractor recovery schedule",
        action_type="RECOVERY_PLAN",
        approval_class="managerial",
        urgency="HIGH",
        proposed_by=proposer,
        cost_cr=10.0,
        implementation_risk=0.20
    )

    # 1. Attempt direct execution without approval record
    with pytest.raises(UnauthorizedExecutionError, match="Autonomous Execution Blocked"):
        exec_engine.reject_unauthorized_execution(raw_candidate=request, actor=pd)

    # 2. Attempt execution with rejected approval record
    rejected_record = app_engine.process_decision(
        request=request,
        approver=ce,
        decision=ApprovalStatus.REJECTED,
        justification="Proposal rejected due to insufficient field supervision resources."
    )
    with pytest.raises(UnauthorizedExecutionError, match="approval status 'REJECTED'"):
        exec_engine.execute_approved_action(approval_record=rejected_record, executor=pd)

    # 3. Attempt execution with expired approval record
    valid_record = app_engine.process_decision(
        request=request,
        approver=ce,
        decision=ApprovalStatus.APPROVED,
        justification="Fully approved."
    )
    valid_record.decision.expires_at = time.time() - 100.0  # Expired
    with pytest.raises(UnauthorizedExecutionError, match="has expired"):
        exec_engine.execute_approved_action(approval_record=valid_record, executor=pd)

    # 4. Attempt execution on a terminated project (circuit breaker)
    valid_record.decision.expires_at = time.time() + 86400.0  # Reset expiration
    with pytest.raises(UnauthorizedExecutionError, match="circuit breaker: Project status is 'TERMINATED'"):
        exec_engine.execute_approved_action(
            approval_record=valid_record,
            executor=pd,
            project_current_state={"status": "Terminated"}
        )

    # 5. Successful Execution by Authorized Human
    clean_store.save_snapshot("NH-EXEC-GUARD-01", 1, {"project_code": "NH-EXEC-GUARD-01"})
    exec_record = exec_engine.execute_approved_action(
        approval_record=valid_record,
        executor=pd,
        store=clean_store,
        project_current_state={"status": "Delayed"}
    )
    assert exec_record.execution_status == ExecutionStatus.COMPLETED
    assert exec_record.execution_id.startswith("EXEC-NH-EXEC-GUARD-01")
    assert exec_record.audit_hash != ""

    # Verify intervention was persisted into store
    interventions = clean_store.list_interventions("NH-EXEC-GUARD-01")
    assert len(interventions) == 1
    assert "Mandate revised contractor recovery schedule" in interventions[0]["action"]


# ============================================================================
# 9. Governance Audit Ledger & Cryptographic Chain
# ============================================================================
def test_governance_audit_ledger_cryptographic_chain(actors):
    """Verifies that the audit ledger maintains an unbroken, tamper-evident cryptographic chain."""
    ledger = GovernanceAuditLedger()
    proj_code = "NH-AUDIT-99"

    # Step 1: Investigation milestone
    e1 = ledger.append_investigation(
        project_code=proj_code,
        investigator_id=actors["ai_investigator"].id,
        investigator_role=actors["ai_investigator"].role.value,
        findings_summary={"primary_hypothesis": "contractor_liquidity_crisis", "confidence": 0.85}
    )
    assert e1.previous_hash == "GENESIS_BLOCK"

    # Step 2: Recommendation milestone
    e2 = ledger.append_recommendation(
        project_code=proj_code,
        recommender_id=actors["ai_recommender"].id,
        recommender_role=actors["ai_recommender"].role.value,
        recommendation_decision={"selected_action": "Restructure escrow disbursements", "utility": 0.82}
    )
    assert e2.previous_hash == e1.entry_hash

    # Step 3: Approval milestone
    app_engine = ApprovalEngine()
    req = ApprovalRequest(
        request_id="REQ-AUD-01",
        project_code=proj_code,
        candidate_id="CAND-01",
        action_title="Restructure escrow disbursements",
        action_type="FINANCIAL_RESTRUCTURING",
        approval_class="managerial",
        urgency="HIGH",
        proposed_by=actors["ai_recommender"],
        cost_cr=20.0
    )
    app_record = app_engine.process_decision(
        request=req,
        approver=actors["chief_engineer"],
        decision=ApprovalStatus.APPROVED,
        justification="Approved by Chief Engineer after technical review."
    )
    e3 = ledger.append_approval(app_record)
    assert e3.previous_hash == e2.entry_hash

    # Step 4: Execution milestone
    exec_engine = ExecutionEngine()
    exec_record = exec_engine.execute_approved_action(
        approval_record=app_record,
        executor=actors["project_director"]
    )
    e4 = ledger.append_execution(exec_record)
    assert e4.previous_hash == e3.entry_hash

    # Verify overall ledger integrity
    assert ledger.verify_ledger_integrity() is True

    # Test tampering detection: alter entry 2
    e2.action_details["utility"] = 0.99
    assert ledger.verify_ledger_integrity() is False, "Altering entry payload must break cryptographic audit chain"


# ============================================================================
# 10. End-to-End Investigation to Human Approval & Execution Loop
# ============================================================================
def test_end_to_end_investigation_to_human_approval_loop(clean_store, actors):
    """Full lifecycle integration test: Supervisor investigates, prepares human approval request,
    human authorizes, and executor safely dispatches with immutable audit records."""
    proj_code = "NH-E2E-GOV-01"
    p_proj = {
        "project_code": proj_code,
        "project_name": "NH-GOV Corridor Expansion",
        "sector": "Roads & Highways",
        "original_cost_cr": 850.0,
        "revised_cost_cr": 1100.0,
        "cumulative_expenditure_cr": 520.0,
        "physical_progress_pct": 36.0,
        "financial_progress_pct": 58.2,
        "original_completion_date": "2024-12-31",
        "revised_completion_date": "2026-03-31",
        "agency": "NHAI",
        "state": "Madhya Pradesh",
        "contract_type": "EPC",
        "is_mega_project": False,
        "status": "Delayed"
    }
    clean_store.save_snapshot(proj_code, 1, p_proj)

    events = [{
        "type": "PROGRESS_STALLED",
        "message": "Physical progress stalled at 36%",
        "event_id": "EV-GOV-01",
        "timestamp": 1700000000.0
    }]

    # Stage 1: Investigation by AI Supervisor
    registry = ToolRegistry(enable_recovery=True)
    supervisor = SupervisorAgent(tool_registry=registry)
    report = supervisor.run_investigation(
        store=clean_store,
        p=p_proj,
        res={"project_code": proj_code, "tier": "High", "risk_score": 79.0},
        drivers=["progress_expenditure_gap_pct"],
        events=events,
        max_steps=3
    )

    # Verify AI outputs recommendation proposal, but DOES NOT execute
    assert report.get("action_execution_status") == "LOCKED_AWAITING_APPROVAL"
    assert report.get("status") == "pending_approval"
    
    app_req_dict = report.get("governance_approval_request")
    assert app_req_dict is not None, "Supervisor must emit formal ApprovalRequest"
    assert app_req_dict["status"] == "PENDING"
    assert app_req_dict["project_code"] == proj_code

    # Stage 2: Convert to request object and Human Approval by Chief Engineer
    app_engine = ApprovalEngine()
    ce = actors["chief_engineer"]
    pd = actors["project_director"]

    # Reconstruct request object
    request = ApprovalRequest(
        request_id=app_req_dict["request_id"],
        project_code=app_req_dict["project_code"],
        candidate_id=app_req_dict["candidate_id"],
        action_title=app_req_dict["action_title"],
        action_type=app_req_dict["action_type"],
        approval_class=app_req_dict["approval_class"],
        urgency=app_req_dict["urgency"],
        proposed_by=actors["ai_recommender"],
        justification=app_req_dict["justification"],
        evidence_ids=app_req_dict["evidence_ids"],
        hypothesis_ids=app_req_dict["hypothesis_ids"],
        cost_cr=app_req_dict["cost_cr"],
        implementation_risk=app_req_dict["implementation_risk"],
        is_mega_project=app_req_dict["is_mega_project"]
    )

    approval_record = app_engine.process_decision(
        request=request,
        approver=ce,
        decision=ApprovalStatus.APPROVED,
        justification="Action verified against physical inspection data and approved for deployment."
    )
    assert approval_record.is_valid() is True
    assert approval_record.decision.decision == ApprovalStatus.APPROVED

    # Stage 3: Execution by authorized Project Director
    exec_engine = ExecutionEngine()
    exec_record = exec_engine.execute_approved_action(
        approval_record=approval_record,
        executor=pd,
        store=clean_store,
        project_current_state={"status": "Delayed"}
    )
    assert exec_record.execution_status == ExecutionStatus.COMPLETED
    assert exec_record.project_code == proj_code

    # Verify project store received intervention record
    interventions = clean_store.list_interventions(proj_code)
    assert len(interventions) >= 1
    assert any(approval_record.decision.approver.name in i["action"] for i in interventions)
