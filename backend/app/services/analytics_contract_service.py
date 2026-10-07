"""Honest analytics aggregations. Never fabricate zeros for unknown metrics."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from collections import defaultdict

from app.domain.availability import metric_payload
from app.repositories import (
    data_quality_repo,
    events_repo,
    interventions_repo,
    investigations_repo,
    outcomes_repo,
    peer_analyses_repo,
    projects_repo,
    snapshots_repo,
)
from app.services.data_quality_service import classify_freshness

HIGH_DPHIS = 65.0
CRITICAL_DPHIS = 80.0


def _num(value: Any) -> Optional[float]:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def _dphis(project: Dict[str, Any]) -> Optional[float]:
    return _num(project.get("current_dphis") if project.get("current_dphis") is not None else project.get("dphis"))


def _matches_filters(project: Dict[str, Any], filters: Dict[str, Any]) -> bool:
    for key in ("ministry", "sector", "state", "agency"):
        wanted = filters.get(key)
        if not wanted or str(wanted).lower() in ("all",):
            continue
        hay = project.get(key) or (project.get("metadata") or {}).get("implementing_agency") or project.get("department")
        if not hay or wanted.lower() not in str(hay).lower():
            return False
    risk = filters.get("risk_tier")
    if risk and str(risk).lower() not in ("all",):
        dphis = _dphis(project)
        if dphis is None:
            return False
        tier = "critical" if dphis >= CRITICAL_DPHIS else "high" if dphis >= HIGH_DPHIS else "moderate" if dphis >= 50 else "low"
        if tier != str(risk).lower():
            return False
    return True


async def load_projects(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    projects = await projects_repo.find_many({}, limit=2000)
    filters = filters or {}
    return [p for p in projects if _matches_filters(p, filters)]


async def overview(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    projects = await load_projects(filters)
    scores = [s for s in (_dphis(p) for p in projects) if s is not None]
    high = sum(1 for s in scores if HIGH_DPHIS <= s < CRITICAL_DPHIS)
    critical = sum(1 for s in scores if s >= CRITICAL_DPHIS)
    accelerating = 0
    stale = 0
    for p in projects:
        prev = _num(p.get("previous_dphis"))
        curr = _dphis(p)
        if prev is not None and curr is not None and (curr - prev) >= 8:
            accelerating += 1
        freshness = classify_freshness(p.get("last_observed_at") or p.get("updated_at"))
        if freshness.value in ("Stale", "Unavailable"):
            stale += 1
    avg = round(sum(scores) / len(scores), 1) if scores else None
    budgets = []
    for p in projects:
        cost = p.get("cost") if isinstance(p.get("cost"), dict) else {}
        val = _num(cost.get("revised") or cost.get("original"))
        if val is not None:
            budgets.append(val)
    return {
        "period": {
            "from": (filters or {}).get("from"),
            "to": (filters or {}).get("to"),
        },
        "project_count": len(projects),
        "high_risk_count": high,
        "critical_count": critical,
        "average_dphis": avg,
        "risk_accelerating_count": accelerating,
        "stale_count": stale,
        "budget_exposure": round(sum(budgets), 2) if budgets else None,
        "availability": True,
        "reason": None if projects else "no_projects_in_filter",
    }


async def risk_trends(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    snaps = await snapshots_repo.find_many({}, sort=[("report_period", 1)], limit=5000)
    allowed = {p["project_id"] for p in await load_projects(filters)}
    buckets: Dict[str, List[float]] = defaultdict(list)
    for snap in snaps:
        if snap.get("project_id") not in allowed:
            continue
        period = snap.get("report_period") or str(snap.get("snapshot_date", ""))[:7]
        score = _num(snap.get("dphis") or snap.get("current_dphis"))
        if period and score is not None:
            buckets[period].append(score)
    if not buckets:
        return []
    rows = []
    for period in sorted(buckets):
        values = sorted(buckets[period])
        mid = values[len(values) // 2]
        rows.append(
            {
                "period": period,
                "average_dphis": round(sum(values) / len(values), 1),
                "median_dphis": round(mid, 1),
                "high_count": sum(1 for v in values if HIGH_DPHIS <= v < CRITICAL_DPHIS),
                "critical_count": sum(1 for v in values if v >= CRITICAL_DPHIS),
                "project_count": len(values),
            }
        )
    return rows


async def risk_matrix(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    projects = await load_projects(filters)
    points = []
    missing = 0
    for p in projects:
        cost_risk = _num(p.get("C_cost_risk") or p.get("predicted_cost_overrun_pct"))
        schedule_risk = _num(p.get("T_time_risk") or p.get("schedule_slippage_months"))
        dphis = _dphis(p)
        budget = _num((p.get("cost") or {}).get("revised") if isinstance(p.get("cost"), dict) else None)
        if cost_risk is None or schedule_risk is None or dphis is None:
            missing += 1
            continue
        points.append(
            {
                "project_id": p.get("project_id"),
                "project_name": p.get("project_name"),
                "cost_risk": cost_risk,
                "schedule_risk": schedule_risk,
                "dphis": dphis,
                "budget": budget,
                "sector": p.get("sector"),
                "state": p.get("state"),
                "event": p.get("latest_event_type"),
            }
        )
    return {
        "points": points,
        "availability": bool(points),
        "reason": None if points else "insufficient_risk_dimensions",
        "excluded_incomplete": missing,
    }


async def event_heatmap(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    events = await events_repo.find_many({}, limit=5000)
    allowed = {p["project_id"] for p in await load_projects(filters)}
    counts: Dict[tuple, int] = defaultdict(int)
    for ev in events:
        if ev.get("project_id") not in allowed:
            continue
        created = ev.get("created_at") or ev.get("timestamp")
        period = None
        if isinstance(created, datetime):
            period = created.strftime("%Y-%m")
        elif isinstance(created, str) and len(created) >= 7:
            period = created[:7]
        counts[(ev.get("event_type") or "UNKNOWN", period or "unknown")] += 1
    return [{"event_type": k[0], "period": k[1], "count": v} for k, v in sorted(counts.items())]


async def geography(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    projects = await load_projects(filters)
    by_state: Dict[str, List[float]] = defaultdict(list)
    for p in projects:
        state = p.get("state") or "Unknown"
        score = _dphis(p)
        if score is not None:
            by_state[state].append(score)
    rows = []
    for state, scores in sorted(by_state.items()):
        rows.append(
            {
                "state": state,
                "average_dphis": round(sum(scores) / len(scores), 1) if scores else None,
                "high_critical_count": sum(1 for s in scores if s >= HIGH_DPHIS),
                "project_count": len(scores),
            }
        )
    return {"regions": rows, "availability": bool(rows), "reason": None if rows else "no_geographic_data"}


async def group_metric(key: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    projects = await load_projects(filters)
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for p in projects:
        label = p.get(key) or "Unknown"
        groups[str(label)].append(p)
    rows = []
    for label, items in sorted(groups.items()):
        scores = [s for s in (_dphis(p) for p in items) if s is not None]
        rows.append(
            {
                key: label,
                "project_count": len(items),
                "average_dphis": round(sum(scores) / len(scores), 1) if scores else None,
                "high_critical_count": sum(1 for s in scores if s >= HIGH_DPHIS),
            }
        )
    return {"rows": rows, "availability": bool(rows), "reason": None if rows else "no_group_data"}


async def investigation_funnel(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    allowed = {p["project_id"] for p in await load_projects(filters)}
    events = await events_repo.count({"project_id": {"$in": list(allowed)}} ) if allowed else 0
    investigations = await investigations_repo.find_many({}, limit=2000)
    investigations = [i for i in investigations if i.get("project_id") in allowed]
    recs_pending = sum(1 for i in investigations if str(i.get("status", "")).upper() in ("PENDING_APPROVAL", "READY_FOR_DECISION"))
    approved = sum(1 for i in investigations if str(i.get("status", "")).upper() == "APPROVED")
    interventions = await interventions_repo.find_many({}, limit=2000)
    interventions = [i for i in interventions if i.get("project_id") in allowed]
    outcomes = await outcomes_repo.find_many({}, limit=2000)
    return {
        "events": events,
        "investigations": len(investigations),
        "recommendations_pending_review": recs_pending,
        "approved": approved,
        "executed": len(interventions),
        "outcomes_recorded": len(outcomes),
    }


async def intervention_outcomes(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    rows = await outcomes_repo.find_many({}, limit=500)
    if not rows:
        return {
            "items": [],
            "availability": False,
            "reason": "no_intervention_outcomes",
        }
    return {"items": rows, "availability": True, "reason": None}


async def data_quality_summary(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    projects = await load_projects(filters)
    quality_docs = await data_quality_repo.find_many({}, limit=2000)
    by_id = {d.get("project_id"): d for d in quality_docs}
    fresh = delayed = stale = missing = 0
    for p in projects:
        q = by_id.get(p.get("project_id"))
        status = (q or {}).get("freshness") or classify_freshness(p.get("last_observed_at")).value
        if status in ("Fresh",):
            fresh += 1
        elif status in ("Delayed",):
            delayed += 1
        elif status in ("Stale",):
            stale += 1
        else:
            missing += 1
    return {
        "fresh": fresh,
        "delayed": delayed,
        "stale": stale,
        "missing_baseline": missing,
        "project_count": len(projects),
    }


async def model_health() -> Dict[str, Any]:
    from app.services.paimana_ml_service import paimana_ml
    available = True
    reason = None
    try:
        _ = getattr(paimana_ml, "models", None)
    except Exception as exc:
        available = False
        reason = str(exc)
    return {
        "availability": available,
        "reason": reason,
        "models": [
            {"name": "cost_risk", "status": "integrated"},
            {"name": "schedule_risk", "status": "integrated"},
            {"name": "combined_risk", "status": "integrated"},
        ],
    }


async def peer_analytics(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    rows = await peer_analyses_repo.find_many({}, sort=[("created_at", -1)], limit=500)
    if not rows:
        return {"items": [], "availability": False, "reason": "insufficient_peer_data"}
    compact = []
    for row in rows:
        benches = row.get("benchmarks") or {}
        devs = row.get("deviations") or {}
        compact.append(
            {
                "project_id": row.get("project_id"),
                "cohort_size": row.get("cohort_size"),
                "cohort_quality": row.get("cohort_quality"),
                "peer_median_dphis": benches.get("peer_median_dphis"),
                "peer_p75_dphis": benches.get("peer_p75_dphis"),
                "peer_p90_dphis": benches.get("peer_p90_dphis"),
                "target_dphis": benches.get("target_dphis"),
                "peer_deviation": devs.get("peer_deviation"),
                "peer_trend": row.get("trajectory_summary"),
                "classification": row.get("classification"),
                "availability": row.get("availability", True),
                "reason": row.get("reason"),
            }
        )
    return {"items": compact, "availability": True, "reason": None}


async def change_feed(limit: int = 50) -> List[Dict[str, Any]]:
    events = await events_repo.find_many({}, sort=[("timestamp", -1), ("created_at", -1)], limit=limit)
    project_ids = list({e.get("project_id") for e in events if e.get("project_id")})
    projects = {}
    if project_ids:
        found = await projects_repo.find_many({"project_id": {"$in": project_ids}}, limit=500)
        projects = {p["project_id"]: p for p in found}
    feed = []
    for ev in events:
        proj = projects.get(ev.get("project_id"), {})
        feed.append(
            {
                "project_id": ev.get("project_id"),
                "project_name": proj.get("project_name"),
                "previous_dphis": _num(proj.get("previous_dphis")),
                "current_dphis": _dphis(proj),
                "event_type": ev.get("event_type"),
                "severity": ev.get("severity"),
                "created_at": ev.get("created_at") or ev.get("timestamp"),
            }
        )
    return feed
