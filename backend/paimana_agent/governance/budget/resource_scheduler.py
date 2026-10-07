"""Resource Priority Scheduler.

Dispatches queued investigations and resolves multi-project contention based on
composite priority scores, deadlines, and project materiality.
"""
from __future__ import annotations
from typing import Any, Optional
from .concurrency import InvestigationPriority


class PriorityScheduler:
    """Dispatches work items according to priority rankings."""

    @classmethod
    def rank_queue(cls, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Ranks queued investigation items descending by priority score."""
        return sorted(items, key=lambda x: getattr(x.get("priority"), "priority_score", 0.0), reverse=True)

    @classmethod
    def select_next(cls, items: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
        """Selects the highest priority item from the queue."""
        if not items:
            return None
        ranked = cls.rank_queue(items)
        return ranked[0]
