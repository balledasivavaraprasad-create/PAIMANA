"""Terrain Difficulty, Geological Complexity & Seasonal Downtime Analyzer (DSI-08, DSI-09).

Evaluates topological terrain challenges, major civil structural complexities (tunnels,
viaducts, major bridges), and seasonal weather vulnerabilities (monsoons, snowbound winters).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .schemas import ConstraintSeverity, EvidenceStatus, PhysicalContextAnalysis, TerrainType


TERRAIN_DIFFICULTY_WEIGHTS = {
    TerrainType.PLAIN: 1.0,
    TerrainType.ROLLING: 1.15,
    TerrainType.COASTAL: 1.25,
    TerrainType.RIVERINE: 1.35,
    TerrainType.URBAN_CONGESTED: 1.50,
    TerrainType.HILLY: 1.65,
    TerrainType.MOUNTAINOUS: 2.0,
    TerrainType.MIXED: 1.30,
    TerrainType.UNKNOWN: 1.0,
}


class PhysicalContextAnalyzer:
    """Evaluates terrain topology, structural complexity, and seasonal execution windows."""

    def analyze(
        self,
        project_data: Dict[str, Any],
        terrain: Optional[TerrainType] = None,
    ) -> PhysicalContextAnalysis:
        findings: List[str] = []

        phys_dict = project_data.get("physical_context") or {}
        if not isinstance(phys_dict, dict):
            phys_dict = {}

        # Resolve Terrain
        if terrain is None:
            raw_t = str(phys_dict.get("terrain") or project_data.get("terrain") or "").upper()
            terrain = TerrainType.PLAIN
            for t in TerrainType:
                if t.value == raw_t:
                    terrain = t
                    break

        base_difficulty = TERRAIN_DIFFICULTY_WEIGHTS.get(terrain, 1.0)

        # Structural Metrics
        tunnels_km = float(phys_dict.get("tunnels_km") or project_data.get("tunnels_km") or 0.0)
        bridges_km = float(phys_dict.get("bridges_viaducts_km") or project_data.get("viaduct_length_km") or 0.0)
        bridges_count = int(phys_dict.get("complex_structures_count") or project_data.get("major_bridges_count") or 0)
        geo_surprises = phys_dict.get("geological_surprises") or project_data.get("geotechnical_issues") or []
        if isinstance(geo_surprises, str):
            geo_surprises = [geo_surprises]

        # Downtimes
        monsoon_downtime = float(phys_dict.get("seasonal_monsoon_downtime_months") or 0.0)
        winter_downtime = float(phys_dict.get("winter_downtime_months") or 0.0)

        # Automatic estimation of seasonal windows if not explicitly provided
        state = str(project_data.get("state") or project_data.get("location") or "").lower()
        if monsoon_downtime == 0.0:
            if any(h in state for h in ["kerala", "assam", "meghalaya", "goa", "coastal karnataka", "tripura"]):
                monsoon_downtime = 3.5
            elif any(m in state for m in ["odisha", "west bengal", "maharashtra", "chhattisgarh", "bihar"]):
                monsoon_downtime = 2.5
            elif terrain in (TerrainType.HILLY, TerrainType.MOUNTAINOUS):
                monsoon_downtime = 3.0
            else:
                monsoon_downtime = 1.5

        if winter_downtime == 0.0:
            if any(s in state for s in ["ladakh", "jammu", "kashmir", "himachal", "uttarakhand", "sikkim"]):
                winter_downtime = 3.5

        working_window = max(3.0, 12.0 - (monsoon_downtime + winter_downtime))

        # Adjust difficulty multiplier for tunnels and structures
        difficulty = base_difficulty
        if tunnels_km > 5.0:
            difficulty += 0.35
            findings.append(f"Substantial tunneling ({tunnels_km:.1f} km) significantly amplifies subsurface geotechnical risks.")
        elif tunnels_km > 0.0:
            difficulty += 0.15
            findings.append(f"Tunneling scope: {tunnels_km:.1f} km.")

        if bridges_km > 10.0 or bridges_count > 5:
            difficulty += 0.20
            findings.append(f"High structural bridge/viaduct density ({bridges_km:.1f} km / {bridges_count} major structures).")

        if geo_surprises:
            difficulty += 0.25
            findings.append(f"Geological surprises encountered: {', '.join(geo_surprises)}.")

        findings.append(f"Topography classified as {terrain.value} (difficulty index: {difficulty:.2f}x).")
        findings.append(f"Effective working window is constrained to {working_window:.1f} months/year (monsoon: {monsoon_downtime:.1f}m, winter: {winter_downtime:.1f}m).")

        flood_hazard = str(phys_dict.get("flood_hazard_level") or project_data.get("flood_hazard") or "LOW").upper()
        if flood_hazard in ("HIGH", "SEVERE"):
            findings.append(f"High recurring flood and inundation hazard during execution.")

        has_explicit = bool(
            tunnels_km > 0 or bridges_km > 0 or bridges_count > 0 or geo_surprises or
            "terrain" in project_data or "physical_context" in project_data
        )

        return PhysicalContextAnalysis(
            terrain=terrain,
            tunnels_km=tunnels_km,
            bridges_viaducts_km=bridges_km,
            complex_structures_count=bridges_count,
            seasonal_monsoon_downtime_months=monsoon_downtime,
            winter_downtime_months=winter_downtime,
            working_window_months_per_year=working_window,
            geological_surprises=list(geo_surprises),
            flood_hazard_level=flood_hazard,
            terrain_difficulty_factor=round(difficulty, 2),
            findings=findings,
            evidence_status=EvidenceStatus.VERIFIED if has_explicit else EvidenceStatus.INFERRED,
        )
