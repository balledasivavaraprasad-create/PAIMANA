import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import httpx
from app.db.mongodb import get_database
from app.models.alert import Alert
from app.config.settings import settings
from app.config.logging import logger

def get_centralized_severity(dphis: float) -> str:
    """
    Centralized risk classification:
    - 0  - 44: LOW (ON TRACK)
    - 45 - 64: MODERATE (NEEDS ATTENTION)
    - 65 - 79: HIGH (HIGH RISK)
    - 80 - 100: CRITICAL (CRITICAL)
    """
    if dphis >= 80.0:
        return "CRITICAL"
    if dphis >= 65.0:
        return "HIGH"
    if dphis >= 45.0:
        return "MODERATE"
    return "LOW"

def generate_risk_reasons(project: Dict[str, Any], current_dphis: float) -> List[str]:
    """Derives plain-language, non-technical risk reasons for normal users."""
    reasons = []
    
    # Check physical vs planned progress
    phys = project.get("physical_progress_percent") or project.get("physical_progress") or 0.0
    exp = project.get("expenditure_crores") or 0.0
    cost = project.get("revised_cost_crores") or (project.get("cost", {}).get("revised") if isinstance(project.get("cost"), dict) else 0.0) or 1.0
    fin = round((exp / max(1.0, cost)) * 100.0, 1) if cost > 0 else 0.0

    if phys < 50.0:
        reasons.append("Progress significantly behind planned schedule")
    if fin > (phys + 10.0):
        reasons.append("Spending ahead of physical progress")
    
    # Milestone delays
    if project.get("schedule_slippage_months") and float(project.get("schedule_slippage_months", 0)) > 3.0:
        reasons.append(f"Milestone delay of {int(project.get('schedule_slippage_months'))} months detected")
    else:
        reasons.append("Milestone delay detected in critical execution phase")

    if not reasons:
        reasons = [
            "Progress significantly behind planned schedule",
            "Spending ahead of physical progress",
            "Milestone delay detected"
        ]

    return reasons[:3]

