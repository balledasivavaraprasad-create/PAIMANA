"""Budget Escalation and Expansion Protocol.

Manages auditable requests for additional resources when high-severity uncertainty
demands extended evidence gathering beyond the initial allocation.
"""
from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional
from .models import InvestigationBudget


@dataclass
class BudgetExpansionRequest:
    """Formal, auditable request to expand an investigation's resource envelope."""
    investigation_id: str
    reason: str
    requested_resources: dict[str, Any]
    current_uncertainty: float
    expected_information_gain: float
    severity: str = "MEDIUM"
    status: str = "PENDING"  # PENDING, APPROVED, DENIED, PARTIAL, EMERGENCY_GRANTED
    audit_notes: str = ""
    request_id: str = field(default_factory=lambda: f"exp_{uuid.uuid4().hex[:8]}")
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "investigation_id": self.investigation_id,
            "reason": self.reason,
            "requested_resources": dict(self.requested_resources),
            "current_uncertainty": round(self.current_uncertainty, 3),
            "expected_information_gain": round(self.expected_information_gain, 3),
            "severity": self.severity,
            "status": self.status,
            "audit_notes": self.audit_notes,
            "created_at": self.created_at,
        }


class BudgetEscalator:
    """Evaluates and decides on budget expansion requests with strict auditable criteria."""

    @classmethod
    def evaluate_request(
        cls,
        request: BudgetExpansionRequest,
        budget: InvestigationBudget,
    ) -> BudgetExpansionRequest:
        """Evaluates whether the requested budget expansion is justified.
        
        Requires:
        1. High or Critical project/event severity.
        2. Substantial remaining uncertainty (>= 0.35) or active material contradiction.
        3. High expected information gain from next tool (>= 0.10).
        """
        sev = request.severity.upper()
        gain = request.expected_information_gain
        uncertainty = request.current_uncertainty

        # Trivial or low severity cannot expand budget
        if sev == "LOW":
            request.status = "DENIED"
            request.audit_notes = "Expansion denied: LOW severity investigations are strictly bounded to prevent budget drift."
            return request

        if gain < 0.08:
            request.status = "DENIED"
            request.audit_notes = f"Expansion denied: Expected information gain ({gain:.3f} < 0.08) does not justify additional resource expenditure."
            return request

        # High / Critical severity with decisive uncertainty
        if sev in ("CRITICAL", "HIGH") and (uncertainty >= 0.30 or "contradiction" in request.reason.lower()):
            if sev == "CRITICAL":
                request.status = "EMERGENCY_GRANTED"
            else:
                request.status = "APPROVED"

            added_tools = int(request.requested_resources.get("tool_calls", 2))
            added_cost = float(request.requested_resources.get("cost", 0.30))
            added_latency = float(request.requested_resources.get("latency_ms", 5000.0))

            budget.max_tool_calls += added_tools
            budget.max_estimated_cost += added_cost
            budget.max_latency_ms += added_latency
            budget.max_execution_seconds += (added_latency / 1000.0)

            request.audit_notes = f"Expansion {request.status}: Granted +{added_tools} tool calls, +${added_cost:.2f} cost ceiling."
            return request

        # Medium severity with strong gain
        if sev == "MEDIUM" and gain >= 0.15 and uncertainty >= 0.40:
            request.status = "PARTIAL"
            added_tools = 1
            budget.max_tool_calls += added_tools
            request.audit_notes = "Partial expansion: Granted +1 discretionary tool call."
            return request

        request.status = "DENIED"
        request.audit_notes = "Expansion denied: Evidentiary conditions did not satisfy policy escalation criteria."
        return request
