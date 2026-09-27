import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any
from app.config.logging import logger
from app.ml.models.new_model_loader import prepare_feature_dataframe, BaggedHGB, log_shift, inv_log_shift

PRIMARY_ARTIFACT_PATH = os.path.join(os.path.dirname(__file__), "..", "artifacts", "model_cost_overrun.joblib")
FALLBACK_ARTIFACT_PATH = os.path.join(os.path.dirname(__file__), "..", "artifacts", "cost_model.joblib")

class CostPredictionModel:
    def __init__(self):
        self.model = None
        self.is_new_pipeline = False
        self.load_or_init()

    def load_or_init(self):
        if os.path.exists(PRIMARY_ARTIFACT_PATH):
            try:
                self.model = joblib.load(PRIMARY_ARTIFACT_PATH)
                self.is_new_pipeline = True
                logger.info("Loaded pre-trained Cost BaggedHGB Model from model_cost_overrun.joblib.")
                return
            except Exception as e:
                logger.warning(f"Could not load primary cost model artifact: {e}")

        if os.path.exists(FALLBACK_ARTIFACT_PATH):
            try:
                self.model = joblib.load(FALLBACK_ARTIFACT_PATH)
                self.is_new_pipeline = False
                logger.info("Loaded legacy cost model fallback.")
                return
            except Exception as e:
                logger.warning(f"Could not load fallback cost model: {e}")

    def save(self):
        os.makedirs(os.path.dirname(PRIMARY_ARTIFACT_PATH), exist_ok=True)
        joblib.dump(self.model, PRIMARY_ARTIFACT_PATH)

    def predict(self, features: Dict[str, Any]) -> Dict[str, float]:
        df = prepare_feature_dataframe(features)

        if self.model is not None:
            try:
                if self.is_new_pipeline or hasattr(self.model, "named_steps"):
                    predicted_overrun_pct = float(self.model.predict(df)[0])
                else:
                    # Legacy fallback
                    from app.services.feature_service import FEATURE_COLUMNS
                    X = np.array([[features.get(col, 0.0) for col in FEATURE_COLUMNS]])
                    predicted_overrun_pct = float(self.model.predict(X)[0])
            except Exception as e:
                logger.warning(f"Prediction error in CostPredictionModel: {e}, using heuristic")
                predicted_overrun_pct = max(0.0, float(features.get("cost_escalation", 0.0) * 100.0))
        else:
            predicted_overrun_pct = max(0.0, float(features.get("cost_escalation", 0.0) * 100.0))

        predicted_overrun_pct = round(max(-20.0, min(200.0, predicted_overrun_pct)), 2)
        cost_risk_score = min(1.0, max(0.05, (predicted_overrun_pct / 35.0) if predicted_overrun_pct > 0 else 0.05))

        return {
            "predicted_overrun_pct": round(predicted_overrun_pct, 2),
            "cost_risk_score": round(cost_risk_score, 3)
        }

cost_model = CostPredictionModel()
