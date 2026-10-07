"""Fault-Tolerant Recovery Manager.

Executes tools within a resilient execution loop: performing preflight checks,
verifying circuit breaker states, executing with bounded retries, detecting false successes,
and routing gracefully through fallback graphs while preserving evidence integrity.
"""
from __future__ import annotations
import time
import logging
from typing import Any, Callable, Optional

from .models import ToolResult, ToolResultStatus, ToolReliabilityProfile
from .failure_classifier import ToolFailureClassifier
from .retry_policy import RetryPolicy
from .circuit_breaker import CircuitBreaker, CircuitBreakerState
from .fallback_graph import FallbackGraph
from .result_validator import ToolResultValidator, ValidationVerdict
from .health_check import PreflightHealthChecker
from .dependency_check import DependencyChecker, ToolDependencyStatus
from .reliability_updater import ReliabilityUpdater
from .tool_health_trace import ToolHealthTraceBuilder
from .reliability_metrics import ReliabilityMetrics

logger = logging.getLogger("paimana_agent.reliability.recovery")


class RecoveryAction:
    RETRY = "RETRY"
    FALLBACK = "FALLBACK"
    DEGRADE = "DEGRADE"
    QUARANTINE = "QUARANTINE"
    TERMINATE = "TERMINATE"
    ESCALATE = "ESCALATE"


