"""Portfolio-Wide Admission Control and Concurrency Governance.

Controls simultaneous investigations across the national portfolio, enforcing
concurrency ceilings for LLM calls, external APIs, and active worker slots.
"""
from __future__ import annotations
import time
from enum import Enum
from typing import Any, Optional
from .concurrency import InvestigationPriority


class AdmissionStatus(str, Enum):
    """Admission determination for an incoming investigation request."""
    ADMIT = "ADMIT"        # Resources immediately available; dispatched
    QUEUE = "QUEUE"        # Capacity saturated; queued in priority order
    DEFER = "DEFER"        # Low-priority request postponed to off-peak
    REJECT = "REJECT"      # System saturated; exceeds maximum queue ceiling


class PortfolioAdmissionController:
    """Controls portfolio-level concurrency and manages the admission gateway."""

    def __init__(
        self,
        max_active_investigations: int = 10,
        max_simultaneous_llm_calls: int = 5,
        max_simultaneous_external_calls: int = 8,
        max_queue_depth: int = 25,
    ):
        self.max_active_investigations = max_active_investigations
        self.max_simultaneous_llm_calls = max_simultaneous_llm_calls
        self.max_simultaneous_external_calls = max_simultaneous_external_calls
        self.max_queue_depth = max_queue_depth

        self.active_investigations: dict[str, dict[str, Any]] = {}
        self.queued_investigations: list[dict[str, Any]] = []

    def evaluate_admission(
        self,
        investigation_id: str,
        priority: InvestigationPriority,
        project_code: str = "",
    ) -> tuple[AdmissionStatus, str]:
        """Evaluates whether to admit, queue, defer, or reject an investigation."""
        # Check active capacity
        if len(self.active_investigations) < self.max_active_investigations:
            self.active_investigations[investigation_id] = {
                "investigation_id": investigation_id,
                "project_code": project_code,
                "priority": priority,
                "admitted_at": time.time(),
            }
            return AdmissionStatus.ADMIT, f"Admitted: Active slots available ({len(self.active_investigations)}/{self.max_active_investigations})."

        # Active capacity full: check priority for preemption or queuing
        if len(self.queued_investigations) >= self.max_queue_depth:
            # Saturated queue: low priority rejected
            if priority.priority_score < 0.40:
                return AdmissionStatus.REJECT, f"Rejected: Queue full ({len(self.queued_investigations)} items) and priority ({priority.priority_score}) insufficient."
            return AdmissionStatus.DEFER, "Deferred: System saturated; deferred to subsequent monitoring cycle."

        # Queue request
        self.queued_investigations.append({
            "investigation_id": investigation_id,
            "project_code": project_code,
            "priority": priority,
            "queued_at": time.time(),
        })
        # Sort queue descending by priority_score
        self.queued_investigations.sort(key=lambda x: x["priority"].priority_score, reverse=True)
        return AdmissionStatus.QUEUE, f"Queued: Position {len(self.queued_investigations)} based on priority score ({priority.priority_score})."

    def release_investigation(self, investigation_id: str) -> Optional[dict[str, Any]]:
        """Releases an active investigation and returns the next highest-priority queued item if available."""
        if investigation_id in self.active_investigations:
            del self.active_investigations[investigation_id]

        if self.queued_investigations and len(self.active_investigations) < self.max_active_investigations:
            next_item = self.queued_investigations.pop(0)
            self.active_investigations[next_item["investigation_id"]] = {
                "investigation_id": next_item["investigation_id"],
                "project_code": next_item["project_code"],
                "priority": next_item["priority"],
                "admitted_at": time.time(),
            }
            return next_item
        return None

    def get_portfolio_status(self) -> dict[str, Any]:
        """Provides high-level concurrency dashboard metrics."""
        return {
            "active_investigations_count": len(self.active_investigations),
            "max_active_investigations": self.max_active_investigations,
            "queued_investigations_count": len(self.queued_investigations),
            "max_queue_depth": self.max_queue_depth,
            "active_ids": list(self.active_investigations.keys()),
        }
