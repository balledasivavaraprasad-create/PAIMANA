from typing import List, Dict, Any

def compute_environmental_features(project: Dict[str, Any], snapshots: List[Dict[str, Any]]) -> Dict[str, float]:
    sector = (project.get("sector", "") or "").lower()
    project_type = (project.get("metadata", {}).get("project_type", "") or "").lower()

    # Base weather stats from snapshots
    rainfalls = []
    wind_speeds = []
    disruptions = 0

    for s in snapshots:
        w = s.get("weather", {}) or {}
        rain = float(w.get("rainfall_mm", 0.0))
        wind = float(w.get("wind_speed_kmh", 0.0))
        if rain > 50.0 or wind > 45.0 or w.get("disruption_flag", False):
            disruptions += 1
        rainfalls.append(rain)
        wind_speeds.append(wind)

    avg_rain = float(sum(rainfalls) / max(1, len(rainfalls))) if rainfalls else 15.0
    avg_wind = float(sum(wind_speeds) / max(1, len(wind_speeds))) if wind_speeds else 12.0

    # Sector specific hazard multipliers
    hazard_score = 0.1
    if "road" in sector or "highway" in sector or "highway" in project_type:
        hazard_score = min(1.0, (avg_rain / 120.0) * 0.7 + (disruptions / 6.0) * 0.3)
    elif "port" in sector or "shipping" in sector or "marine" in project_type:
        hazard_score = min(1.0, (avg_wind / 60.0) * 0.6 + (avg_rain / 100.0) * 0.4)
    elif "rail" in sector or "metro" in sector:
        hazard_score = min(1.0, (avg_rain / 140.0) * 0.5 + (disruptions / 5.0) * 0.5)
    elif "tunnel" in project_type or "mountain" in project_type:
        hazard_score = min(1.0, (avg_rain / 80.0) * 0.8 + (disruptions / 4.0) * 0.4)
    else:
        hazard_score = min(1.0, (avg_rain / 150.0) * 0.5)

    return {
        "avg_rainfall_mm": round(avg_rain, 1),
        "weather_disruption_months": float(disruptions),
        "environmental_hazard_index": round(hazard_score, 3),
    }