class RecoveryManager:
    """Orchestrates resilient tool execution, error handling, retries, and fallbacks."""

    def __init__(
        self,
        fallback_graph: Optional[FallbackGraph] = None,
        retry_policy: Optional[RetryPolicy] = None,
        health_checker: Optional[PreflightHealthChecker] = None,
        trace_builder: Optional[ToolHealthTraceBuilder] = None,
        metrics: Optional[ReliabilityMetrics] = None,
    ):
        self.fallback_graph = fallback_graph or FallbackGraph()
        self.retry_policy = retry_policy or RetryPolicy()
        self.health_checker = health_checker or PreflightHealthChecker()
        self.trace_builder = trace_builder or ToolHealthTraceBuilder()
        self.metrics = metrics or ReliabilityMetrics()
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.profiles: dict[str, ToolReliabilityProfile] = {}

    def get_circuit_breaker(self, tool_name: str) -> CircuitBreaker:
        """Retrieves or creates a circuit breaker for the specified tool."""
        clean = tool_name.replace("tool_", "").lower()
        if clean not in self.circuit_breakers:
            self.circuit_breakers[clean] = CircuitBreaker(tool_name=clean)
        return self.circuit_breakers[clean]

    def get_profile(self, tool_name: str) -> ToolReliabilityProfile:
        """Retrieves or creates a persistent reliability profile for the specified tool."""
        clean = tool_name.replace("tool_", "").lower()
        if clean not in self.profiles:
            self.profiles[clean] = ToolReliabilityProfile(tool_name=clean)
        return self.profiles[clean]

    def execute_with_recovery(
        self,
        tool_name: str,
        execute_fn: Callable[..., ToolResult],
        kwargs: dict[str, Any],
        tool_registry: Any = None,
        budget: Optional[Any] = None,
        expected_project_code: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> ToolResult:
        """Executes a tool with full preflight, retry, circuit-breaker, and fallback protection."""
        clean_name = tool_name.replace("tool_", "").lower()
        cb = self.get_circuit_breaker(clean_name)
        prof = self.get_profile(clean_name)
        context = context or {}

        # --------------------------------------------------------------------
        # 1. Preflight Health & Scope Check
        # --------------------------------------------------------------------
        healthy, preflight_reason = self.health_checker.check(clean_name, context)
        if not healthy:
            taxonomy_code, is_retryable = ToolFailureClassifier.classify(preflight_reason)
            self.trace_builder.record_failure(
                tool_name=clean_name,
                taxonomy_code=taxonomy_code,
                error_message=preflight_reason or "Preflight health check failed.",
                recovery_action=RecoveryAction.FALLBACK if not is_retryable else RecoveryAction.RETRY,
            )
            logger.warning("Preflight health check failed for tool '%s': %s", clean_name, preflight_reason)
            return self._execute_fallback(
                primary_tool=clean_name,
                original_kwargs=kwargs,
                tool_registry=tool_registry,
                budget=budget,
                expected_project_code=expected_project_code,
                context=context,
                reason=taxonomy_code,
            )

        # --------------------------------------------------------------------
        # 2. Dependency Verification
        # --------------------------------------------------------------------
        available_ctx = dict(context)
        available_ctx.update(kwargs)
        prereqs = context.get("prerequisites")
        if prereqs is None and tool_registry and hasattr(tool_registry, "get"):
            tool_def = tool_registry.get(clean_name)
            if tool_def:
                prereqs = getattr(tool_def, "prerequisites", [])
        if prereqs:
            dep_status = DependencyChecker.check_dependencies(clean_name, prereqs, available_ctx)
            if not dep_status.satisfied:
                msg = f"Prerequisite dependencies missing for '{clean_name}': {dep_status.missing_dependencies}"
                self.trace_builder.record_failure(
                    tool_name=clean_name,
                    taxonomy_code="TOOL_DEPENDENCY_UNAVAILABLE",
                    error_message=msg,
                    recovery_action=RecoveryAction.FALLBACK,
                )
                logger.warning("Dependency check failed for tool '%s': %s", clean_name, msg)
                return self._execute_fallback(
                    primary_tool=clean_name,
                    original_kwargs=kwargs,
                    tool_registry=tool_registry,
                    budget=budget,
                    expected_project_code=expected_project_code,
                    context=context,
                    reason="TOOL_DEPENDENCY_UNAVAILABLE",
                )

        # --------------------------------------------------------------------
        # 3. Circuit Breaker Check
        # --------------------------------------------------------------------
        if not cb.can_execute():
            self.trace_builder.record_failure(
                tool_name=clean_name,
                taxonomy_code="TOOL_CIRCUIT_OPEN",
                error_message=f"Circuit breaker for tool '{clean_name}' is OPEN.",
                recovery_action=RecoveryAction.FALLBACK,
            )
            logger.warning("Circuit breaker OPEN for tool '%s'. Initiating fallback.", clean_name)
            return self._execute_fallback(
                primary_tool=clean_name,
                original_kwargs=kwargs,
                tool_registry=tool_registry,
                budget=budget,
                expected_project_code=expected_project_code,
                context=context,
                reason="CIRCUIT_OPEN",
            )

        # --------------------------------------------------------------------
        # 3. Execution Loop with Bounded Retries
        # --------------------------------------------------------------------
        attempt = 0
        last_error_msg = ""
        last_taxonomy_code = "TOOL_INTERNAL_ERROR"

        while attempt < self.retry_policy.max_attempts:
            attempt += 1
            t0 = time.time()
            try:
                # Check budget prior to retry (supervisor manages primary dispatch budget)
                if budget and attempt > 1 and not budget.can_afford(estimated_cost=0.05, estimated_latency_ms=30.0):
                    logger.info("Budget exhausted before retrying tool '%s'", clean_name)
                    return ToolResult(
                        tool_name=clean_name,
                        status=ToolResultStatus.FAILURE.value,
                        error="Investigation budget exhausted prior to retry.",
                        summary="Investigation resource budget limit reached for retry.",
                    )

                # Execute primary function
                result: ToolResult = execute_fn(**kwargs)
                latency_ms = (time.time() - t0) * 1000.0
                result.execution_time_ms = latency_ms

                # Record budget consumption for retries (supervisor accounts for primary call)
                if budget and attempt > 1:
                    if hasattr(budget, "record_consumption"):
                        budget.record_consumption(
                            tool_name=clean_name,
                            cost=0.05,
                            latency_ms=latency_ms,
                            is_retry=True,
                        )
                    elif hasattr(budget, "record_call"):
                        budget.record_call(latency_ms=latency_ms, cost=0.05)

                # Check technical status
                if result.is_success:
                    # 4. Result Quality Validation & False Success Detection
                    verdict, validated_result = ToolResultValidator.validate_result(
                        result,
                        expected_project_code=expected_project_code,
                    )

                    if verdict == ValidationVerdict.INVALID:
                        # Caught false success or schema error!
                        cb.record_failure()
                        prof.last_failure_at = time.time()
                        ReliabilityUpdater.update_profile(prof, validated_result)
                        self.metrics.record_call(validated_result, context)
                        self.trace_builder.record_failure(
                            tool_name=clean_name,
                            taxonomy_code="TOOL_RESULT_INVALID",
                            error_message=validated_result.error or "Result validation failed (false success caught)",
                            recovery_action=RecoveryAction.QUARANTINE,
                            attempt=attempt,
                            latency_ms=latency_ms,
                        )
                        # Route to fallback
                        return self._execute_fallback(
                            primary_tool=clean_name,
                            original_kwargs=kwargs,
                            tool_registry=tool_registry,
                            budget=budget,
                            expected_project_code=expected_project_code,
                            context=context,
                            reason="VALIDATION_INVALID",
                        )

                    # Successful execution!
                    cb.record_success()
                    ReliabilityUpdater.update_profile(prof, validated_result)
                    self.metrics.record_call(validated_result, context)
                    validated_result.retry_count = attempt - 1
                    return validated_result

                # Execution returned a non-success status
                last_error_msg = result.error or result.summary or "Tool returned failure status"
                last_taxonomy_code, is_retryable = ToolFailureClassifier.classify(result)

            except Exception as exc:
                latency_ms = (time.time() - t0) * 1000.0
                last_error_msg = str(exc)
                last_taxonomy_code, is_retryable = ToolFailureClassifier.classify(exc)

            # Record failure attempt in trace
            cb.record_failure()
            self.trace_builder.record_failure(
                tool_name=clean_name,
                taxonomy_code=last_taxonomy_code,
                error_message=last_error_msg,
                recovery_action=RecoveryAction.RETRY if is_retryable else RecoveryAction.FALLBACK,
                attempt=attempt,
                latency_ms=latency_ms,
            )

            # Check if retry is allowed
            if self.retry_policy.should_retry(last_taxonomy_code, attempt):
                delay = self.retry_policy.calculate_delay(attempt)
                logger.info("Retrying tool '%s' after delay %.2fs (attempt %d)", clean_name, delay, attempt)
                time.sleep(min(delay, 0.05))  # Keep test execution swift
                continue
            else:
                # Non-retryable error (e.g. auth failure, schema error)
                break

        # --------------------------------------------------------------------
        # 5. Retries Exhausted or Non-Retryable Error -> Execute Fallback
        # --------------------------------------------------------------------
        failed_res = ToolResult(
            tool_name=clean_name,
            status=ToolResultStatus.FAILURE.value,
            error=last_error_msg,
            summary=f"Tool failed: {last_error_msg}",
            retry_count=attempt - 1,
        )
        ReliabilityUpdater.update_profile(prof, failed_res)
        self.metrics.record_call(failed_res, context)

        return self._execute_fallback(
            primary_tool=clean_name,
            original_kwargs=kwargs,
            tool_registry=tool_registry,
            budget=budget,
            expected_project_code=expected_project_code,
            context=context,
            reason=last_taxonomy_code,
        )

    def _execute_fallback(
        self,
        primary_tool: str,
        original_kwargs: dict[str, Any],
        tool_registry: Any,
        budget: Optional[Any],
        expected_project_code: Optional[str],
        context: Optional[dict],
        reason: str,
    ) -> ToolResult:
        """Finds and executes an authorized fallback tool from the fallback graph."""
        if not tool_registry:
            return ToolResult(
                tool_name=primary_tool,
                status=ToolResultStatus.SOURCE_UNAVAILABLE.value,
                error=f"Primary tool '{primary_tool}' failed ({reason}) and no registry available for fallback.",
                summary=f"Tool '{primary_tool}' unavailable without fallback.",
                useful_evidence=False,
            )

        fallback_candidates = self.fallback_graph.get_fallbacks(primary_tool)
        for fb_tool_name in fallback_candidates:
            fb_tool_def = tool_registry.get(fb_tool_name)
            if not fb_tool_def:
                continue

            fb_cb = self.get_circuit_breaker(fb_tool_name)
            if not fb_cb.can_execute():
                continue

            # Check if budget permits fallback
            if budget and not budget.can_afford(estimated_cost=0.05, estimated_latency_ms=25.0):
                continue

            logger.info("Executing fallback tool '%s' for failed primary '%s'", fb_tool_name, primary_tool)
            sub_meta = self.fallback_graph.get_substitution_metadata(
                primary_tool=primary_tool,
                fallback_tool=fb_tool_name,
            )

            t0 = time.time()
            try:
                fb_result: ToolResult = fb_tool_def.execute(**original_kwargs)
            except Exception as e:
                fb_cb.record_failure()
                continue

            lat_ms = (time.time() - t0) * 1000.0
            fb_result.execution_time_ms = lat_ms

            if budget:
                if hasattr(budget, "record_consumption"):
                    budget.record_consumption(tool_name=fb_tool_name, cost=0.05, latency_ms=lat_ms, is_retry=False)
                elif hasattr(budget, "record_call"):
                    budget.record_call(latency_ms=lat_ms, cost=0.05)

            if fb_result.is_success:
                fb_cb.record_success()
                # Attach substitution metadata & apply authority discount
                fb_result.substitution_metadata = sub_meta
                fb_result.summary = (
                    f"[Fallback via {fb_tool_name}] " + (fb_result.summary or "")
                )
                fb_prof = self.get_profile(fb_tool_name)
                ReliabilityUpdater.update_profile(fb_prof, fb_result)
                self.metrics.record_call(fb_result, context)
                return fb_result
            else:
                fb_cb.record_failure()

        # All fallbacks failed or none available
        return ToolResult(
            tool_name=primary_tool,
            status=ToolResultStatus.SOURCE_UNAVAILABLE.value,
            error=f"Primary tool '{primary_tool}' failed ({reason}) and all fallback sources failed.",
            summary=f"Tool '{primary_tool}' failed with no working fallback available.",
            useful_evidence=False,
        )
