"""Rolling Window Reliability Metrics & Context Tracking.

Maintains sliding-window execution metrics (e.g. last 20, last 100 calls) and
context-specific performance breakdowns (by sector, project phase, source system).
"""
from __future__ import annotations
import collections
from dataclasses import dataclass, field
from typing import Any, Optional
from .models import ToolResult, ToolResultStatus


@dataclass
class CallRecord:
    tool_name: str
    status: str
    is_success: bool
    is_useful: bool
    latency_ms: float
    timestamp: float
    context: dict = field(default_factory=dict)


class ReliabilityMetrics:
    """Sliding-window telemetry and contextual segmentation for tool reliability."""

    def __init__(self, max_history: int = 200):
        self.max_history = max_history
        self._history: collections.deque[CallRecord] = collections.deque(maxlen=max_history)
        self._by_tool: dict[str, collections.deque[CallRecord]] = collections.defaultdict(
            lambda: collections.deque(maxlen=max_history)
        )

    def record_call(self, result: ToolResult, context: Optional[dict] = None):
        """Records an execution outcome for sliding window analysis."""
        rec = CallRecord(
            tool_name=result.tool_name,
            status=result.status,
            is_success=result.is_success,
            is_useful=result.is_usable_evidence,
            latency_ms=result.execution_time_ms,
            timestamp=result.retrieved_at,
            context=dict(context or {}),
        )
        self._history.append(rec)
        self._by_tool[result.tool_name].append(rec)

    def get_rolling_success_rate(self, tool_name: str, window: int = 20) -> float:
        """Returns the technical success rate over the last `window` invocations."""
        recs = list(self._by_tool.get(tool_name, []))[-window:]
        if not recs:
            return 1.0
        successes = sum(1 for r in recs if r.is_success)
        return round(successes / len(recs), 3)

    def get_rolling_useful_evidence_rate(self, tool_name: str, window: int = 20) -> float:
        """Returns the useful evidence rate over the last `window` invocations."""
        recs = list(self._by_tool.get(tool_name, []))[-window:]
        if not recs:
            return 1.0
        useful = sum(1 for r in recs if r.is_useful)
        return round(useful / len(recs), 3)

    def get_contextual_success_rate(self, tool_name: str, context_key: str, context_val: Any) -> float:
        """Returns the success rate within a specific context segment (e.g. stage='EXECUTION')."""
        recs = [
            r for r in self._by_tool.get(tool_name, [])
            if str(r.context.get(context_key, "")).lower() == str(context_val).lower()
        ]
        if not recs:
            return 1.0
        successes = sum(1 for r in recs if r.is_success)
        return round(successes / len(recs), 3)

    def to_dict(self) -> dict[str, Any]:
        tools_summary = {}
        for t_name in self._by_tool:
            tools_summary[t_name] = {
                "rolling_20_success_rate": self.get_rolling_success_rate(t_name, 20),
                "rolling_20_useful_evidence_rate": self.get_rolling_useful_evidence_rate(t_name, 20),
                "total_recorded_calls": len(self._by_tool[t_name]),
            }
        return {
            "total_system_calls": len(self._history),
            "tools": tools_summary,
        }
