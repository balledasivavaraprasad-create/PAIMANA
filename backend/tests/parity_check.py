"""Feature parity: rebuild engineered features from raw CUF fields and compare to the CSV's own columns."""
import json, sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
from paimana_agent import features as F
ref = json.load(open("reference_stats.json"))
df = pd.read_csv(sys.argv[1], low_memory=False, encoding="utf-8-sig")
df["R"] = pd.to_datetime(df.report_month, format="%Y-%m").map(lambda d: d.year * 12 + d.month)
df = df.sort_values(["project_code", "R"])
raw = ["project_code","project_name","ministry","sector","implementing_agency","state","approval_date","start_date",
       "original_completion_date","revised_completion_date","original_cost_cr","revised_cost_cr",
       "cumulative_expenditure_cr","physical_progress_pct"]
cmp_cols = {"expenditure_original_cost_pct":"expenditure_original_cost_pct","project_age_months":"project_age_months",
            "planned_duration_months":"planned_duration_months","progress_expenditure_gap_pct":"progress_expenditure_gap_pct",
            "remaining_progress_pct":"remaining_progress_pct","monthly_progress_change_pct":"monthly_progress_change_pct",
            "monthly_expenditure_change_cr":"monthly_expenditure_change_cr","progress_velocity_pct_per_month":"progress_velocity_pct_per_month",
            "schedule_slippage_months":"schedule_slippage_months","cost_overrun_pct":"cost_overrun_pct"}
rows, skipped = [], 0
sample = df[df.report_month == df.report_month.max()].sample(600, random_state=1)
for _, r in sample.iterrows():
    rec = {k: (None if pd.isna(r[k]) else r[k]) for k in raw}
    hist = df[(df.project_code == r.project_code) & (df.R < r.R)]
    prev = None
    if len(hist):
        h = hist.iloc[-1]
        prev = {"report_index": int(h.R), "physical_progress_pct": h.physical_progress_pct, "cumulative_expenditure_cr": h.cumulative_expenditure_cr}
    try:
        p = F.validate(rec)
    except F.ValidationError:
        skipped += 1; continue
    f = F.build_features(p, ref, prev, r.report_month)
    rows.append((r, f))
print("compared", len(rows), "skipped invalid", skipped)
for mine, theirs in cmp_cols.items():
    a = np.array([f[mine] for _, f in rows], float); b = np.array([r[theirs] for r, _ in rows], float)
    if mine in ("schedule_slippage_months", "cost_overrun_pct"):
        b = np.nan_to_num(b, nan=0.0)
    m = ~np.isnan(a) & ~np.isnan(b) & np.isfinite(b)
    both_nan = (np.isnan(a) & np.isnan(b)).sum()
    err = np.abs(a[m] - b[m])
    print(f"{mine:36s} n={m.sum():4d} within 0.15: {(err<0.15).mean():.3f}  max err {err.max() if len(err) else 0:9.3f}  nan-agree {both_nan}")
