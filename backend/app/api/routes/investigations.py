from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.db.mongodb import get_database
from app.agents.investigator import run_investigation
from app.models.investigation import InvestigationReport

router = APIRouter(prefix="/projects", tags=["Agentic Investigations"])

@router.post("/{project_id}/investigate", response_model=InvestigationReport)
async def trigger_investigation(
    project_id: str,
    trigger_reason: Optional[str] = Query(default="MANUAL_OFFICER_REQUEST")
):
    try:
        report = await run_investigation(project_id, trigger_reason=trigger_reason)
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
