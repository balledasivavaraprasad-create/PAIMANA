import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any
from app.config.logging import logger
from app.ml.models.new_model_loader import prepare_feature_dataframe

PRIMARY_ARTIFACT_PATH = os.path.join(os.path.dirname(__file__), "..", "artifacts", "model_time_overrun.joblib")
FALLBACK_ARTIFACT_PATH = os.path.join(os.path.dirname(__file__), "..", "artifacts", "delay_model.joblib")

class DelayPredictionModel:
    def __init__(self):
        self.model = None
        self.is_new_pipeline = False
        self.load_or_init()

    def load_or_init(self):
        if os.path.exists(PRIMARY_ARTIFACT_PATH):
            try:
                self.model = joblib.load(PRIMARY_ARTIFACT_PATH)
                self.is_new_pipeline = True
                logger.info("Loaded pre-trained Time Overrun Model from model_time_overrun.joblib.")
                return
            except Exception as e:
                logger.warning(f"Could not load primary time model artifact: {e}")

        if os.path.exists(FALLBACK_ARTIFACT_PATH):
            try:
                self.model = joblib.load(FALLBACK_ARTIFACT_PATH)
                self.is_new_pipeline = False
                logger.info("Loaded legacy delay model fallback.")
                return
            except Exception as e:
                logger.warning(f"Could not load fallback delay model: {e}")

    def save(self):
        os.makedirs(os.path.dirname(PRIMARY_ARTIFACT_PATH), exist_ok=True)
        joblib.dump(self.model, PRIMARY_ARTIFACT_PATH)

    def predict(self, features: Dict[str, Any]) -> Dict[str, float]:
        df = prepare_feature_dataframe(features)

        if self.model is not None:
            try:
                if self.is_new_pipeline or hasattr(self.model, "named_steps"):
                    expected_delay_months = float(self.model.predict(df)[0])
                else:
                    from app.services.feature_service import FEATURE_COLUMNS
                    X = np.array([[features.get(col, 0.0) for col in FEATURE_COLUMNS]])
                    expected_delay_months = float(self.model.predict(X)[0])
            except Exception as e:
                logger.warning(f"Prediction error in DelayPredictionModel: {e}, using heuristic")
                expected_delay_months = max(0.0, float(features.get("deadline_slip_months", 0.0)))
        else:
            expected_delay_months = max(0.0, float(features.get("deadline_slip_months", 0.0)))

        expected_delay_months = max(0.0, round(expected_delay_months, 1))
        time_risk_score = min(1.0, max(0.05, expected_delay_months / 36.0))

        return {
            "expected_delay_months": expected_delay_months,
            "time_risk_score": round(time_risk_score, 3)
        }

delay_model = DelayPredictionModel()
