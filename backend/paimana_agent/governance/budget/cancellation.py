"""Investigation Cancellation and Cascading Teardown.

Manages clean cancellation, preemption, and cascading teardown of child tool
executions and reserved resources when investigations are superseded or preempted.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from .models import InvestigationBudget
from .budget_reservation import ReservationManager


class CancellationReason(str, Enum):
    """Standardized reasons for aborting an active investigation."""
    SUPERSEDED = "SUPERSEDED"                          # New monitoring cycle replaced snapshot
    RISK_RESOLVED = "RISK_RESOLVED"                    # Anomaly auto-resolved or corrected
    DUPLICATE_INVESTIGATION = "DUPLICATE_INVESTIGATION"# Identical investigation already running
    BUDGET_REALLOCATION = "BUDGET_REALLOCATION"        # Portfolio manager reclaimed resources
    HIGHER_PRIORITY_EVENT = "HIGHER_PRIORITY_EVENT"    # Preempted by critical infrastructure emergency


@dataclass
class CancellationRecord:
    """Audit record capturing the cancellation of an investigation."""
    investigation_id: str
    reason: CancellationReason
    explanation: str
    released_reservations: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "investigation_id": self.investigation_id,
            "reason": self.reason.value,
            "explanation": self.explanation,
            "released_reservations": self.released_reservations,
            "timestamp": self.timestamp,
        }


class CancellationManager:
    """Orchestrates cascading cancellation across budget reservations and running tools."""

    @classmethod
    def cancel_investigation(
        cls,
        investigation_id: str,
        reason: CancellationReason,
        explanation: str,
        reservation_manager: Optional[ReservationManager] = None,
    ) -> CancellationRecord:
        """Aborts the investigation and cascades downward to release holds."""
        released = 0
        if reservation_manager:
            for res_id, res in list(reservation_manager.reservations.items()):
                if res.status == "PENDING":
                    reservation_manager.cancel(res_id)
                    released += 1

        return CancellationRecord(
            investigation_id=investigation_id,
            reason=reason,
            explanation=explanation,
            released_reservations=released,
        )
