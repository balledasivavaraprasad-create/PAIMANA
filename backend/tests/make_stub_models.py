"""Stand-ins for models 2 and 3 for machines WITHOUT xgboost (same feature columns, sklearn only).
Real deployment uses the trained joblib files; this exists only so the agent can be tested here."""
import json, sys, numpy as np, pandas as pd, joblib
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import HistGradientBoostingRegressor
sys.path.insert(0, ".")
from paimana_agent import features as F

ref = json.load(open("reference_stats.json"))
df = pd.read_csv(sys.argv[1], low_memory=False, encoding="utf-8-sig")
df = df.sort_values("report_month").groupby("project_code").tail(1)
raw = ["project_code","project_name","ministry","sector","implementing_agency","state","approval_date","start_date",
       "original_completion_date","revised_completion_date","original_cost_cr","revised_cost_cr","cumulative_expenditure_cr","physical_progress_pct"]
X, ok = [], []
for _, r in df.iterrows():
    try:
        p = F.validate({k: (None if pd.isna(r[k]) else r[k]) for k in raw})
        X.append(F.build_features(p, ref, None, r.report_month)); ok.append(r.name)
    except F.ValidationError:
        pass
X = pd.DataFrame(X); d = df.loc[ok]
slip = d.schedule_slippage_months.fillna(0).values
cost = d.cost_overrun_pct.fillna(0).values
risk = (0.5 * pd.Series(cost).clip(lower=0).rank(pct=True) + 0.5 * pd.Series(slip).clip(lower=0).rank(pct=True)).values * 100
num_t = ["original_cost_cr","cumulative_expenditure_cr","physical_progress_pct","expenditure_original_cost_pct","project_age_months","planned_duration_months",
 "monthly_progress_change_pct","monthly_expenditure_change_cr","progress_velocity_pct_per_month","expenditure_growth_pct","progress_expenditure_gap_pct",
 "remaining_progress_pct","state_freq","agency_freq","age_to_planned_ratio","burn_rate_ratio","is_mega_project","log_orig_cost","log_expenditure","remaining_work_rate","has_cost_overrun","cost_overrun_pct"]
num_r = [c for c in num_t if c not in ("has_cost_overrun","cost_overrun_pct")] + ["cost_per_pct_progress"]
def fit(cols, y, name):
    pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), ["ministry","sector"]), ("num","passthrough",cols)])
    m = Pipeline([("prep", pre), ("model", HistGradientBoostingRegressor(max_iter=150, learning_rate=0.06, max_depth=4))])
    m.fit(X[cols + ["ministry","sector"]].replace([np.inf,-np.inf],np.nan), y)
    joblib.dump(m, f"tests/stub_{name}.joblib")
fit(num_t, slip, "time_overrun"); fit(num_r, risk, "risk_score")
print("stub models written")
