from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from datetime import datetime
from app.db.mongodb import get_database
from app.models.project import ProjectCreate, ProjectUpdate, ProjectInDB
from app.models.snapshot import SnapshotCreate, ProjectSnapshot
from app.services.feature_service import engineer_features
from app.services.dphis_service import calculate_dphis
from app.ml.models.cost_model import cost_model
from app.ml.models.delay_model import delay_model
from app.services.alert_service import evaluate_and_trigger_alert

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("", response_model=List[dict])
async def list_projects(
    risk: Optional[str] = None,
    state: Optional[str] = None,
    sector: Optional[str] = None,
    limit: int = Query(default=50, le=500),
    skip: int = Query(default=0, ge=0)
):
    db = get_database()
    if db is None:
        return []

    filter_q = {}
    if risk:
        filter_q["risk_level"] = risk.lower()
    if state:
        filter_q["state"] = state
    if sector:
        filter_q["sector"] = sector

    cursor = db.projects.find(filter_q, {"_id": 0}).sort("dphis", -1).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)

@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    existing = await db.projects.find_one({"project_id": payload.project_id})
    if existing:
        raise HTTPException(status_code=400, detail=f"Project with ID {payload.project_id} already exists")

    doc = payload.model_dump()
    doc["created_at"] = datetime.utcnow()
    doc["updated_at"] = datetime.utcnow()

    # Initial baseline snapshot
    baseline_snap = {
        "project_id": payload.project_id,
        "snapshot_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "physical_progress": 0.0,
        "financial_progress": 0.0,
        "cumulative_expenditure": 0.0,
        "milestones": {"completed": 0, "delayed": 0, "pending": 10, "total": 10},
        "created_at": datetime.utcnow()
    }

    features = engineer_features(doc, [baseline_snap])
    c_res = cost_model.predict(features)
    d_res = delay_model.predict(features)
    dphis_obj = calculate_dphis(payload.project_id, features, c_res["cost_risk_score"], d_res["time_risk_score"])

    doc["dphis"] = dphis_obj.dphis
    doc["risk_level"] = dphis_obj.level.value

    await db.projects.insert_one(doc)
    await db.project_snapshots.insert_one(baseline_snap)

    doc.pop("_id", None)
    return doc

@router.get("/{project_id}", response_model=dict)
async def get_project(project_id: str):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    proj = await db.projects.find_one({"project_id": project_id}, {"_id": 0})
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return proj

@router.put("/{project_id}", response_model=dict)
async def update_project(project_id: str, payload: ProjectUpdate):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    update_data = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()

    res = await db.projects.update_one({"project_id": project_id}, {"$set": update_data})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    return await get_project(project_id)

@router.get("/{project_id}/history", response_model=List[dict])
async def get_project_history(project_id: str):
    db = get_database()
    if db is None:
        return []

    cursor = db.project_snapshots.find({"project_id": project_id}, {"_id": 0}).sort("snapshot_date", 1)
    return await cursor.to_list(length=60)

@router.post("/{project_id}/snapshots", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_snapshot(project_id: str, payload: SnapshotCreate):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    proj = await db.projects.find_one({"project_id": project_id})
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    snap_doc = payload.model_dump()
    snap_doc["project_id"] = project_id
    snap_doc["created_at"] = datetime.utcnow()

    # Upsert snapshot for that date
    await db.project_snapshots.update_one(
        {"project_id": project_id, "snapshot_date": payload.snapshot_date},
        {"$set": snap_doc},
        upsert=True
    )

    # Re-evaluate project features and DPHIS
    all_snaps = await (db.project_snapshots.find({"project_id": project_id}, {"_id": 0}).sort("snapshot_date", 1)).to_list(length=60)
    features = engineer_features(proj, all_snaps)
    c_res = cost_model.predict(features)
    d_res = delay_model.predict(features)

    prev_dphis = proj.get("dphis", 50.0)
    prev_level = proj.get("risk_level", "moderate")

    dphis_obj = calculate_dphis(project_id, features, c_res["cost_risk_score"], d_res["time_risk_score"], previous_dphis=prev_dphis)

    await db.projects.update_one(
        {"project_id": project_id},
        {"$set": {
            "dphis": dphis_obj.dphis,
            "risk_level": dphis_obj.level.value,
            "updated_at": datetime.utcnow()
        }}
    )

    # Trigger alert if critical or escalation
    await evaluate_and_trigger_alert(
        project_id=project_id,
        project_name=proj.get("project_name", project_id),
        current_dphis=dphis_obj.dphis,
        current_severity=dphis_obj.level.value,
        previous_severity=prev_level
    )

    snap_doc.pop("_id", None)
    return {
        "snapshot": snap_doc,
        "updated_dphis": dphis_obj.dphis,
        "risk_level": dphis_obj.level.value,
        "trend_direction": dphis_obj.trend.direction
    }
