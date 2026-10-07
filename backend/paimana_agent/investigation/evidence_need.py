"""First-Class EvidenceNeed Model for Uncertainty-Driven Information Acquisition.

Defines the explicit information gaps and uncertainties that the agent seeks
to resolve through targeted tool execution rather than heuristic routing.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EvidenceNeed:
    """Explicit declaration of required empirical evidence to resolve an active uncertainty."""
    id: str
    question: str
    target_hypothesis_ids: list[str] = field(default_factory=list)
    required_evidence_types: list[str] = field(default_factory=list)
    priority: float = 0.50
    discrimination_power: float = 0.50
    urgency: float = 0.50
    freshness_requirement: float = 0.70
    status: str = "OPEN"  # OPEN, SATISFIED, UNRESOLVABLE
    satisfied_by_tool: Optional[str] = None
    satisfied_by_evidence_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None
    unresolvable_reason: Optional[str] = None

    def mark_satisfied(self, tool_name: str, evidence_id: Optional[str] = None):
        """Marks this need as resolved by an empirical observation."""
        self.status = "SATISFIED"
        self.satisfied_by_tool = tool_name
        self.satisfied_by_evidence_id = evidence_id
        self.resolved_at = time.time()

    def mark_unresolvable(self, reason: str = ""):
        """Marks this need as currently unresolvable due to missing tool or authorization."""
        self.status = "UNRESOLVABLE"
        self.unresolvable_reason = reason
        self.resolved_at = time.time()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "question": self.question,
            "target_hypothesis_ids": list(self.target_hypothesis_ids),
            "required_evidence_types": list(self.required_evidence_types),
            "priority": round(self.priority, 3),
            "discrimination_power": round(self.discrimination_power, 3),
            "urgency": round(self.urgency, 3),
            "freshness_requirement": round(self.freshness_requirement, 3),
            "status": self.status,
            "satisfied_by_tool": self.satisfied_by_tool,
            "satisfied_by_evidence_id": self.satisfied_by_evidence_id,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
            "unresolvable_reason": self.unresolvable_reason,
        }
