"""Phase 13 — Outcome Learning Verification Suite.

Validates the canonical 7-stage closed loop:
    recommendation
    → approval
    → intervention
    → outcome
    → effectiveness
    → memory
    → recommendation evaluation

Ensures empirical delta calculation, confounder discounting, failure indexing,
Bayesian track record updating, dynamic benefit recalibration, and portfolio MACE tracking.
"""
from __future__ import annotations
import time
import pytest

from paimana_agent.store import Store
from paimana_agent.memory.precedent_memory import PrecedentMemoryStore
from paimana_agent.memory.failure_memory import FailureMemoryManager
from paimana_agent.recommendations.candidate import RecommendationCandidate
from paimana_agent.governance.approval import (
    Role,
    Permission,
    Actor,
    ApprovalStatus,
    ApprovalRequest,
    ApprovalDecision,
    ApprovalRecord,
    ExecutionRecord,
    ExecutionStatus,
)
from paimana_agent.learning import (
    OutcomeAttribution,
    OutcomeObservation,
    EffectivenessAssessment,
    RecommendationCalibration,
    LearningMilestone,
    EffectivenessAnalyzer,
    InstitutionalMemorySyncer,
    RecommendationEvaluator,
    OutcomeLearningEngine,
)


@pytest.fixture
def clean_memory_store(tmp_path):
    db_path = str(tmp_path / "test_phase13_memory.db")
    store = PrecedentMemoryStore(db_path)
    store.reset()
    return store


@pytest.fixture
def clean_store(tmp_path):
    db_path = str(tmp_path / "test_phase13_store.db")
    return Store(db_path)


# ============================================================================
# 1. Empirical Effectiveness Evaluation
# ============================================================================
def test_empirical_effectiveness_evaluation():
    """Verifies that empirical metric deltas produce accurate effectiveness scores and attributions."""
    analyzer = EffectivenessAnalyzer()

    # Pre-intervention metrics on a stalled, high-risk corridor
    pre_metrics = {
        "risk_score": 78.0,
        "progress_expenditure_gap_pct": 18.0,
        "completion_delay_months": 8.0,
    }

    # Post-intervention metrics showing operational recovery
    post_metrics = {
        "risk_score": 60.0,                    # Delta: -18.0 (Strong risk reduction)
        "progress_expenditure_gap_pct": 6.0,   # Delta: -12.0 (Gap closed)
        "completion_delay_months": 7.0,        # Delta: -1.0 (Delay stabilized)
    }

    obs = OutcomeObservation(
        observation_id="OBS-001",
        project_code="NH-LRN-01",
        intervention_id="EXEC-001",
        pre_metrics=pre_metrics,
        post_metrics=post_metrics,
        confounders=[]
    )

    assessment = analyzer.evaluate_effectiveness(
        observation=obs,
        predicted_benefit=0.85,
        predicted_risk_reduction=0.80
    )

    assert assessment.attribution == OutcomeAttribution.LIKELY_EFFECTIVE
    assert assessment.is_success is True
    assert assessment.is_failure is False
    assert assessment.net_effectiveness_score >= 0.85
    assert assessment.calibration_error <= 0.15
    assert assessment.component_breakdown["risk_reduction_component"] == 1.0


# ============================================================================
# 2. Adverse Outcome and Failure Classification
# ============================================================================
def test_adverse_outcome_and_failure_classification():
    """Verifies that catastrophic post-intervention outcomes are classified as FAILED."""
    analyzer = EffectivenessAnalyzer()

    pre_metrics = {"risk_score": 65.0, "progress_expenditure_gap_pct": 5.0, "completion_delay_months": 3.0}
    
    # Situation deteriorated severely after intervention (e.g., contractor dispute / abandonment)
    post_metrics = {"risk_score": 82.0, "progress_expenditure_gap_pct": 15.0, "completion_delay_months": 9.0}

    obs = OutcomeObservation(
        observation_id="OBS-FAIL-01",
        project_code="NH-FAIL-01",
        intervention_id="EXEC-FAIL-01",
        pre_metrics=pre_metrics,
        post_metrics=post_metrics,
        confounders=[]
    )

    assessment = analyzer.evaluate_effectiveness(
        observation=obs,
        predicted_benefit=0.70,
        predicted_risk_reduction=0.60
    )

    assert assessment.attribution == OutcomeAttribution.FAILED
    assert assessment.is_failure is True
    assert assessment.is_success is False
    assert assessment.net_effectiveness_score <= 0.20
    assert assessment.calibration_error >= 0.50


