import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.ensemble import HistGradientBoostingRegressor
import joblib

logger = logging.getLogger(__name__)

# Target transformations for BaggedHGB TransformedTargetRegressor
SHIFT = 100.0

def log_shift(y):
    return np.log1p(np.asarray(y) + SHIFT)

def inv_log_shift(y):
    return np.expm1(y) - SHIFT

class BaggedHGB(BaseEstimator, RegressorMixin):
    """
    Bootstrap-bagged HistGradientBoostingRegressor ensemble with regularized depth,
    early stopping, and target transformation as trained in 01_cost_overrun_model.ipynb.
    """
    def __init__(
        self,
        n_models=12,
        subsample_frac=0.85,
        max_depth=4,
        max_leaf_nodes=20,
        min_samples_leaf=20,
        l2=1.5,
        lr=0.035,
        max_iter=500
    ):
        self.n_models = n_models
        self.subsample_frac = subsample_frac
        self.max_depth = max_depth
        self.max_leaf_nodes = max_leaf_nodes
        self.min_samples_leaf = min_samples_leaf
        self.l2 = l2
        self.lr = lr
        self.max_iter = max_iter
        self.models_ = []

    def fit(self, X, y):
        rng = np.random.RandomState(42)
        self.models_ = []
        n = len(X)
        for i in range(self.n_models):
            idx = rng.choice(n, size=int(n * self.subsample_frac), replace=True)
            Xi = X.iloc[idx] if hasattr(X, "iloc") else X[idx]
            yi = y.iloc[idx] if hasattr(y, "iloc") else y[idx]
            m = HistGradientBoostingRegressor(
                max_iter=self.max_iter,
                learning_rate=self.lr,
                max_depth=self.max_depth,
                max_leaf_nodes=self.max_leaf_nodes,
                min_samples_leaf=self.min_samples_leaf,
                l2_regularization=self.l2,
                early_stopping=True,
                validation_fraction=0.15,
                n_iter_no_change=25,
                random_state=i
            )
            m.fit(Xi, yi)
            self.models_.append(m)
        return self

    def predict(self, X):
        preds = np.column_stack([m.predict(X) for m in self.models_])
        return preds.mean(axis=1)

# Dynamically register into __main__ so joblib unpickles correctly
import __main__
setattr(__main__, "BaggedHGB", BaggedHGB)
setattr(__main__, "log_shift", log_shift)
setattr(__main__, "inv_log_shift", inv_log_shift)
if "__main__" in sys.modules:
    sys.modules["__main__"].BaggedHGB = BaggedHGB
    sys.modules["__main__"].log_shift = log_shift
    sys.modules["__main__"].inv_log_shift = inv_log_shift

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "..", "artifacts")
FREQ_MAPS_PATH = os.path.join(ARTIFACTS_DIR, "freq_maps.json")

# Load frequency maps
STATE_FREQ: Dict[str, float] = {}
AGENCY_FREQ: Dict[str, float] = {}
if os.path.exists(FREQ_MAPS_PATH):
    try:
        with open(FREQ_MAPS_PATH, "r") as f:
            data = json.load(f)
            STATE_FREQ = data.get("state_freq", {})
            AGENCY_FREQ = data.get("agency_freq", {})
    except Exception as e:
        logger.warning(f"Could not load freq_maps.json: {e}")

