"""First-Class Investigation Budget and Resource Consumption Data Models.

Defines the core ledgers, consumption counters, and resource constraints
governing investigation execution, latency, computational cost, token usage,
tool calls, and emergency reserves.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ResourceClass(str, Enum):
    """Classification of scarce operational resources."""
    COMPUTE = "COMPUTE"
    LLM = "LLM"
    EXTERNAL_API = "EXTERNAL_API"
    DATABASE = "DATABASE"
    NETWORK = "NETWORK"
    TIME = "TIME"
    HUMAN_REVIEW = "HUMAN_REVIEW"


@dataclass
class ResourceConsumption:
    """Detailed accounting ledger of consumed resources across an investigation."""
    iterations: int = 0
    tool_calls: int = 0
    llm_calls: int = 0
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0
    external_api_calls: int = 0
    execution_seconds: float = 0.0
    wall_clock_seconds: float = 0.0
    estimated_cost: float = 0.0
    peak_concurrency: int = 1

    @property
    def total_tokens(self) -> int:
        return self.llm_input_tokens + self.llm_output_tokens

    def record_consumption(
        self,
        tool_calls: int = 0,
        iterations: int = 0,
        llm_calls: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        external_calls: int = 0,
        execution_seconds: float = 0.0,
        cost: float = 0.0,
    ):
        """Increments consumed resource counts."""
        self.tool_calls += tool_calls
        self.iterations += iterations
        self.llm_calls += llm_calls
        self.llm_input_tokens += input_tokens
        self.llm_output_tokens += output_tokens
        self.external_api_calls += external_calls
        self.execution_seconds += execution_seconds
        self.estimated_cost += cost

    def to_dict(self) -> dict[str, Any]:
        return {
            "iterations": self.iterations,
            "tool_calls": self.tool_calls,
            "llm_calls": self.llm_calls,
            "llm_input_tokens": self.llm_input_tokens,
            "llm_output_tokens": self.llm_output_tokens,
            "total_tokens": self.total_tokens,
            "external_api_calls": self.external_api_calls,
            "execution_seconds": round(self.execution_seconds, 3),
            "wall_clock_seconds": round(self.wall_clock_seconds, 3),
            "estimated_cost": round(self.estimated_cost, 4),
            "peak_concurrency": self.peak_concurrency,
        }


@dataclass
class InvestigationBudget:
    """First-class investigation budget constraint and allocation ledger.

    Maintains 100% backward compatibility with previous InvestigationBudget
    while supporting multi-resource governance, emergency reserves, and pressure tracking.
    """
    investigation_id: str = ""

    # Primary resource limits
    max_iterations: int = 8
    max_tool_calls: int = 5
    max_llm_calls: int = 6
    max_llm_tokens: int = 12000
    max_external_calls: int = 5
    max_execution_seconds: float = 45.0
    max_wall_clock_seconds: float = 60.0
    max_estimated_cost: float = 1.50
    max_concurrent_tools: int = 2

    # Emergency Reserve (percentage reserved for critical/contradiction resolution)
    reserved_emergency_budget: float = 0.15

    # Consumption Ledger
    consumed: ResourceConsumption = field(default_factory=ResourceConsumption)

    # Policy metadata
    policy_version: str = "1.0"
    severity: str = "MEDIUM"

    # Backward-compatible attributes
    max_latency_ms: float = 10000.0
    min_utility_threshold: float = 0.15
    diminishing_returns_threshold: float = 0.04
    created_at: float = field(default_factory=time.time)

    # Explicit tracker for backward-compatible call count / latency
    tool_calls_used: int = 0
    cumulative_latency_ms: float = 0.0

    def __post_init__(self):
        # Sync backward-compatible fields if initialized explicitly
        if self.tool_calls_used > 0 and self.consumed.tool_calls == 0:
            self.consumed.tool_calls = self.tool_calls_used
        if self.cumulative_latency_ms > 0 and self.consumed.execution_seconds == 0.0:
            self.consumed.execution_seconds = self.cumulative_latency_ms / 1000.0

    @property
    def remaining_calls(self) -> int:
        used = max(self.tool_calls_used, self.consumed.tool_calls)
        return max(0, self.max_tool_calls - used)

    @property
    def remaining_iterations(self) -> int:
        return max(0, self.max_iterations - self.consumed.iterations)

    @property
    def remaining_llm_calls(self) -> int:
        return max(0, self.max_llm_calls - self.consumed.llm_calls)

    @property
    def remaining_tokens(self) -> int:
        return max(0, self.max_llm_tokens - self.consumed.total_tokens)

    @property
    def remaining_external_calls(self) -> int:
        return max(0, self.max_external_calls - self.consumed.external_api_calls)

    @property
    def remaining_execution_seconds(self) -> float:
        return max(0.0, self.max_execution_seconds - self.consumed.execution_seconds)

    @property
    def remaining_cost(self) -> float:
        return max(0.0, self.max_estimated_cost - self.consumed.estimated_cost)

    @property
    def resource_pressure(self) -> float:
        """Calculates normalized resource pressure in [0.0, 1.0].

        Represents the highest strain across tool calls, time, cost, and tokens.
        """
        tool_ratio = max(self.tool_calls_used, self.consumed.tool_calls) / max(1, self.max_tool_calls)
        time_ratio = self.consumed.execution_seconds / max(0.1, self.max_execution_seconds)
        cost_ratio = self.consumed.estimated_cost / max(0.01, self.max_estimated_cost)
        token_ratio = self.consumed.total_tokens / max(1, self.max_llm_tokens)
        call_ratio = self.consumed.llm_calls / max(1, self.max_llm_calls)
        ext_ratio = self.consumed.external_api_calls / max(1, self.max_external_calls)

        pressure = max(tool_ratio, time_ratio, cost_ratio, token_ratio, call_ratio, ext_ratio)
        return round(min(1.0, max(0.0, pressure)), 3)

    def is_exhausted(self) -> bool:
        """Checks whether any hard resource constraint has been met."""
        used_calls = max(self.tool_calls_used, self.consumed.tool_calls)
        used_latency_ms = max(self.cumulative_latency_ms, self.consumed.execution_seconds * 1000.0)

        # Hard boundaries
        if used_calls >= self.max_tool_calls:
            return True
        if used_latency_ms >= self.max_latency_ms:
            return True
        if self.consumed.execution_seconds >= self.max_execution_seconds:
            return True
        if self.consumed.iterations >= self.max_iterations:
            return True
        if self.consumed.estimated_cost >= self.max_estimated_cost:
            return True
        if self.consumed.external_api_calls >= self.max_external_calls:
            return True
        if self.consumed.llm_calls >= self.max_llm_calls:
            return True
        if self.consumed.total_tokens >= self.max_llm_tokens:
            return True
        return False

    def can_afford(
        self,
        estimated_cost: float = 0.0,
        estimated_latency_ms: float = 0.0,
        estimated_tokens: int = 0,
        external_calls: int = 0,
        llm_calls: int = 0,
        is_emergency: bool = False,
    ) -> bool:
        """Verifies if budget can support the requested operation without breaching limits."""
        if self.is_exhausted():
            return False

        # If not an emergency, protect the emergency reserve
        usable_cost_limit = self.max_estimated_cost if is_emergency else self.max_estimated_cost * (1.0 - self.reserved_emergency_budget)
        usable_tool_limit = self.max_tool_calls if is_emergency else max(1, int(self.max_tool_calls * (1.0 - self.reserved_emergency_budget)))

        used_calls = max(self.tool_calls_used, self.consumed.tool_calls)
        if used_calls + 1 > self.max_tool_calls:
            return False
        if not is_emergency and (used_calls + 1 > usable_tool_limit):
            return False

        if (self.consumed.estimated_cost + estimated_cost) > usable_cost_limit:
            return False
        if (self.consumed.external_api_calls + external_calls) > self.max_external_calls:
            return False
        if (self.consumed.llm_calls + llm_calls) > self.max_llm_calls:
            return False
        if (self.consumed.total_tokens + estimated_tokens) > self.max_llm_tokens:
            return False
        if (self.consumed.execution_seconds + (estimated_latency_ms / 1000.0)) > self.max_execution_seconds:
            return False

        return True

    def record_call(
        self,
        latency_ms: float = 0.0,
        cost: float = 0.0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        external_calls: int = 0,
        llm_calls: int = 0,
    ):
        """Records a tool or operation execution, keeping backward compatibility."""
        self.tool_calls_used += 1
        self.cumulative_latency_ms += latency_ms

        self.consumed.record_consumption(
            tool_calls=1,
            execution_seconds=latency_ms / 1000.0,
            cost=cost,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            external_calls=external_calls,
            llm_calls=llm_calls,
        )

    def record_consumption(
        self,
        tool_name: str = "",
        cost: float = 0.0,
        latency_ms: float = 0.0,
        is_retry: bool = False,
        **kwargs
    ):
        """Records tool execution or recovery consumption in budget ledger."""
        self.record_call(latency_ms=latency_ms, cost=cost)

    def to_dict(self) -> dict[str, Any]:
        """Serializes budget state and ledger."""
        used_calls = max(self.tool_calls_used, self.consumed.tool_calls)
        used_latency = max(self.cumulative_latency_ms, self.consumed.execution_seconds * 1000.0)

        return {
            "investigation_id": self.investigation_id,
            "max_tool_calls": self.max_tool_calls,
            "max_iterations": self.max_iterations,
            "max_llm_calls": self.max_llm_calls,
            "max_llm_tokens": self.max_llm_tokens,
            "max_external_calls": self.max_external_calls,
            "max_execution_seconds": self.max_execution_seconds,
            "max_latency_ms": self.max_latency_ms,
            "max_estimated_cost": round(self.max_estimated_cost, 3),
            "reserved_emergency_budget": self.reserved_emergency_budget,
            "min_utility_threshold": self.min_utility_threshold,
            "diminishing_returns_threshold": self.diminishing_returns_threshold,
            "tool_calls_used": used_calls,
            "remaining_calls": self.remaining_calls,
            "cumulative_latency_ms": round(used_latency, 1),
            "resource_pressure": self.resource_pressure,
            "is_exhausted": self.is_exhausted(),
            "policy_version": self.policy_version,
            "severity": self.severity,
            "consumed": self.consumed.to_dict(),
        }