# ============================================================================
# 3. Confounder Discounting
# ============================================================================
def test_confounder_discounting():
    """Verifies that external confounders discount direct causal attribution."""
    analyzer = EffectivenessAnalyzer()

    pre_metrics = {"risk_score": 75.0, "progress_expenditure_gap_pct": 12.0, "completion_delay_months": 6.0}
    post_metrics = {"risk_score": 62.0, "progress_expenditure_gap_pct": 5.0, "completion_delay_months": 5.0}

    # External confounder: unexpected central monsoon cessation and emergency state grant
    obs_confounded = OutcomeObservation(
        observation_id="OBS-CONF-01",
        project_code="NH-CONF-01",
        intervention_id="EXEC-CONF-01",
        pre_metrics=pre_metrics,
        post_metrics=post_metrics,
        confounders=["monsoon_cessation", "supplementary_state_grant"]
    )

    assessment = analyzer.evaluate_effectiveness(
        observation=obs_confounded,
        predicted_benefit=0.80
    )

    assert assessment.attribution == OutcomeAttribution.CONFOUNDED
    assert assessment.confounder_discount == 0.50
    # Net effectiveness must be discounted
    assert assessment.net_effectiveness_score < assessment.raw_effectiveness_score


# ============================================================================
# 4. Institutional Memory Synchronization
# ============================================================================
def test_institutional_memory_synchronization(clean_memory_store):
    """Verifies that evaluated outcomes update PrecedentMemoryStore and FailureMemoryManager."""
    syncer = InstitutionalMemorySyncer(clean_memory_store)
    analyzer = EffectivenessAnalyzer()

    # 1. Sync Successful Outcome
    pre_metrics = {"risk_score": 75.0, "progress_expenditure_gap_pct": 10.0, "completion_delay_months": 4.0}
    post_metrics_succ = {"risk_score": 60.0, "progress_expenditure_gap_pct": 2.0, "completion_delay_months": 4.0}
    obs_succ = OutcomeObservation(
        observation_id="OBS-S1",
        project_code="NH-SYNC-SUCC",
        intervention_id="EXEC-S1",
        pre_metrics=pre_metrics,
        post_metrics=post_metrics_succ
    )
    ass_succ = analyzer.evaluate_effectiveness(obs_succ, predicted_benefit=0.80)

    prec_succ = syncer.sync_outcome_to_precedent(
        observation=obs_succ,
        assessment=ass_succ,
        action_title="Restructure escrow milestone disbursements",
        action_type="FINANCIAL_RESTRUCTURING"
    )

    assert prec_succ.status == "VALIDATED"
    assert prec_succ.success_count == 2  # Created with 1 + updated with 1
    assert prec_succ.failure_count == 0
    assert prec_succ.track_record > 0.60
    assert clean_memory_store.get_precedent(prec_succ.id) is not None

    # 2. Sync Failed Outcome
    post_metrics_fail = {"risk_score": 88.0, "progress_expenditure_gap_pct": 20.0, "completion_delay_months": 10.0}
    obs_fail = OutcomeObservation(
        observation_id="OBS-F1",
        project_code="NH-SYNC-FAIL",
        intervention_id="EXEC-F1",
        pre_metrics=pre_metrics,
        post_metrics=post_metrics_fail
    )
    ass_fail = analyzer.evaluate_effectiveness(obs_fail, predicted_benefit=0.75)

    prec_fail = syncer.sync_outcome_to_precedent(
        observation=obs_fail,
        assessment=ass_fail,
        action_title="Immediate unilateral penalty and forfeit bank guarantee",
        action_type="PENALTY_ENFORCEMENT"
    )

    assert prec_fail.failure_count == 2
    assert prec_fail.success_count == 0
    assert prec_fail.track_record < 0.40

    # Verify negative warnings emitted for similar future actions
    failed_list = clean_memory_store.find_failed_precedents()
    assert any(f.id == prec_fail.id for f in failed_list)
    warnings = FailureMemoryManager.check_negative_warnings(
        failed_precedents=failed_list,
        candidate_action="Immediate unilateral penalty on contractor"
    )
    assert len(warnings) >= 1
    assert any("failed" in w.lower() for w in warnings)


