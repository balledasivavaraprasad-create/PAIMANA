"""Risk-Calibrated Investigation Budget Policy.

Calibrates resource limits (iterations, tool calls, LLM tokens, external calls,
latency, monetary cost, and emergency reserves) dynamically according to
event and anomaly severity.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
from .models import InvestigationBudget, ResourceConsumption


@dataclass
class BudgetPolicy:
    """Configurable multi-resource policy governing an investigation's resource envelope."""
    severity: str = "MEDIUM"
    max_iterations: int = 6
    max_tool_calls: int = 6
    max_llm_calls: int = 4
    max_tokens: int = 8000
    max_external_calls: int = 4
    max_seconds: float = 40.0
    max_cost: float = 0.80

    minimum_reserve: float = 0.15
    escalation_rules: dict[str, Any] = field(default_factory=dict)
    version: str = "1.0"

    @classmethod
    def for_severity(cls, severity: str = "MEDIUM") -> BudgetPolicy:
        """Constructs an investigation budget policy calibrated to the event risk/severity."""
        sev = (severity or "MEDIUM").upper()

        if sev == "CRITICAL":
            return cls(
                severity="CRITICAL",
                max_iterations=10,
                max_tool_calls=12,
                max_llm_calls=8,
                max_tokens=20000,
                max_external_calls=10,
                max_seconds=90.0,
                max_cost=2.50,
                minimum_reserve=0.20,
                escalation_rules={
                    "auto_approve_material_contradiction": True,
                    "max_expansions": 2,
                    "expansion_allowance_tools": 3,
                },
                version="1.0-critical",
            )
        elif sev == "HIGH":
            return cls(
                severity="HIGH",
                max_iterations=8,
                max_tool_calls=8,
                max_llm_calls=6,
                max_tokens=14000,
                max_external_calls=6,
                max_seconds=60.0,
                max_cost=1.50,
                minimum_reserve=0.15,
                escalation_rules={
                    "auto_approve_material_contradiction": True,
                    "max_expansions": 1,
                    "expansion_allowance_tools": 2,
                },
                version="1.0-high",
            )
        elif sev == "LOW":
            return cls(
                severity="LOW",
                max_iterations=3,
                max_tool_calls=4,
                max_llm_calls=2,
                max_tokens=4000,
                max_external_calls=2,
                max_seconds=20.0,
                max_cost=0.35,
                minimum_reserve=0.10,
                escalation_rules={
                    "auto_approve_material_contradiction": False,
                    "max_expansions": 0,
                    "expansion_allowance_tools": 0,
                },
                version="1.0-low",
            )
        else:  # MEDIUM default
            return cls(
                severity="MEDIUM",
                max_iterations=6,
                max_tool_calls=6,
                max_llm_calls=4,
                max_tokens=8000,
                max_external_calls=4,
                max_seconds=40.0,
                max_cost=0.80,
                minimum_reserve=0.15,
                escalation_rules={
                    "auto_approve_material_contradiction": True,
                    "max_expansions": 1,
                    "expansion_allowance_tools": 2,
                },
                version="1.0-medium",
            )

    def create_budget(self, investigation_id: str = "") -> InvestigationBudget:
        """Instantiates an InvestigationBudget from this policy."""
        return InvestigationBudget(
            investigation_id=investigation_id,
            max_iterations=self.max_iterations,
            max_tool_calls=self.max_tool_calls,
            max_llm_calls=self.max_llm_calls,
            max_llm_tokens=self.max_tokens,
            max_external_calls=self.max_external_calls,
            max_execution_seconds=self.max_seconds,
            max_wall_clock_seconds=self.max_seconds * 1.33,
            max_estimated_cost=self.max_cost,
            reserved_emergency_budget=self.minimum_reserve,
            policy_version=self.version,
            severity=self.severity,
            consumed=ResourceConsumption(),
            tool_calls_used=0,
            cumulative_latency_ms=0.0,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "max_iterations": self.max_iterations,
            "max_tool_calls": self.max_tool_calls,
            "max_llm_calls": self.max_llm_calls,
            "max_tokens": self.max_tokens,
            "max_external_calls": self.max_external_calls,
            "max_seconds": self.max_seconds,
            "max_cost": self.max_cost,
            "minimum_reserve": self.minimum_reserve,
            "escalation_rules": dict(self.escalation_rules),
            "version": self.version,
        }
