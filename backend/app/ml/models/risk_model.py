import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any
from app.config.logging import logger
from app.ml.models.new_model_loader import prepare_feature_dataframe

PRIMARY_ARTIFACT_PATH = os.path.join(os.path.dirname(__file__), "..", "artifacts", "model_risk_score.joblib")
FALLBACK_ARTIFACT_PATH = os.path.join(os.path.dirname(__file__), "..", "artifacts", "risk_model.joblib")

class OverallRiskModel:
    def __init__(self):
        self.model = None
        self.is_new_pipeline = False
        self.load_or_init()

    def load_or_init(self):
        if os.path.exists(PRIMARY_ARTIFACT_PATH):
            try:
                self.model = joblib.load(PRIMARY_ARTIFACT_PATH)
                self.is_new_pipeline = True
                logger.info("Loaded pre-trained Composite Risk Score Model from model_risk_score.joblib.")
                return
            except Exception as e:
                logger.warning(f"Could not load primary risk model artifact: {e}")

        if os.path.exists(FALLBACK_ARTIFACT_PATH):
            try:
                self.model = joblib.load(FALLBACK_ARTIFACT_PATH)
                self.is_new_pipeline = False
                logger.info("Loaded legacy risk model fallback.")
                return
            except Exception as e:
                logger.warning(f"Could not load fallback risk model: {e}")

    def save(self):
        os.makedirs(os.path.dirname(PRIMARY_ARTIFACT_PATH), exist_ok=True)
        joblib.dump(self.model, PRIMARY_ARTIFACT_PATH)

    def predict_risk_score(self, features: Dict[str, Any]) -> float:
        """
        Returns continuous composite risk score on 0-100 scale.
        """
        df = prepare_feature_dataframe(features)
        if self.model is not None:
            try:
                if self.is_new_pipeline or hasattr(self.model, "named_steps"):
                    score = float(self.model.predict(df)[0])
                    return float(np.clip(score, 0.0, 100.0))
                elif hasattr(self.model, "predict_proba"):
                    from app.services.feature_service import FEATURE_COLUMNS
                    X = np.array([[features.get(col, 0.0) for col in FEATURE_COLUMNS]])
                    probs = self.model.predict_proba(X)[0]
                    prob = float(probs[1]) if len(probs) > 1 else float(probs[0])
                    return float(prob * 100.0)
            except Exception as e:
                logger.warning(f"Prediction error in OverallRiskModel: {e}")

        # Baseline fallback
        gap = float(features.get("physical_financial_gap", 0.0))
        delay = float(features.get("deadline_slip_months", 0.0))
        esc = float(features.get("cost_escalation", 0.0))
        return float(np.clip(25.0 + gap * 0.5 + delay * 1.5 + esc * 40.0, 5.0, 95.0))

    def predict_probability(self, features: Dict[str, Any]) -> float:
        """
        Returns risk probability between 0.0 and 1.0.
        """
        score = self.predict_risk_score(features)
        return float(round(score / 100.0, 3))

    def predict(self, features: Dict[str, Any]) -> Dict[str, float]:
        score = self.predict_risk_score(features)
        return {
            "risk_score": round(score, 2),
            "risk_probability": round(score / 100.0, 3)
        }

risk_model = OverallRiskModel()
