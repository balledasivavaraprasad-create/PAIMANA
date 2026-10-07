"""Tests for Phase 8 — Tool Reliability & Failure Recovery.

Validates the canonical 8-stage production-grade tool reliability lifecycle:
health → dependency checks → execution → result validation → failure classification → retry/fallback → circuit breaker → reliability update

And verifies:
1. Preflight Health & Scope Checks: Intercepts offline endpoints and authorization mismatches before dispatch.
2. Dependency Verification: Validates prerequisite models, data stores, and context before execution.
3. Result Quality Validation & False Success Detection: Catches empty payloads, all-null records, misattributions, and staleness.
4. Standardized Failure Classification: Deterministic taxonomy mapping for timeouts, rate limits, schema errors, and circuit trips.
5. Bounded Retry Policy: Exponential backoff with jitter and non-retryable error short-circuiting.
6. Circuit Breaker FSM: Enforces CLOSED → OPEN → HALF_OPEN → CLOSED transitions.
7. Fallback Graph & Substitution Semantics: Graceful degradation to secondary sources with authority discounting and shared lineage tracking.
8. Persistent Reliability Profiles: First-class separation of Execution Reliability (ER) vs Evidence Reliability (EDR).
9. End-to-End Supervisor Integration: Resilient investigation execution through tool faults and fallback recoveries.
"""
import pytest
import time
from paimana_agent.state import InvestigationState
from paimana_agent.reliability.models import (
    ToolResult,
    ToolResultStatus,
    ToolReliabilityProfile,
)
from paimana_agent.reliability.health_check import PreflightHealthChecker
from paimana_agent.reliability.dependency_check import DependencyChecker, ToolDependencyStatus
from paimana_agent.reliability.result_validator import ToolResultValidator, ValidationVerdict
from paimana_agent.reliability.failure_classifier import ToolFailureClassifier
from paimana_agent.reliability.retry_policy import RetryPolicy
from paimana_agent.reliability.circuit_breaker import CircuitBreaker, CircuitBreakerState
from paimana_agent.reliability.fallback_graph import FallbackGraph, FallbackNode
from paimana_agent.reliability.reliability_updater import ReliabilityUpdater
from paimana_agent.reliability.recovery_manager import RecoveryManager
from paimana_agent.tools import ToolRegistry, ToolDefinition
from paimana_agent.supervisor import SupervisorAgent
from paimana_agent.store import Store


def test_phase8_1_preflight_health_and_authorization_checks():
    """Stage 1: Preflight health check intercepts offline endpoints and unauthorized callers."""
    checker = PreflightHealthChecker()
    
    # Check A: Authorization mismatch (caller is read_only, tool requires privileged)
    ctx_unauth = {"required_auth": "privileged", "caller_auth": "read_only"}
    healthy, reason = checker.check("financial_velocity", ctx_unauth)
    assert healthy is False
    assert "Permission Denied" in reason
    
    # Check B: Endpoint flagged offline in environment
    ctx_offline = {"offline_sources": {"milestone_audit"}}
    healthy_offline, reason_offline = checker.check("milestone_audit", ctx_offline)
    assert healthy_offline is False
    assert "Source Unavailable" in reason_offline
    
    # Check C: Normal operational check passes
    healthy_ok, reason_ok = checker.check("peer_intelligence", {"caller_auth": "read_only"})
    assert healthy_ok is True
    assert reason_ok is None


def test_phase8_2_dependency_verification():
    """Stage 2: Dependency verification ensures prerequisite objects exist before dispatch."""
    prereqs = ["store", "model", "feats"]
    
    # Case A: Missing required model
    ctx_incomplete = {"store": object(), "feats": {"risk_score": 75}}
    dep_fail = DependencyChecker.check_dependencies("shap_attribution", prereqs, ctx_incomplete)
    assert dep_fail.satisfied is False
    assert dep_fail.missing_dependencies == ["model"]
    assert "remediation_hint" in dep_fail.__dict__ and dep_fail.remediation_hint is not None
    
    # Case B: All dependencies present
    ctx_complete = {"store": object(), "model": object(), "feats": {"risk_score": 75}}
    dep_ok = DependencyChecker.check_dependencies("shap_attribution", prereqs, ctx_complete)
    assert dep_ok.satisfied is True
    assert len(dep_ok.missing_dependencies) == 0


