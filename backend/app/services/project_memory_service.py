import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.db.mongodb import get_database
from app.config.logging import logger

async def get_project_memory(project_id: str) -> Dict[str, Any]:
    """
    Retrieves the longitudinal memory for a specific project.
    Strictly isolated: returns ONLY records tagged with project_id.
    """
    db = get_database()
    if db is None:
        return {
            "project_id": project_id,
            "risk_history": [],
            "detected_issues": [],
            "interventions": [],
            "outcomes": [],
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    memory = await db.project_memory.find_one({"project_id": project_id}, {"_id": 0})
    if not memory:
        # Initialize project memory container if it doesn't exist
        memory = {
            "project_id": project_id,
            "risk_history": [],
            "detected_issues": [],
            "interventions": [],
            "outcomes": [],
            "last_updated": datetime.now(timezone.utc)
        }
        await db.project_memory.update_one(
            {"project_id": project_id},
            {"$set": memory},
            upsert=True
        )

    # Ensure default fields exist
    memory.setdefault("project_id", project_id)
    memory.setdefault("risk_history", [])
    memory.setdefault("detected_issues", [])
    memory.setdefault("interventions", [])
    memory.setdefault("outcomes", [])

    # Synchronize with any interventions created directly in db.interventions
    if db is not None:
        db_interventions = await db.interventions.find({"project_id": project_id}, {"_id": 0}).to_list(length=100)
        existing_ids = {i.get("intervention_id") for i in memory["interventions"] if isinstance(i, dict) and i.get("intervention_id")}
        for item in db_interventions:
            if item.get("intervention_id") not in existing_ids:
                memory["interventions"].append(item)

    # Convert datetime to isoformat if needed
    if "last_updated" in memory and isinstance(memory["last_updated"], datetime):
        memory["last_updated"] = memory["last_updated"].isoformat()

    return memory

async def record_risk_point(project_id: str, dphis: float, level: str, reason: str):
    """Appends a risk assessment to project memory."""
    db = get_database()
    if db is None:
        return

    entry = {
        "dphis": round(float(dphis), 1),
        "level": level,
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    await db.project_memory.update_one(
        {"project_id": project_id},
        {
            "$push": {"risk_history": {"$each": [entry], "$slice": -50}},
            "$set": {"last_updated": datetime.now(timezone.utc)}
        },
        upsert=True
    )

async def record_detected_issue(project_id: str, issue_text: str):
    """Records an operational issue in project memory."""
    db = get_database()
    if db is None:
        return

    await db.project_memory.update_one(
        {"project_id": project_id},
        {
            "$addToSet": {"detected_issues": issue_text},
            "$set": {"last_updated": datetime.now(timezone.utc)}
        },
        upsert=True
    )

async def record_intervention(project_id: str, intervention: Dict[str, Any]):
    """Appends an approved intervention to project memory and interventions collection."""
    db = get_database()
    if db is None:
        return

    await db.interventions.insert_one(dict(intervention))

    await db.project_memory.update_one(
        {"project_id": project_id},
        {
            "$push": {"interventions": intervention},
            "$set": {"last_updated": datetime.now(timezone.utc)}
        },
        upsert=True
    )

async def record_outcome(
    project_id: str,
    intervention_id: str,
    outcome: str,
    outcome_metrics: Optional[Dict[str, Any]] = None,
    recorded_by: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Records an outcome for an approved intervention and closes it."""
    db = get_database()
    if db is None:
        return None

    now = datetime.now(timezone.utc)
    outcome_record = {
        "outcome": outcome,
        "outcome_metrics": outcome_metrics or {},
        "recorded_by": recorded_by or "system",
        "timestamp": now.isoformat()
    }

    # Update intervention collection
    res = await db.interventions.find_one_and_update(
        {"intervention_id": intervention_id, "project_id": project_id},
        {"$set": {
            "status": "closed",
            "outcome": outcome,
            "outcome_metrics": outcome_metrics or {},
            "outcome_recorded_at": now
        }},
        return_document=True
    )

    if not res:
        return None

    # Update project memory
    await db.project_memory.update_one(
        {"project_id": project_id},
        {
            "$push": {"outcomes": {
                "intervention_id": intervention_id,
                **outcome_record
            }},
            "$set": {"last_updated": now}
        },
        upsert=True
    )

    res.pop("_id", None)
    return res
