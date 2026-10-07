"""Tool Reliability Registry.

Unifies specialist tool definitions, circuit breakers, fallback graphs,
preflight checks, and recovery execution into a single robust operational registry.
"""
from __future__ import annotations
import logging
from typing import Any, Callable, Optional

from .models import ToolResult, ToolResultStatus, ToolReliabilityProfile
from .circuit_breaker import CircuitBreaker
from .fallback_graph import FallbackGraph
from .retry_policy import RetryPolicy
from .health_check import PreflightHealthChecker
from .tool_health_trace import ToolHealthTraceBuilder
from .reliability_metrics import ReliabilityMetrics
from .recovery_manager import RecoveryManager

logger = logging.getLogger("paimana_agent.reliability.registry")


class ToolReliabilityRegistry:
    """Enhanced ToolRegistry featuring first-class fault-tolerance, circuit breaking, and fallbacks."""

    def __init__(self, base_registry: Optional[Any] = None):
        # Lazy import of base ToolRegistry if not provided
        if base_registry is None:
            from ..tools import ToolRegistry
            self.base_registry = ToolRegistry()
        else:
            self.base_registry = base_registry

        self.fallback_graph = FallbackGraph()
        self.retry_policy = RetryPolicy()
        self.health_checker = PreflightHealthChecker()
        self.trace_builder = ToolHealthTraceBuilder()
        self.metrics = ReliabilityMetrics()

        self.recovery_manager = RecoveryManager(
            fallback_graph=self.fallback_graph,
            retry_policy=self.retry_policy,
            health_checker=self.health_checker,
            trace_builder=self.trace_builder,
            metrics=self.metrics,
        )

    @property
    def _tools(self) -> dict:
        return self.base_registry._tools

    def register(self, tool_def: Any):
        """Registers a specialist tool definition."""
        self.base_registry.register(tool_def)
        # Initialize profile
        self.recovery_manager.get_profile(tool_def.name)

    def get(self, name: str) -> Optional[Any]:
        """Retrieves a tool definition by name."""
        return self.base_registry.get(name)

    def list_tools(self) -> list[dict]:
        """Lists registered tools."""
        return self.base_registry.list_tools()

    def export_mcp_manifest(self) -> list[dict]:
        """Exports tools as Model Context Protocol (MCP) definitions."""
        return self.base_registry.export_mcp_manifest()

    def export_tools_manifest(self) -> list[dict]:
        """Exports tools manifest for LLM agent planning."""
        return self.base_registry.export_tools_manifest()

    def get_circuit_breaker(self, tool_name: str) -> CircuitBreaker:
        return self.recovery_manager.get_circuit_breaker(tool_name)

    def get_reliability_profile(self, tool_name: str) -> ToolReliabilityProfile:
        return self.recovery_manager.get_profile(tool_name)

    def execute(
        self,
        tool_name: str,
        budget: Optional[Any] = None,
        expected_project_code: Optional[str] = None,
        context: Optional[dict] = None,
        **kwargs
    ) -> ToolResult:
        """Executes a tool with recovery management, retries, and fallback handling."""
        tool_def = self.base_registry.get(tool_name)
        if not tool_def:
            return ToolResult(
                tool_name=tool_name,
                status=ToolResultStatus.SOURCE_UNAVAILABLE.value,
                error=f"Tool '{tool_name}' is not registered in ToolReliabilityRegistry",
                summary=f"Unrecognized tool: {tool_name}",
            )

        return self.recovery_manager.execute_with_recovery(
            tool_name=tool_name,
            execute_fn=tool_def.execute,
            kwargs=kwargs,
            tool_registry=self.base_registry,
            budget=budget,
            expected_project_code=expected_project_code,
            context=context,
        )
