import uuid
from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from app.db.mongodb import get_database
from app.agents.investigator import run_investigation
from app.models.investigation import (
    InvestigationReport,
    Intervention,
    InterventionApprovalRequest,
    InterventionOutcomeRequest,
    ProjectMemory
)
from app.services.project_memory_service import (
    get_project_memory,
    record_intervention,
    record_outcome,
    record_detected_issue
)

router = APIRouter(prefix="/projects", tags=["Agentic Investigations & Interventions"])

@router.post("/{project_id}/investigate", response_model=InvestigationReport)
async def trigger_investigation(
    project_id: str,
    trigger_reason: Optional[str] = Query(default="MANUAL_OFFICER_REQUEST")
):
    try:
        report = await run_investigation(project_id, trigger_reason=trigger_reason)
        db = get_database()
        if db is not None:
            report_doc = report.model_dump()
            await db.investigations.insert_one(report_doc)
            # Record detected findings in project memory
            for finding in report.findings:
                await record_detected_issue(project_id, finding.title)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Investigation workflow failed: {str(e)}")

@router.get("/{project_id}/investigations", response_model=List[dict])
async def list_investigations(project_id: str):
    db = get_database()
    if db is None:
        return []
    cursor = db.investigations.find({"project_id": project_id}, {"_id": 0}).sort("created_at", -1)
    return await cursor.to_list(length=20)

@router.post("/{project_id}/investigations/{investigation_id}/approve", response_model=dict)
async def approve_investigation(
    project_id: str,
    investigation_id: str,
    payload: Optional[InterventionApprovalRequest] = None
):
    """
    Approves an agentic investigation report and initiates an active intervention.
    Guarantees:
    - Rejects already-approved investigations (no duplicate approvals).
    - Preserves recommendation and creates an Intervention object.
    - Records timestamp and approving user.
    - Updates project memory.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    inv = await db.investigations.find_one({"investigation_id": investigation_id, "project_id": project_id})
    if not inv:
        # Check if in-memory investigation
        raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found for project {project_id}")

    if inv.get("status") == "approved":
        raise HTTPException(status_code=400, detail="Investigation has already been approved")

    now_utc = datetime.now(timezone.utc)
    approver = (payload.approved_by if payload and payload.approved_by else "admin")

    # Update investigation status
    await db.investigations.update_one(
        {"investigation_id": investigation_id},
        {"$set": {
            "status": "approved",
            "approved_by": approver,
            "approved_at": now_utc
        }}
    )

    # Extract primary recommendation safely
    recs = inv.get("recommendations", [])
    primary_action = recs[0].get("action", "Remedial schedule recovery plan") if recs else "Remedial schedule recovery plan"
    primary_reason = (recs[0].get("reason") or recs[0].get("title") or "DPHIS escalation mitigations") if recs else "DPHIS escalation mitigations"

    intervention_id = f"INT-{uuid.uuid4().hex[:8].upper()}"
    intervention_doc = {
        "intervention_id": intervention_id,
        "project_id": project_id,
        "investigation_id": investigation_id,
        "action": primary_action,
        "recommendation": primary_reason,
        "approved_by": approver,
        "approved_at": now_utc.isoformat(),
        "status": "active",
        "outcome": None,
        "outcome_recorded_at": None,
        "outcome_metrics": {}
    }

    await record_intervention(project_id, intervention_doc)

    return {
        "success": True,
        "message": f"Investigation {investigation_id} approved. Intervention {intervention_id} created.",
        "intervention": intervention_doc,
        "intervention_id": intervention_id,
        "investigation_status": "approved"
    }

@router.post("/{project_id}/interventions/{intervention_id}/outcome", response_model=dict)
async def submit_intervention_outcome(
    project_id: str,
    intervention_id: str,
    payload: InterventionOutcomeRequest
):
    """
    Records outcome for an approved intervention, closes the intervention loop,
    and updates project memory.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    res = await record_outcome(
        project_id=project_id,
        intervention_id=intervention_id,
        outcome=payload.outcome,
        outcome_metrics=payload.outcome_metrics,
        recorded_by=payload.recorded_by
    )

    if not res:
        raise HTTPException(status_code=404, detail=f"Active intervention {intervention_id} not found for project {project_id}")

    return {
        "success": True,
        "message": f"Intervention {intervention_id} outcome recorded and closed.",
        "intervention": res
    }

@router.get("/{project_id}/memory", response_model=dict)
async def retrieve_project_memory(project_id: str):
    """
    Retrieves longitudinal project memory (risk history, issues, interventions, outcomes).
    Guarantees: Strict project isolation (never leaks data across projects).
    """
    memory = await get_project_memory(project_id)
    return memory

@router.get("/{project_id}/interventions", response_model=List[dict])
async def list_interventions(project_id: str):
    db = get_database()
    if db is None:
        return []
    cursor = db.interventions.find({"project_id": project_id}, {"_id": 0}).sort("approved_at", -1)
    return await cursor.to_list(length=30)
