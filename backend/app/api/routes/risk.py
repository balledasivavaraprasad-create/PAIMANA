from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.db.mongodb import get_database
from app.services.dphis_service import calculate_dphis
from app.models.risk import DPHISScore, RiskLevel, RiskComponents, RiskTrend

router = APIRouter(prefix="/projects", tags=["Risk Intelligence"])

@router.get("/{project_id}/risk", response_model=DPHISScore)
async def get_project_risk(project_id: str):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    proj = await db.projects.find_one({"project_id": project_id}, {"_id": 0})
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    if "dphis" in proj and "T_time_risk" in proj:
        t_val = float(proj.get("T_time_risk", 0.34) or 0.34)
        c_val = float(proj.get("C_cost_risk", 0.10) or 0.10)
        p_val = float(proj.get("P_progress_risk", 0.30) or 0.30)
        f_val = float(proj.get("F_financial_risk", 0.30) or 0.30)
        ml_val = float(proj.get("ML_combined_risk", 0.27) or 0.27)
        dphis_val = float(proj.get("dphis", 50.0) or 50.0)

        level_str = proj.get("risk_level", "moderate").lower()
        if level_str == "critical":
            level = RiskLevel.CRITICAL
        elif level_str == "high":
            level = RiskLevel.HIGH
        elif level_str in ("medium", "watch", "moderate"):
            level = RiskLevel.MODERATE
        else:
            level = RiskLevel.LOW

        vel = float(proj.get("risk_velocity_1m", 0.0) or 0.0)
        direction = "WORSENING" if vel >= 1.5 else ("IMPROVING" if vel <= -1.5 else "STABLE")
        prev_val = round(max(5.0, dphis_val - vel), 1)

        return DPHISScore(
            project_id=project_id,
            dphis=round(dphis_val, 1),
            level=level,
            components=RiskComponents(
                time=round(t_val, 3),
                cost=round(c_val, 3),
                progress=round(p_val, 3),
                milestone=round(min(1.0, float(proj.get("schedule_slippage_months", 0.0) or 0.0) / 36.0), 3),
                financial=round(f_val, 3),
                implementation=round(ml_val, 3),
            ),
            trend=RiskTrend(
                previous=prev_val,
                current=dphis_val,
                change_pts=round(vel, 1),
                direction=direction,
            ),
            trend_multiplier=round(1.0 + (float(proj.get("emerging_risk_score", 50.0) or 50.0) - 50.0) / 100.0 * 0.15, 3),
            timestamp=datetime.utcnow()
        )

    features = dict(proj)
    if "cost" in proj and isinstance(proj["cost"], dict):
        features["original_cost_cr"] = proj["cost"].get("original", 1000.0)
        features["revised_cost_cr"] = proj["cost"].get("revised", 1000.0)

    # Fallback to live inference
    dphis_obj = calculate_dphis(
        project_id=project_id,
        features=features,
        previous_dphis=proj.get("previous_dphis") or proj.get("dphis")
    )
    return dphis_obj


