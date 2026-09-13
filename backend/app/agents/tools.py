from typing import Dict, Any, List, Optional
from app.db.mongodb import get_database
from app.services.feature_service import engineer_features
from app.services.shap_service import explain_features
from app.ml.models.cost_model import cost_model
from app.ml.models.delay_model import delay_model

async def tool_get_project(project_id: str) -> Optional[Dict[str, Any]]:
    db = get_database()
    if db is None:
        return None
    proj = await db.projects.find_one({"project_id": project_id}, {"_id": 0})
    return proj

async def tool_get_history(project_id: str) -> List[Dict[str, Any]]:
    db = get_database()
    if db is None:
        return []
    cursor = db.project_snapshots.find({"project_id": project_id}, {"_id": 0}).sort("snapshot_date", 1)
    return await cursor.to_list(length=36)

async def tool_get_milestones(project_id: str) -> Dict[str, Any]:
    history = await tool_get_history(project_id)
    if not history:
        return {"completed": 0, "delayed": 0, "pending": 0, "status": "NO_DATA"}
    latest = history[-1]
    return latest.get("milestones", {})

async def tool_get_shap(project_id: str) -> List[Dict[str, Any]]:
    proj = await tool_get_project(project_id)
    if not proj:
        return []
    history = await tool_get_history(project_id)
    features = engineer_features(proj, history)
    shap_items = explain_features(features)
    return [item.model_dump() for item in shap_items]

async def tool_get_environment(project_id: str) -> Dict[str, Any]:
    history = await tool_get_history(project_id)
    if not history:
        return {"rainfall": 0.0, "disruption_days": 0}
    latest = history[-1]
    return latest.get("weather", {})

async def tool_compare_peers(project_id: str) -> List[Dict[str, Any]]:
    db = get_database()
    if db is None:
        return []
    proj = await tool_get_project(project_id)
    if not proj:
        return []
    sector = proj.get("sector", "")
    cursor = db.projects.find({"sector": sector, "project_id": {"$ne": project_id}}, {"_id": 0}).limit(3)
    return await cursor.to_list(length=3)
