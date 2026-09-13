from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from app.db.mongodb import get_database

router = APIRouter(prefix="/alerts", tags=["Alerts & Notifications"])

@router.get("", response_model=List[dict])
async def list_alerts(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=50, le=200)
):
    db = get_database()
    if db is None:
        return []

    filter_q = {}
    if severity:
        filter_q["severity"] = severity.lower()
    if status:
        filter_q["status"] = status.upper()

    cursor = db.alerts.find(filter_q, {"_id": 0}).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)

@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    res = await db.alerts.update_one(
        {"alert_id": alert_id},
        {"$set": {"status": "ACKNOWLEDGED", "acknowledged_at": datetime.utcnow()}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert acknowledged successfully", "alert_id": alert_id}

@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    res = await db.alerts.update_one(
        {"alert_id": alert_id},
        {"$set": {"status": "RESOLVED", "resolved_at": datetime.utcnow()}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert resolved successfully", "alert_id": alert_id}
