from typing import List, Dict, Any

def compute_financial_features(project: Dict[str, Any], snapshots: List[Dict[str, Any]]) -> Dict[str, float]:
    cost = project.get("cost", {})
    orig = float(cost.get("original", 1.0) or 1.0)
    rev = float(cost.get("revised", orig) or orig)

    cost_escalation = max(0.0, (rev - orig) / max(1.0, orig))

    if not snapshots:
        return {
            "cost_escalation": cost_escalation,
            "expenditure_ratio": 0.0,
            "monthly_burn_rate": 0.0,
            "cost_acceleration": 0.0,
        }

    # Sort snapshots chronologically
    sorted_snaps = sorted(snapshots, key=lambda x: x.get("snapshot_date", ""))
    latest = sorted_snaps[-1]
    cum_exp = float(latest.get("cumulative_expenditure", 0.0))
    expenditure_ratio = min(2.0, cum_exp / max(1.0, rev))

    # Monthly burn rate from consecutive snapshots
    burn_rates = []
    for i in range(1, len(sorted_snaps)):
        delta_exp = float(sorted_snaps[i].get("cumulative_expenditure", 0.0)) - float(sorted_snaps[i-1].get("cumulative_expenditure", 0.0))
        burn_rates.append(max(0.0, delta_exp))

    avg_burn = float(sum(burn_rates) / max(1, len(burn_rates))) if burn_rates else 0.0

    # Cost acceleration
    cost_accel = 0.0
    if len(burn_rates) >= 2:
        cost_accel = burn_rates[-1] - burn_rates[-2]

    return {
        "cost_escalation": round(cost_escalation, 4),
        "expenditure_ratio": round(expenditure_ratio, 4),
        "monthly_burn_rate": round(avg_burn, 2),
        "cost_acceleration": round(cost_accel, 2),
    }
