import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

HASH_FIELDS = (
    "physical_progress",
    "financial_progress",
    "cumulative_expenditure",
    "milestones",
    "cost",
    "schedule",
    "report_period",
)

MATERIAL_PROGRESS_PTS = 1.0
MATERIAL_EXPENDITURE_RATIO = 0.02


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))


def compute_snapshot_hash(project: Dict[str, Any], snapshot: Dict[str, Any]) -> str:
    body = {}
    for field in HASH_FIELDS:
        if field in snapshot:
            body[field] = snapshot.get(field)
        elif field in project:
            body[field] = project.get(field)
    body["project_id"] = project.get("project_id") or snapshot.get("project_id")
    digest = hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()
    return digest


def _num(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def is_material_change(
    previous: Optional[Dict[str, Any]],
    current: Dict[str, Any],
    *,
    force: bool = False,
) -> Tuple[bool, Optional[str]]:
    if force:
        return True, "manual_reassessment"
    if previous is None:
        return True, "first_snapshot"
    prev_hash = previous.get("snapshot_hash")
    curr_hash = current.get("snapshot_hash")
    if prev_hash and curr_hash and prev_hash == curr_hash:
        prev_period = previous.get("report_period")
        curr_period = current.get("report_period")
        if prev_period and curr_period and prev_period != curr_period:
            return True, "new_report_period"
        return False, "no_material_change"
    prev_phys = _num(previous.get("physical_progress"))
    curr_phys = _num(current.get("physical_progress"))
    if prev_phys is not None and curr_phys is not None and abs(curr_phys - prev_phys) >= MATERIAL_PROGRESS_PTS:
        return True, "physical_progress_delta"
    prev_exp = _num(previous.get("cumulative_expenditure"))
    curr_exp = _num(current.get("cumulative_expenditure"))
    if prev_exp and curr_exp and abs(curr_exp - prev_exp) / max(prev_exp, 1.0) >= MATERIAL_EXPENDITURE_RATIO:
        return True, "expenditure_delta"
    if prev_hash != curr_hash:
        return True, "snapshot_hash_changed"
    return False, "no_material_change"


def parse_observed_at(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str) and value:
        text = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            parsed = datetime.strptime(value[:10], "%Y-%m-%d")
            return parsed.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc)
