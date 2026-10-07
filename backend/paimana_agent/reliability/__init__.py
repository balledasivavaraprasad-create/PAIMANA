"""Tool Reliability, Fault-Tolerant Evidence Acquisition, and Recovery Framework.

Provides first-class execution and evidence reliability profiling, standardized failure taxonomy,
circuit breaking, bounded retries, source fallback graphs, and preflight health verification.
"""
from __future__ import annotations
import sys

from .models import ToolResultStatus, ToolResult, ToolReliabilityProfile
from .circuit_breaker import CircuitBreaker, CircuitBreakerState
from .failure_classifier import ToolFailureClassifier
from .retry_policy import RetryPolicy
from .fallback_graph import FallbackNode, FallbackGraph
from .result_validator import ValidationVerdict, ToolResultValidator
from .health_check import PreflightHealthChecker
from .dependency_check import ToolDependencyStatus, DependencyChecker
from .reliability_metrics import ReliabilityMetrics
from .reliability_updater import ReliabilityUpdater
from .tool_health_trace import ToolFailureEvent, ToolHealthTraceBuilder
from .recovery_manager import RecoveryAction, RecoveryManager
from .registry import ToolReliabilityRegistry

__all__ = [
    "ToolResultStatus",
    "ToolResult",
    "ToolReliabilityProfile",
    "CircuitBreaker",
    "CircuitBreakerState",
    "ToolFailureClassifier",
    "RetryPolicy",
    "FallbackNode",
    "FallbackGraph",
    "ValidationVerdict",
    "ToolResultValidator",
    "PreflightHealthChecker",
    "ToolDependencyStatus",
    "DependencyChecker",
    "ReliabilityMetrics",
    "ReliabilityUpdater",
    "ToolFailureEvent",
    "ToolHealthTraceBuilder",
    "RecoveryAction",
    "RecoveryManager",
    "ToolReliabilityRegistry",
]

# Alias for compatibility if referenced via paimana_agent.tools.reliability
sys.modules["paimana_agent.tools.reliability"] = sys.modules[__name__]