# ============================================================================
# 5. Dynamic Recommendation Recalibration
# ============================================================================
def test_dynamic_recommendation_recalibration():
    """Verifies that empirical track records adjust future candidate benefit and risk scores."""
    recalibrator = RecommendationEvaluator()
    analyzer = EffectivenessAnalyzer()

    # Action Type A: Highly successful forensic audit
    pre_metrics = {"risk_score": 75.0, "progress_expenditure_gap_pct": 15.0, "completion_delay_months": 6.0}
    post_metrics_succ = {"risk_score": 58.0, "progress_expenditure_gap_pct": 3.0, "completion_delay_months": 5.0}
    obs_succ = OutcomeObservation("OBS-A1", "NH-01", "EX-01", pre_metrics, post_metrics_succ)
    ass_succ = analyzer.evaluate_effectiveness(obs_succ, predicted_benefit=0.82)

    # Record 3 consecutive successes for FORENSIC_AUDIT
    for _ in range(3):
        recalibrator.record_outcome_feedback("FORENSIC_AUDIT", 0.82, ass_succ)

    calib_succ = recalibrator.get_calibration("FORENSIC_AUDIT")
    assert calib_succ.track_record >= 0.75
    assert calib_succ.calibration_multiplier > 1.20

    # Calibrate candidate with FORENSIC_AUDIT
    cand_forensic = RecommendationCandidate(
        id="CAND-TEST-CALIB",
        title="Joint Fact-Finding Audit",
        action_type="FORENSIC_AUDIT",
        expected_benefit=0.70,
        implementation_risk=0.20
    )
    recalibrator.calibrate_candidate(cand_forensic)
    assert cand_forensic.expected_benefit > 0.70, "Proven action type must receive benefit boost"

    # Action Type B: High-failure punitive enforcement
    post_metrics_fail = {"risk_score": 88.0, "progress_expenditure_gap_pct": 20.0, "completion_delay_months": 12.0}
    obs_fail = OutcomeObservation("OBS-B1", "NH-02", "EX-02", pre_metrics, post_metrics_fail)
    ass_fail = analyzer.evaluate_effectiveness(obs_fail, predicted_benefit=0.75)

    # Record 3 failures for PENALTY_ENFORCEMENT
    for _ in range(3):
        recalibrator.record_outcome_feedback("PENALTY_ENFORCEMENT", 0.75, ass_fail)

    calib_fail = recalibrator.get_calibration("PENALTY_ENFORCEMENT")
    assert calib_fail.track_record < 0.35
    assert calib_fail.calibration_multiplier < 0.90

    # Calibrate candidate with PENALTY_ENFORCEMENT
    cand_penalty = RecommendationCandidate(
        id="CAND-TEST-FAIL",
        title="Forfeit Bank Guarantee",
        action_type="PENALTY_ENFORCEMENT",
        expected_benefit=0.70,
        implementation_risk=0.30
    )
    recalibrator.calibrate_candidate(cand_penalty)
    assert cand_penalty.expected_benefit < 0.70, "Failed action type must have benefit dampened"
    assert cand_penalty.implementation_risk > 0.30, "Failed action type must have risk penalized"


# ============================================================================
# 6. Portfolio MACE and Learning Metrics
# ============================================================================
def test_portfolio_mace_and_learning_metrics():
    """Verifies computation of portfolio-wide Mean Absolute Calibration Error (MACE) and success rate."""
    recalibrator = RecommendationEvaluator()
    analyzer = EffectivenessAnalyzer()

    # Case 1: High accuracy prediction
    obs1 = OutcomeObservation("OBS-M1", "P-1", "EX-1", {"risk_score": 70.0}, {"risk_score": 58.0})
    ass1 = analyzer.evaluate_effectiveness(obs1, predicted_benefit=0.80)
    recalibrator.record_outcome_feedback("AUDIT", 0.80, ass1)

    # Case 2: Overconfident prediction
    obs2 = OutcomeObservation("OBS-M2", "P-2", "EX-2", {"risk_score": 70.0}, {"risk_score": 68.0})
    ass2 = analyzer.evaluate_effectiveness(obs2, predicted_benefit=0.90)
    recalibrator.record_outcome_feedback("RECOVERY", 0.90, ass2)

    portfolio = recalibrator.compute_portfolio_metrics()
    assert portfolio["total_evaluations"] == 2
    assert portfolio["mean_absolute_calibration_error"] > 0.0
    assert 0.0 <= portfolio["portfolio_success_rate"] <= 1.0


