from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.db.mongodb import get_database
from app.services.alert_service import evaluate_project_threshold_crossing
from app.services.event_service import evaluate_project_events, persist_and_deduplicate_events
from app.services.dphis_service import calculate_dphis
from app.services.feature_service import engineer_features
from app.ml.models.cost_model import cost_model
from app.ml.models.delay_model import delay_model
from app.config.logging import logger

class ContinuousMonitoringScheduler:
    def __init__(self):
        self.is_running = False

    async def scan_all_projects(self, manual: bool = False, limit: int = 500) -> Dict[str, Any]:
        """
        Executes a continuous monitoring scan over all registered projects.
        Guarantees:
        1. Fault Isolation: An unhandled exception in one project does not crash the scan for others.
        2. Idempotency: Duplicate alerts are suppressed if project is already above threshold.
        3. Event Engine: Generates deduplicated multi-type operational events.
        4. State Synchronization: Persists updated DPHIS and risk levels.
        """
        db = get_database()
        if db is None:
            return {
                "success": False,
                "error": "Database unavailable",
                "scanned_count": 0,
                "alerts_triggered": 0,
                "errors_count": 0
            }

        start_time = datetime.now(timezone.utc)
        self.is_running = True

        cursor = db.projects.find({}, {"_id": 0}).limit(limit)
        projects = await cursor.to_list(length=limit)

        scanned_count = 0
        alerts_triggered = 0
        events_generated = 0
        errors = []

        for p in projects:
            project_id = p.get("project_id")
            if not project_id:
                continue

            try:
                # Retrieve snapshots
                snaps = await db.project_snapshots.find(
                    {"project_id": project_id},
                    {"_id": 0}
                ).sort("snapshot_date", 1).to_list(length=60)

                features = engineer_features(p, snaps)
                c_res = cost_model.predict(features)
                d_res = delay_model.predict(features)

                prev_dphis = p.get("current_dphis") or p.get("dphis")
                dphis_obj = calculate_dphis(
                    project_id=project_id,
                    features=features,
                    cost_risk=c_res.get("cost_risk_score"),
                    time_risk=d_res.get("time_risk_score"),
                    previous_dphis=prev_dphis
                )

                # Evaluate threshold crossing
                thresh_eval = await evaluate_project_threshold_crossing(
                    project_id=project_id,
                    current_dphis=dphis_obj.dphis,
                    previous_dphis=prev_dphis,
                    trigger_source="scheduler_scan"
                )

                if thresh_eval.get("triggered"):
                    alerts_triggered += 1

                # Evaluate operational events
                threshold_val = float(p.get("dphis_threshold", 70.0))
                evts = evaluate_project_events(
                    project=p,
                    snapshots=snaps,
                    current_dphis=dphis_obj.dphis,
                    previous_dphis=prev_dphis,
                    threshold=threshold_val
                )
                persisted = await persist_and_deduplicate_events(evts)
                events_generated += len(persisted)

                scanned_count += 1

            except Exception as e:
                # Crucial: Failure in one project does not stop the entire scan
                logger.error(f"Error scanning project {project_id}: {e}", exc_info=True)
                errors.append({"project_id": project_id, "error": str(e)})

        self.is_running = False
        duration_s = (datetime.now(timezone.utc) - start_time).total_seconds()

        return {
            "success": True,
            "scan_type": "manual" if manual else "scheduled",
            "total_projects": len(projects),
            "scanned_count": scanned_count,
            "alerts_triggered": alerts_triggered,
            "events_generated": events_generated,
            "errors_count": len(errors),
            "errors": errors,
            "duration_seconds": round(duration_s, 2),
            "timestamp": start_time.isoformat()
        }

scheduler = ContinuousMonitoringScheduler()
