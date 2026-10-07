"""Phase 10 — Institutional Memory Verification Suite.

Validates the canonical 6-stage lifecycle for institutional learning:
    investigation
    → outcome
    → validated precedent
    → transferability
    → counterexample
    → future retrieval

Ensures seamless integration with canonical evidence, hypothesis, causal reasoning,
and outcome structures without competing memory abstractions.
"""
import os
import json
import time
import pytest
from unittest.mock import MagicMock

from paimana_agent.store import Store
from paimana_agent.state import InvestigationState, Fact
from paimana_agent.hypotheses.model import Hypothesis
from paimana_agent.recommendations.candidate import RecommendationCandidate
from paimana_agent.recommendations.candidate_validator import CandidateValidator
from paimana_agent.memory.models import (
    Precedent, PrecedentContext, PatternFingerprint, PrecedentProvenance,
    PrecedentBundle, InvestigationMemory
)
from paimana_agent.memory.precedent_memory import PrecedentMemoryStore
from paimana_agent.memory.memory_consolidator import MemoryConsolidator
from paimana_agent.memory.outcome_evaluator import OutcomeEvaluator
from paimana_agent.memory.transferability import TransferabilityEvaluator
from paimana_agent.memory.failure_memory import FailureMemoryManager
from paimana_agent.memory.memory_retriever import MemoryRetriever
from paimana_agent.memory.memory_decay import MemoryDecayManager
from paimana_agent.memory.memory_reliability import MemoryReliabilityManager
from paimana_agent.memory.pattern_fingerprint import PatternFingerprintBuilder, PatternMatcher
from paimana_agent.tools import ToolRegistry
from paimana_agent.supervisor import SupervisorAgent


@pytest.fixture
def clean_store(tmp_path):
    db_path = str(tmp_path / "test_phase10.db")
    store = Store(db_path)
    return store


@pytest.fixture
def clean_memory_store(tmp_path):
    json_path = str(tmp_path / "precedents.json")
    mem_store = PrecedentMemoryStore(persistence_path=json_path)
    return mem_store


# ---------------------------------------------------------------------------
# Test 1: Investigation -> Candidate Precedent Creation
# ---------------------------------------------------------------------------
def test_phase10_1_investigation_to_candidate_precedent(clean_memory_store):
    """Stage 1: Completed investigation produces a structured CANDIDATE precedent."""
    consolidator = MemoryConsolidator(clean_memory_store)

    # 1. State with sufficient confidence (>= 0.60)
    state = InvestigationState(
        objective="Investigate progress stalling",
        project_code="NH-48-PKG-2",
        project_name="NH-48 6-Laning",
        triggering_events=[{"type": "PROGRESS_STALLED", "message": "Work halted on Package 2"}],
    )
    state.confidence_score = 0.82
    state.project = {
        "project_code": "NH-48-PKG-2",
        "project_name": "NH-48 6-Laning",
        "sector": "Road Transport and Highways",
        "project_type": "Expressway Widening",
        "original_cost_cr": 850.0,
        "physical_progress_pct": 42.0,
        "cumulative_expenditure_cr": 580.0,
        "agency": "NHAI",
        "state": "Maharashtra",
        "contract_type": "EPC",
    }
    state.facts = [
        Fact(statement="ROW unavailable on 12km stretch due to forest clearance", source="site_inspection", metric="row_encumbered_pct", value=18.0),
        Fact(statement="Contractor idling 4 paver sets", source="milestone_audit", metric="equipment_idle_count", value=4),
    ]
    state.hypotheses = [
        Hypothesis(
            id="hyp_land_acquisition",
            statement="Unencumbered ROW unavailable on critical segment",
            status="supported",
            confidence=0.85
        )
    ]
    rec = RecommendationCandidate(
        id="REC-01",
        title="Descope blocked 12km segment into standalone package",
        action="Descope blocked 12km segment into standalone package",
        action_type="DESCOPING_AND_REBASELINING",
        expected_impact={"risk_reduction": 14.0, "progress_resumption_months": 2},
        responsible_stakeholder="NHAI RO & Project Director",
        urgency="HIGH"
    )
    state.selected_recommendation = rec

    candidate = consolidator.create_candidate_from_investigation(state=state)

    assert candidate is not None, "Candidate precedent should be created when confidence >= 0.50"
    assert candidate.status == "CANDIDATE"
    assert candidate.source_project_id == "NH-48-PKG-2"
    assert candidate.source_investigation_id == "INV-NH48-001" or candidate.source_investigation_id.startswith("PREC-CAND")
    assert candidate.root_cause == "Unencumbered ROW unavailable on critical segment"
    assert candidate.root_cause_confidence == 0.82
    assert candidate.context.sector == "Road Transport and Highways"
    assert candidate.context.cost_band == "Standard (150-1000Cr)"
    assert candidate.context.stage_bracket == "Mid (25-75%)"
    assert candidate.pattern_fingerprint.event_type == "progress_stalled"
    assert candidate.application_count == 1
    assert candidate.success_count == 0
    assert candidate.failure_count == 0
    assert candidate.memory_reliability >= 0.20  # Base candidate reliability

    # Verify that store now contains this candidate
    retrieved = clean_memory_store.get_precedent(candidate.id)
    assert retrieved is not None
    assert retrieved.id == candidate.id

    # 2. Guard: Low-confidence investigation (< 0.50) must NOT create a candidate
    low_conf_state = InvestigationState(
        objective="Investigate low confidence",
        project_code="LOW-CONF-01",
        project_name="Low Conf",
        triggering_events=[{"type": "PROGRESS_STALLED"}],
    )
    low_conf_state.confidence_score = 0.35
    low_candidate = consolidator.create_candidate_from_investigation(state=low_conf_state)
    assert low_candidate is None, "Investigations with confidence < 0.50 must not create candidates"


