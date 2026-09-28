import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from app.db.mongodb import get_database
from app.config.logging import logger

SUPPORTED_EVENT_TYPES = [
    "THRESHOLD_CROSSED",
    "RISK_ACCELERATING",
    "MILESTONE_DELAYED",
    "PROGRESS_STALLED",
    "COST_PROGRESS_MISMATCH"
]

def evaluate_project_events(
    project: Dict[str, Any],
    snapshots: List[Dict[str, Any]],
    current_dphis: float,
    previous_dphis: Optional[float] = None,
    threshold: float = 70.0
) -> List[Dict[str, Any]]:
    """
    Evaluates project status and generates structured event objects for any
    detected risk conditions across all 5 standard PAIMANA event types.
    """
    events: List[Dict[str, Any]] = []
    now_utc = datetime.now(timezone.utc)
    project_id = project.get("project_id", "UNKNOWN")

    # 1. THRESHOLD_CROSSED
    is_initial_crossing = (previous_dphis is None and current_dphis >= threshold)
    is_upward_crossing = (previous_dphis is not None and previous_dphis < threshold and current_dphis >= threshold)
    if is_initial_crossing or is_upward_crossing:
        sev = "CRITICAL" if current_dphis >= 80.0 else "HIGH"
        events.append({
            "event_id": f"EVT-{uuid.uuid4().hex[:12].upper()}",
            "project_id": project_id,
            "event_type": "THRESHOLD_CROSSED",
            "severity": sev,
            "timestamp": now_utc,
            "details": {
                "threshold": threshold,
                "current_dphis": current_dphis,
                "previous_dphis": previous_dphis,
                "crossed_by": round(current_dphis - threshold, 1)
            }
        })

    # 2. RISK_ACCELERATING
    if previous_dphis is not None:
        velocity = current_dphis - previous_dphis
        if velocity >= 8.0:
            events.append({
                "event_id": f"EVT-{uuid.uuid4().hex[:12].upper()}",
                "project_id": project_id,
                "event_type": "RISK_ACCELERATING",
                "severity": "CRITICAL" if velocity >= 12.0 else "HIGH",
                "timestamp": now_utc,
                "details": {
                    "risk_velocity": round(velocity, 2),
                    "current_dphis": current_dphis,
                    "previous_dphis": previous_dphis
                }
            })

    # 3. MILESTONE_DELAYED
    schedule_slip = float(project.get("schedule_slippage_months", 0.0) or 0.0)
    latest_milestones = {}
    if snapshots:
        sorted_snaps = sorted(snapshots, key=lambda s: s.get("snapshot_date", ""))
        latest_milestones = sorted_snaps[-1].get("milestones", {})
    delayed_count = int(latest_milestones.get("delayed", 0) or 0)

    if delayed_count > 0 or schedule_slip >= 3.0:
        events.append({
            "event_id": f"EVT-{uuid.uuid4().hex[:12].upper()}",
            "project_id": project_id,
            "event_type": "MILESTONE_DELAYED",
            "severity": "CRITICAL" if schedule_slip >= 12.0 or delayed_count >= 3 else "HIGH",
            "timestamp": now_utc,
            "details": {
                "delayed_milestones": delayed_count,
                "schedule_slippage_months": schedule_slip
            }
        })

    # 4. PROGRESS_STALLED
    phys_prog = float(project.get("physical_progress_percent") or project.get("physical_progress") or 0.0)
    velocity = 0.0
    stagnation_cycles = 0
    if len(snapshots) >= 2:
        sorted_snaps = sorted(snapshots, key=lambda s: s.get("snapshot_date", ""))
        p_now = float(sorted_snaps[-1].get("physical_progress", 0.0))
        p_prev = float(sorted_snaps[-2].get("physical_progress", 0.0))
        velocity = p_now - p_prev
        if velocity < 0.5:
            stagnation_cycles = 1

    if stagnation_cycles > 0 or (len(snapshots) >= 2 and velocity < 0.3 and phys_prog < 90.0):
        events.append({
            "event_id": f"EVT-{uuid.uuid4().hex[:12].upper()}",
            "project_id": project_id,
            "event_type": "PROGRESS_STALLED",
            "severity": "HIGH" if velocity <= 0.0 else "MODERATE",
            "timestamp": now_utc,
            "details": {
                "progress_velocity": round(velocity, 2),
                "physical_progress": phys_prog
            }
        })

    # 5. COST_PROGRESS_MISMATCH
    cost_rev = float(project.get("revised_cost_crores") or (project.get("cost", {}).get("revised") if isinstance(project.get("cost"), dict) else 0.0) or 1.0)
    cum_exp = float(project.get("expenditure_crores") or 0.0)
    fin_prog = round((cum_exp / max(1.0, cost_rev)) * 100.0, 1) if cost_rev > 0 else 0.0
    gap = fin_prog - phys_prog

    if gap >= 15.0:
        events.append({
            "event_id": f"EVT-{uuid.uuid4().hex[:12].upper()}",
            "project_id": project_id,
            "event_type": "COST_PROGRESS_MISMATCH",
            "severity": "CRITICAL" if gap >= 25.0 else "HIGH",
            "timestamp": now_utc,
            "details": {
                "financial_progress": fin_prog,
                "physical_progress": phys_prog,
                "gap_pts": round(gap, 1)
            }
        })

    return events

async def persist_and_deduplicate_events(events: List[Dict[str, Any]], cooldown_hours: int = 24) -> List[Dict[str, Any]]:
    """
    Persists events to MongoDB while deduplicating events of the same type
    for the same project within the specified cooldown window.
    """
    db = get_database()
    persisted: List[Dict[str, Any]] = []

    for event in events:
        project_id = event["project_id"]
        event_type = event["event_type"]

        if db is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=cooldown_hours)
            existing = await db.project_events.find_one({
                "project_id": project_id,
                "event_type": event_type,
                "timestamp": {"$gte": cutoff}
            })
            if existing:
                logger.info(f"Duplicate event {event_type} for {project_id} suppressed by cooldown.")
                continue

            await db.project_events.insert_one(dict(event))

        persisted.append(event)

    return persisted
