from typing import Dict, Any

# State infrastructure execution indices (based on historical state execution velocity)
STATE_EXECUTION_INDEX = {
    "Gujarat": 0.88,
    "Maharashtra": 0.82,
    "Tamil Nadu": 0.80,
    "Karnataka": 0.78,
    "Uttar Pradesh": 0.72,
    "Rajasthan": 0.70,
    "Andhra Pradesh": 0.69,
    "Telangana": 0.74,
    "Madhya Pradesh": 0.68,
    "West Bengal": 0.62,
    "Bihar": 0.58,
    "Assam": 0.55,
    "Odisha": 0.65,
    "Jharkhand": 0.57,
}

def compute_geospatial_features(project: Dict[str, Any]) -> Dict[str, float]:
    state = project.get("state", "Uttar Pradesh")
    loc = project.get("location", {})
    lat = float(loc.get("latitude", 20.5937))
    lng = float(loc.get("longitude", 78.9629))

    state_factor = STATE_EXECUTION_INDEX.get(state, 0.70)
    # Terrain roughness approximation from coordinates
    terrain_elevation = 150.0
    if lat > 28.0 and lng > 75.0:  # Northern Himalayan belt
        terrain_elevation = 850.0
    elif lng > 88.0:  # North-East
        terrain_elevation = 500.0

    return {
        "state_execution_index": state_factor,
        "latitude": lat,
        "longitude": lng,
        "terrain_elevation_m": terrain_elevation,
    }
