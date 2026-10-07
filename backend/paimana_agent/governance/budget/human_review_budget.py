"""Human Attention and Review Budget Governance.

Treats human attention as a scarce, bounded resource. Prevents overwhelming human review
queues with routine noise and routes critical interventions to appropriate priority tiers.
"""
from __future__ import annotations
import time
from enum import Enum
from typing import Any, Optional


class ReviewClass(str, Enum):
    """Categorization of human review urgency and impact."""
    AUTO_ANALYSIS = "AUTO_ANALYSIS"                # Low impact: automated logging, no immediate human block
    REVIEW_REQUIRED = "REVIEW_REQUIRED"            # Standard impact: normal review queue
    HIGH_PRIORITY_REVIEW = "HIGH_PRIORITY_REVIEW"  # High impact: priority queue, notifications
    EMERGENCY_REVIEW = "EMERGENCY_REVIEW"          # Critical infrastructure crisis: immediate paging


class HumanReviewCapacity:
    """Manages human review attention limits and queue capacity."""

    def __init__(self, max_pending_approvals: int = 20):
        self.max_pending_approvals = max_pending_approvals
        self.pending_items: list[dict[str, Any]] = []

    @property
    def pending_count(self) -> int:
        return len(self.pending_items)

    @property
    def is_saturated(self) -> bool:
        return self.pending_count >= self.max_pending_approvals

    def classify_and_admit(
        self,
        recommendation_id: str,
        severity: str,
        cost_impact_cr: float = 0.0,
        is_punitive: bool = False,
    ) -> tuple[bool, ReviewClass, str]:
        """Classifies the review urgency and admits or batches it according to capacity."""
        sev = (severity or "MEDIUM").upper()

        # Determine review classification
        if sev == "CRITICAL" or cost_impact_cr >= 500.0 or is_punitive:
            review_class = ReviewClass.EMERGENCY_REVIEW if sev == "CRITICAL" else ReviewClass.HIGH_PRIORITY_REVIEW
        elif sev == "HIGH" or cost_impact_cr >= 100.0:
            review_class = ReviewClass.HIGH_PRIORITY_REVIEW
        elif sev == "MEDIUM":
            review_class = ReviewClass.REVIEW_REQUIRED
        else:
            review_class = ReviewClass.AUTO_ANALYSIS

        # Check queue saturation
        if self.is_saturated:
            # Emergency and High Priority always bypass saturation to human queue
            if review_class in (ReviewClass.EMERGENCY_REVIEW, ReviewClass.HIGH_PRIORITY_REVIEW):
                self.pending_items.append({
                    "recommendation_id": recommendation_id,
                    "review_class": review_class,
                    "submitted_at": time.time(),
                })
                return True, review_class, f"Admitted (Bypass): Critical item prioritized despite queue saturation ({self.pending_count} pending)."
            else:
                return False, review_class, f"Batched / Deferred: Human review capacity saturated ({self.pending_count}/{self.max_pending_approvals} pending)."

        self.pending_items.append({
            "recommendation_id": recommendation_id,
            "review_class": review_class,
            "submitted_at": time.time(),
        })
        return True, review_class, f"Admitted to {review_class.value} queue."

    def resolve_item(self, recommendation_id: str) -> bool:
        """Removes a resolved approval from the pending queue."""
        initial_len = len(self.pending_items)
        self.pending_items = [item for item in self.pending_items if item["recommendation_id"] != recommendation_id]
        return len(self.pending_items) < initial_len
