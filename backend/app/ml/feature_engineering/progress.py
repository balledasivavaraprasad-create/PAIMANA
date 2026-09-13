from typing import List, Dict, Any

def compute_progress_features(snapshots: List[Dict[str, Any]]) -> Dict[str, float]:
    if not snapshots:
        return {
            "current_physical_progress": 0.0,
            "current_financial_progress": 0.0,
            "progress_velocity": 0.0,
            "progress_acceleration": 0.0,
            "physical_financial_gap": 0.0,
            "stagnation_months": 0.0,
        }

    sorted_snaps = sorted(snapshots, key=lambda x: x.get("snapshot_date", ""))
    latest = sorted_snaps[-1]

    curr_phys = float(latest.get("physical_progress", 0.0))
    curr_fin = float(latest.get("financial_progress", 0.0))
    pfd = round(curr_fin - curr_phys, 2)

    # Velocities between monthly snapshots
    velocities = []
    stagnation_count = 0
    for i in range(1, len(sorted_snaps)):
        delta_p = float(sorted_snaps[i].get("physical_progress", 0.0)) - float(sorted_snaps[i-1].get("physical_progress", 0.0))
        velocities.append(delta_p)
        if delta_p < 0.5:
            stagnation_count += 1
        else:
            stagnation_count = 0  # consecutive count

    progress_velocity = velocities[-1] if velocities else 0.0
    progress_accel = (velocities[-1] - velocities[-2]) if len(velocities) >= 2 else 0.0

    return {
        "current_physical_progress": round(curr_phys, 2),
        "current_financial_progress": round(curr_fin, 2),
        "progress_velocity": round(progress_velocity, 3),
        "progress_acceleration": round(progress_accel, 3),
        "physical_financial_gap": pfd,
        "stagnation_months": float(stagnation_count),
    }
