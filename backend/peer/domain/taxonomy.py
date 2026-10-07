"""Hierarchical Infrastructure Taxonomy & Classification (DSI-01).

Maps raw sector strings, agency acronyms, project names, and department tags to formal
InfrastructureSector and InfrastructureCategory classifications.
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

from .schemas import InfrastructureCategory, InfrastructureSector


SECTOR_KEYWORDS = {
    InfrastructureSector.ROADS_HIGHWAYS: [
        "road", "highway", "expressway", "nhai", "morth", "nhidcl", "pwd", "bypass",
        "flyover", "ring road", "corridor", "four laning", "six laning", "widening",
        "state highway", "national highway"
    ],
    InfrastructureSector.RAILWAYS: [
        "rail", "railway", "rvnl", "dfccil", "ircon", "crb", "doubling", "tripling",
        "gauge conversion", "electrification", "freight corridor", "dedicated freight",
        "station redevelopment", "zonal railway"
    ],
    InfrastructureSector.URBAN_METRO: [
        "metro", "dmrc", "bmrcl", "mmrda", "cmrl", "kmrl", "upmrc", "maha metro",
        "rapid transit", "mrt", "monorail", "light rail", "subway", "urban rail", "rrtc"
    ],
    InfrastructureSector.POWER_ENERGY: [
        "power", "thermal", "hydro", "solar", "wind", "transmission", "substation",
        "ntpc", "nhpc", "pgcil", "powergrid", "discom", "transco", "grid", "reactor",
        "nuclear", "generation", "renewable"
    ],
    InfrastructureSector.WATER_RESOURCES: [
        "dam", "canal", "irrigation", "water supply", "barrage", "drinking water",
        "cwc", "jal shakti", "weir", "reservoir", "river basin", "lift irrigation"
    ],
    InfrastructureSector.PORTS_SHIPPING: [
        "port", "harbour", "shipping", "berth", "jetty", "sagarmala", "dock",
        "terminal", "waterway", "inland waterway", "dredging"
    ],
    InfrastructureSector.AIRPORTS: [
        "airport", "runway", "aai", "aerodrome", "airfield", "terminal building",
        "aviation", "airside", "city side"
    ],
    InfrastructureSector.PETROLEUM_GAS: [
        "petroleum", "gas", "pipeline", "refinery", "iocl", "bpcl", "hpcl", "gail",
        "ongc", "oil", "lng", "lpg", "city gas"
    ],
    InfrastructureSector.TELECOM: [
        "telecom", "optical fiber", "ofc", "bsnl", "bharatnet", "tower", "cellular",
        "broadband", "network"
    ],
    InfrastructureSector.BUILDINGS_URBAN: [
        "building", "housing", "hospital", "aiims", "iit", "iim", "campus", "court",
        "secretariat", "urban development", "smart city", "commercial complex"
    ],
}

AGENCY_MAPPINGS = {
    "nhai": (InfrastructureSector.ROADS_HIGHWAYS, InfrastructureCategory.LINEAR_TRANSPORT),
    "morth": (InfrastructureSector.ROADS_HIGHWAYS, InfrastructureCategory.LINEAR_TRANSPORT),
    "nhidcl": (InfrastructureSector.ROADS_HIGHWAYS, InfrastructureCategory.LINEAR_TRANSPORT),
    "rvnl": (InfrastructureSector.RAILWAYS, InfrastructureCategory.LINEAR_TRANSPORT),
    "dfccil": (InfrastructureSector.RAILWAYS, InfrastructureCategory.LINEAR_TRANSPORT),
    "ircon": (InfrastructureSector.RAILWAYS, InfrastructureCategory.LINEAR_TRANSPORT),
    "dmrc": (InfrastructureSector.URBAN_METRO, InfrastructureCategory.URBAN_TRANSIT),
    "bmrcl": (InfrastructureSector.URBAN_METRO, InfrastructureCategory.URBAN_TRANSIT),
    "mmrda": (InfrastructureSector.URBAN_METRO, InfrastructureCategory.URBAN_TRANSIT),
    "kmrl": (InfrastructureSector.URBAN_METRO, InfrastructureCategory.URBAN_TRANSIT),
    "ntpc": (InfrastructureSector.POWER_ENERGY, InfrastructureCategory.INDUSTRIAL_PLANT),
    "nhpc": (InfrastructureSector.POWER_ENERGY, InfrastructureCategory.HEAVY_CIVIL_WATER),
    "pgcil": (InfrastructureSector.POWER_ENERGY, InfrastructureCategory.LINEAR_ENERGY),
    "powergrid": (InfrastructureSector.POWER_ENERGY, InfrastructureCategory.LINEAR_ENERGY),
    "aai": (InfrastructureSector.AIRPORTS, InfrastructureCategory.NODAL_FACILITY),
    "gail": (InfrastructureSector.PETROLEUM_GAS, InfrastructureCategory.LINEAR_ENERGY),
    "iocl": (InfrastructureSector.PETROLEUM_GAS, InfrastructureCategory.INDUSTRIAL_PLANT),
    "ongc": (InfrastructureSector.PETROLEUM_GAS, InfrastructureCategory.INDUSTRIAL_PLANT),
    "cwc": (InfrastructureSector.WATER_RESOURCES, InfrastructureCategory.HEAVY_CIVIL_WATER),
}

CATEGORY_DEFAULT_MAPPING = {
    InfrastructureSector.ROADS_HIGHWAYS: InfrastructureCategory.LINEAR_TRANSPORT,
    InfrastructureSector.RAILWAYS: InfrastructureCategory.LINEAR_TRANSPORT,
    InfrastructureSector.URBAN_METRO: InfrastructureCategory.URBAN_TRANSIT,
    InfrastructureSector.POWER_ENERGY: InfrastructureCategory.INDUSTRIAL_PLANT,
    InfrastructureSector.WATER_RESOURCES: InfrastructureCategory.HEAVY_CIVIL_WATER,
    InfrastructureSector.PORTS_SHIPPING: InfrastructureCategory.NODAL_FACILITY,
    InfrastructureSector.AIRPORTS: InfrastructureCategory.NODAL_FACILITY,
    InfrastructureSector.TELECOM: InfrastructureCategory.LINEAR_ENERGY,
    InfrastructureSector.PETROLEUM_GAS: InfrastructureCategory.LINEAR_ENERGY,
    InfrastructureSector.BUILDINGS_URBAN: InfrastructureCategory.GENERAL_CIVIL,
    InfrastructureSector.OTHER: InfrastructureCategory.GENERAL_CIVIL,
}


def classify_sector(
    raw_sector: Optional[str] = None,
    project_name: Optional[str] = None,
    agency: Optional[str] = None,
    subsector: Optional[str] = None,
) -> Tuple[InfrastructureSector, InfrastructureCategory, str]:
    """Classifies a project into formal sector, category, and canonical subsector."""
    text_pool = f"{raw_sector or ''} {project_name or ''} {agency or ''} {subsector or ''}".lower()

    # 1. Direct Agency Check
    if agency:
        clean_agency = agency.strip().lower()
        for ag_key, (sec, cat) in AGENCY_MAPPINGS.items():
            if ag_key in clean_agency:
                sub = subsector or raw_sector or sec.value
                return sec, cat, str(sub).strip().title()

    # 2. Strict Keyword Priority Check (Metro takes precedence over generic rail)
    if any(k in text_pool for k in ["metro", "dmrc", "bmrcl", "mmrda", "rapid transit", "monorail"]):
        return InfrastructureSector.URBAN_METRO, InfrastructureCategory.URBAN_TRANSIT, "Urban Metro Rail"

    # 3. Keyword Pattern Matching
    for sector, keywords in SECTOR_KEYWORDS.items():
        for kw in keywords:
            # Word boundary regex search to avoid substring collisions
            if re.search(r'\b' + re.escape(kw) + r'\b', text_pool):
                cat = CATEGORY_DEFAULT_MAPPING.get(sector, InfrastructureCategory.GENERAL_CIVIL)
                # Refine power transmission vs plant
                if sector == InfrastructureSector.POWER_ENERGY:
                    if any(tx in text_pool for tx in ["transmission", "substation", "grid", "line"]):
                        cat = InfrastructureCategory.LINEAR_ENERGY
                    elif any(hy in text_pool for hy in ["hydro", "dam", "barrage"]):
                        cat = InfrastructureCategory.HEAVY_CIVIL_WATER
                sub = subsector or kw.title()
                return sector, cat, str(sub).strip()

    # 4. Fallback Default
    fallback_sec = InfrastructureSector.OTHER
    if raw_sector:
        rs_lower = raw_sector.lower()
        if "road" in rs_lower or "highway" in rs_lower:
            fallback_sec = InfrastructureSector.ROADS_HIGHWAYS
        elif "rail" in rs_lower:
            fallback_sec = InfrastructureSector.RAILWAYS
        elif "power" in rs_lower:
            fallback_sec = InfrastructureSector.POWER_ENERGY

    cat = CATEGORY_DEFAULT_MAPPING.get(fallback_sec, InfrastructureCategory.GENERAL_CIVIL)
    return fallback_sec, cat, str(subsector or raw_sector or "General").strip()


def is_linear_infrastructure(sector: InfrastructureSector, category: InfrastructureCategory) -> bool:
    """Returns True if the project is linear infrastructure with sequential right-of-way dependencies."""
    if category in (InfrastructureCategory.LINEAR_TRANSPORT, InfrastructureCategory.LINEAR_ENERGY):
        return True
    return sector in (
        InfrastructureSector.ROADS_HIGHWAYS,
        InfrastructureSector.RAILWAYS,
        InfrastructureSector.PETROLEUM_GAS,
        InfrastructureSector.TELECOM,
    )