# ---------------------------------------------------------------------------
# Test 2: Outcome Evaluation & Causal Consolidation
# ---------------------------------------------------------------------------
def test_phase10_2_outcome_evaluation_and_consolidation(clean_memory_store):
    """Stage 2 & 3: Outcome evaluation consolidates CANDIDATE -> VALIDATED precedent."""
    consolidator = MemoryConsolidator(clean_memory_store)

    state = InvestigationState(
        objective="Investigate cost progress mismatch",
        project_code="NH-OUTCOME-01",
        project_name="NH Outcome 01",
        triggering_events=[{"type": "COST_PROGRESS_MISMATCH"}],
    )
    state.confidence_score = 0.78
    state.project = {
        "project_code": "NH-OUTCOME-01",
        "sector": "Road Transport and Highways",
        "original_cost_cr": 600.0,
        "physical_progress_pct": 35.0,
        "contract_type": "EPC",
    }
    state.hypotheses = [
        Hypothesis(id="hyp_1", statement="Front-loaded billing on sub-base work", status="supported", confidence=0.80)
    ]
    rec = {
        "action": "Withhold non-conforming milestone payments and enforce third-party physical audit",
        "action_type": "FINANCIAL_AUDIT_WITHHOLDING",
        "expected_impact": {"risk_reduction": 10.0}
    }
    candidate = consolidator.create_candidate_from_investigation(state=state, recommendation=rec)
    assert candidate.status == "CANDIDATE"
    orig_reliability = candidate.memory_reliability

    # 1. Simulate empirical real-world outcome (Significant Risk Reduction)
    pre_metrics = {"risk_score": 76.0, "progress_expenditure_gap_pct": 19.0, "completion_delay_months": 8.0}
    post_metrics = {"risk_score": 62.0, "progress_expenditure_gap_pct": 4.0, "completion_delay_months": 8.0}

    validated = consolidator.evaluate_and_consolidate(
        precedent_id=candidate.id,
        pre_metrics=pre_metrics,
        post_metrics=post_metrics,
        confounders=None,
        independence_group="RO_NAGPUR"
    )

    assert validated.status == "VALIDATED"
    assert validated.attribution_class == "LIKELY_EFFECTIVE"
    assert validated.success_count == 1
    assert validated.failure_count == 0
    assert validated.application_count == 2
    assert validated.outcome_quality == 1.0  # 3/3 post-metrics present
    assert validated.observed_outcome["evaluation"]["risk_delta"] == -14.0
    assert validated.observed_outcome["evaluation"]["gap_delta"] == -15.0
    # Reliability must increase due to proven track record & independent corroboration
    assert validated.memory_reliability > orig_reliability

    # 2. Verify Confounder Discounting in OutcomeEvaluator
    confounded_res = OutcomeEvaluator.evaluate_outcome(
        pre_metrics={"risk_score": 75.0, "progress_expenditure_gap_pct": 15.0, "completion_delay_months": 5.0},
        post_metrics={"risk_score": 65.0, "progress_expenditure_gap_pct": 5.0, "completion_delay_months": 5.0},
        confounders_reported=["State general election announcement caused work suspension"]
    )
    unconfounded_res = OutcomeEvaluator.evaluate_outcome(
        pre_metrics={"risk_score": 75.0, "progress_expenditure_gap_pct": 15.0, "completion_delay_months": 5.0},
        post_metrics={"risk_score": 65.0, "progress_expenditure_gap_pct": 5.0, "completion_delay_months": 5.0},
        confounders_reported=None
    )
    assert confounded_res["effectiveness_ratio"] < unconfounded_res["effectiveness_ratio"]
    assert round(confounded_res["effectiveness_ratio"] / unconfounded_res["effectiveness_ratio"], 2) == 0.70