def test_phase8_3_result_validation_and_false_success_detection():
    """Stage 3 & 4: Deep validation detects false successes, misattributions, and staleness."""
    # Subtest 3a: Empty payload masquerading as success
    res_empty = ToolResult(
        tool_name="financial_velocity",
        status="SUCCESS",
        data={},
    )
    verdict_empty, fixed_empty = ToolResultValidator.validate_result(res_empty, expected_project_code="P-101")
    assert verdict_empty == ValidationVerdict.INVALID
    assert fixed_empty.status == ToolResultStatus.EMPTY_RESULT.value
    assert fixed_empty.useful_evidence is False
    
    # Subtest 3b: Project code mismatch (data misattribution)
    res_mismatch = ToolResult(
        tool_name="milestone_audit",
        status="SUCCESS",
        data={"project_code": "P-999_WRONG", "slippage_months": 12},
    )
    verdict_mis, fixed_mis = ToolResultValidator.validate_result(res_mismatch, expected_project_code="P-101")
    assert verdict_mis == ValidationVerdict.INVALID
    assert fixed_mis.status == ToolResultStatus.VALIDATION_ERROR.value
    assert "mismatch" in fixed_mis.error
    
    # Subtest 3c: Stale result (observation is 150 days old)
    res_stale = ToolResult(
        tool_name="project_history",
        status="SUCCESS",
        data={"project_code": "P-101", "monthly_progress": [10, 12, 14]},
        observed_at=time.time() - (150 * 86400.0),
    )
    verdict_stale, fixed_stale = ToolResultValidator.validate_result(res_stale, expected_project_code="P-101", max_staleness_days=120.0)
    assert fixed_stale.status == ToolResultStatus.STALE_RESULT.value
    assert fixed_stale.freshness_score < 0.60
    
    # Subtest 3d: Valid complete result
    res_valid = ToolResult(
        tool_name="financial_velocity",
        status="SUCCESS",
        data={"project_code": "P-101", "progress_expenditure_gap_pct": 24.5, "burn_rate": 1.2},
        observed_at=time.time() - 3600,
    )
    verdict_ok, fixed_ok = ToolResultValidator.validate_result(res_valid, expected_project_code="P-101")
    assert verdict_ok == ValidationVerdict.VALID
    assert fixed_ok.completeness_score == 1.0


def test_phase8_4_standardized_failure_classification():
    """Stage 5: Standardized taxonomy mapping and retryability classification."""
    # Timeout -> retryable
    code_to, retry_to = ToolFailureClassifier.classify("Read timed out after 5000ms")
    assert code_to == "TOOL_TIMEOUT"
    assert retry_to is True
    
    # Rate limit -> retryable
    code_rl, retry_rl = ToolFailureClassifier.classify("HTTP 429 Too Many Requests: quota exceeded")
    assert code_rl == "TOOL_RATE_LIMITED"
    assert retry_rl is True
    
    # Auth failure -> non-retryable
    code_auth, retry_auth = ToolFailureClassifier.classify("HTTP 401 Unauthorized: token expired")
    assert code_auth == "TOOL_AUTH_FAILED"
    assert retry_auth is False
    
    # Schema error -> non-retryable
    code_schema, retry_schema = ToolFailureClassifier.classify("JSONDecodeError: invalid syntax at line 1")
    assert code_schema == "TOOL_SCHEMA_INVALID"
    assert retry_schema is False


def test_phase8_5_retry_policy_with_bounded_backoff():
    """Stage 6: Retry policy enforces exponential delays and max attempt limits."""
    policy = RetryPolicy(max_attempts=3, base_delay=0.10, max_delay=2.0)
    
    # Should retry up to max_attempts for retryable errors
    assert policy.should_retry("TOOL_TIMEOUT", attempt=1) is True
    assert policy.should_retry("TOOL_TIMEOUT", attempt=2) is True
    assert policy.should_retry("TOOL_TIMEOUT", attempt=3) is False  # Reached max attempts
    
    # Non-retryable errors stop immediately on attempt 1
    assert policy.should_retry("TOOL_AUTH_FAILED", attempt=1) is False
    assert policy.should_retry("TOOL_SCHEMA_INVALID", attempt=1) is False
    
    # Delay increases exponentially with backoff
    d1 = policy.calculate_delay(1)
    d2 = policy.calculate_delay(2)
    assert d2 > d1


