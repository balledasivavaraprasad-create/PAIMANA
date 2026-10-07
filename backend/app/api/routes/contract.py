from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user
from app.domain.errors import DomainError, ErrorCode
from app.observability.metrics import monitoring_metrics
from app.repositories import (
    alerts_repo,
    investigations_repo,
    monitoring_cycles_repo,
    projects_repo,
    snapshots_repo,
)
from app.services.agent_adapter import agent_adapter, risk_tier_from_dphis
from app.services.analytics_contract_service import (
    change_feed,
    data_quality_summary,
    event_heatmap,
    geography,
    group_metric,
    intervention_outcomes,
    investigation_funnel,
    model_health,
    overview,
    peer_analytics,
    risk_matrix,
    risk_trends,
)
from app.services.audit_service import record_audit
from app.services.data_quality_service import assess_project_quality
from app.services.investigation_orchestration import (
    decide_investigation,
    execute_queued_investigation,
    get_investigation_bundle,
    queue_investigation,
    record_investigation_outcome,
)
from app.services.monitoring_pipeline import monitoring_service
from app.services.peer_intelligence_service import analyze_peers
from app.services.rbac import has_permission, require_permission

router = APIRouter(tags=["InfraBuild Contract API"])


class ProjectIngestRequest(BaseModel):
    payload: Dict[str, Any] = Field(default_factory=dict)
    force: bool = False


class InvestigationCreateRequest(BaseModel):
    project_id: str
    trigger_reason: str = "MANUAL_OFFICER_REQUEST"


class DecisionRequest(BaseModel):
    reason: Optional[str] = None


class OutcomeRequest(BaseModel):
    notes: Optional[str] = None
    after_metrics: Optional[Dict[str, Any]] = None


def _filters(
    period_from: Optional[str],
    period_to: Optional[str],
    ministry: Optional[str],
    sector: Optional[str],
    state: Optional[str],
    agency: Optional[str],
    risk_tier: Optional[str],
) -> dict:
    return {
        "from": period_from,
        "to": period_to,
        "ministry": ministry,
        "sector": sector,
        "state": state,
        "agency": agency,
        "risk_tier": risk_tier,
    }


@router.get("/system/monitoring-status")
async def monitoring_status(current_user: dict = Depends(require_permission("projects:read"))):
    last_cycle = await monitoring_cycles_repo.find_many({}, sort=[("started_at", -1)], limit=1)
    cycle = last_cycle[0] if last_cycle else None
    now = datetime.now(timezone.utc)
    stale_projects = 0
    projects = await projects_repo.find_many({}, limit=2000)
    for p in projects:
        observed = p.get("last_observed_at") or p.get("updated_at")
        if observed is None:
            stale_projects += 1
            continue
        if isinstance(observed, str):
            continue
        if isinstance(observed, datetime) and now - observed.replace(tzinfo=observed.tzinfo or timezone.utc) > timedelta(days=14):
            stale_projects += 1
    last_scan = cycle.get("completed_at") if cycle else monitoring_metrics.last_scan_at
    next_scan = (last_scan + timedelta(hours=24)) if isinstance(last_scan, datetime) else None
    return {
        "status": "active",
        "last_sync_at": last_scan.isoformat() if isinstance(last_scan, datetime) else last_scan,
        "last_scan_at": last_scan.isoformat() if isinstance(last_scan, datetime) else last_scan,
        "next_scan_at": next_scan.isoformat() if next_scan else None,
        "projects_monitored": len(projects),
        "stale_projects": stale_projects,
        "metrics": monitoring_metrics.snapshot(),
    }


@router.post("/system/monitoring-scan")
async def run_monitoring_scan(
    background: BackgroundTasks,
    current_user: dict = Depends(require_permission("system:admin")),
    limit: int = Query(default=500, le=2000),
):
    background.add_task(monitoring_service.run_scheduled_scan, limit=limit, trigger="manual_scan")
    return {"status": "queued", "limit": limit}


@router.post("/projects/{project_id}/reassess")
async def reassess_project(
    project_id: str,
    body: ProjectIngestRequest,
    current_user: dict = Depends(require_permission("projects:reassess")),
    request: Request = None,
):
    result = await monitoring_service.ingest_project_update(
        project_id,
        body.payload,
        trigger="manual_reassessment",
        force=body.force or True,
    )
    await record_audit(
        actor=current_user.get("username", "unknown"),
        action="project.reassess",
        target_type="project",
        target_id=project_id,
        request_id=getattr(getattr(request, "state", None), "request_id", None),
    )
    return result.model_dump()


@router.get("/projects/{project_id}/risk/history")
async def project_risk_history(
    project_id: str,
    current_user: dict = Depends(require_permission("projects:read")),
):
    snaps = await snapshots_repo.find_many(
        {"project_id": project_id},
        sort=[("observed_at", 1), ("snapshot_date", 1)],
        limit=120,
    )
    history = []
    for snap in snaps:
        dphis = snap.get("dphis")
        history.append(
            {
                "snapshot_id": snap.get("snapshot_id"),
                "observed_at": snap.get("observed_at") or snap.get("snapshot_date"),
                "report_period": snap.get("report_period"),
                "dphis": dphis,
                "availability": dphis is not None,
                "reason": None if dphis is not None else "dphis_not_persisted_on_snapshot",
            }
        )
    return {"project_id": project_id, "history": history}