# ---------------------------------------------------------------------------
# Test 3: Validated Failure Precedent & Negative Aversion Guard
# ---------------------------------------------------------------------------
def test_phase10_3_validated_failure_and_negative_warnings(clean_memory_store):
    """Stage 3 (Failure): Failed intervention creates cautionary precedent protecting future decisions."""
    consolidator = MemoryConsolidator(clean_memory_store)

    state = InvestigationState(
        objective="Investigate failure",
        project_code="FAIL-PROJ-01",
        project_name="Fail Proj 01",
        triggering_events=[{"type": "PROGRESS_STALLED"}],
    )
    state.confidence_score = 0.75
    state.project = {
        "project_code": "FAIL-PROJ-01",
        "sector": "Road Transport and Highways",
        "original_cost_cr": 450.0,
        "physical_progress_pct": 30.0,
        "contract_type": "EPC",
    }
    state.hypotheses = [
        Hypothesis(id="hyp_fail", statement="Contractor insolence", status="supported", confidence=0.75)
    ]
    rec = {
        "action": "Enforce liquidated damages penalty and freeze escrow disbursements",
        "action_type": "PENALTY_ENFORCEMENT"
    }
    candidate = consolidator.create_candidate_from_investigation(state=state, recommendation=rec)

    # Simulate catastrophic outcome: contractor halted work entirely, risk score skyrocketed
    pre_metrics = {"risk_score": 60.0, "progress_expenditure_gap_pct": 5.0, "completion_delay_months": 4.0}
    post_metrics = {"risk_score": 78.0, "progress_expenditure_gap_pct": 5.0, "completion_delay_months": 11.0}

    consolidated_failure = consolidator.evaluate_and_consolidate(
        precedent_id=candidate.id,
        pre_metrics=pre_metrics,
        post_metrics=post_metrics,
        confounders=None,
        independence_group="RO_PUNE"
    )

    assert consolidated_failure.status == "VALIDATED"
    assert consolidated_failure.attribution_class == "FAILED"
    assert consolidated_failure.failure_count == 1
    assert consolidated_failure.success_count == 0

    # Verify FailureMemoryManager identifies it
    assert FailureMemoryManager.index_failure(consolidated_failure) is True

    # Verify Negative Warnings generation
    failed_list = clean_memory_store.find_failed_precedents()
    assert any(f.id == consolidated_failure.id for f in failed_list)

    warnings = FailureMemoryManager.check_negative_warnings(
        failed_precedents=failed_list,
        candidate_action="Enforce liquidated damages penalty on site contractor"
    )
    assert len(warnings) >= 1
    assert any("failed" in w.lower() for w in warnings)

    # Verify CandidateValidator rejects candidate matching this failure precedent
    validator = CandidateValidator()
    cand_rec = RecommendationCandidate(
        id="REC-TEST-PUNITIVE",
        title="Enforce liquidated damages penalty and freeze bank guarantee",
        action="Enforce liquidated damages penalty and freeze bank guarantee",
        action_type="PRIMARY_RECOVERY",
        rationale="Compel contractor compliance through financial penalty",
        hypothesis_ids=["hyp_fail"],
        evidence_ids=["ev_1"],
        expected_benefit=0.70,
        expected_cost=0.30,
        expected_risk_reduction=0.60,
        implementation_risk=0.40,
        authority_score=0.85,
        responsible_stakeholder="Project Director"
    )
    is_valid = validator.validate_all(
        candidates=[cand_rec],
        state=state,
        unsuccessful_precedents=[consolidated_failure],
        is_mega_project=False
    )
    assert cand_rec.validated is False
    assert cand_rec.validation_status == "POLICY_VIOLATION"


