"""Tool Candidate & Selection Record Models.

Provides auditable representations of evaluated tool candidates, their
multi-criteria utility breakdowns, and historical selection decisions.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCandidate:
    """Evaluated tool candidate with full multi-criteria scoring breakdown."""
    tool_name: str
    target_needs: list[str] = field(default_factory=list)
    expected_information_gain: float = 0.0
    discrimination_power: float = 0.0
    source_authority: float = 0.80
    expected_freshness: float = 1.0
    execution_cost: float = 0.10
    expected_latency_ms: float = 20.0
    redundancy_penalty: float = 0.0
    failure_penalty: float = 0.0
    net_utility: float = 0.0
    resource_adjusted_value: float = 0.0
    estimated_financial_cost: float = 0.0
    is_affordable: bool = True
    information_value: float = 0.0
    execution_reliability: float = 0.95
    evidence_reliability: float = 0.95
    composite_reliability: float = 0.95
    selection_rationale: str = ""
    eligible: bool = True
    ineligibility_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "target_needs": list(self.target_needs),
            "information_value": round(self.information_value, 3),
            "expected_information_gain": round(self.expected_information_gain, 3),
            "discrimination_power": round(self.discrimination_power, 3),
            "source_authority": round(self.source_authority, 3),
            "execution_reliability": round(self.execution_reliability, 3),
            "evidence_reliability": round(self.evidence_reliability, 3),
            "composite_reliability": round(self.composite_reliability, 3),
            "expected_freshness": round(self.expected_freshness, 3),
            "execution_cost": round(self.execution_cost, 3),
            "expected_latency_ms": round(self.expected_latency_ms, 1),
            "redundancy_penalty": round(self.redundancy_penalty, 3),
            "failure_penalty": round(self.failure_penalty, 3),
            "net_utility": round(self.net_utility, 3),
            "resource_adjusted_value": round(self.resource_adjusted_value, 4),
            "estimated_financial_cost": round(self.estimated_financial_cost, 4),
            "is_affordable": self.is_affordable,
            "selection_rationale": self.selection_rationale,
            "eligible": self.eligible,
            "ineligibility_reasons": list(self.ineligibility_reasons),
        }


@dataclass
class ToolSelectionRecord:
    """Historical audit record capturing why a specific tool was chosen over alternatives."""
    step: int
    phase: str
    selected_tool: str
    net_utility: float
    candidates_evaluated: list[dict] = field(default_factory=list)
    evidence_needs_addressed: list[str] = field(default_factory=list)
    selection_rationale: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "phase": self.phase,
            "selected_tool": self.selected_tool,
            "net_utility": round(self.net_utility, 3),
            "candidates_evaluated": self.candidates_evaluated,
            "evidence_needs_addressed": list(self.evidence_needs_addressed),
            "selection_rationale": self.selection_rationale,
            "timestamp": self.timestamp,
        }