@router.get("/projects/{project_id}/explanations")
async def project_explanations(
    project_id: str,
    current_user: dict = Depends(require_permission("projects:read")),
):
    project = await projects_repo.find_one({"project_id": project_id})
    if not project:
        raise DomainError(ErrorCode.PROJECT_NOT_FOUND, "Project not found", 404)
    snaps = await snapshots_repo.find_many({"project_id": project_id}, sort=[("snapshot_date", 1)], limit=60)
    features = agent_adapter.engineer(project, snaps)
    drivers = agent_adapter.explain(features)
    return {
        "project_id": project_id,
        "shap_drivers": drivers,
        "interpretation": "SHAP drivers indicate model contribution, not verified causation.",
        "availability": bool(drivers),
        "reason": None if drivers else "explanation_unavailable",
    }


@router.get("/projects/{project_id}/risk-summary")
async def project_risk_summary(
    project_id: str,
    current_user: dict = Depends(require_permission("projects:read")),
):
    project = await projects_repo.find_one({"project_id": project_id})
    if not project:
        raise DomainError(ErrorCode.PROJECT_NOT_FOUND, "Project not found", 404)
    snaps = await snapshots_repo.find_many({"project_id": project_id}, sort=[("snapshot_date", 1)], limit=60)
    features = agent_adapter.engineer(project, snaps)
    prediction = agent_adapter.predict(project_id, project.get("current_snapshot_id"), features)
    current = project.get("current_dphis")
    if current is None:
        current = project.get("dphis")
    previous = project.get("previous_dphis")
    dphis = float(current) if current is not None else None
    prev = float(previous) if previous is not None else None
    delta = round(dphis - prev, 1) if dphis is not None and prev is not None else None
    quality = assess_project_quality(project, snaps[-1] if snaps else None)
    from app.repositories import events_repo

    events = await events_repo.find_many({"project_id": project_id}, sort=[("timestamp", -1)], limit=20)
    trend = None
    if delta is None:
        trend = None
    elif delta >= 1.5:
        trend = "increasing"
    elif delta <= -1.5:
        trend = "decreasing"
    else:
        trend = "stable"
    return {
        "project_id": project_id,
        "current": {
            "dphis": dphis,
            "risk_tier": risk_tier_from_dphis(dphis).value if dphis is not None else None,
            "predicted_cost_overrun_pct": prediction.cost_overrun_prediction,
            "predicted_schedule_slippage_months": prediction.schedule_slippage_prediction,
            "availability": dphis is not None,
            "reason": None if dphis is not None else "prediction_unavailable",
        },
        "previous": {"dphis": prev, "availability": prev is not None, "reason": None if prev is not None else "no_prior_snapshot"},
        "change": {
            "dphis_delta": delta,
            "trend": trend,
            "availability": delta is not None,
            "reason": None if delta is not None else "insufficient_history",
        },
        "events": events,
        "data_quality": quality.model_dump(),
        "prediction": prediction.model_dump(),
    }


@router.get("/projects/{project_id}/peers")
@router.get("/projects/{project_id}/peer-analysis")
async def project_peers(
    project_id: str,
    current_user: dict = Depends(require_permission("projects:read")),
):
    project = await projects_repo.find_one({"project_id": project_id})
    if not project:
        raise DomainError(ErrorCode.PROJECT_NOT_FOUND, "Project not found", 404)
    analysis = await analyze_peers(project)
    payload = analysis.model_dump()
    payload["note"] = "Peer deviation is contextual evidence, not proof of causation."
    return payload


@router.get("/investigations")
async def list_investigations(
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(require_permission("investigations:read")),
    limit: int = Query(default=50, le=200),
):
    query: Dict[str, Any] = {}
    if project_id:
        query["project_id"] = project_id
    if status:
        query["status"] = status
    return await investigations_repo.find_many(query, sort=[("created_at", -1)], limit=limit)


@router.get("/investigations/{investigation_id}")
async def get_investigation(
    investigation_id: str,
    current_user: dict = Depends(require_permission("investigations:read")),
):
    return await get_investigation_bundle(investigation_id)


@router.post("/investigations")
async def create_investigation(
    body: InvestigationCreateRequest,
    background: BackgroundTasks,
    current_user: dict = Depends(require_permission("investigations:create")),
):
    project = await projects_repo.find_one({"project_id": body.project_id})
    if not project:
        raise DomainError(ErrorCode.PROJECT_NOT_FOUND, "Project not found", 404)
    queued = await queue_investigation(
        body.project_id,
        body.trigger_reason,
        actor=current_user.get("username", "unknown"),
    )
    background.add_task(execute_queued_investigation, queued["investigation_id"])
    return {"status": "queued", "investigation": queued}


