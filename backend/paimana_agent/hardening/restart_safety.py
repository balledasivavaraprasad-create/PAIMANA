"""Restart Safety and Crash Recovery Subsystem.

Detects uncompleted or interrupted operations following an unexpected crash or service
restart, safely reconciling pending outbox tasks and in-flight investigations.
"""
from __future__ import annotations
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any

from ..store import Store

logger = logging.getLogger("paimana_agent.hardening.restart_safety")


@dataclass
class RecoverySummary:
    recovered_outbox_tasks: int = 0
    reconciled_investigations: int = 0
    recovery_timestamp: float = field(default_factory=time.time)
    details: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recovered_outbox_tasks": self.recovered_outbox_tasks,
            "reconciled_investigations": self.reconciled_investigations,
            "recovery_timestamp": self.recovery_timestamp,
            "details": self.details,
        }


class RestartRecoveryManager:
    """Manages system recovery following service restart or container crash."""

    @classmethod
    def reconcile_on_startup(cls, store: Store) -> RecoverySummary:
        """Inspects DB for interrupted tasks and safely resets them for re-processing."""
        summary = RecoverySummary()
        now = time.time()

        with store._lock, store._c:
            # 1. Recover in-flight automation outbox tasks
            # Any task stuck in 'processing' or 'in_progress' from pre-crash
            cur = store._c.execute(
                "SELECT id, task_type, attempts FROM automation_outbox WHERE status IN ('processing', 'in_progress')"
            )
            stuck_tasks = cur.fetchall()

            for task in stuck_tasks:
                tid = task["id"]
                attempts = task["attempts"] + 1
                store._c.execute(
                    "UPDATE automation_outbox SET status='pending', attempts=?, last_error=?, updated_at=? WHERE id=?",
                    (attempts, "Recovered from unexpected service restart", now, tid)
                )
                summary.recovered_outbox_tasks += 1
                summary.details.append(f"Reset outbox task #{tid} ({task['task_type']}) to pending.")

            # 2. Check for investigations without completion
            cur = store._c.execute(
                "SELECT id, project_code FROM investigations WHERE report IS NULL OR report = ''"
            )
            empty_invs = cur.fetchall()
            for inv in empty_invs:
                summary.reconciled_investigations += 1
                summary.details.append(f"Flagged empty investigation #{inv['id']} for project {inv['project_code']}.")

        logger.info(
            f"Startup recovery completed: {summary.recovered_outbox_tasks} outbox tasks recovered, "
            f"{summary.reconciled_investigations} investigations reconciled."
        )
        return summary