# ============================================================================
# 7. End-to-End 7-Stage Closed Loop Lifecycle
# ============================================================================
def test_end_to_end_7_stage_closed_loop_lifecycle(clean_memory_store):
    """Executes the complete canonical closed loop connecting all 7 stages:
    recommendation -> approval -> intervention -> outcome -> effectiveness -> memory -> recommendation evaluation.
    """
    engine = OutcomeLearningEngine(memory_store=clean_memory_store)

    # Stage 1: Recommendation Candidate (from Phase 11)
    cand = RecommendationCandidate(
        id="REC-CANONICAL-01",
        title="Restructure contractor milestone escrow account with third-party technical audit",
        action_type="FINANCIAL_RESTRUCTURING",
        expected_benefit=0.86,
        expected_risk_reduction=0.80,
        implementation_risk=0.20,
        approval_class="managerial"
    )

    # Stage 2: Human Approval Record (from Phase 12)
    approver = Actor(id="sec_01", name="Secretary Infrastructure", role=Role.MINISTRY_SECRETARY)
    req = ApprovalRequest(
        request_id="REQ-LRN-01",
        project_code="NH-CLOSE-LOOP-99",
        candidate_id=cand.id,
        action_title=cand.title,
        action_type=cand.action_type,
        approval_class="managerial",
        urgency="HIGH",
        proposed_by=Actor(id="ai_rec", name="AI Recommender", role=Role.AI_RECOMMENDER),
        cost_cr=25.0
    )
    app_record = ApprovalRecord(
        record_id="REC-APP-LRN-01",
        request=req,
        decision=ApprovalDecision(
            decision=ApprovalStatus.APPROVED,
            approver=approver,
            justification="Approved for escrow restructuring."
        ),
        gate_evaluations={"all": True},
        signature_token="MOCK_SIG_01"
    )

    # Stage 3: Operational Intervention Execution (from Phase 12)
    executor = Actor(id="pd_01", name="Project Director", role=Role.PROJECT_DIRECTOR)
    exec_record = ExecutionRecord(
        execution_id="EXEC-LRN-99",
        approval_record_id=app_record.record_id,
        project_code=req.project_code,
        action_title=cand.title,
        action_type=cand.action_type,
        executor=executor,
        dispatch_channel="PMIS_DISPATCH",
        execution_status=ExecutionStatus.COMPLETED
    )

    # Stage 4: Empirical Post-Intervention Observation
    pre_metrics = {"risk_score": 80.0, "progress_expenditure_gap_pct": 22.0, "completion_delay_months": 10.0}
    post_metrics = {"risk_score": 62.0, "progress_expenditure_gap_pct": 8.0, "completion_delay_months": 9.0}

    # Execute Stages 4 -> 5 -> 6 -> 7 via OutcomeLearningEngine
    milestone = engine.process_closed_loop(
        candidate=cand,
        approval_record=app_record,
        execution_record=exec_record,
        pre_metrics=pre_metrics,
        post_metrics=post_metrics,
        confounders=None,
        independence_group="RO_NAGPUR"
    )

    # 1. Verify Milestone Structure and Lifecycle Integration
    assert milestone.milestone_id.startswith("MLS-LRN-")
    assert milestone.project_code == "NH-CLOSE-LOOP-99"
    assert milestone.candidate_id == cand.id
    assert milestone.approval_record_id == app_record.record_id
    assert milestone.execution_id == exec_record.execution_id

    # 2. Verify Effectiveness Assessment
    assert milestone.assessment.attribution == OutcomeAttribution.LIKELY_EFFECTIVE
    assert milestone.assessment.net_effectiveness_score >= 0.85
    assert milestone.assessment.calibration_error <= 0.15

    # 3. Verify Institutional Memory Consolidation
    assert milestone.precedent_status == "VALIDATED"
    assert milestone.precedent_track_record > 0.60
    stored_prec = clean_memory_store.get_precedent(milestone.precedent_id)
    assert stored_prec is not None
    assert stored_prec.success_count >= 1

    # 4. Verify Recommendation Recalibration Feedback
    calib = milestone.updated_calibration
    assert calib.action_type == "FINANCIAL_RESTRUCTURING"
    assert calib.success_count == 1
    assert calib.calibration_multiplier > 1.0

    # 5. Verify Future Candidate Generation receives empirical calibration boost!
    future_cand = RecommendationCandidate(
        id="REC-FUTURE-01",
        title="Escrow restructuring package 2",
        action_type="FINANCIAL_RESTRUCTURING",
        expected_benefit=0.75
    )
    engine.recommendation_evaluator.calibrate_candidate(future_cand)
    assert future_cand.expected_benefit > 0.75, "Subsequent candidate must be dynamically calibrated by outcome memory"
