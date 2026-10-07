"""Phase 14 — Agent Quality Benchmark Verification Suite.

Validates the empirical benchmarking framework across known infrastructure cases:
  1. Hypothesis Quality (accuracy, entropy reduction, discrimination)
  2. Causal Reasoning (confounder isolation, temporal ordering, Level 0-4 calibration)
  3. Tool Selection (precision, active gap targeting, information-seeking)
  4. Convergence (early exit on benign cases, termination bounds, stability)
  5. Recommendation Quality (Pareto optimality, authority feasibility, causal alignment)
  6. Peer Intelligence (cohort relevance, outlier detection, no demo defaults)
  7. Memory Usefulness (precedent retrieval, failure memory warning avoidance)
  8. False Escalation (noise control, benign case non-alarm)
  9. Unsupported Claims (0.0% ungrounded assertions or unbacked punitive actions)
 10. Resource Efficiency (budget preservation, cost per information gain)
 11. End-to-End Comparative Benchmark Report (AQI uplift vs legacy baseline)
"""
from __future__ import annotations
import pytest
from paimana_agent.benchmark.models import (
    BenchmarkDimension,
    BenchmarkCase,
    DimensionScore,
    CaseEvaluationResult,
    AgentBenchmarkReport,
)
from paimana_agent.benchmark.cases import get_benchmark_cases
from paimana_agent.benchmark.evaluator import (
    BaselineBenchmarkRunner,
    AgenticBenchmarkRunner,
    AgentQualityBenchmark,
)
from paimana_agent.memory.precedent_memory import PrecedentMemoryStore
from paimana_agent.memory.failure_memory import FailureMemoryManager


@pytest.fixture
def benchmark_cases():
    return get_benchmark_cases()


@pytest.fixture
def clean_memory_store():
    store = PrecedentMemoryStore()
    store.reset()
    return store


# ============================================================================
# 1. Benchmark Cases Integrity Test
# ============================================================================
def test_benchmark_cases_integrity(benchmark_cases):
    """Verifies that all 6 benchmark cases are fully specified with ground truths."""
    assert len(benchmark_cases) == 6
    case_ids = [c.case_id for c in benchmark_cases]
    assert len(case_ids) == len(set(case_ids)), "Case IDs must be unique"

    for case in benchmark_cases:
        assert case.case_id.startswith("CASE-")
        assert len(case.title) > 5
        assert len(case.description) > 20
        assert case.ground_truth_root_cause != ""
        assert 1 <= case.ground_truth_causal_level <= 4
        assert case.max_budget_steps >= 3

        p = case.project_data
        assert "project_code" in p
        assert "original_cost_cr" in p and p["original_cost_cr"] > 0
        assert "physical_progress_pct" in p
        assert "cumulative_expenditure_cr" in p


# ============================================================================
# 2. Hypothesis Quality Dimension
# ============================================================================
def test_hypothesis_quality_dimension(benchmark_cases, clean_memory_store):
    """Verifies that V3+ correctly identifies ground-truth root causes across scenarios."""
    runner = AgenticBenchmarkRunner(memory_store=clean_memory_store)

    # Test Case 1: Front-loaded billing
    case1 = next(c for c in benchmark_cases if c.case_id == "CASE-01-FRONT-LOADED-BILLING")
    res1 = runner.evaluate_case(case1)
    score1 = res1.dimension_scores[BenchmarkDimension.HYPOTHESIS_QUALITY]

    assert score1.passed
    assert score1.score >= 0.90
    assert res1.top_hypothesis == case1.ground_truth_root_cause