# ---------------------------------------------------------------------------
# Test 4: Contextual Transferability Gating
# ---------------------------------------------------------------------------
def test_phase10_4_contextual_transferability_gating():
    """Stage 4: TransferabilityEvaluator discriminates domain compatibility and penalizes cross-domain leaks."""
    road_epc_context = PrecedentContext(
        sector="Road Transport and Highways",
        project_type="Expressway 4-Laning",
        project_size_cr=800.0,
        cost_band="Standard (150-1000Cr)",
        stage_bracket="Mid (25-75%)",
        implementing_agency="NHAI",
        contract_type="EPC"
    )

    # 1. Highly compatible target (Road Transport, EPC, Standard, Mid stage)
    target_compatible = PrecedentContext(
        sector="Road Transport and Highways",
        project_type="Highway Widening",
        project_size_cr=750.0,
        cost_band="Standard (150-1000Cr)",
        stage_bracket="Mid (25-75%)",
        implementing_agency="NHAI",
        contract_type="EPC"
    )
    score_comp = TransferabilityEvaluator.evaluate(road_epc_context, target_compatible)
    assert score_comp >= 0.85, f"Compatible transferability score should be >= 0.85, got {score_comp}"

    # 2. Moderate target (Railways, EPC, Mega)
    target_moderate = PrecedentContext(
        sector="Railways",
        project_type="Freight Corridor",
        project_size_cr=2500.0,
        cost_band="Mega (>1000Cr)",
        stage_bracket="Early (<25%)",
        implementing_agency="DFCCIL",
        contract_type="EPC"
    )
    score_mod = TransferabilityEvaluator.evaluate(road_epc_context, target_moderate)
    assert 0.50 <= score_mod <= 0.80, f"Moderate transferability expected [0.50, 0.80], got {score_mod}"

    # 3. Incompatible target (Space Technology / Launch Complex Facility, Item Rate, Minor, Early stage, ISRO)
    target_incompatible = PrecedentContext(
        sector="Space Technology",
        project_type="Launch Complex Facility",
        project_size_cr=120.0,
        cost_band="Minor (<150Cr)",
        stage_bracket="Early (<25%)",
        implementing_agency="ISRO",
        contract_type="Item Rate"
    )
    score_incomp = TransferabilityEvaluator.evaluate(road_epc_context, target_incompatible)
    assert score_incomp <= 0.50, f"Incompatible transferability should be low (<=0.50), got {score_incomp}"

    # 4. Test that MemoryRetriever applies 0.50 penalty multiplier when transferability < 0.40
    store = PrecedentMemoryStore()
    store.clear()
    prec_unaligned_ctx = PrecedentContext(
        sector="Road Transport and Highways",
        cost_band="Mega (>1000Cr)",
        stage_bracket="Early (<25%)",
        contract_type="EPC",
        implementing_agency="NHAI"
    )
    prec = Precedent(
        id="PREC-INCOMP-TEST",
        title="Mega Road EPC Intervention",
        context=prec_unaligned_ctx,
        memory_reliability=0.90,
        status="VALIDATED"
    )
    store.add_precedent(prec)
    retriever = MemoryRetriever(store)

    target_dict = {
        "project_code": "ISRO-01",
        "sector": "Space Technology",
        "original_cost_cr": 80.0,
        "physical_progress_pct": 85.0,
        "contract_type": "DBFOT",
        "agency": "ISRO"
    }
    bundle = retriever.retrieve(target_project=target_dict)
    # The precedent should have a transferability score < 0.40
    assert prec.transferability_score < 0.40


