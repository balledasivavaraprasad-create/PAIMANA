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

@router.post("", response_model=dict, status_code=201)
async def create_alert(payload: dict):
    db = get_database()
    alert_id = payload.get("alert_id") or f"ALT-{int(datetime.utcnow().timestamp())}"
    alert_doc = {
        "alert_id": alert_id,
        "project_id": payload.get("project_id", "P1024"),
        "project_name": payload.get("project_name", f"Corridor {payload.get('project_id', 'P1024')}"),
        "severity": str(payload.get("severity", "critical")).lower(),
        "trigger": payload.get("trigger", "DPHIS_THRESHOLD_EXCEEDED"),
        "dphis": float(payload.get("dphis", 82.4)),
        "message": payload.get("message", "High risk threshold exceeded"),
        "investigation_id": payload.get("investigation_id"),
        "recommendations": payload.get("recommendations", []),
        "status": payload.get("status", "PENDING").upper(),
        "notification_sent": payload.get("notification_sent", True),
        "created_at": datetime.utcnow()
    }
    if db is not None:
        await db.alerts.insert_one(alert_doc)

    alert_doc.pop("_id", None)
    return {"message": "Alert created successfully", "alert": alert_doc}

@router.post("/trigger-n8n-event")
async def trigger_n8n_event(
    project_id: str = Query(default="P1024"),
    dphis: float = Query(default=82.4),
    threshold: float = Query(default=75.0, description="Alert threshold limit set by user (default 75.0)"),
    recipient_email: Optional[str] = Query(default=None, description="User email to send alert notification to"),
    recipient_name: Optional[str] = Query(default=None),
    test_mode: bool = Query(default=False)
):
    """
    Dispatches a structured risk event to the n8n Cloud webhook.
    Checks if dphis > threshold (default 75.0).
    Includes the user's recipient credentials so n8n can email them directly.
    """
    import httpx
    from app.config.settings import settings

    db = get_database()
    email_to = recipient_email
    name_to = recipient_name or "Executive Officer"

    if not email_to and db is not None:
        user = await db.users.find_one({"is_active": True})
        if user:
            email_to = user.get("alert_email") or user.get("email")
            name_to = user.get("full_name") or name_to
            if threshold == 75.0 and "dphis_alert_threshold" in user:
                threshold = float(user["dphis_alert_threshold"])

    if not email_to:
        email_to = "balledasivavaraprasad@gmail.com"

    threshold_exceeded = dphis > threshold
    if not threshold_exceeded:
        return {
            "success": False,
            "threshold_exceeded": False,
            "message": f"DPHIS score {dphis} is below the threshold of {threshold}. No alert or email triggered.",
            "dphis": dphis,
            "threshold": threshold
        }

    target_url = settings.N8N_TEST_WEBHOOK_URL if test_mode else settings.N8N_RISK_WEBHOOK_URL
    payload = {
        "event_type": "RISK_UPDATE",
        "project_id": project_id,
        "dphis": dphis,
        "previous_dphis": round(max(0.0, dphis - 11.2), 1),
        "risk_level": "CRITICAL" if dphis >= 75 else "HIGH" if dphis >= 50 else "MODERATE",
        "risk_change": 15.7,
        "risk_trend": "WORSENING" if dphis >= threshold else "STABLE",
        "threshold": threshold,
        "threshold_exceeded": True,
        "recipient": {
            "email": email_to,
            "name": name_to,
            "username": "admin"
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(target_url, json=payload)
            return {
                "success": resp.status_code in (200, 201, 202),
                "threshold_exceeded": True,
                "status_code": resp.status_code,
                "target_url": target_url,
                "recipient_email": email_to,
                "dispatched_payload": payload,
                "n8n_response": resp.text[:500]
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "target_url": target_url,
            "dispatched_payload": payload
        }

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