# ============================================================================
# 3. Causal Reasoning & Confounder Isolation
# ============================================================================
def test_causal_reasoning_and_confounders(benchmark_cases, clean_memory_store):
    """Verifies that external confounders (statutory stay, force majeure) are detected
    and prevent false causal blame on contractors."""
    runner = AgenticBenchmarkRunner(memory_store=clean_memory_store)

    # Case 2: Regulatory stay order
    case2 = next(c for c in benchmark_cases if c.case_id == "CASE-02-REGULATORY-STAY")
    res2 = runner.evaluate_case(case2)
    score2 = res2.dimension_scores[BenchmarkDimension.CAUSAL_REASONING]

    assert score2.passed
    assert score2.score >= 0.85
    assert len(res2.confounders_detected) >= 1
    assert "stay" in res2.confounders_detected[0].lower() or "statutory" in res2.confounders_detected[0].lower()

    # Case 3: Force majeure flood
    case3 = next(c for c in benchmark_cases if c.case_id == "CASE-03-ENVIRONMENTAL-FORCE-MAJEURE")
    res3 = runner.evaluate_case(case3)
    assert len(res3.confounders_detected) >= 1
    assert any("flood" in c.lower() for c in res3.confounders_detected)


# ============================================================================
# 4. Tool Selection & Information Value
# ============================================================================
def test_tool_selection_and_precision(benchmark_cases, clean_memory_store):
    """Verifies that information-seeking tools invoked directly match active gaps."""
    runner = AgenticBenchmarkRunner(memory_store=clean_memory_store)

    case1 = next(c for c in benchmark_cases if c.case_id == "CASE-01-FRONT-LOADED-BILLING")
    res1 = runner.evaluate_case(case1)
    score1 = res1.dimension_scores[BenchmarkDimension.TOOL_SELECTION]

    assert score1.passed
    assert score1.score >= 0.80
    assert "financial_velocity" in res1.tools_used
    assert "milestone_audit" in res1.tools_used


# ============================================================================
# 5. Convergence & Early Termination on Benign Noise
# ============================================================================
def test_convergence_and_benign_early_exit(benchmark_cases, clean_memory_store):
    """Verifies that benign reporting discrepancies exit immediately without wasting budget."""
    runner = AgenticBenchmarkRunner(memory_store=clean_memory_store)

    case4 = next(c for c in benchmark_cases if c.case_id == "CASE-04-BENIGN-REPORTING-DISCREPANCY")
    res4 = runner.evaluate_case(case4)
    score4 = res4.dimension_scores[BenchmarkDimension.CONVERGENCE]

    assert score4.passed
    assert score4.score >= 0.95
    assert res4.steps_executed <= 2, "Benign cases must terminate in <= 2 steps"
    assert res4.steps_executed < case4.max_budget_steps


# ============================================================================
# 6. Recommendation Quality & Avoidance of Prohibited Actions
# ============================================================================
def test_recommendation_quality_and_safety(benchmark_cases, clean_memory_store):
    """Verifies that recommendations are Pareto-optimal and strictly avoid prohibited actions."""
    runner = AgenticBenchmarkRunner(memory_store=clean_memory_store)

    for case in benchmark_cases:
        res = runner.evaluate_case(case)
        score = res.dimension_scores[BenchmarkDimension.RECOMMENDATION_QUALITY]
        assert score.passed
        assert score.score >= 0.80
        for prohibited in case.prohibited_actions:
            assert prohibited not in res.recommended_action


# ============================================================================
# 7. Peer Intelligence & Anomaly Detection
# ============================================================================
def test_peer_intelligence_dimension(benchmark_cases, clean_memory_store):
    """Verifies that peer intelligence accurately detects chronic contractor stagnation outliers."""
    runner = AgenticBenchmarkRunner(memory_store=clean_memory_store)

    case5 = next(c for c in benchmark_cases if c.case_id == "CASE-05-CHRONIC-CONTRACTOR-STAGNATION")
    res5 = runner.evaluate_case(case5)
    score5 = res5.dimension_scores[BenchmarkDimension.PEER_INTELLIGENCE]

    assert score5.passed
    assert score5.score >= 0.85
    assert "peer_intelligence" in res5.tools_used
    assert res5.causal_level == 4