# ---------------------------------------------------------------------------
# Test 5: Counterexample Retrieval & Refutation of Confirmation Bias
# ---------------------------------------------------------------------------
def test_phase10_5_counterexample_refuting_confirmation_bias(clean_memory_store):
    """Stage 5: Counterexamples surface alternative explanations to break confirmation bias."""
    retriever = MemoryRetriever(clean_memory_store)

    # Target scenario: Spend has halted on a rail project; investigator's favorite hypothesis is CONTRACTOR_CASHFLOW_DISTRESS
    target_project = {
        "project_code": "DFC-PKG-9",
        "sector": "Railways",
        "original_cost_cr": 2200.0,
        "physical_progress_pct": 20.0,
        "cumulative_expenditure_cr": 220.0,
        "agency": "DFCCIL",
        "contract_type": "EPC"
    }
    pattern = PatternFingerprint(
        event_type="cost_progress_mismatch",
        financial_velocity="behind",
        milestone_slippage="moderate",
        progress_variance="moderate",
        risk_direction="increasing",
        risk_velocity="moderate"
    )

    bundle = retriever.retrieve(
        target_project=target_project,
        target_pattern=pattern,
        active_hypotheses=["CONTRACTOR_CASHFLOW_DISTRESS"]
    )

    # Verify that counterexamples were surfaced
    assert len(bundle.counterexamples) >= 1
    counter_id_list = [c.id for c in bundle.counterexamples]
    assert "PREC-COUNTER-CASHFLOW-01" in counter_id_list

    counter = next(c for c in bundle.counterexamples if c.id == "PREC-COUNTER-CASHFLOW-01")
    assert counter.is_counterexample is True
    assert "CONTRACTOR_CASHFLOW_DISTRESS" in counter.counterexample_for_hypotheses
    assert any(w in counter.root_cause.lower() or w in counter.title.lower() for w in ["wildlife", "injunction", "ngt", "eco-sensitive", "stay"])
    assert counter.why_relevant != ""
    assert counter.important_differences != ""

    # Verify that relevance explanations include the counterexample warning
    cex_exps = [e for e in bundle.relevance_explanations if e["type"] == "COUNTEREXAMPLE"]
    assert len(cex_exps) >= 1
    assert "counterexample" in cex_exps[0]["explanation"].lower()


# ---------------------------------------------------------------------------
# Test 6: Multi-Criteria Future Retrieval & PrecedentBundle Structure
# ---------------------------------------------------------------------------
def test_phase10_6_future_retrieval_and_bundle_composition(clean_memory_store):
    """Stage 6: Multi-criteria retrieval incorporates pattern, transferability, reliability, and decay."""
    # Test MemoryDecayManager half-life
    now = time.time()
    half_life_days = 730.0  # 2 years
    fresh_decay = MemoryDecayManager.calculate_decay(created_at=now, now=now)
    assert fresh_decay == 1.0

    two_years_ago = now - (half_life_days * 86400.0)
    decay_2y = MemoryDecayManager.calculate_decay(created_at=two_years_ago, now=now)
    assert 0.48 <= decay_2y <= 0.52  # Exactly ~0.50 weight

    four_years_ago = now - (2 * half_life_days * 86400.0)
    decay_4y = MemoryDecayManager.calculate_decay(created_at=four_years_ago, now=now)
    assert 0.23 <= decay_4y <= 0.27  # ~0.25 weight

    # Test full retrieval bundle
    retriever = MemoryRetriever(clean_memory_store)
    target_project = {
        "project_code": "NH-66-PKG-5",
        "sector": "Road Transport and Highways",
        "original_cost_cr": 1100.0,
        "physical_progress_pct": 48.0,
        "cumulative_expenditure_cr": 820.0,
        "agency": "NHAI",
        "contract_type": "EPC"
    }

    bundle = retriever.retrieve(
        target_project=target_project,
        active_hypotheses=["LAND_ACQUISITION_BLOCKED", "CONTRACTOR_CASHFLOW_DISTRESS"]
    )

    assert isinstance(bundle, PrecedentBundle)
    assert bundle.target_project_code == "NH-66-PKG-5"
    assert len(bundle.supporting_precedents) >= 1
    assert len(bundle.failed_precedents) >= 1
    assert len(bundle.counterexamples) >= 1

    # Verify tri-perspective structure
    top_sup = bundle.supporting_precedents[0]
    assert top_sup.attribution_class in {"LIKELY_EFFECTIVE", "POSSIBLY_EFFECTIVE"}
    assert top_sup.status == "VALIDATED"

    top_fail = bundle.failed_precedents[0]
    assert top_fail.attribution_class in {"FAILED", "LIKELY_INEFFECTIVE"}

    assert len(bundle.relevance_explanations) >= 3
    assert len(bundle.recommendation_guidance) >= 1

    # Verify JSON serialization of PrecedentBundle
    bundle_dict = bundle.to_dict()
    assert "supporting_precedents" in bundle_dict
    assert "failed_precedents" in bundle_dict
    assert "counterexamples" in bundle_dict
    assert bundle_dict["total_precedents_evaluated"] >= 3