async def evaluate_project_threshold_crossing(
    project_id: str,
    current_dphis: float,
    previous_dphis: Optional[float] = None,
    custom_threshold: Optional[float] = None,
    trigger_source: str = "automated_monitor"
) -> Dict[str, Any]:
    """
    Core Source-of-Truth for Project-Specific DPHIS Alert Thresholds.
    
    Rules:
    1. Each project has its OWN independent dphis_threshold (default 70.0).
    2. Crossing condition strictly requires:
       (previous_dphis < threshold) AND (current_dphis >= threshold)
       OR for newly evaluated projects: (previous_dphis is None) AND (current_dphis >= threshold)
    3. If current_dphis < threshold -> reset threshold_status to 'below'.
    4. If previous_dphis >= threshold AND current_dphis >= threshold -> NO duplicate alert.
    5. Alerts are persisted in MongoDB BEFORE invoking n8n webhook.
    6. Unique event_id ensures idempotency across retries.
    """
    db = get_database()
    if db is None:
        logger.error("Database connection unavailable for threshold evaluation")
        return {"success": False, "triggered": False, "error": "Database unavailable"}

    project = await db.projects.find_one({"project_id": project_id})
    if not project:
        logger.warning(f"Project {project_id} not found during threshold check")
        return {"success": False, "triggered": False, "error": f"Project {project_id} not found"}

    # Load project-specific threshold
    threshold = custom_threshold
    if threshold is None:
        threshold = float(project.get("dphis_threshold", 70.0))

    threshold_enabled = project.get("threshold_enabled", True)
    if not threshold_enabled:
        return {
            "success": True,
            "triggered": False,
            "message": f"Threshold alerting disabled for project {project_id}",
            "threshold": threshold,
            "current_dphis": current_dphis
        }

    # Resolve previous_dphis if not explicitly supplied
    if previous_dphis is None:
        if "previous_dphis" in project and project["previous_dphis"] is not None:
            previous_dphis = float(project["previous_dphis"])
        elif "current_dphis" in project and project["current_dphis"] is not None:
            previous_dphis = float(project["current_dphis"])
        elif "dphis" in project and project["dphis"] is not None:
            previous_dphis = float(project["dphis"])

    current_dphis = round(float(current_dphis), 1)
    if previous_dphis is not None:
        previous_dphis = round(float(previous_dphis), 1)

    severity = get_centralized_severity(current_dphis)

    # CASE A: Score is BELOW threshold
    if current_dphis < threshold:
        await db.projects.update_one(
            {"project_id": project_id},
            {"$set": {
                "dphis": current_dphis,
                "current_dphis": current_dphis,
                "previous_dphis": previous_dphis if previous_dphis is not None else current_dphis,
                "threshold_status": "below",
                "risk_level": severity.lower(),
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        return {
            "success": True,
            "triggered": False,
            "threshold_status": "below",
            "previous_dphis": previous_dphis,
            "current_dphis": current_dphis,
            "threshold": threshold,
            "severity": severity,
            "message": f"DPHIS {current_dphis} is below threshold {threshold}. Alert reset/suppressed."
        }

    # CASE B: Score is GREATER THAN OR EQUAL TO threshold
    # Check if this is a genuine crossing
    is_initial_crossing = (previous_dphis is None)
    is_upward_crossing = (previous_dphis is not None and previous_dphis < threshold)
    has_crossed = is_initial_crossing or is_upward_crossing

    if not has_crossed:
        # Already triggered, continuous high score (e.g. 71 -> 73)
        await db.projects.update_one(
            {"project_id": project_id},
            {"$set": {
                "dphis": current_dphis,
                "current_dphis": current_dphis,
                "previous_dphis": previous_dphis,
                "threshold_status": "triggered",
                "risk_level": severity.lower(),
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        return {
            "success": True,
            "triggered": False,
            "threshold_status": "triggered",
            "previous_dphis": previous_dphis,
            "current_dphis": current_dphis,
            "threshold": threshold,
            "severity": severity,
            "message": f"DPHIS {current_dphis} remains above threshold {threshold}. Duplicate alert suppressed."
        }

    # GENUINE THRESHOLD CROSSING DETECTED!
    event_id = f"EVT-{uuid.uuid4().hex[:12].upper()}"
    alert_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"
    now_utc = datetime.now(timezone.utc)

    # Resolve project user & admin details
    user_name = "Project Officer"
    user_email = "balledasivavaraprasad@gmail.com"
    user_id = "USER-DEFAULT"
    assigned_users = project.get("assigned_users", [])
    
    if assigned_users and isinstance(assigned_users, list):
        first_uname = assigned_users[0]
        u = await db.users.find_one({"username": first_uname})
        if u:
            user_name = u.get("full_name") or u.get("username") or user_name
            user_email = u.get("alert_email") or u.get("email") or user_email
            user_id = str(u.get("_id", user_id))
    elif project.get("threshold_configured_by"):
        u = await db.users.find_one({"username": project.get("threshold_configured_by")})
        if u:
            user_name = u.get("full_name") or u.get("username") or user_name
            user_email = u.get("alert_email") or u.get("email") or user_email
            user_id = str(u.get("_id", user_id))

    # Resolve admin email
    admin_email = "syntaxtrrors@gmail.com"
    admin_user = await db.users.find_one({"role": "ADMIN"})
    if admin_user:
        admin_email = admin_user.get("alert_email") or admin_user.get("email") or admin_email

    top_reasons = generate_risk_reasons(project, current_dphis)
    project_name = project.get("project_name", project_id)
    dept = project.get("department") or project.get("ministry") or "Infrastructure & Urban Affairs"
    loc = project.get("state") or (project.get("location", {}).get("state") if isinstance(project.get("location"), dict) else "India")

    msg = (
        f"DPHIS ALERT THRESHOLD REACHED: Project {project_name} ({project_id}) has reached DPHIS {current_dphis} "
        f"(Threshold: {threshold}). Severity: {severity}."
    )

    alert_doc = {
        "alert_id": alert_id,
        "event_id": event_id,
        "project_id": project_id,
        "project_name": project_name,
        "user_id": user_id,
        "previous_dphis": previous_dphis,
        "current_dphis": current_dphis,
        "threshold": threshold,
        "severity": severity.lower(),
        "trigger": "DPHIS_THRESHOLD_CROSSED",
        "trigger_type": "DPHIS_THRESHOLD_CROSSED",
        "top_risk_reasons": top_reasons,
        "dphis": current_dphis,
        "message": msg,
        "status": "PENDING",
        "notification_status": "pending",
        "user_notified": False,
        "admin_notified": False,
        "n8n_execution_reference": None,
        "webhook_dispatched": False,
        "created_at": now_utc
    }

    # STEP 1: PERSIST ALERT IN MONGODB BEFORE WEBHOOK DISPATCH (Guarantee no lost alerts)
    await db.alerts.insert_one(alert_doc)

    # STEP 2: UPDATE PROJECT STATE IN MONGODB
    await db.projects.update_one(
        {"project_id": project_id},
        {"$set": {
            "dphis": current_dphis,
            "current_dphis": current_dphis,
            "previous_dphis": previous_dphis,
            "threshold_status": "triggered",
            "threshold_last_crossed_at": now_utc,
            "last_threshold_alert_id": alert_id,
            "risk_level": severity.lower(),
            "updated_at": now_utc
        }}
    )

    # STEP 3: PREPARE AND SEND STRUCTURED PAYLOAD TO N8N WEBHOOK
    target_webhook = settings.N8N_THRESHOLD_WEBHOOK_URL or "https://hrishikesh1.app.n8n.cloud/webhook/project-risk-threshold"
    n8n_payload = {
        "event_type": "DPHIS_THRESHOLD_CROSSED",
        "event_id": event_id,
        "alert_id": alert_id,
        "timestamp": now_utc.isoformat(),
        "project": {
            "project_id": project_id,
            "project_name": project_name,
            "department": dept,
            "location": loc
        },
        "risk": {
            "previous_dphis": previous_dphis,
            "current_dphis": current_dphis,
            "threshold": threshold,
            "crossed_by": round(current_dphis - threshold, 1),
            "severity": severity
        },
        "user": {
            "user_id": user_id,
            "name": user_name,
            "email": user_email
        },
        "admin": {
            "email": admin_email
        },
        "top_risk_reasons": top_reasons,
        "project_url": f"https://paimana-seven.vercel.app?project={project_id}"
    }

    webhook_ok = False
    exec_ref = None

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(target_webhook, json=n8n_payload)
            if resp.status_code in (200, 201, 202):
                webhook_ok = True
                exec_ref = resp.headers.get("x-execution-id") or resp.text[:120] or "SUCCESS"
                logger.info(f"Dispatched threshold event {event_id} to n8n ({resp.status_code})")
            else:
                exec_ref = f"HTTP {resp.status_code}: {resp.text[:100]}"
                logger.warning(f"n8n webhook responded with non-200: {resp.status_code}")
    except Exception as e:
        exec_ref = f"Webhook error: {str(e)[:100]}"
        logger.warning(f"Could not reach n8n webhook: {e}")

    # STEP 4: UPDATE ALERT NOTIFICATION STATUS
    new_notif_status = "sent" if webhook_ok else "failed"
    await db.alerts.update_one(
        {"alert_id": alert_id},
        {"$set": {
            "notification_status": new_notif_status,
            "user_notified": webhook_ok,
            "admin_notified": webhook_ok,
            "webhook_dispatched": webhook_ok,
            "n8n_execution_reference": str(exec_ref)
        }}
    )

    alert_doc.pop("_id", None)
    return {
        "success": True,
        "triggered": True,
        "alert_id": alert_id,
        "event_id": event_id,
        "threshold_status": "triggered",
        "previous_dphis": previous_dphis,
        "current_dphis": current_dphis,
        "threshold": threshold,
        "severity": severity,
        "notification_status": new_notif_status,
        "webhook_dispatched": webhook_ok,
        "n8n_execution_reference": exec_ref,
        "alert": alert_doc
    }

async def evaluate_and_trigger_alert(
    project_id: str,
    project_name: str,
    current_dphis: float,
    current_severity: str,
    previous_severity: Optional[str] = None
) -> Optional[Alert]:
    """Compatibility bridge for existing callers like snapshot updates."""
    res = await evaluate_project_threshold_crossing(
        project_id=project_id,
        current_dphis=current_dphis
    )
    if res.get("triggered") and "alert" in res:
        return Alert(**res["alert"])
    return None
