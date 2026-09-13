from typing import List, Dict, Any
from datetime import datetime

def parse_date(date_str: str) -> datetime:
    for fmt in ("%Y-%m-%d", "%Y-%m", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    return datetime.utcnow()

def compute_schedule_features(project: Dict[str, Any], snapshots: List[Dict[str, Any]]) -> Dict[str, float]:
    schedule = project.get("schedule", {})
    start_str = schedule.get("original_start", "2023-01-01")
    orig_end_str = schedule.get("original_end", "2025-12-31")
    rev_end_str = schedule.get("revised_end", orig_end_str)

    start = parse_date(start_str)
    orig_end = parse_date(orig_end_str)
    rev_end = parse_date(rev_end_str)

    planned_duration_months = max(1.0, (orig_end - start).days / 30.4)
    revised_duration_months = max(1.0, (rev_end - start).days / 30.4)
    deadline_slip_months = max(0.0, (rev_end - orig_end).days / 30.4)
    schedule_gap_ratio = deadline_slip_months / planned_duration_months

    # Milestone delay statistics from latest snapshot
    milestone_delay_rate = 0.0
    if snapshots:
        sorted_snaps = sorted(snapshots, key=lambda x: x.get("snapshot_date", ""))
        latest = sorted_snaps[-1]
        m = latest.get("milestones", {})
        total_m = max(1, int(m.get("total", 0) or (int(m.get("completed", 0)) + int(m.get("delayed", 0)) + int(m.get("pending", 0)))))
        delayed_m = int(m.get("delayed", 0))
        milestone_delay_rate = min(1.0, delayed_m / total_m)

    return {
        "planned_duration_months": round(planned_duration_months, 1),
        "deadline_slip_months": round(deadline_slip_months, 1),
        "schedule_gap_ratio": round(schedule_gap_ratio, 4),
        "milestone_delay_rate": round(milestone_delay_rate, 4),
    }
