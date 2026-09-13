from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.db.mongodb import get_database
from app.services.feature_service import engineer_features
from app.services.shap_service import explain_features
from app.ml.models.cost_model import cost_model
from app.ml.models.delay_model import delay_model
from app.ml.models.risk_model import risk_model
from app.models.prediction import PredictionResult, CostPrediction, DelayPrediction

router = APIRouter(prefix="/projects", tags=["ML Predictions"])

@router.get("/{project_id}/predictions", response_model=PredictionResult)
async def get_project_predictions(project_id: str):
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
    risk_prob = risk_model.predict_probability(features)
    shap_factors = explain_features(features)

    orig_cost = float(proj.get("cost", {}).get("original", 1000.0) or 1000.0)
    pred_final_cost = round(orig_cost * (1.0 + c_res["predicted_overrun_pct"] / 100.0), 2)

    return PredictionResult(
        project_id=project_id,
        cost=CostPrediction(
            predicted_final_cost=pred_final_cost,
            predicted_overrun_pct=c_res["predicted_overrun_pct"],
            cost_risk_score=c_res["cost_risk_score"]
        ),
        delay=DelayPrediction(
            predicted_completion_date=proj.get("schedule", {}).get("revised_end", "2027-12-31"),
            expected_delay_months=d_res["expected_delay_months"],
            time_risk_score=d_res["time_risk_score"]
        ),
        overall_risk_probability=round(risk_prob, 3),
        top_shap_factors=shap_factors,
        model_version="xgb_v1.0",
        created_at=datetime.utcnow()
    )
