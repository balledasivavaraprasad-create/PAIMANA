from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from app.db.mongodb import get_database
from app.services.paimana_ml_service import paimana_ml
from app.services.shap_service import explain_features
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

    # Merge features from project document
    features = dict(proj)
    if "cost" in proj and isinstance(proj["cost"], dict):
        features["original_cost_cr"] = proj["cost"].get("original", 1000.0)
        features["revised_cost_cr"] = proj["cost"].get("revised", 1000.0)
    if "schedule" in proj and isinstance(proj["schedule"], dict):
        features["schedule_slippage_months"] = proj.get("schedule_slippage_months", 12.0)

    probs = paimana_ml.predict_probabilities(features)
    comps = paimana_ml.compute_component_risks(features, probs)
    shap_factors = explain_features(features)

    orig_cost = float(proj.get("cost", {}).get("original", 1000.0) or 1000.0)
    overrun_pct = float(proj.get("cost_overrun_pct", 0.0) or 0.0)
    if overrun_pct <= 0 and probs.get("cost_risk_1m", 0) > 0.3:
        overrun_pct = round(probs["cost_risk_1m"] * 25.0, 1)

    pred_final_cost = round(orig_cost * (1.0 + overrun_pct / 100.0), 2)
    expected_delay = float(proj.get("schedule_slippage_months", 0.0) or (probs.get("schedule_risk_1m", 0.34) * 24.0))

    return PredictionResult(
        project_id=project_id,
        cost=CostPrediction(
            predicted_final_cost=pred_final_cost,
            predicted_overrun_pct=round(overrun_pct, 2),
            cost_risk_score=round(comps["C_cost_risk"], 3)
        ),
        delay=DelayPrediction(
            predicted_completion_date=proj.get("schedule", {}).get("revised_end", "2027-12-31"),
            expected_delay_months=round(expected_delay, 1),
            time_risk_score=round(comps["T_time_risk"], 3)
        ),
        overall_risk_probability=round(comps["ML_combined_risk"], 3),
        top_shap_factors=shap_factors,
        model_version="LightGBM_Platt_Calibrated_v1.0",
        created_at=datetime.now(timezone.utc)
    )

