"""Multi-Attribute Project Profiling (DSI-02).

Extracts and infers comprehensive domain execution profiles from project metadata,
including execution models, terrain difficulties, linear nature, and structural intensities.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

from .schemas import (
    ExecutionModel,
    InfrastructureCategory,
    InfrastructureSector,
    ProjectDomainProfile,
    TerrainType,
)
from .taxonomy import classify_sector, is_linear_infrastructure


MOUNTAINOUS_STATES = {
    "himachal pradesh", "uttarakhand", "jammu & kashmir", "jammu and kashmir",
    "ladakh", "sikkim", "arunachal pradesh", "nagaland", "manipur", "mizoram",
    "meghalaya", "tripura",
}

COASTAL_REGIONS = {
    "goa", "kerala", "coastal karnataka", "andaman", "nicobar", "lakshadweep",
}

URBAN_CONGESTED_CENTERS = {
    "delhi", "mumbai", "bengaluru", "bangalore", "kolkata", "chennai", "hyderabad",
    "pune", "ahmedabad",
}

PLAIN_REGIONS = {
    "punjab", "haryana", "uttar pradesh", "bihar", "rajasthan", "madhya pradesh",
}


def infer_execution_model(data: Dict[str, Any]) -> ExecutionModel:
    """Detects contracting and execution delivery model."""
    raw = str(
        data.get("execution_mode")
        or data.get("contract_type")
        or data.get("mode")
        or data.get("project_mode")
        or data.get("model")
        or ""
    ).strip().upper()

    name_and_desc = f"{data.get('project_name', '')} {data.get('description', '')}".upper()
    combined = f"{raw} {name_and_desc}"

    if "HAM" in combined or "HYBRID ANNUITY" in combined:
        return ExecutionModel.HAM
    if "BOT (TOLL)" in combined or "BOT TOLL" in combined or "BOT-TOLL" in combined:
        return ExecutionModel.BOT_TOLL
    if "BOT (ANNUITY)" in combined or "BOT ANNUITY" in combined or "BOT-ANNUITY" in combined:
        return ExecutionModel.BOT_ANNUITY
    if "EPC" in combined:
        return ExecutionModel.EPC
    if "ITEM RATE" in combined or "BOQ" in combined or "ITEM-RATE" in combined:
        return ExecutionModel.ITEM_RATE
    if "DESIGN BUILD" in combined or "DESIGN-BUILD" in combined:
        return ExecutionModel.DESIGN_BUILD
    if "PPP" in combined or "CONCESSION" in combined:
        return ExecutionModel.PPP_CONCESSION
    if "DEPARTMENTAL" in combined:
        return ExecutionModel.DEPARTMENTAL

    return ExecutionModel.UNKNOWN


def infer_terrain(data: Dict[str, Any], category: InfrastructureCategory) -> TerrainType:
    """Infers terrain topography based on location, state, and physical descriptors."""
    raw_terrain = str(data.get("terrain") or "").strip().lower()
    if raw_terrain:
        for t in TerrainType:
            if t.value.lower() == raw_terrain:
                return t

    state = str(data.get("state") or data.get("state_name") or data.get("location") or "").lower()
    name = str(data.get("project_name") or "").lower()
    combined = f"{state} {name}"

    if category == InfrastructureCategory.URBAN_TRANSIT or any(u in combined for u in URBAN_CONGESTED_CENTERS):
        return TerrainType.URBAN_CONGESTED

    if any(m in combined for m in MOUNTAINOUS_STATES):
        if any(h in combined for h in ["himalaya", "ghat", "hill", "tunnel", "valley"]):
            return TerrainType.MOUNTAINOUS
        return TerrainType.HILLY

    if any(c in combined for c in COASTAL_REGIONS):
        return TerrainType.COASTAL

    if any(r in combined for r in ["river", "barrage", "canal", "basin", "delta"]):
        return TerrainType.RIVERINE

    if any(p in combined for p in PLAIN_REGIONS):
        return TerrainType.PLAIN

    return TerrainType.PLAIN


def extract_length_km(data: Dict[str, Any]) -> Optional[float]:
    """Extracts project alignment length in kilometers."""
    for key in ["length_km", "length", "route_length", "total_length"]:
        val = data.get(key)
        if val is not None:
            try:
                f = float(val)
                if f > 0:
                    return f
            except (ValueError, TypeError):
                pass

    # Regex extraction from project name (e.g. '4-Laning of NH-44 from km 120 to km 185 (65 km)')
    name = str(data.get("project_name") or "")
    match = re.search(r'(\d+(?:\.\d+)?)\s*(?:km|kms|k\.m\.)\b', name, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except (ValueError, TypeError):
            pass

    return None


def calculate_structural_intensity(
    elevated_ratio: Optional[float],
    underground_ratio: Optional[float],
    tunnels_km: float,
    bridges_count: int,
) -> str:
    """Calculates categorical structural complexity."""
    ug = underground_ratio or 0.0
    el = elevated_ratio or 0.0

    if ug > 0.3 or tunnels_km > 10.0:
        return "VERY_HIGH"
    if ug > 0.0 or el > 0.4 or bridges_count > 10 or tunnels_km > 3.0:
        return "HIGH"
    if el > 0.1 or bridges_count > 2:
        return "MEDIUM"
    return "LOW"


def calculate_seasonal_vulnerability(
    terrain: TerrainType,
    state: str,
) -> str:
    """Assesses vulnerability to seasonal interruptions (monsoon, snowbound winters)."""
    s_clean = state.lower()
    if terrain in (TerrainType.MOUNTAINOUS, TerrainType.HILLY):
        if any(snow in s_clean for snow in ["ladakh", "jammu", "kashmir", "himachal", "uttarakhand"]):
            return "SEVERE"
        return "HIGH"

    if terrain == TerrainType.COASTAL or any(rf in s_clean for rf in ["kerala", "assam", "meghalaya", "goa"]):
        return "HIGH"

    if terrain == TerrainType.RIVERINE:
        return "MEDIUM"

    return "LOW"


class ProjectProfileBuilder:
    """Constructs formal ProjectDomainProfile instances."""

    @staticmethod
    def build_profile(project_data: Dict[str, Any]) -> ProjectDomainProfile:
        code = str(project_data.get("project_code") or project_data.get("code") or "UNKNOWN").strip()
        name = str(project_data.get("project_name") or project_data.get("name") or "Unnamed Project").strip()
        raw_sector = project_data.get("sector")
        agency = project_data.get("agency") or project_data.get("implementing_agency")
        subsector = project_data.get("subsector")

        sector, category, canonical_subsector = classify_sector(
            raw_sector=raw_sector,
            project_name=name,
            agency=agency,
            subsector=subsector,
        )

        execution_model = infer_execution_model(project_data)
        terrain = infer_terrain(project_data, category)
        is_linear = is_linear_infrastructure(sector, category)
        length_km = extract_length_km(project_data)

        # Ratios & structural metrics
        elevated_ratio = None
        if "elevated_ratio" in project_data:
            try:
                elevated_ratio = float(project_data["elevated_ratio"])
            except (ValueError, TypeError):
                pass

        underground_ratio = None
        if "underground_ratio" in project_data:
            try:
                underground_ratio = float(project_data["underground_ratio"])
            except (ValueError, TypeError):
                pass

        tunnels_km = float(project_data.get("tunnels_km") or 0.0)
        bridges_count = int(project_data.get("bridges_count") or project_data.get("major_bridges_count") or 0)

        structural_intensity = calculate_structural_intensity(
            elevated_ratio=elevated_ratio,
            underground_ratio=underground_ratio,
            tunnels_km=tunnels_km,
            bridges_count=bridges_count,
        )

        state = str(project_data.get("state") or project_data.get("location") or "")
        seasonal_vulnerability = calculate_seasonal_vulnerability(terrain, state)

        # Land intensity
        if is_linear and length_km and length_km > 50.0:
            land_intensity = "CRITICAL"
        elif is_linear:
            land_intensity = "HIGH"
        elif category in (InfrastructureCategory.NODAL_FACILITY, InfrastructureCategory.INDUSTRIAL_PLANT):
            land_intensity = "MEDIUM"
        else:
            land_intensity = "LOW"

        return ProjectDomainProfile(
            project_code=code,
            project_name=name,
            sector=sector,
            category=category,
            subsector=canonical_subsector,
            execution_model=execution_model,
            terrain=terrain,
            is_linear=is_linear,
            length_km=length_km,
            elevated_ratio=elevated_ratio,
            underground_ratio=underground_ratio,
            structural_intensity=structural_intensity,
            seasonal_vulnerability=seasonal_vulnerability,
            land_intensity=land_intensity,
            attributes=dict(project_data),
        )
