import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from app.config.logging import logger

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "..", "ml", "artifacts", "paimana_models")

FEATURE_COLUMNS_NUMERIC = [
    'original_cost_cr', 'revised_cost_cr', 'cumulative_expenditure_cr', 'physical_progress_pct', 'cost_overrun_pct',
    'expenditure_original_cost_pct', 'expenditure_revised_cost_pct', 'progress_expenditure_gap_pct', 'project_age_months',
    'planned_duration_months', 'remaining_duration_months', 'remaining_progress_pct', 'schedule_slippage_months',
    'completion_date_revised_flag', 'monthly_progress_change_pct', 'monthly_expenditure_change_cr', 'monthly_revised_cost_change_cr',
    'monthly_cost_growth_pct', 'progress_velocity_pct_per_month', 'expenditure_growth_pct', 'required_progress_velocity_pct_per_month',
    'velocity_gap_pct_points', 'prev_cost_overrun_pct', 'prev_physical_progress_pct', 'prev_completion_revised_flag', 'cost_overrun_trend_1m',
    'progress_trend_1m', 'rolling_progress_velocity_3m', 'rolling_cost_growth_3m', 'rolling_expenditure_growth_3m', 'snapshots_so_far',
    'expected_progress_pct', 'progress_gap_enhanced_pct', 'progress_gap_change_1m', 'expenditure_progress_efficiency_gap',
    'efficiency_gap_change_1m', 'progress_velocity_change_1m', 'expenditure_growth_change_1m'
]
FEATURE_COLUMNS_CATEGORICAL = ['ministry', 'sector', 'state', 'implementing_agency']
ALL_MODEL_FEATURES = FEATURE_COLUMNS_NUMERIC + FEATURE_COLUMNS_CATEGORICAL

# Quantile normalization constants derived from empirical PAIMANA training corpus
QUANTILES = {
    "F_gap": (-52.4231898589, 29.2554568355),
    "F_worsen": (-3.2671010450, 3.8685518085),
    "F_accel": (-20.1194216372, 15.9989198127),
    "P_gap": (-1.0980341122, 50.3798136646),
    "P_vel": (-9.5, 1.3194002726),
    "P_det": (-3.0, 4.2640),
    "trend_vel": (-2.6327672614, 2.1650677089),
    "trend_acc": (-4.2990588631, 4.1709091858),
}

def robust_scale(x: float, qlo: float, qhi: float, clip_lo: Optional[float] = None, clip_hi: Optional[float] = None) -> float:
    if x is None or not np.isfinite(x):
        return 0.5
    if clip_lo is not None and clip_hi is not None:
        x = max(clip_lo, min(clip_hi, x))
    if qhi <= qlo:
        return 0.0
    return float(np.clip((x - qlo) / (qhi - qlo), 0.0, 1.0))