@router.post("/investigations/{investigation_id}/approve")
async def approve_investigation(
    investigation_id: str,
    body: DecisionRequest,
    current_user: dict = Depends(require_permission("investigations:approve")),
):
    return await decide_investigation(
        investigation_id,
        approved=True,
        actor=current_user.get("username", "unknown"),
        reason=body.reason,
    )


@router.post("/investigations/{investigation_id}/reject")
async def reject_investigation(
    investigation_id: str,
    body: DecisionRequest,
    current_user: dict = Depends(require_permission("investigations:approve")),
):
    return await decide_investigation(
        investigation_id,
        approved=False,
        actor=current_user.get("username", "unknown"),
        reason=body.reason,
    )


@router.post("/investigations/{investigation_id}/outcome")
async def investigation_outcome(
    investigation_id: str,
    body: OutcomeRequest,
    current_user: dict = Depends(require_permission("investigations:approve")),
):
    return await record_investigation_outcome(
        investigation_id,
        actor=current_user.get("username", "unknown"),
        notes=body.notes,
        after_metrics=body.after_metrics,
    )


@router.get("/analytics/overview-contract")
async def analytics_overview_contract(
    current_user: dict = Depends(require_permission("analytics:read")),
    period_from: Optional[str] = None,
    period_to: Optional[str] = None,
    ministry: Optional[str] = None,
    sector: Optional[str] = None,
    state: Optional[str] = None,
    agency: Optional[str] = None,
    risk_tier: Optional[str] = None,
):
    return await overview(_filters(period_from, period_to, ministry, sector, state, agency, risk_tier))


@router.get("/analytics/risk-trends")
async def analytics_risk_trends(current_user: dict = Depends(require_permission("analytics:read"))):
    return await risk_trends()


@router.get("/analytics/risk-matrix")
async def analytics_risk_matrix(current_user: dict = Depends(require_permission("analytics:read"))):
    return await risk_matrix()


@router.get("/analytics/changes")
async def analytics_changes(current_user: dict = Depends(require_permission("analytics:read"))):
    return {"items": await change_feed()}


@router.get("/analytics/events")
async def analytics_events(current_user: dict = Depends(require_permission("analytics:read"))):
    return await event_heatmap()


@router.get("/analytics/geography")
async def analytics_geography(current_user: dict = Depends(require_permission("analytics:read"))):
    return await geography()


@router.get("/analytics/sectors")
async def analytics_sectors(current_user: dict = Depends(require_permission("analytics:read"))):
    return await group_metric("sector")


@router.get("/analytics/agencies")
async def analytics_agencies(current_user: dict = Depends(require_permission("analytics:read"))):
    return await group_metric("department")


@router.get("/analytics/cost")
async def analytics_cost(current_user: dict = Depends(require_permission("analytics:read"))):
    projects = await projects_repo.find_many({}, limit=2000)
    overruns = []
    for p in projects:
        cost = p.get("cost") if isinstance(p.get("cost"), dict) else {}
        original = cost.get("original")
        revised = cost.get("revised")
        if original and revised:
            overruns.append(
                {
                    "project_id": p.get("project_id"),
                    "original": original,
                    "revised": revised,
                    "overrun_pct": round(((revised - original) / original) * 100.0, 1) if original else None,
                }
            )
    return {"items": overruns, "availability": bool(overruns), "reason": None if overruns else "cost_fields_unavailable"}


@router.get("/analytics/schedule")
async def analytics_schedule(current_user: dict = Depends(require_permission("analytics:read"))):
    projects = await projects_repo.find_many({}, limit=2000)
    items = []
    for p in projects:
        slip = p.get("schedule_slippage_months")
        items.append(
            {
                "project_id": p.get("project_id"),
                "schedule_slippage_months": slip if slip is not None else None,
                "availability": slip is not None,
                "reason": None if slip is not None else "schedule_slippage_unavailable",
            }
        )
    return {"items": items}


@router.get("/analytics/investigations")
async def analytics_investigations(current_user: dict = Depends(require_permission("analytics:read"))):
    return await investigation_funnel()


@router.get("/analytics/interventions")
async def analytics_interventions(current_user: dict = Depends(require_permission("analytics:read"))):
    return await intervention_outcomes()


@router.get("/analytics/data-quality")
async def analytics_data_quality(current_user: dict = Depends(require_permission("analytics:read"))):
    return await data_quality_summary()


@router.get("/analytics/model-health")
async def analytics_model_health(current_user: dict = Depends(require_permission("analytics:read"))):
    return await model_health()


@router.get("/analytics/peers")
async def analytics_peers(current_user: dict = Depends(require_permission("analytics:read"))):
    return await peer_analytics()


@router.get("/me/permissions")
async def me_permissions(current_user: dict = Depends(get_current_user)):
    from app.services.rbac import PERMISSIONS, product_roles_for

    roles = [r.value for r in product_roles_for(current_user)]
    return {
        "username": current_user.get("username"),
        "legacy_role": current_user.get("role"),
        "product_roles": roles,
        "permissions": [p for p in PERMISSIONS if has_permission(current_user, p)],
    }
