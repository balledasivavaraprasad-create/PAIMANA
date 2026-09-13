import os
import joblib
import numpy as np
import xgboost as xgb
from typing import Dict, Any
from app.services.feature_service import FEATURE_COLUMNS
from app.config.logging import logger

ARTIFACT_PATH = os.path.join(os.path.dirname(__file__), "..", "artifacts", "risk_model.joblib")

class OverallRiskModel:
    def __init__(self):
        self.model = None
        self.load_or_init()

    def load_or_init(self):
        if os.path.exists(ARTIFACT_PATH):
            try:
                self.model = joblib.load(ARTIFACT_PATH)
                logger.info("Loaded pre-trained Risk XGBoost Model.")
                return
            except Exception as e:
                logger.warning(f"Could not load risk model artifact: {e}, initializing baseline.")

        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.08,
            random_state=42
        )

    def save(self):
        os.makedirs(os.path.dirname(ARTIFACT_PATH), exist_ok=True)
        joblib.dump(self.model, ARTIFACT_PATH)

    def predict_probability(self, features: Dict[str, float]) -> float:
        X = np.array([[features.get(col, 0.0) for col in FEATURE_COLUMNS]])
        if hasattr(self.model, "n_features_in_"):
            probs = self.model.predict_proba(X)[0]
            # Probability of high/critical class
            return float(probs[1]) if len(probs) > 1 else float(probs[0])
        else:
            # Baseline domain heuristic risk calculation
            score = (
                features.get("physical_financial_gap", 0.0) * 0.015 +
                features.get("milestone_delay_rate", 0.0) * 0.40 +
                features.get("cost_escalation", 0.0) * 0.30 +
                features.get("environmental_hazard_index", 0.0) * 0.15
            )
            return float(min(1.0, max(0.05, score)))

risk_model = OverallRiskModel()
