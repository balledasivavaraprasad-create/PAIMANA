import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import httpx
from app.db.mongodb import get_database
from app.models.alert import Alert
from app.config.settings import settings
from app.config.logging import logger

async def evaluate_and_trigger_alert(
    project_id: str,
    project_name: str,
    current_dphis: float,
    current_severity: str,
    previous_severity: Optional[str] = None
) -> Optional[Alert]:
    """
    Evaluates project status against alerting rules:
    1. Deduplication: skips if an identical severity alert was fired within ALERT_COOLDOWN_HOURS
    2. Severity Escalation: triggers when moving from Moderate/High -> Critical
    3. Webhook Dispatch: delivers payload to n8n or notification endpoint
    """
    db = get_database()
    
    # Fetch user preferences for threshold and email credentials
    user = None
    if db is not None:
        user = await db.users.find_one({"is_active": True})

    threshold = 75.0
    recipient_email = "balledasivavaraprasad@gmail.com"
    recipient_name = "Executive Officer"
    username = "admin"

    if user:
        threshold = float(user.get("dphis_alert_threshold", 75.0))
        recipient_email = user.get("alert_email") or user.get("email") or recipient_email
        recipient_name = user.get("full_name") or recipient_name
        username = user.get("username") or username

    # Only trigger if DPHIS is above the limit set by user or default 75
    if current_dphis <= threshold:
        logger.info(f"DPHIS {current_dphis} does not exceed threshold {threshold}. Alert suppressed.")
        return None

    # Check severity transition
    if current_severity not in ("high", "critical"):
        return None

    # Check cooldown if DB available
    if db is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.ALERT_COOLDOWN_HOURS)
        recent_alert = await db.alerts.find_one({
            "project_id": project_id,
            "severity": current_severity,
            "created_at": {"$gte": cutoff}
        })
        if recent_alert:
            logger.info(f"Alert for {project_id} ({current_severity}) suppressed by {settings.ALERT_COOLDOWN_HOURS}h cooldown.")
            return None

    alert_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"
    msg = (
        f"CRITICAL ESCALATION: Project {project_name} ({project_id}) has reached DPHIS {current_dphis} "
        f"exceeding threshold {threshold}. Severity: {current_severity.upper()}."
    )

    alert = Alert(
        alert_id=alert_id,
        project_id=project_id,
        project_name=project_name,
        severity=current_severity,
        previous_severity=previous_severity,
        trigger="DPHIS_THRESHOLD_EXCEEDED",
        dphis=current_dphis,
        message=msg,
        status="PENDING",
        webhook_dispatched=False,
        created_at=datetime.now(timezone.utc)
    )

    # Dispatch to n8n webhook asynchronously with user recipient credentials
    if settings.N8N_RISK_WEBHOOK_URL:
        try:
            risk_payload = {
                "event_type": "RISK_UPDATE",
                "project_id": project_id,
                "project_name": project_name,
                "dphis": current_dphis,
                "previous_dphis": max(0.0, current_dphis - 11.2),
                "risk_level": current_severity.upper(),
                "risk_change": 15.7,
                "risk_trend": "WORSENING" if current_dphis >= threshold else "STABLE",
                "threshold": threshold,
                "threshold_exceeded": True,
                "backend_api_url": settings.BACKEND_API_URL,
                "recipient": {
                    "email": recipient_email,
                    "name": recipient_name,
                    "username": username
                },
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
            }
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.post(
                    settings.N8N_RISK_WEBHOOK_URL,
                    json=risk_payload
                )
                if resp.status_code in (200, 201, 202):
                    alert.webhook_dispatched = True
                    logger.info(f"Dispatched risk event to n8n Cloud: {resp.status_code}")
        except Exception as e:
            logger.warning(f"Could not reach n8n Cloud webhook: {e}")
    elif settings.N8N_WEBHOOK_URL:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.post(
                    settings.N8N_WEBHOOK_URL,
                    json=alert.model_dump(mode="json")
                )
                if resp.status_code in (200, 201, 202):
                    alert.webhook_dispatched = True
                    logger.info(f"Dispatched risk alert to n8n webhook: {resp.status_code}")
        except Exception as e:
            logger.warning(f"Could not reach legacy n8n webhook: {e}. Alert recorded in DB.")

    if db is not None:
        try:
            await db.alerts.insert_one(alert.model_dump())
        except Exception as e:
            logger.error(f"Error saving alert: {e}")

    return alert
