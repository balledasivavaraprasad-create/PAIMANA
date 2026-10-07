"""Authoritative monitoring lifecycle.

PROJECT SOURCE → INGESTION → VALIDATION → FRESHNESS → SNAPSHOT → HASH →
MATERIAL CHANGE → FEATURE ENGINEERING → PREDICTION → SHAP → DPHIS →
EVENT ENGINE → PEER INTELLIGENCE → INVESTIGATION TRIGGER

DPHIS, thresholds, events, and investigation decisions stay in this layer.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from app.config.logging import logger
from app.domain.entities import (
    DataQuality,
    Event,
    MonitoringCycle,
    MonitoringEvaluation,
    ProjectSnapshot,
)
from app.domain.enums import EventType, InvestigationStatus
from app.domain.errors import DomainError, ErrorCode
from app.observability.metrics import monitoring_metrics
from app.repositories import (
    alerts_repo,
    events_repo,
    investigations_repo,
    monitoring_cycles_repo,
    predictions_repo,
    projects_repo,
    snapshots_repo,
)
from app.services.agent_adapter import agent_adapter, risk_tier_from_dphis
from app.services.alert_service import evaluate_project_threshold_crossing
from app.services.data_quality_service import assess_project_quality, persist_data_quality
from app.services.event_service import evaluate_project_events, persist_and_deduplicate_events
from app.services.peer_intelligence_service import analyze_peers, peer_event_payload
from app.services.snapshot_identity import (
    compute_snapshot_hash,
    is_material_change,
    parse_observed_at,
)

INVESTIGATION_EVENT_TYPES = {
    EventType.THRESHOLD_CROSSED.value,
    EventType.RISK_ACCELERATING.value,
    EventType.PEER_OUTLIER.value,
}


def _num(value: Any) -> Optional[float]:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


class MonitoringService:
    async def ingest_project_update(
        self,
        project_id: str,
        payload: Optional[Dict[str, Any]] = None,
        *,
        trigger: str = "project_update",
        force: bool = False,
        queue_investigation: bool = True,
    ) -> MonitoringEvaluation:
        project = await projects_repo.find_one({"project_id": project_id})
        if not project:
            raise DomainError(ErrorCode.PROJECT_NOT_FOUND, "Project not found", 404, {"project_id": project_id})
        if payload:
            merged = dict(project)
            merged.update(payload)
            project = merged
        return await self.evaluate_project(
            project,
            trigger=trigger,
            force=force,
            queue_investigation=queue_investigation,
        )

    async def run_scheduled_scan(self, *, limit: int = 500, trigger: str = "scheduled_scan") -> MonitoringCycle:
        cycle = MonitoringCycle(
            cycle_id=f"CYC-{uuid.uuid4().hex[:10].upper()}",
            trigger=trigger,
            status="running",
        )
        await monitoring_cycles_repo.insert_one(cycle.model_dump())
        projects = await projects_repo.find_many({}, limit=limit)
        for project in projects:
            try:
                result = await self.evaluate_project(project, trigger=trigger, force=False)
                cycle.projects_evaluated += 1
                if not result.material_change:
                    cycle.projects_skipped_no_change += 1
                cycle.events_generated += len(result.events)
                cycle.alerts_generated += len(result.alert_ids)
                if result.investigation_id:
                    cycle.investigations_triggered += 1
            except Exception as exc:
                cycle.failures += 1
                logger.warning(f"Monitoring scan failed for {project.get('project_id')}: {exc}")
        cycle.status = "completed"
        cycle.completed_at = datetime.now(timezone.utc)
        await monitoring_cycles_repo.update_one({"cycle_id": cycle.cycle_id}, cycle.model_dump())
        monitoring_metrics.record_cycle(cycle)
        return cycle

    async def evaluate_project(
        self,
        project: Dict[str, Any],
        *,
        trigger: str = "project_update",
        force: bool = False,
        queue_investigation: bool = True,
    ) -> MonitoringEvaluation:
        project_id = project["project_id"]
        snapshots = await snapshots_repo.find_many(
            {"project_id": project_id},
            sort=[("observed_at", 1), ("snapshot_date", 1)],
            limit=60,
        )
        latest_existing = snapshots[-1] if snapshots else None

        observed_at = parse_observed_at(
            project.get("last_observed_at")
            or (latest_existing or {}).get("observed_at")
            or (latest_existing or {}).get("snapshot_date")
            or datetime.now(timezone.utc)
        )
        report_period = observed_at.strftime("%Y-%m")
        snapshot_doc = {
            "project_id": project_id,
            "observed_at": observed_at,
            "snapshot_date": observed_at.strftime("%Y-%m-%d"),
            "report_period": report_period,
            "source": trigger,
            "physical_progress": _num(project.get("physical_progress_pct") or project.get("physical_progress") or (latest_existing or {}).get("physical_progress")),
            "financial_progress": _num(project.get("financial_progress_pct") or project.get("financial_progress") or (latest_existing or {}).get("financial_progress")),
            "cumulative_expenditure": _num(project.get("expenditure_crores") or (latest_existing or {}).get("cumulative_expenditure")),
            "milestones": project.get("milestones") or (latest_existing or {}).get("milestones"),
            "cost": project.get("cost"),
            "schedule": project.get("schedule"),
        }
        snapshot_hash = compute_snapshot_hash(project, snapshot_doc)
        snapshot_doc["snapshot_hash"] = snapshot_hash
        snapshot_id = f"SNP-{uuid.uuid4().hex[:12].upper()}"
        snapshot_doc["snapshot_id"] = snapshot_id

        quality = assess_project_quality(project, snapshot_doc)
        await persist_data_quality(quality)

        material, skip_reason = is_material_change(latest_existing, snapshot_doc, force=force)
        if not material:
            monitoring_metrics.skipped_no_change += 1
            return MonitoringEvaluation(
                project_id=project_id,
                snapshot_id=(latest_existing or {}).get("snapshot_id"),
                snapshot_hash=snapshot_hash,
                material_change=False,
                skipped_reason=skip_reason,
                data_quality=quality,
                previous_dphis=_num(project.get("previous_dphis") or project.get("dphis")),
                dphis=_num(project.get("current_dphis") or project.get("dphis")),
            )

        snapshot_model = ProjectSnapshot(
            snapshot_id=snapshot_id,
            project_id=project_id,
            observed_at=observed_at,
            report_period=report_period,
            source=trigger,
            snapshot_hash=snapshot_hash,
            quality_status=quality.quality_status,
            physical_progress=snapshot_doc.get("physical_progress"),
            financial_progress=snapshot_doc.get("financial_progress"),
            cumulative_expenditure=snapshot_doc.get("cumulative_expenditure"),
            milestones=snapshot_doc.get("milestones"),
        )
        await snapshots_repo.insert_one({**snapshot_doc, **snapshot_model.model_dump(exclude_none=True)})

        history = snapshots + [snapshot_doc]
        features = agent_adapter.engineer(project, history)
        prediction = agent_adapter.predict(project_id, snapshot_id, features)
        await predictions_repo.insert_one(prediction.model_dump())
        shap_drivers = agent_adapter.explain(features)

        previous_dphis = _num(project.get("current_dphis") or project.get("dphis"))
        dphis_obj = agent_adapter.score_dphis(project_id, features, prediction, previous_dphis)
        current_dphis = float(dphis_obj.dphis)
        threshold = float(project.get("dphis_threshold") or 70.0)

        raw_events = evaluate_project_events(
            project=project,
            snapshots=history,
            current_dphis=current_dphis,
            previous_dphis=previous_dphis,
            threshold=threshold,
        )
        if quality.stale:
            raw_events.append(
                {
                    "event_id": f"EVT-{uuid.uuid4().hex[:12].upper()}",
                    "project_id": project_id,
                    "event_type": EventType.DATA_STALE.value,
                    "severity": "MODERATE",
                    "timestamp": datetime.now(timezone.utc),
                    "details": {
                        "freshness": quality.freshness.value,
                        "last_observed_at": quality.last_observed_at.isoformat() if quality.last_observed_at else None,
                    },
                }
            )

        peer = await analyze_peers(project, current_dphis=current_dphis)
        peer_event = peer_event_payload(peer)
        if peer_event:
            raw_events.append(
                {
                    "event_id": f"EVT-{uuid.uuid4().hex[:12].upper()}",
                    "project_id": project_id,
                    "snapshot_id": snapshot_id,
                    **peer_event,
                    "timestamp": datetime.now(timezone.utc),
                    "details": peer_event.get("trigger_metrics") or {},
                }
            )

        persisted_events = await persist_and_deduplicate_events(raw_events)
        domain_events = [
            Event(
                event_id=ev["event_id"],
                project_id=project_id,
                snapshot_id=snapshot_id,
                event_type=EventType(ev["event_type"]) if ev["event_type"] in EventType._value2member_map_ else EventType.THRESHOLD_CROSSED,
                severity=str(ev.get("severity", "HIGH")),
                trigger_metrics=ev.get("details") or ev.get("trigger_metrics") or {},
            )
            for ev in persisted_events
        ]

        alert_ids: List[str] = []
        try:
            thresh = await evaluate_project_threshold_crossing(
                project_id=project_id,
                current_dphis=current_dphis,
                previous_dphis=previous_dphis,
                trigger_source=trigger,
            )
            if thresh.get("triggered") and thresh.get("alert_id"):
                alert_ids.append(thresh["alert_id"])
        except Exception as exc:
            logger.warning(f"Threshold evaluation failed for {project_id}: {exc}")

        investigation_id = None
        should_investigate = any(ev.event_type.value in INVESTIGATION_EVENT_TYPES for ev in domain_events)
        if queue_investigation and should_investigate:
            investigation_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
            await investigations_repo.insert_one(
                {
                    "investigation_id": investigation_id,
                    "project_id": project_id,
                    "trigger_event_id": domain_events[0].event_id if domain_events else None,
                    "trigger_reason": domain_events[0].event_type.value if domain_events else trigger,
                    "status": InvestigationStatus.QUEUED.value,
                    "created_at": datetime.now(timezone.utc),
                }
            )

        await projects_repo.update_one(
            {"project_id": project_id},
            {
                "previous_dphis": previous_dphis,
                "current_dphis": current_dphis,
                "dphis": current_dphis,
                "risk_level": (risk_tier_from_dphis(current_dphis).value.lower() if risk_tier_from_dphis(current_dphis) else project.get("risk_level")),
                "current_snapshot_id": snapshot_id,
                "last_observed_at": observed_at,
                "updated_at": datetime.now(timezone.utc),
            },
        )

        monitoring_metrics.projects_evaluated += 1
        monitoring_metrics.events_generated += len(domain_events)
        monitoring_metrics.alerts_generated += len(alert_ids)

        return MonitoringEvaluation(
            project_id=project_id,
            snapshot_id=snapshot_id,
            snapshot_hash=snapshot_hash,
            material_change=True,
            prediction=prediction,
            shap_drivers=shap_drivers,
            dphis=current_dphis,
            previous_dphis=previous_dphis,
            risk_tier=risk_tier_from_dphis(current_dphis).value if risk_tier_from_dphis(current_dphis) else None,
            events=domain_events,
            peer_analysis=peer,
            data_quality=quality,
            investigation_id=investigation_id,
            alert_ids=alert_ids,
        )


monitoring_service = MonitoringService()