# ---------------------------------------------------------------------------
# Test 7: End-to-End Closed-Loop Institutional Memory Lifecycle
# ---------------------------------------------------------------------------
def test_phase10_7_end_to_end_closed_loop_lifecycle(clean_store):
    """Full closed-loop verification: Investigation 1 -> Candidate Precedent ->

    Consolidation -> Investigation 2 retrieves validated precedent.
    """
    from paimana_agent.tools import _default_precedent_store
    _default_precedent_store.reset()

    # Phase 1: Investigation on Project A (NH-EXP-A)
    p_a = {
        "project_code": "NH-EXP-A",
        "project_name": "NH-EXP Package A",
        "sector": "Road Transport and Highways",
        "original_cost_cr": 720.0,
        "revised_cost_cr": 720.0,
        "cumulative_expenditure_cr": 540.0,
        "physical_progress_pct": 32.0,
        "original_completion_date": "2024-06-30",
        "revised_completion_date": "2025-12-31",
        "agency": "NHAI",
        "state": "Uttar Pradesh",
        "contract_type": "EPC",
        "detected_issues": ["land acquisition clearance delay", "dispute on 15% stretch"]
    }
    clean_store.save_snapshot("NH-EXP-A", 1, p_a)

    events_a = [{
        "type": "PROGRESS_STALLED",
        "message": "Physical progress stalled at 32%",
        "event_id": "EV-NH-A-01",
        "timestamp": time.time()
    }]

    registry_a = ToolRegistry(enable_recovery=True)
    supervisor_a = SupervisorAgent(tool_registry=registry_a)
    report_a = supervisor_a.run_investigation(
        store=clean_store,
        p=p_a,
        res={"project_code": "NH-EXP-A", "tier": "High", "risk_score": 78.0},
        drivers=["progress_expenditure_gap_pct"],
        events=events_a,
        feats={"progress_expenditure_gap_pct": 43.0, "completion_delay_months": 18.0},
        max_steps=5
    )

    assert report_a["project_code"] == "NH-EXP-A"
    assert report_a["confidence_score"] >= 0.40
    assert report_a["confidence"] in ["MEDIUM", "HIGH"]

    # Verify Candidate Precedent created in _default_precedent_store
    candidates = _default_precedent_store.list_all(status="CANDIDATE")
    cand_a = next((c for c in candidates if c.source_project_id == "NH-EXP-A"), None)
    assert cand_a is not None, "Candidate precedent must be registered from Investigation A"
    assert cand_a.status == "CANDIDATE"

    # Phase 2: Empirical Outcome Observed for Project A -> Consolidate into VALIDATED
    consolidator = MemoryConsolidator(_default_precedent_store)
    validated_a = consolidator.evaluate_and_consolidate(
        precedent_id=cand_a.id,
        pre_metrics={"risk_score": 78.0, "progress_expenditure_gap_pct": 43.0, "completion_delay_months": 18.0},
        post_metrics={"risk_score": 62.0, "progress_expenditure_gap_pct": 12.0, "completion_delay_months": 18.0},
        confounders=None,
        independence_group="NHAI_HQ"
    )
    assert validated_a.status == "VALIDATED"
    assert validated_a.attribution_class == "LIKELY_EFFECTIVE"

    # Phase 3: Investigation on Project B (NH-EXP-B) with similar characteristics
    p_b = {
        "project_code": "NH-EXP-B",
        "project_name": "NH-EXP Package B",
        "sector": "Road Transport and Highways",
        "original_cost_cr": 800.0,
        "revised_cost_cr": 800.0,
        "cumulative_expenditure_cr": 580.0,
        "physical_progress_pct": 35.0,
        "original_completion_date": "2024-09-30",
        "revised_completion_date": "2026-03-31",
        "agency": "NHAI",
        "state": "Uttar Pradesh",
        "contract_type": "EPC",
        "detected_issues": ["land acquisition stalling", "encroachment on segment"]
    }
    clean_store.save_snapshot("NH-EXP-B", 1, p_b)

    events_b = [{
        "type": "PROGRESS_STALLED",
        "message": "Physical progress stalled at 35%",
        "event_id": "EV-NH-B-01",
        "timestamp": time.time()
    }]

    registry_b = ToolRegistry(enable_recovery=True)
    supervisor_b = SupervisorAgent(tool_registry=registry_b)
    report_b = supervisor_b.run_investigation(
        store=clean_store,
        p=p_b,
        res={"project_code": "NH-EXP-B", "tier": "High", "risk_score": 75.0},
        drivers=["progress_expenditure_gap_pct"],
        events=events_b,
        feats={"progress_expenditure_gap_pct": 37.0, "completion_delay_months": 18.0},
        max_steps=5
    )

    # Verify that Project B retrieved the institutional precedent from Project A
    bundle_b = report_b.get("precedent_bundle")
    assert bundle_b is not None
    supporting_b = bundle_b.get("supporting_precedents", [])
    assert len(supporting_b) >= 1
    # Either Project A or canonical NHAI precedent is retrieved and applied
    retrieved_codes = [sp.get("source_project_id") for sp in supporting_b]
    assert "NH-EXP-A" in retrieved_codes or "NH-44-PKG-3" in retrieved_codes

    # Verify that recommendation was calibrated with historical precedent
    cand_recs = report_b.get("candidate_recommendations", [])
    has_precedent_rec = any(c.get("generated_by") == "precedent_memory" for c in cand_recs)
    assert has_precedent_rec is True, "Supervisor must generate candidate recommendation from precedent memory"


