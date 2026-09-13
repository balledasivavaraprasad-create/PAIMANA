import os
import joblib
import numpy as np
import xgboost as xgb
from typing import Dict, Any
from app.services.feature_service import FEATURE_COLUMNS
from app.config.logging import logger

ARTIFACT_PATH = os.path.join(os.path.dirname(__file__), "..", "artifacts", "delay_model.joblib")

class DelayPredictionModel:
    def __init__(self):
        self.model = None
        self.load_or_init()

    def load_or_init(self):
        if os.path.exists(ARTIFACT_PATH):
            try:
                self.model = joblib.load(ARTIFACT_PATH)
                logger.info("Loaded pre-trained Delay XGBoost Model.")
                return
            except Exception as e:
                logger.warning(f"Could not load delay model artifact: {e}, initializing baseline.")

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
            expected_delay_months = float(self.model.predict(X)[0])
        else:
            # Baseline domain heuristic
            slip = features.get("deadline_slip_months", 0.0)
            m_delay = features.get("milestone_delay_rate", 0.0) * 18.0
            stagnation = features.get("stagnation_months", 0.0) * 2.5
            expected_delay_months = max(0.0, slip + m_delay + stagnation)

        expected_delay_months = max(0.0, round(expected_delay_months, 1))
        time_risk_score = min(1.0, expected_delay_months / 24.0)

        return {
            "expected_delay_months": expected_delay_months,
            "time_risk_score": round(time_risk_score, 3)
        }

delay_model = DelayPredictionModel()
