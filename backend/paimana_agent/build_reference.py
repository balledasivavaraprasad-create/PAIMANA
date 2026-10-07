"""Build reference_stats.json from Paimana.csv (run once, or after retraining).

Reproduces the training-time statistics the notebooks computed on the
latest-snapshot-per-project table: state/agency frequency encodings and the
sorted cost-overrun / slippage arrays used for the percentile-rank risk score.
"""
import json, sys
import numpy as np, pandas as pd


def build(csv_path: str, out_path: str) -> dict:
    df = pd.read_csv(csv_path, low_memory=False, encoding="utf-8-sig")
    df["report_month"] = pd.to_datetime(df["report_month"], format="%Y-%m")
    df = df.sort_values("report_month").groupby("project_code", as_index=False).tail(1)
    cost_o = df["cost_overrun_pct"].fillna(0).clip(lower=0)
    time_o = df["schedule_slippage_months"].fillna(0).clip(lower=0)
    sector_stats = {}
    for s, g in df.groupby("sector"):
        s_cost = g["cost_overrun_pct"].fillna(0).clip(lower=0)
        s_time = g["schedule_slippage_months"].fillna(0).clip(lower=0)
        sector_stats[s] = {
            "n_projects": int(len(g)),
            "cost_overrun_freq_pct": round(float((s_cost > 0).mean() * 100), 1),
            "cost_overrun_pct_mean": round(float(s_cost.mean()), 1),
            "slippage_freq_pct": round(float((s_time > 0).mean() * 100), 1),
            "slippage_months_median": round(float(s_time.median()), 1),
            "slippage_months_mean": round(float(s_time.mean()), 1),
        }

    ref = {
        "n_projects": int(len(df)),
        "state_freq": df["state"].value_counts(normalize=True).to_dict(),
        "agency_freq": df["implementing_agency"].value_counts(normalize=True).to_dict(),
        "cost_overrun_sorted": np.sort(cost_o.values).round(4).tolist(),
        "slippage_sorted": np.sort(time_o.values).round(4).tolist(),
        "ministries": sorted(df["ministry"].dropna().unique().tolist()),
        "sectors": sorted(df["sector"].dropna().unique().tolist()),
        "sector_stats": sector_stats,
    }
    with open(out_path, "w") as f:
        json.dump(ref, f)
    return ref


if __name__ == "__main__":
    r = build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "reference_stats.json")
    print("reference built for", r["n_projects"], "projects")
