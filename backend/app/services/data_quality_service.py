from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from app.domain.entities import DataQuality
from app.domain.enums import DataFreshness
from app.repositories import data_quality_repo

REQUIRED_FIELDS = [
    "project_id",
    "project_name",
    "sector",
    "state",
    "cost",
    "schedule",
]

STALE_AFTER_DAYS = 14
DELAYED_AFTER_DAYS = 7


def _as_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, str):
        text = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            try:
                parsed = datetime.strptime(value[:10], "%Y-%m-%d")
                return parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                return None
    return None


def classify_freshness(last_observed_at: Optional[datetime], now: Optional[datetime] = None) -> DataFreshness:
    if last_observed_at is None:
        return DataFreshness.UNAVAILABLE
    now = now or datetime.now(timezone.utc)
    age = now - last_observed_at
    if age <= timedelta(days=DELAYED_AFTER_DAYS):
        return DataFreshness.FRESH
    if age <= timedelta(days=STALE_AFTER_DAYS):
        return DataFreshness.DELAYED
    return DataFreshness.STALE


def missing_project_fields(project: Dict[str, Any]) -> List[str]:
    missing = []
    for field in REQUIRED_FIELDS:
        if project.get(field) in (None, "", {}, []):
            missing.append(field)
    cost = project.get("cost") if isinstance(project.get("cost"), dict) else {}
    if not cost.get("original") and not cost.get("revised"):
        if "cost" not in missing:
            missing.append("cost.original_or_revised")
    return missing


def assess_project_quality(
    project: Dict[str, Any],
    snapshot: Optional[Dict[str, Any]] = None,
    now: Optional[datetime] = None,
) -> DataQuality:
    observed = None
    if snapshot:
        observed = _as_dt(snapshot.get("observed_at") or snapshot.get("snapshot_date") or snapshot.get("created_at"))
    if observed is None:
        observed = _as_dt(project.get("last_observed_at") or project.get("updated_at"))
    freshness = classify_freshness(observed, now)
    missing = missing_project_fields(project)
    quality_status = "ok"
    if freshness == DataFreshness.STALE:
        quality_status = "stale"
    elif missing:
        quality_status = "incomplete"
    elif freshness == DataFreshness.DELAYED:
        quality_status = "delayed"
    return DataQuality(
        data_quality_id=f"DQ-{project.get('project_id', 'UNKNOWN')}",
        project_id=str(project.get("project_id", "UNKNOWN")),
        snapshot_id=(snapshot or {}).get("snapshot_id"),
        freshness=freshness,
        missing_fields=missing,
        stale=freshness == DataFreshness.STALE,
        quality_status=quality_status,
        last_observed_at=observed,
        notes=None if not missing else "Required fields are incomplete",
    )


async def persist_data_quality(quality: DataQuality) -> dict:
    existing = await data_quality_repo.find_one({"project_id": quality.project_id})
    payload = quality.model_dump()
    if existing:
        updated = await data_quality_repo.update_one({"project_id": quality.project_id}, payload)
        return updated or payload
    return await data_quality_repo.insert_one(payload)