class PaimanaMLEngine:
    def __init__(self):
        self.ready = False
        self.models = {}
        self.calibrators = {}
        self.thresholds = {
            "schedule_risk_1m": 0.34,
            "cost_risk_1m": 0.10,
            "combined_risk_1m": 0.27
        }
        self.feature_importance = {}
        self.load_models()

    def load_models(self):
        try:
            for target in ["cost_risk_1m", "schedule_risk_1m", "combined_risk_1m"]:
                model_path = os.path.join(MODELS_DIR, f"{target}_model.joblib")
                cal_path = os.path.join(MODELS_DIR, f"{target}_platt_calibrator.joblib")
                if os.path.exists(model_path) and os.path.exists(cal_path):
                    self.models[target] = joblib.load(model_path)
                    self.calibrators[target] = joblib.load(cal_path)
                    logger.info(f"Loaded LightGBM model & Platt calibrator for: {target}")
                else:
                    logger.warning(f"Model or calibrator file missing for {target} at {model_path}")

            fi_path = os.path.join(MODELS_DIR, "combined_risk_1m_feature_importance.csv")
            if os.path.exists(fi_path):
                fi_df = pd.read_csv(fi_path)
                self.feature_importance = dict(zip(fi_df['feature'], fi_df['importance']))

            if len(self.models) == 3 and len(self.calibrators) == 3:
                self.ready = True
                logger.info("Paimana ML Engine successfully initialized with all 3 calibrated models.")
        except Exception as e:
            logger.error(f"Failed to initialize Paimana ML Engine: {e}", exc_info=True)

    def is_ready(self) -> bool:
        return self.ready

    def predict_probabilities(self, feature_row: Dict[str, Any]) -> Dict[str, float]:
        """
        Runs inference through the 3 LightGBM models + Platt calibrators.
        """
        if not self.ready:
            # Domain heuristic fallback if models are not loaded
            cost_overrun = float(feature_row.get("cost_overrun_pct", 0.0) or 0.0)
            slip = float(feature_row.get("schedule_slippage_months", 0.0) or 0.0)
            return {
                "schedule_risk_1m": min(1.0, max(0.05, slip / 36.0)),
                "cost_risk_1m": min(1.0, max(0.05, cost_overrun / 40.0)),
                "combined_risk_1m": min(1.0, max(0.05, (slip / 36.0 + cost_overrun / 40.0) / 2.0))
            }

        # Build single-row DataFrame with expected types
        row_dict = {}
        for col in FEATURE_COLUMNS_NUMERIC:
            val = feature_row.get(col, 0.0)
            try:
                row_dict[col] = [float(val) if (val is not None and not np.isnan(float(val))) else 0.0]
            except (ValueError, TypeError):
                row_dict[col] = [0.0]

        for col in FEATURE_COLUMNS_CATEGORICAL:
            val = feature_row.get(col, "Unknown")
            row_dict[col] = [str(val) if val is not None else "Unknown"]

        X = pd.DataFrame(row_dict)[ALL_MODEL_FEATURES]
        for c in FEATURE_COLUMNS_CATEGORICAL:
            X[c] = X[c].astype('category')

        probs = {}
        for target in ["cost_risk_1m", "schedule_risk_1m", "combined_risk_1m"]:
            raw = self.models[target].predict_proba(X)[:, 1]
            calibrated = self.calibrators[target].predict_proba(raw.reshape(-1, 1))[:, 1]
            probs[target] = float(np.clip(calibrated[0], 0.0, 1.0))

        return probs

    def compute_component_risks(
        self,
        feature_row: Dict[str, Any],
        model_probs: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Computes the 5 component risk vectors: T, C, P, F, and ML_combined.
        """
        T = model_probs.get("schedule_risk_1m", 0.34)
        C = model_probs.get("cost_risk_1m", 0.10)
        ML_comb = model_probs.get("combined_risk_1m", 0.27)

        # Progress Risk (P):
        prog_gap = float(feature_row.get("progress_gap_enhanced_pct", 0.0) or 0.0)
        vel_gap = float(feature_row.get("velocity_gap_pct_points", 0.0) or 0.0)
        vel_chg = float(feature_row.get("progress_velocity_change_1m", 0.0) or 0.0)

        P_gap = robust_scale(prog_gap, QUANTILES["P_gap"][0], QUANTILES["P_gap"][1], -100, 100)
        P_vel = robust_scale(vel_gap, QUANTILES["P_vel"][0], QUANTILES["P_vel"][1], -50, 50)
        P_det = robust_scale(-vel_chg, QUANTILES["P_det"][0], QUANTILES["P_det"][1], -20, 20)
        P = float(np.clip(0.45 * P_gap + 0.35 * P_vel + 0.20 * P_det, 0.0, 1.0))

        # Financial Efficiency Risk (F):
        eff_gap = float(feature_row.get("expenditure_progress_efficiency_gap", 0.0) or 0.0)
        eff_worsen = float(feature_row.get("efficiency_gap_change_1m", 0.0) or 0.0)
        exp_accel = float(feature_row.get("expenditure_growth_change_1m", 0.0) or 0.0)
        phys_prog = float(feature_row.get("physical_progress_pct", 0.0) or 0.0)
        stage = max(0.0, min(1.0, phys_prog / 100.0))

        F_gap = robust_scale(eff_gap, QUANTILES["F_gap"][0], QUANTILES["F_gap"][1], -100, 100)
        F_worsen = robust_scale(eff_worsen, QUANTILES["F_worsen"][0], QUANTILES["F_worsen"][1], -50, 50)
        F_accel = robust_scale(exp_accel, QUANTILES["F_accel"][0], QUANTILES["F_accel"][1], -100, 100)
        F = float(np.clip((0.55 * F_gap + 0.25 * F_worsen + 0.20 * F_accel) * (0.70 + 0.30 * stage), 0.0, 1.0))

        return {
            "T_time_risk": round(T, 4),
            "C_cost_risk": round(C, 4),
            "P_progress_risk": round(P, 4),
            "F_financial_risk": round(F, 4),
            "ML_combined_risk": round(ML_comb, 4)
        }

    def compute_composite_dphis(
        self,
        components: Dict[str, float],
        previous_current_risk: Optional[float] = None,
        previous_velocity: Optional[float] = None,
        snapshots_so_far: int = 1
    ) -> Dict[str, Any]:
        """
        Computes the official PAIMANA DPHIS composite score:
        - Current Risk (30% T + 30% C + 25% P + 10% F + 5% ML_comb)
        - Risk Velocity & Acceleration
        - Emerging Risk (50 + 100 * trend_signal)
        - Final DPHIS (78% Current + 22% Emerging)
        - Risk Tier & Deterioration Flag
        - Confidence Score
        """
        T = components["T_time_risk"]
        C = components["C_cost_risk"]
        P = components["P_progress_risk"]
        F = components["F_financial_risk"]
        ML_comb = components["ML_combined_risk"]

        # Current Risk (0 - 100)
        current_risk = 100.0 * (0.30 * T + 0.30 * C + 0.25 * P + 0.10 * F + 0.05 * ML_comb)
        current_risk = float(np.clip(current_risk, 0.0, 100.0))

        # Risk Velocity & Acceleration
        if previous_current_risk is not None and np.isfinite(previous_current_risk):
            velocity = current_risk - float(previous_current_risk)
        else:
            velocity = 0.0

        if previous_velocity is not None and np.isfinite(previous_velocity):
            acceleration = velocity - float(previous_velocity)
        else:
            acceleration = 0.0

        # Emerging Risk
        trend_vel = robust_scale(velocity, QUANTILES["trend_vel"][0], QUANTILES["trend_vel"][1], -30, 30)
        trend_acc = robust_scale(acceleration, QUANTILES["trend_acc"][0], QUANTILES["trend_acc"][1], -20, 20)
        trend_signal = np.clip((trend_vel - 0.5) * 0.7 + (trend_acc - 0.5) * 0.3, -0.5, 0.5)
        emerging_risk = float(np.clip(50.0 + 100.0 * trend_signal, 0.0, 100.0))

        # Final DPHIS
        dphis = float(np.clip(0.78 * current_risk + 0.22 * emerging_risk, 0.0, 100.0))

        # Risk Tier
        if dphis >= 80.0:
            tier = "Critical"
        elif dphis >= 66.0:
            tier = "High"
        elif dphis >= 50.0:
            tier = "Medium"
        elif dphis >= 33.0:
            tier = "Watch"
        else:
            tier = "Low"

        rapid_deterioration = bool(velocity >= 8.0 or acceleration >= 5.0)

        # Confidence & Data Quality Score
        hist_conf = float(np.clip(1.0 - np.exp(-max(1, snapshots_so_far) / 4.0), 0.0, 1.0))
        data_quality = round(0.65 * hist_conf + 0.35 * 0.95, 3)
        model_agreement = float(1.0 - np.clip(max(T, C, ML_comb) - min(T, C, ML_comb), 0.0, 1.0))
        stability = float(1.0 - np.clip(abs(velocity), 0.0, 20.0) / 20.0)
        confidence = float(np.clip(100.0 * (0.55 * data_quality + 0.30 * model_agreement + 0.15 * stability), 0.0, 100.0))

        # Driver Decomposition
        drivers = [
            {"name": "Critical Path Schedule Variance (T)", "weight": 0.30, "contribution": round(0.30 * T * 100, 1)},
            {"name": "Stochastic Cost Escalation Exposure (C)", "weight": 0.30, "contribution": round(0.30 * C * 100, 1)},
            {"name": "Physical Progress Stagnation Gap (P)", "weight": 0.25, "contribution": round(0.25 * P * 100, 1)},
            {"name": "CapEx Disbursement-Absorption Ratio (F)", "weight": 0.10, "contribution": round(0.10 * F * 100, 1)},
            {"name": "Multi-Model Consistency Cross-Check (ML_comb)", "weight": 0.05, "contribution": round(0.05 * ML_comb * 100, 1)},
        ]
        drivers.sort(key=lambda d: d["contribution"], reverse=True)

        return {
            "dphis": round(dphis, 1),
            "current_risk": round(current_risk, 1),
            "emerging_risk": round(emerging_risk, 1),
            "risk_velocity": round(velocity, 2),
            "risk_acceleration": round(acceleration, 2),
            "risk_tier": tier,
            "rapid_deterioration": rapid_deterioration,
            "data_quality_score": round(data_quality * 100, 1),
            "confidence_score": round(confidence, 1),
            "drivers": drivers
        }

paimana_ml = PaimanaMLEngine()
