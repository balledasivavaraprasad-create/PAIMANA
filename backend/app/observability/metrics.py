from datetime import datetime, timezone
from typing import Any, Dict, Optional
from app.domain.entities import MonitoringCycle


class MonitoringMetrics:
    def __init__(self):
        self.projects_evaluated = 0
        self.skipped_no_change = 0
        self.events_generated = 0
        self.alerts_generated = 0
        self.last_cycle: Optional[Dict[str, Any]] = None
        self.last_scan_at: Optional[datetime] = None

    def record_cycle(self, cycle: MonitoringCycle) -> None:
        self.last_cycle = cycle.model_dump()
        self.last_scan_at = cycle.completed_at or datetime.now(timezone.utc)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "projects_evaluated": self.projects_evaluated,
            "projects_skipped_no_change": self.skipped_no_change,
            "events_generated": self.events_generated,
            "alerts_generated": self.alerts_generated,
            "last_scan_at": self.last_scan_at.isoformat() if self.last_scan_at else None,
            "last_cycle": self.last_cycle,
        }


monitoring_metrics = MonitoringMetrics()