# ============================================================================
# 8. Memory Usefulness & Institutional Failure Warning Avoidance
# ============================================================================
def test_memory_usefulness_and_failure_avoidance(benchmark_cases, clean_memory_store):
    """Verifies that historical failure precedent warns against repeating disastrous terminations."""
    runner = AgenticBenchmarkRunner(memory_store=clean_memory_store)

    case6 = next(c for c in benchmark_cases if c.case_id == "CASE-06-ADVERSE-PRECEDENT-RISK")
    res6 = runner.evaluate_case(case6)
    score6 = res6.dimension_scores[BenchmarkDimension.MEMORY_USEFULNESS]

    assert score6.passed
    assert score6.score == 1.0
    # Prohibited action is unilateral contract termination
    assert "UNILATERAL_CONTRACT_TERMINATION" not in res6.recommended_action
    assert "CONCILIATION" in res6.recommended_action or "ESCROW" in res6.recommended_action


# ============================================================================
# 9. False Escalation & Unsupported Claims (Noise Control & Integrity)
# ============================================================================
def test_false_escalation_and_unsupported_claims(benchmark_cases, clean_memory_store):
    """Verifies 0.0% false escalation on benign cases and 0.0% unsupported claims."""
    runner = AgenticBenchmarkRunner(memory_store=clean_memory_store)

    # 1. Benign Case 4 MUST NOT escalate
    case4 = next(c for c in benchmark_cases if c.case_id == "CASE-04-BENIGN-REPORTING-DISCREPANCY")
    res4 = runner.evaluate_case(case4)
    fe_score = res4.dimension_scores[BenchmarkDimension.FALSE_ESCALATION]
    assert fe_score.passed
    assert fe_score.score == 1.0
    assert not res4.is_escalated, "Benign data sync lag must not trigger false escalation"

    # 2. Unsupported claims must be 0.0 across all cases
    for case in benchmark_cases:
        res = runner.evaluate_case(case)
        unsupp_score = res.dimension_scores[BenchmarkDimension.UNSUPPORTED_CLAIMS]
        assert unsupp_score.score == 1.0
        assert not res.has_unsupported_claim


# ============================================================================
# 10. Resource Efficiency
# ============================================================================
def test_resource_efficiency_dimension(benchmark_cases, clean_memory_store):
    """Verifies that budget preservation and cost-effectiveness meet high standards."""
    runner = AgenticBenchmarkRunner(memory_store=clean_memory_store)

    case4 = next(c for c in benchmark_cases if c.case_id == "CASE-04-BENIGN-REPORTING-DISCREPANCY")
    res4 = runner.evaluate_case(case4)
    eff_score = res4.dimension_scores[BenchmarkDimension.RESOURCE_EFFICIENCY]

    assert eff_score.passed
    assert eff_score.score >= 0.80
    assert res4.steps_executed == 1


# ============================================================================
# 11. End-to-End Comparative Benchmark Report (AQI Uplift)
# ============================================================================
def test_end_to_end_comparative_benchmark_uplift():
    """Executes the full benchmark across both V3+ and Baseline, verifying substantial uplift."""
    benchmark = AgentQualityBenchmark()
    report = benchmark.run_benchmark()

    # Verify Report Structure
    assert report.total_cases == 6
    assert len(report.v3_case_results) == 6
    assert len(report.baseline_case_results) == 6

    # Verify AQI and Net Improvement
    assert report.v3_aqi >= 88.0, f"Expected V3+ AQI >= 88.0, got {report.v3_aqi:.2f}"
    assert report.baseline_aqi <= 50.0, f"Expected Baseline AQI <= 50.0, got {report.baseline_aqi:.2f}"
    assert report.net_improvement >= 40.0, f"Expected AQI uplift >= 40.0, got {report.net_improvement:.2f}"
    assert report.verdict == "SUBSTANTIALLY_IMPROVED"

    # Verify all 10 dimensions show positive deltas
    for dim in BenchmarkDimension:
        v3_score = report.v3_dimension_scores[dim]
        base_score = report.baseline_dimension_scores[dim]
        delta = report.dimension_deltas[dim]
        assert v3_score > base_score, f"Dimension '{dim.value}' failed to show positive uplift: V3={v3_score}, Base={base_score}"
        assert delta > 0.15, f"Dimension '{dim.value}' delta {delta} was too small"

    # Verify JSON serializability
    rep_dict = report.to_dict()
    assert rep_dict["verdict"] == "SUBSTANTIALLY_IMPROVED"
    assert "dimensions" in rep_dict
    assert len(rep_dict["dimensions"]) == 10
