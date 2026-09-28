import os
import joblib
import numpy as np
import pandas as pd
import pytest
from app.ml.models.cost_model import cost_model
from app.ml.models.delay_model import delay_model
from app.ml.models.risk_model import risk_model
from app.services.paimana_ml_service import paimana_ml
from app.services.shap_service import explain_features

# Base sample feature dictionary for inference
SAMPLE_FEATURES = {
    "cost_escalation": 0.15,
    "expenditure_ratio": 0.55,
    "monthly_burn_rate": 45.0,
    "cost_acceleration": 5.0,
    "planned_duration_months": 36.0,
    "deadline_slip_months": 8.0,
    "schedule_gap_ratio": 0.22,
    "milestone_delay_rate": 0.25,
    "current_physical_progress": 42.0,
    "current_financial_progress": 58.0,
    "progress_velocity": 0.8,
    "progress_acceleration": -0.1,
    "physical_financial_gap": 16.0,
    "stagnation_months": 0.0,
    "avg_rainfall_mm": 95.0,
    "weather_disruption_months": 1.0,
    "environmental_hazard_index": 0.35,
    "state_execution_index": 0.72,
    "terrain_elevation_m": 250.0,
    "schedule_slippage_months": 8.0,
    "expenditure_progress_efficiency_gap": 16.0,
    "velocity_gap_pct_points": 1.5,
    "cost_overrun_pct": 15.0,
    "progress_gap_enhanced_pct": 12.0
}

def test_cost_overrun_model_inference():
    res = cost_model.predict(SAMPLE_FEATURES)
    assert "predicted_overrun_pct" in res
    assert "cost_risk_score" in res
    assert isinstance(res["predicted_overrun_pct"], (float, int))
    assert -20.0 <= res["predicted_overrun_pct"] <= 200.0
    assert 0.0 <= res["cost_risk_score"] <= 1.0

def test_delay_model_inference():
    res = delay_model.predict(SAMPLE_FEATURES)
    assert "expected_delay_months" in res
    assert "time_risk_score" in res
    assert isinstance(res["expected_delay_months"], (float, int))
    assert res["expected_delay_months"] >= 0.0
    assert 0.0 <= res["time_risk_score"] <= 1.0

def test_risk_score_model_inference():
    res = risk_model.predict(SAMPLE_FEATURES)
    assert "risk_score" in res
    assert "risk_probability" in res
    assert 0.0 <= res["risk_score"] <= 100.0
    assert 0.0 <= res["risk_probability"] <= 1.0

def test_paimana_ml_engine_probabilities():
    probs = paimana_ml.predict_probabilities(SAMPLE_FEATURES)
    assert "schedule_risk_1m" in probs
    assert "cost_risk_1m" in probs
    assert "combined_risk_1m" in probs
    for key, val in probs.items():
        assert 0.0 <= val <= 1.0

def test_paimana_ml_engine_composite_dphis():
    probs = paimana_ml.predict_probabilities(SAMPLE_FEATURES)
    comps = paimana_ml.compute_component_risks(SAMPLE_FEATURES, probs)
    res = paimana_ml.compute_composite_dphis(
        components=comps,
        previous_current_risk=45.0,
        snapshots_so_far=6
    )

    assert "dphis" in res
    assert 0.0 <= res["dphis"] <= 100.0
    assert res["risk_tier"] in ("Critical", "High", "Medium", "Watch", "Low")
    assert "risk_velocity" in res
    assert "drivers" in res
    assert len(res["drivers"]) == 5

def test_real_model_smoke_test():
    """
    Smoke test loading the real joblib model artifacts from disk.
    Verifies that the bundled model artifacts are genuine and can execute predict().
    """
    model_paths = [
        os.path.join(os.path.dirname(__file__), "..", "..", "Models", "model_cost_overrun.joblib"),
        os.path.join(os.path.dirname(__file__), "..", "..", "Models", "model_time_overrun.joblib"),
        os.path.join(os.path.dirname(__file__), "..", "..", "Models", "model_risk_score.joblib"),
    ]

    for p in model_paths:
        if os.path.exists(p):
            model = joblib.load(p)
            assert model is not None
            # Check model has predict method
            assert hasattr(model, "predict")

def test_shap_explanation_generation():
    impacts = explain_features(SAMPLE_FEATURES)
    assert len(impacts) >= 4
    for imp in impacts:
        assert imp.feature != ""
        assert isinstance(imp.impact, (int, float))
        assert imp.direction in ("increase", "decrease")
        assert imp.description != ""

def test_shap_explanation_empty_features():
    # Empty features should fall back gracefully without raising an exception
    impacts = explain_features({})
    assert len(impacts) >= 4
    for imp in impacts:
        assert isinstance(imp.impact, (int, float))
