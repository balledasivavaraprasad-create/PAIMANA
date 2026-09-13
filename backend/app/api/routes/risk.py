from fastapi import APIRouter, HTTPException
from app.db.mongodb import get_database
from app.services.feature_service import engineer_features
from app.services.dphis_service import calculate_dphis
from app.ml.models.cost_model import cost_model
from app.ml.models.delay_model import delay_model
from app.models.risk import DPHISScore

router = APIRouter(prefix="/projects", tags=["Risk Intelligence"])

@router.get("/{project_id}/risk", response_model=DPHISScore)
async def get_project_risk(project_id: str):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    proj = await db.projects.find_one({"project_id": project_id}, {"_id": 0})
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    cursor = db.project_snapshots.find({"project_id": project_id}, {"_id": 0}).sort("snapshot_date", 1)
    snapshots = await cursor.to_list(length=60)

    features = engineer_features(proj, snapshots)
    c_res = cost_model.predict(features)
    d_res = delay_model.predict(features)

    dphis_obj = calculate_dphis(
        project_id=project_id,
        features=features,
        cost_risk=c_res["cost_risk_score"],
        time_risk=d_res["time_risk_score"],
        previous_dphis=proj.get("dphis")
    )

    return dphis_obj
