from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class FeatureImpact(BaseModel):
    feature: str
    impact: float
    direction: str  # "increase" or "decrease"
    description: Optional[str] = None

class CostPrediction(BaseModel):
    predicted_final_cost: float
    predicted_overrun_pct: float
    cost_risk_score: float

class DelayPrediction(BaseModel):
    predicted_completion_date: str
    expected_delay_months: float
    time_risk_score: float

class PredictionResult(BaseModel):
    project_id: str
    cost: CostPrediction
    delay: DelayPrediction
    overall_risk_probability: float
    top_shap_factors: List[FeatureImpact] = Field(default_factory=list)
    model_version: str = "xgb_v1.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)