def test_phase8_6_circuit_breaker_lifecycle():
    """Stage 7: Circuit Breaker FSM enforces CLOSED → OPEN → HALF_OPEN → CLOSED."""
    cb = CircuitBreaker(tool_name="gis_satellite", failure_threshold=2, cooldown_seconds=0.10)
    
    # 1. Initially CLOSED
    assert cb.state == CircuitBreakerState.CLOSED
    assert cb.can_execute() is True
    
    # 2. First failure -> still CLOSED
    cb.record_failure()
    assert cb.state == CircuitBreakerState.CLOSED
    assert cb.can_execute() is True
    
    # 3. Second failure reaches threshold -> trips to OPEN
    cb.record_failure()
    assert cb.state == CircuitBreakerState.OPEN
    assert cb.can_execute() is False
    
    # 4. Wait for cooldown to expire -> transitions to HALF_OPEN
    time.sleep(0.12)
    assert cb.can_execute() is True
    assert cb.state == CircuitBreakerState.HALF_OPEN
    
    # 5. Successful probe resets to CLOSED
    cb.record_success()
    assert cb.state == CircuitBreakerState.CLOSED
    assert cb.consecutive_failures == 0


def test_phase8_7_fallback_graph_and_substitution_discounting():
    """Stage 6 & 7: Fallback Graph routes failing tools with lineage and authority tracking."""
    graph = FallbackGraph()
    
    # Primary tool approval_timeline has defined fallback chain
    fallbacks = graph.get_fallbacks("approval_timeline")
    assert "project_history" in fallbacks
    assert "milestone_audit" in fallbacks
    
    # Substitution metadata calculates authority discount and shared lineage
    sub_meta = graph.get_substitution_metadata("approval_timeline", "project_history")
    assert sub_meta["primary_tool"] == "approval_timeline"
    assert sub_meta["fallback_tool"] == "project_history"
    assert sub_meta["authority_discount"] <= 1.0
    assert "fallback_authority" in sub_meta
    assert "same_underlying_lineage" in sub_meta


def test_phase8_8_reliability_profile_updates_and_metrics():
    """Stage 8: Persistent reliability profile separates Execution vs Evidence Reliability."""
    prof = ToolReliabilityProfile(tool_name="financial_velocity")
    
    # Initial clean state (default baseline prior = 0.95)
    assert prof.execution_reliability == 0.95
    assert prof.evidence_reliability > 0.85
    assert prof.composite_reliability > 0.85
    
    # Record a successful but partial result with low completeness
    res_flawed = ToolResult(
        tool_name="financial_velocity",
        status=ToolResultStatus.PARTIAL_SUCCESS.value,
        data={"gap": 15.0},
        completeness_score=0.50,
        freshness_score=0.80,
        useful_evidence=True,
    )
    ReliabilityUpdater.update_profile(prof, res_flawed)
    
    # Technical execution succeeded
    assert prof.successful_calls + prof.partial_result_calls > 0
    # But Evidence Reliability degraded due to low completeness!
    assert "DATA_COMPLETENESS_DEGRADED" in prof.reason_codes


def test_phase8_9_end_to_end_recovery_manager_execution():
    """End-to-End: RecoveryManager executes failing tool and recovers transparently via fallback."""
    rm = RecoveryManager()
    registry = ToolRegistry()
    
    # Register failing primary tool that raises timeout
    def failing_primary(**kw):
        raise TimeoutError("Remote server timed out")
        
    registry.register(ToolDefinition(
        name="gis_satellite_validation",
        purpose="Satellite survey",
        execute_fn=failing_primary,
    ))
    
    # Register successful fallback tool
    def working_fallback(**kw):
        return ToolResult(
            tool_name="field_muster_rolls",
            status="SUCCESS",
            data={"project_code": "P-REC-1", "muster_workers": 45, "attendance_pct": 88.0},
            observed_at=time.time(),
        )
        
    registry.register(ToolDefinition(
        name="field_muster_rolls",
        purpose="Field muster validation",
        execute_fn=working_fallback,
    ))
    
    # Execute through RecoveryManager: primary fails -> classifies timeout -> retries -> fallbacks to field_muster_rolls!
    result = rm.execute_with_recovery(
        tool_name="gis_satellite_validation",
        execute_fn=failing_primary,
        kwargs={"project_code": "P-REC-1"},
        tool_registry=registry,
        expected_project_code="P-REC-1",
    )
    
    assert result.is_success is True
    assert "Fallback via field_muster_rolls" in result.summary
    assert result.data["muster_workers"] == 45
    assert result.substitution_metadata is not None
    
    # Verify circuit breaker recorded failures for the primary tool
    cb_primary = rm.get_circuit_breaker("gis_satellite_validation")
    assert cb_primary.consecutive_failures > 0
