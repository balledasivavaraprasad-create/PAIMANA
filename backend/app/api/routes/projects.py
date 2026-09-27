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
from app.services.alert_service import evaluate_and_trigger_alert, evaluate_project_threshold_crossing

router = APIRouter(prefix="/projects", tags=["Projects"])

import re

MINISTRY_ALIASES = {
    "morth": "Road Transport",
    "railway": "Railways",
    "railways": "Railways",
    "coal": "Coal",
    "power": "Power",
    "petroleum": "Petroleum",
    "urban": "Housing & Urban Affairs",
    "telecom": "Telecommunications",
    "shipping": "Ports",
    "ports": "Ports",
}

@router.get("", response_model=List[dict])
async def list_projects(
    risk: Optional[str] = None,
    state: Optional[str] = None,
    sector: Optional[str] = None,
    ministry: Optional[str] = None,
    search: Optional[str] = None,
    username: Optional[str] = None,
    limit: int = Query(default=50, le=500),
    skip: int = Query(default=0, ge=0)
):
    db = get_database()
    if db is None:
        return []

    filter_q = {}

    if username and username.strip():
        u = await db.users.find_one({"username": username.strip()})
        if u and u.get("assigned_projects"):
            filter_q["project_id"] = {"$in": u["assigned_projects"]}
        else:
            filter_q["assigned_users"] = username.strip()

    if risk:
        filter_q["risk_level"] = risk.lower()
    if state:
        filter_q["state"] = state
    if sector:
        filter_q["sector"] = sector
    if ministry and ministry.strip() and ministry.lower() not in ("all", "central infrastructure", "mospi"):
        target_str = ministry.strip()
        lower_min = target_str.lower()
        # Check alias
        for alias_key, alias_val in MINISTRY_ALIASES.items():
            if alias_key in lower_min:
                target_str = alias_val
                break

        tokens = [re.escape(tok) for tok in target_str.replace("&", " ").split() if tok.lower() not in ("of", "and", "&", "the", "ministry", "department")]
        if tokens:
            pat = re.compile(".*".join(tokens), re.IGNORECASE)
        else:
            pat = re.compile(re.escape(target_str), re.IGNORECASE)
        filter_q["ministry"] = pat

    if search and search.strip():
        s_pat = re.compile(re.escape(search.strip()), re.IGNORECASE)
        filter_q["$or"] = [
            {"project_name": s_pat},
            {"project_id": s_pat}
        ]

    cursor = db.projects.find(filter_q, {"_id": 0}).sort("dphis", -1).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)

