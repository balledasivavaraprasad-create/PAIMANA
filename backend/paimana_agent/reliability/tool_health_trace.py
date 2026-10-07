"""Tool Failure Telemetry & Health Trace Logging.

Captures structured tool failure events, recovery traces, and diagnostics for
investigation audit trails and administrative dashboards.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolFailureEvent:
    """Structured event capturing an execution error and applied recovery action."""
    tool_name: str
    taxonomy_code: str
    error_message: str
    recovery_action: str
    attempt: int = 1
    latency_ms: float = 0.0
    budget_spent: float = 0.0
    substituted_by: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "taxonomy_code": self.taxonomy_code,
            "error_message": self.error_message,
            "recovery_action": self.recovery_action,
            "attempt": self.attempt,
            "latency_ms": round(self.latency_ms, 2),
            "budget_spent": round(self.budget_spent, 4),
            "substituted_by": self.substituted_by,
            "timestamp": self.timestamp,
        }


class ToolHealthTraceBuilder:
    """Collects and aggregates failure telemetry across specialist tools."""

    def __init__(self):
        self.events: list[ToolFailureEvent] = []

    def record_failure(
        self,
        tool_name: str,
        taxonomy_code: str,
        error_message: str,
        recovery_action: str,
        attempt: int = 1,
        latency_ms: float = 0.0,
        budget_spent: float = 0.0,
        substituted_by: Optional[str] = None,
    ) -> ToolFailureEvent:
        """Records a new failure and recovery event."""
        ev = ToolFailureEvent(
            tool_name=tool_name,
            taxonomy_code=taxonomy_code,
            error_message=str(error_message),
            recovery_action=recovery_action,
            attempt=attempt,
            latency_ms=latency_ms,
            budget_spent=budget_spent,
            substituted_by=substituted_by,
        )
        self.events.append(ev)
        return ev

    def get_summary(self) -> dict[str, Any]:
        """Provides an aggregated failure and recovery summary."""
        by_tool: dict[str, int] = {}
        by_action: dict[str, int] = {}
        by_code: dict[str, int] = {}

        for ev in self.events:
            by_tool[ev.tool_name] = by_tool.get(ev.tool_name, 0) + 1
            by_action[ev.recovery_action] = by_action.get(ev.recovery_action, 0) + 1
            by_code[ev.taxonomy_code] = by_code.get(ev.taxonomy_code, 0) + 1

        return {
            "total_failure_events": len(self.events),
            "failures_by_tool": by_tool,
            "actions_by_type": by_action,
            "taxonomy_codes": by_code,
            "recent_events": [ev.to_dict() for ev in self.events[-10:]],
        }