def prepare_feature_dataframe(data: Dict[str, Any]) -> pd.DataFrame:
    """
    Extracts and standardizes the 24 required features from any project document,
    feature dictionary, or snapshot for the 3 new PAIMANA ML models.
    """
    # 1. Financial features
    orig_cost = float(
        data.get("original_cost_cr")
        or (data.get("cost", {}).get("original") if isinstance(data.get("cost"), dict) else None)
        or 1000.0
    )
    rev_cost = float(
        data.get("revised_cost_cr")
        or (data.get("cost", {}).get("revised") if isinstance(data.get("cost"), dict) else None)
        or orig_cost
    )
    cum_exp = float(
        data.get("cumulative_expenditure_cr")
        or data.get("cumulative_expenditure")
        or (orig_cost * 0.40)
    )
    phys_prog = float(
        data.get("physical_progress_pct")
        or data.get("physical_progress")
        or data.get("current_physical_progress")
        or 40.0
    )

    planned_dur = float(data.get("planned_duration_months") or 36.0)
    age = float(data.get("project_age_months") or 18.0)
    rem_dur = max(1.0, float(data.get("remaining_duration_months") or (planned_dur - age)))
    rem_prog = max(0.0, 100.0 - phys_prog)

    exp_orig_pct = float(
        data.get("expenditure_original_cost_pct")
        or ((cum_exp / max(1.0, orig_cost)) * 100.0)
    )

    cost_overrun_pct = float(
        data.get("cost_overrun_pct")
        or (data.get("cost_escalation", 0.0) * 100.0)
        or max(0.0, (rev_cost - orig_cost) / max(1.0, orig_cost) * 100.0)
    )

    slippage = float(
        data.get("schedule_slippage_months")
        or data.get("deadline_slip_months")
        or 0.0
    )

    # State & Agency frequencies
    state_name = str(data.get("state") or "")
    agency_name = str(data.get("implementing_agency") or data.get("department") or "")
    s_freq = float(data.get("state_freq") or STATE_FREQ.get(state_name, 0.04))
    a_freq = float(data.get("agency_freq") or AGENCY_FREQ.get(agency_name, 0.04))

    monthly_prog_chg = float(
        data.get("monthly_progress_change_pct")
        or (phys_prog / max(1.0, age))
    )
    monthly_exp_chg = float(
        data.get("monthly_expenditure_change_cr")
        or (cum_exp / max(1.0, age))
    )
    prog_velocity = float(
        data.get("progress_velocity_pct_per_month")
        or data.get("progress_velocity")
        or (phys_prog / max(1.0, age))
    )
    exp_growth = float(data.get("expenditure_growth_pct") or 2.5)

    prog_exp_gap = float(
        data.get("progress_expenditure_gap_pct")
        or data.get("physical_financial_gap")
        or (exp_orig_pct - phys_prog)
    )

    # Engineering domain variables
    age_to_planned_ratio = float(np.clip(age / (planned_dur + 1.0), -5.0, 20.0))
    burn_rate_ratio = float(np.clip(exp_orig_pct / (phys_prog + 1.0), -5.0, 50.0))
    is_mega = 1.0 if orig_cost >= 1000.0 else 0.0
    log_orig = float(np.log1p(max(0.0, orig_cost)))
    log_exp = float(np.log1p(max(0.0, cum_exp)))
    cost_per_pct = float(np.clip(cum_exp / (phys_prog + 1.0), 0.0, 10000.0))
    rem_work_rate = float(np.clip(rem_prog / (rem_dur + 1.0), 0.0, 100.0))

    row = {
        "ministry": str(data.get("ministry") or "Road Transport"),
        "sector": str(data.get("sector") or "Roads & Highways"),
        "original_cost_cr": orig_cost,
        "cumulative_expenditure_cr": cum_exp,
        "physical_progress_pct": phys_prog,
        "expenditure_original_cost_pct": exp_orig_pct,
        "project_age_months": age,
        "planned_duration_months": planned_dur,
        "monthly_progress_change_pct": monthly_prog_chg,
        "monthly_expenditure_change_cr": monthly_exp_chg,
        "progress_velocity_pct_per_month": prog_velocity,
        "expenditure_growth_pct": exp_growth,
        "progress_expenditure_gap_pct": prog_exp_gap,
        "remaining_progress_pct": rem_prog,
        "state_freq": s_freq,
        "agency_freq": a_freq,
        "age_to_planned_ratio": age_to_planned_ratio,
        "burn_rate_ratio": burn_rate_ratio,
        "is_mega_project": is_mega,
        "log_orig_cost": log_orig,
        "log_expenditure": log_exp,
        "cost_per_pct_progress": cost_per_pct,
        "remaining_work_rate": rem_work_rate,
        "has_time_slippage": 1.0 if slippage > 0 else 0.0,
        "schedule_slippage_months": slippage,
        "has_cost_overrun": 1.0 if cost_overrun_pct > 0 else 0.0,
        "cost_overrun_pct": cost_overrun_pct
    }
    return pd.DataFrame([row])