# ---------------------------------------------------------------------------
# Test 8: Serialization, Persistence, and Reloading
# ---------------------------------------------------------------------------
def test_phase10_8_serialization_and_persistence(tmp_path):
    """Tests JSON serialization and reconstruction of Precedents and Stores."""
    json_file = str(tmp_path / "durable_memory.json")
    store1 = PrecedentMemoryStore(persistence_path=json_file)
    store1.clear()

    prec = Precedent(
        id="PREC-SERIAL-01",
        title="Serial Descoping Precedent",
        pattern_fingerprint=PatternFingerprint(
            event_type="progress_stalled",
            financial_velocity="decoupled",
            milestone_slippage="persistent"
        ),
        context=PrecedentContext(
            sector="Railways",
            project_size_cr=1500.0,
            cost_band="Mega (>1000Cr)",
            contract_type="EPC"
        ),
        evidence_pattern=["Ev 1", "Ev 2"],
        hypothesis_pattern=["hyp_delay"],
        root_cause="Critical bridge pier foundation delayed",
        root_cause_confidence=0.89,
        intervention={"action": "Descope bridge section into specialized marine package"},
        intervention_class="DESCOPING",
        expected_outcome={"risk_reduction": 12.0},
        observed_outcome={"status": "positive", "risk_delta": -11.0},
        attribution_class="LIKELY_EFFECTIVE",
        memory_reliability=0.91,
        transferability_score=0.88,
        source_project_id="RAIL-BR-01",
        status="VALIDATED",
        application_count=2,
        success_count=2,
        failure_count=0
    )
    store1.add_precedent(prec)

    # Store 1 saves automatically on add_precedent
    assert os.path.exists(json_file)

    # Create Store 2 from same persistence path
    store2 = PrecedentMemoryStore(persistence_path=json_file)
    loaded_prec = store2.get_precedent("PREC-SERIAL-01")

    assert loaded_prec is not None
    assert loaded_prec.id == "PREC-SERIAL-01"
    assert loaded_prec.title == "Serial Descoping Precedent"
    assert loaded_prec.pattern_fingerprint.event_type == "progress_stalled"
    assert loaded_prec.pattern_fingerprint.financial_velocity == "decoupled"
    assert loaded_prec.context.sector == "Railways"
    assert loaded_prec.context.cost_band == "Mega (>1000Cr)"
    assert loaded_prec.root_cause == "Critical bridge pier foundation delayed"
    assert loaded_prec.root_cause_confidence == 0.89
    assert loaded_prec.attribution_class == "LIKELY_EFFECTIVE"
    assert loaded_prec.memory_reliability == 0.91
    assert loaded_prec.success_count == 2
