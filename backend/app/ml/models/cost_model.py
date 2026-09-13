import os
import joblib
import numpy as np
import xgboost as xgb
from typing import Dict, Any
from app.services.feature_service import FEATURE_COLUMNS
from app.config.logging import logger

ARTIFACT_PATH = os.path.join(os.path.dirname(__file__), "..", "artifacts", "cost_model.joblib")

class CostPredictionModel:
    def __init__(self):
        self.model = None
        self.load_or_init()

    def load_or_init(self):
        if os.path.exists(ARTIFACT_PATH):
            try:
                self.model = joblib.load(ARTIFACT_PATH)
                logger.info("Loaded pre-trained Cost XGBoost Model.")
                return
            except Exception as e:
                logger.warning(f"Could not load cost model artifact: {e}, initializing baseline.")
        
        # Initialize default XGBRegressor
        self.model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.08,
            random_state=42
        )

    def save(self):
        os.makedirs(os.path.dirname(ARTIFACT_PATH), exist_ok=True)
        joblib.dump(self.model, ARTIFACT_PATH)

    def predict(self, features: Dict[str, float]) -> Dict[str, float]:
        X = np.array([[features.get(col, 0.0) for col in FEATURE_COLUMNS]])
        if hasattr(self.model, "n_features_in_"):
            predicted_overrun_pct = float(self.model.predict(X)[0])
        else:
            # Domain heuristic fallback if untrained
            predicted_overrun_pct = max(0.0, (
                features.get("cost_escalation", 0.0) * 40.0 +
                features.get("physical_financial_gap", 0.0) * 0.5 +
                features.get("milestone_delay_rate", 0.0) * 15.0
            ))
        
        predicted_overrun_pct = max(0.0, min(150.0, predicted_overrun_pct))
        cost_risk_score = min(1.0, predicted_overrun_pct / 40.0)

        return {
            "predicted_overrun_pct": round(predicted_overrun_pct, 2),
            "cost_risk_score": round(cost_risk_score, 3)
        }

cost_model = CostPredictionModel()