@router.get("/public-risk-overview")
async def get_public_risk_overview():
    """
    Public Institutional Telemetry Endpoint.
    Strictly read-only and pre-sanitized: returns dynamic macro statistics and top
    at-risk projects exposing ONLY public non-confidential columns.
    Direct access to database tables or private fields is prohibited.
    """
    db = get_database()
    if db is None:
        return {
            "total_projects": 3394,
            "total_capex_lakh_cr": 74.5,
            "at_risk_count": 223,
            "critical_count": 18,
            "ministries_count": 17,
            "sectors_count": 22,
            "top_sectors": ["Roads & Highways", "Railways", "Urban Transit & Metro", "Power", "Coal"],
            "risk_watchlist": [],
            "governance_mode": "RESTRICTED_PUBLIC_PREVIEW"
        }

    total = await db.projects.count_documents({})
    critical = await db.projects.count_documents({"$or": [{"risk_level": "critical"}, {"dphis": {"$gte": 75}}]})
    at_risk = await db.projects.count_documents({"$or": [{"risk_level": {"$in": ["critical", "high"]}}, {"dphis": {"$gte": 65}}]})

    # Capex Sum Aggregation
    agg_res = await db.projects.aggregate([
        {"$group": {"_id": None, "total_cost": {"$sum": "$cost.revised"}}}
    ]).to_list(length=1)
    total_cost = agg_res[0]["total_cost"] if agg_res else 0.0
    total_capex_lakh_cr = round(total_cost / 100000.0, 2)

    distinct_ministries = await db.projects.distinct("ministry")
    distinct_sectors = await db.projects.distinct("sector")
    top_sectors = [s for s in distinct_sectors if s][:8]

    # Query top at-risk projects with STRICT COLUMN RESTRICTION
    # Only exposing project_name, sector, state, risk_level, dphis, cost_revised_cr, schedule_slippage_months
    cursor = db.projects.find(
        {"$or": [{"risk_level": {"$in": ["high", "critical"]}}, {"dphis": {"$gte": 70}}]},
        {"_id": 0, "project_name": 1, "sector": 1, "state": 1, "dphis": 1, "risk_level": 1, "cost.revised": 1, "schedule_slippage_months": 1}
    ).sort("dphis", -1).limit(5)

    projects_raw = await cursor.to_list(length=5)
    watchlist = []
    for p in projects_raw:
        watchlist.append({
            "project_name": p.get("project_name", "National Corridor"),
            "sector": p.get("sector", "Infrastructure"),
            "state": p.get("state", "National"),
            "dphis": round(float(p.get("dphis", 50.0)), 1),
            "risk_level": p.get("risk_level", "high"),
            "cost_revised_cr": round(float(p.get("cost", {}).get("revised", 0.0)), 2),
            "schedule_slippage_months": round(float(p.get("schedule_slippage_months", 0.0)), 1)
        })

    return {
        "total_projects": total,
        "total_capex_lakh_cr": total_capex_lakh_cr,
        "at_risk_count": at_risk,
        "critical_count": critical,
        "ministries_count": len(distinct_ministries),
        "sectors_count": len(distinct_sectors),
        "top_sectors": top_sectors,
        "risk_watchlist": watchlist,
        "governance_mode": "RESTRICTED_PUBLIC_PREVIEW",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/my-projects", response_model=List[dict])
async def get_my_projects(
    username: Optional[str] = None,
    limit: int = Query(default=50, le=200)
):
    """
    Returns only the projects associated with the specified or authenticated user.
    Consults user.assigned_projects in MongoDB.
    """
    db = get_database()
    if db is None:
        return []

    if not username:
        # Return empty if unassigned/unspecified
        return []

    user = await db.users.find_one({"username": username.strip()})
    if not user:
        return []

    if "assigned_projects" in user:
        assigned_ids = user.get("assigned_projects") or []
        if not assigned_ids:
            return []
        cursor = db.projects.find(
            {"project_id": {"$in": assigned_ids}},
            {"_id": 0}
        ).sort("dphis", -1).limit(limit)
        return await cursor.to_list(length=limit)

    # Fallback to projects tagged with assigned_users
    cursor = db.projects.find(
        {"assigned_users": username.strip()},
        {"_id": 0}
    ).sort("dphis", -1).limit(limit)
    res = await cursor.to_list(length=limit)
    if res:
        return res

    # If user belongs to a specific ministry, return sample projects of that ministry
    user_min = user.get("ministry")
    if user_min and "mospi" not in user_min.lower() and "admin" not in user_min.lower():
        min_tokens = [re.escape(t) for t in user_min.replace("&", " ").split() if t.lower() not in ("of", "and", "the", "ministry", "department")]
        pat = re.compile(".*".join(min_tokens), re.IGNORECASE) if min_tokens else re.compile(re.escape(user_min), re.IGNORECASE)
        cursor = db.projects.find({"ministry": pat}, {"_id": 0}).sort("dphis", -1).limit(limit)
        return await cursor.to_list(length=limit)

    return []

from pydantic import BaseModel
from app.services.gemini_feature_service import process_project_ingestion

class NormalAssetIngestRequest(BaseModel):
    project_id: str
    project_name: str
    original_cost_crores: float
    revised_cost_crores: float
    expenditure_crores: float
    physical_progress_percent: float
    s_no: Optional[int] = 1
    page: Optional[int] = 1
    ministry: Optional[str] = None
    sector: Optional[str] = None
    state: Optional[str] = None
    username: Optional[str] = None
    dphis_threshold: Optional[float] = 70.0

@router.post("/ingest-normal-asset", response_model=dict, status_code=status.HTTP_201_CREATED)
async def ingest_normal_asset(payload: NormalAssetIngestRequest):
    """
    Ingests an infrastructure asset using ONLY the 8 standard Flash Report columns:
    page, s_no, project_id, project_name, original_cost_crores, revised_cost_crores,
    expenditure_crores, physical_progress_percent.
    
    1. Invokes Gemini Flash to generate the full 57-feature engineered dataset.
    2. Feeds the 57 features into the LightGBM models + Platt calibrators.
    3. Computes DPHIS score, risk tier, and driver decomposition.
    4. Persists project, features, and snapshot into MongoDB.
    5. Links project to user.assigned_projects.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    # Run Gemini Flash 2.5 Feature Engineering + ML Inference Pipeline
    try:
        pipeline_res = await process_project_ingestion(
            normal_inputs=payload.model_dump(),
            ministry=payload.ministry,
            state=payload.state,
            sector=payload.sector,
            username=payload.username
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature engineering or ML inference failed: {str(e)}")

    project_doc = pipeline_res["project"]
    features_57 = pipeline_res["features_57"]
    project_id = project_doc["project_id"]

    # Set project-specific threshold attributes
    dphis_threshold = float(payload.dphis_threshold if payload.dphis_threshold is not None else 70.0)
    current_score = float(project_doc.get("dphis", 50.0))
    project_doc["dphis_threshold"] = dphis_threshold
    project_doc["threshold_enabled"] = True
    project_doc["threshold_source"] = "project_creator"
    project_doc["threshold_configured_by"] = payload.username or "project_creator"
    project_doc["threshold_configured_at"] = datetime.utcnow()
    project_doc["threshold_updated_at"] = datetime.utcnow()
    project_doc["threshold_status"] = "below" if current_score < dphis_threshold else "triggered"
    project_doc["current_dphis"] = current_score
    project_doc["previous_dphis"] = None
    project_doc["threshold_history"] = [{
        "old_value": None,
        "new_value": dphis_threshold,
        "changed_by": payload.username or "project_creator",
        "timestamp": datetime.utcnow().isoformat()
    }]

    # Upsert into projects collection
    await db.projects.update_one(
        {"project_id": project_id},
        {"$set": project_doc},
        upsert=True
    )

    # Store 57-feature engineered dataset in project_features collection
    feature_record = {
        "project_id": project_id,
        "features": features_57,
        "dphis": project_doc["dphis"],
        "risk_tier": project_doc["risk_tier"],
        "created_at": datetime.utcnow()
    }
    await db.project_features.update_one(
        {"project_id": project_id},
        {"$set": feature_record},
        upsert=True
    )

    # Create baseline snapshot
    baseline_snap = {
        "project_id": project_id,
        "snapshot_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "physical_progress": payload.physical_progress_percent,
        "financial_progress": round((payload.expenditure_crores / max(1.0, payload.revised_cost_crores)) * 100.0, 2),
        "cumulative_expenditure": payload.expenditure_crores,
        "milestones": {"completed": int(payload.physical_progress_percent / 10), "delayed": 1 if project_doc["dphis"] > 65 else 0, "pending": 10 - int(payload.physical_progress_percent / 10), "total": 10},
        "created_at": datetime.utcnow()
    }
    await db.project_snapshots.update_one(
        {"project_id": project_id, "snapshot_date": baseline_snap["snapshot_date"]},
        {"$set": baseline_snap},
        upsert=True
    )

    # Link to user's assigned projects in db.users
    if payload.username and payload.username.strip():
        uname = payload.username.strip()
        await db.users.update_one(
            {"username": uname},
            {"$addToSet": {"assigned_projects": project_id}}
        )
        await db.projects.update_one(
            {"project_id": project_id},
            {"$addToSet": {"assigned_users": uname}}
        )

    # Initial threshold evaluation for newly created project
    await evaluate_project_threshold_crossing(
        project_id=project_id,
        current_dphis=float(project_doc.get("dphis", 50.0)),
        previous_dphis=None,
        custom_threshold=dphis_threshold,
        trigger_source="project_creation"
    )

    project_doc.pop("_id", None)
    return project_doc

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

    # Project-specific threshold setup
    dphis_threshold = float(getattr(payload, "dphis_threshold", 70.0) or 70.0)
    doc["dphis_threshold"] = dphis_threshold
    doc["threshold_enabled"] = True
    doc["threshold_source"] = "project_creator"
    doc["threshold_configured_by"] = "project_creator"
    doc["threshold_configured_at"] = datetime.utcnow()
    doc["threshold_updated_at"] = datetime.utcnow()
    doc["threshold_status"] = "below" if dphis_obj.dphis < dphis_threshold else "triggered"
    doc["current_dphis"] = dphis_obj.dphis
    doc["previous_dphis"] = None
    doc["threshold_history"] = [{
        "old_value": None,
        "new_value": dphis_threshold,
        "changed_by": "project_creator",
        "timestamp": datetime.utcnow().isoformat()
    }]

    await db.projects.insert_one(doc)
    await db.project_snapshots.insert_one(baseline_snap)

    # Evaluate initial threshold crossing
    await evaluate_project_threshold_crossing(
        project_id=payload.project_id,
        current_dphis=dphis_obj.dphis,
        previous_dphis=None,
        custom_threshold=dphis_threshold,
        trigger_source="project_creation"
    )

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

    # Evaluate threshold crossing with project-specific threshold
    threshold_eval = await evaluate_project_threshold_crossing(
        project_id=project_id,
        current_dphis=dphis_obj.dphis,
        previous_dphis=prev_dphis
    )

    snap_doc.pop("_id", None)
    return {
        "snapshot": snap_doc,
        "updated_dphis": dphis_obj.dphis,
        "risk_level": dphis_obj.level.value,
        "trend_direction": dphis_obj.trend.direction,
        "threshold_eval": threshold_eval
    }

class ProjectThresholdPatch(BaseModel):
    dphis_threshold: float
    threshold_enabled: Optional[bool] = True
    changed_by: Optional[str] = "admin"

@router.patch("/{project_id}/threshold", response_model=dict)
async def update_project_threshold(project_id: str, payload: ProjectThresholdPatch):
    """
    Allows Admin to configure a project-specific DPHIS alert threshold.
    Records full change history (old_value, new_value, changed_by, timestamp).
    Re-evaluates threshold status against current project DPHIS.
    """
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    project = await db.projects.find_one({"project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    old_threshold = float(project.get("dphis_threshold", 70.0))
    new_threshold = round(float(payload.dphis_threshold), 1)
    admin_id = payload.changed_by or "admin"
    now_utc = datetime.utcnow()

    history_entry = {
        "old_value": old_threshold,
        "new_value": new_threshold,
        "changed_by": admin_id,
        "timestamp": now_utc.isoformat()
    }

    current_dphis = float(project.get("current_dphis") or project.get("dphis") or 50.0)
    prev_dphis = project.get("previous_dphis")

    new_status = "below" if current_dphis < new_threshold else "triggered"

    update_fields = {
        "dphis_threshold": new_threshold,
        "threshold_enabled": payload.threshold_enabled if payload.threshold_enabled is not None else project.get("threshold_enabled", True),
        "threshold_source": "admin",
        "threshold_configured_by": admin_id,
        "threshold_updated_at": now_utc,
        "threshold_status": new_status,
        "updated_at": now_utc
    }

    await db.projects.update_one(
        {"project_id": project_id},
        {
            "$set": update_fields,
            "$push": {"threshold_history": history_entry}
        }
    )

    eval_res = None
    if payload.threshold_enabled:
        eval_res = await evaluate_project_threshold_crossing(
            project_id=project_id,
            current_dphis=current_dphis,
            previous_dphis=prev_dphis,
            custom_threshold=new_threshold,
            trigger_source="admin_threshold_update"
        )

    updated_proj = await db.projects.find_one({"project_id": project_id}, {"_id": 0})
    return {
        "message": f"Threshold updated to {new_threshold} for project {project_id}",
        "project_id": project_id,
        "old_threshold": old_threshold,
        "new_threshold": new_threshold,
        "threshold_status": updated_proj.get("threshold_status", new_status),
        "threshold_history": updated_proj.get("threshold_history", []),
        "evaluation": eval_res
    }

class ProjectRiskEventRequest(BaseModel):
    project_id: str
    current_dphis: float
    previous_dphis: Optional[float] = None
    threshold: Optional[float] = None

@router.post("/project-risk-events", response_model=dict)
@router.post("/risk-events", response_model=dict)
async def handle_project_risk_event(payload: ProjectRiskEventRequest):
    """
    Evaluates project-specific threshold crossing and triggers n8n automated workflow.
    Ensures idempotency and persists alert prior to webhook delivery.
    """
    res = await evaluate_project_threshold_crossing(
        project_id=payload.project_id,
        current_dphis=payload.current_dphis,
        previous_dphis=payload.previous_dphis,
        custom_threshold=payload.threshold,
        trigger_source="api_event"
    )
    return res

