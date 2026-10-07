"""Domain Schemas & Data Contracts for PAIMANA Domain-Specific Intelligence (DSI-01 to DSI-14).

Defines formal contracts for:
- Infrastructure taxonomy & project profile classification
- Land acquisition lifecycle, bottleneck, and progress alignment
- Statutory, environmental, and forest clearance tracking
- Utility shifting, relocation stages, and workfront blockage
- Procurement, contracting models (EPC/HAM/BOT), and tender timelines
- Contract variations, Extensions of Time (EOT), and milestone compliance
- Terrain difficulty, geological complexity, and seasonal/weather windows
- Contractor execution profile, concentration risk, and workfront fragmentation
- Dependency graph modeling (clearances/utilities/land -> workfronts -> milestones)
- Domain-specific peer normalization adjustments
- Non-conflating domain evidence attribution conforming to CONTEXTUALIZES semantics
- Domain-aware investigation planning and tool recommendations
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class InfrastructureSector(str, Enum):
    """Broad infrastructure sector classification."""
    ROADS_HIGHWAYS = "ROADS_HIGHWAYS"
    RAILWAYS = "RAILWAYS"
    URBAN_METRO = "URBAN_METRO"
    POWER_ENERGY = "POWER_ENERGY"
    WATER_RESOURCES = "WATER_RESOURCES"
    PORTS_SHIPPING = "PORTS_SHIPPING"
    AIRPORTS = "AIRPORTS"
    TELECOM = "TELECOM"
    PETROLEUM_GAS = "PETROLEUM_GAS"
    BUILDINGS_URBAN = "BUILDINGS_URBAN"
    OTHER = "OTHER"


class InfrastructureCategory(str, Enum):
    """Functional infrastructure execution category."""
    LINEAR_TRANSPORT = "LINEAR_TRANSPORT"
    URBAN_TRANSIT = "URBAN_TRANSIT"
    HEAVY_CIVIL_WATER = "HEAVY_CIVIL_WATER"
    LINEAR_ENERGY = "LINEAR_ENERGY"
    NODAL_FACILITY = "NODAL_FACILITY"
    INDUSTRIAL_PLANT = "INDUSTRIAL_PLANT"
    GENERAL_CIVIL = "GENERAL_CIVIL"


class ExecutionModel(str, Enum):
    """Commercial contracting and execution delivery model."""
    EPC = "EPC"  # Engineering, Procurement, Construction
    HAM = "HAM"  # Hybrid Annuity Model
    BOT_TOLL = "BOT_TOLL"  # Build-Operate-Transfer (Toll)
    BOT_ANNUITY = "BOT_ANNUITY"  # Build-Operate-Transfer (Annuity)
    ITEM_RATE = "ITEM_RATE"  # Item Rate / BoQ
    DESIGN_BUILD = "DESIGN_BUILD"
    PPP_CONCESSION = "PPP_CONCESSION"
    DEPARTMENTAL = "DEPARTMENTAL"
    UNKNOWN = "UNKNOWN"


class TerrainType(str, Enum):
    """Geographical and topological terrain profile."""
    PLAIN = "PLAIN"
    ROLLING = "ROLLING"
    HILLY = "HILLY"
    MOUNTAINOUS = "MOUNTAINOUS"
    COASTAL = "COASTAL"
    URBAN_CONGESTED = "URBAN_CONGESTED"
    RIVERINE = "RIVERINE"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"


class LandAcquisitionStage(str, Enum):
    """Statutory land acquisition lifecycle stages (e.g. NH Act 1956 / RFCTLARR 2013)."""
    STAGE_3A_INTENT = "STAGE_3A_INTENT"  # Notification of intention
    STAGE_3D_DECLARATION = "STAGE_3D_DECLARATION"  # Declaration of acquisition
    STAGE_3G_COMPENSATION = "STAGE_3G_COMPENSATION"  # Determination of compensation
    STAGE_3H_POSSESSION = "STAGE_3H_POSSESSION"  # Deposit & taking possession
    HANDED_OVER = "HANDED_OVER"  # Encumbrance-free physical handover to contractor
    DISPUTED = "DISPUTED"  # Litigation / court stay / arbitration
    UNKNOWN = "UNKNOWN"


class ClearanceType(str, Enum):
    """Regulatory and environmental clearance categories."""
    ENVIRONMENTAL = "ENVIRONMENTAL"  # MoEF&CC Environmental Clearance (EC)
    FOREST_STAGE_1 = "FOREST_STAGE_1"  # Forest Clearance In-Principle (FC-I)
    FOREST_STAGE_2 = "FOREST_STAGE_2"  # Forest Clearance Final (FC-II)
    WILDLIFE = "WILDLIFE"  # National Board for Wildlife (NBWL)
    COASTAL_REGULATION_ZONE = "COASTAL_REGULATION_ZONE"  # CRZ clearance
    TREE_FELLING = "TREE_FELLING"  # Tree cutting permission
    RAILWAY_SAFETY = "RAILWAY_SAFETY"  # CRS (Commission of Railway Safety) / GAD
    DEFENSE = "DEFENSE"  # Ministry of Defence clearance
    ARCHAEOLOGICAL = "ARCHAEOLOGICAL"  # ASI clearance
    WATER_BODIES = "WATER_BODIES"  # River basin / canal crossing permission
    OTHER = "OTHER"


class ClearanceStatus(str, Enum):
    """Status in the statutory clearance lifecycle."""
    NOT_APPLIED = "NOT_APPLIED"
    SUBMITTED = "SUBMITTED"
    STAGE_1_APPROVED = "STAGE_1_APPROVED"
    IN_PRINCIPLE_APPROVED = "IN_PRINCIPLE_APPROVED"
    FINAL_APPROVED = "FINAL_APPROVED"
    REJECTED = "REJECTED"
    EXEMPTED = "EXEMPTED"
    PENDING_COMPLIANCE = "PENDING_COMPLIANCE"
    UNKNOWN = "UNKNOWN"


class UtilityType(str, Enum):
    """Categories of utilities requiring relocation."""
    ELECTRICAL_HT_EHT = "ELECTRICAL_HT_EHT"  # High Tension / Extra High Tension lines & towers
    ELECTRICAL_LT_DISTRIBUTION = "ELECTRICAL_LT_DISTRIBUTION"  # Low Tension poles/distribution
    WATER_SUPPLY_PIPELINE = "WATER_SUPPLY_PIPELINE"
    SEWERAGE_LINE = "SEWERAGE_LINE"
    GAS_PIPELINE = "GAS_PIPELINE"
    TELECOM_OFC = "TELECOM_OFC"  # Optical Fiber Cables
    DRAINAGE_CANAL = "DRAINAGE_CANAL"
    OTHER = "OTHER"


class UtilityStage(str, Enum):
    """Relocation lifecycle stages for utilities."""
    IDENTIFIED = "IDENTIFIED"
    ESTIMATE_PREPARED = "ESTIMATE_PREPARED"
    ESTIMATE_SANCTIONED = "ESTIMATE_SANCTIONED"
    SUPERVISION_PAID = "SUPERVISION_PAID"
    AGENCY_AWARDED = "AGENCY_AWARDED"
    SHIFTING_IN_PROGRESS = "SHIFTING_IN_PROGRESS"
    SHIFTING_COMPLETED = "SHIFTING_COMPLETED"
    UNKNOWN = "UNKNOWN"


class ConstraintSeverity(str, Enum):
    """Operational impact severity of domain constraint."""
    CRITICAL = "CRITICAL"  # Total blockage of critical path or >50% workfront
    HIGH = "HIGH"  # Severe slowdown, significant package milestone at risk
    MODERATE = "MODERATE"  # Manageable with sequencing, minor delay risk
    LOW = "LOW"  # Non-critical, easily bypassable
    NEGLIGIBLE = "NEGLIGIBLE"  # No noticeable delay impact
    UNKNOWN = "UNKNOWN"


class EvidenceStatus(str, Enum):
    """Provenance and verification status of domain evidence."""
    VERIFIED = "VERIFIED"  # Backed by explicit records and dates
    UNVERIFIED_GAP = "UNVERIFIED_GAP"  # Explicitly missing from records; absence is noted
    INFERRED = "INFERRED"  # Derived from physical progress vs expenditure or secondary indicators
    INCOMPLETE = "INCOMPLETE"  # Partial data exists, confidence restricted


class DependencyNodeType(str, Enum):
    """Type of entity in the execution dependency graph."""
    LAND_PARCEL = "LAND_PARCEL"
    CLEARANCE = "CLEARANCE"
    UTILITY = "UTILITY"
    PACKAGE = "PACKAGE"
    STRUCTURAL_WORKFRONT = "STRUCTURAL_WORKFRONT"
    MILESTONE = "MILESTONE"
    COMMERCIAL = "COMMERCIAL"


class DependencyStatus(str, Enum):
    """Readiness status of a dependency node."""
    SATISFIED = "SATISFIED"
    PENDING = "PENDING"
    BLOCKED = "BLOCKED"
    AT_RISK = "AT_RISK"
    IN_PROGRESS = "IN_PROGRESS"


# ==============================================================================
# Domain Profile & Constraint Schemas
# ==============================================================================

@dataclass
class ProjectDomainProfile:
    """Multi-attribute domain profile for an infrastructure project."""
    project_code: str
    project_name: str
    sector: InfrastructureSector
    category: InfrastructureCategory
    subsector: str = ""
    execution_model: ExecutionModel = ExecutionModel.UNKNOWN
    terrain: TerrainType = TerrainType.UNKNOWN
    is_linear: bool = False
    length_km: Optional[float] = None
    elevated_ratio: Optional[float] = None
    underground_ratio: Optional[float] = None
    structural_intensity: str = "LOW"  # LOW, MEDIUM, HIGH, VERY_HIGH
    seasonal_vulnerability: str = "LOW"  # LOW, MEDIUM, HIGH, SEVERE
    land_intensity: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_code": self.project_code,
            "project_name": self.project_name,
            "sector": self.sector.value,
            "category": self.category.value,
            "subsector": self.subsector,
            "execution_model": self.execution_model.value,
            "terrain": self.terrain.value,
            "is_linear": self.is_linear,
            "length_km": self.length_km,
            "elevated_ratio": self.elevated_ratio,
            "underground_ratio": self.underground_ratio,
            "structural_intensity": self.structural_intensity,
            "seasonal_vulnerability": self.seasonal_vulnerability,
            "land_intensity": self.land_intensity,
            "attributes": self.attributes,
        }


@dataclass
class LandAcquisitionAnalysis:
    """Status and bottleneck evaluation of land acquisition (DSI-05)."""
    required_ha: float = 0.0
    acquired_ha: float = 0.0
    handed_over_ha: float = 0.0
    pending_ha: float = 0.0
    acquisition_pct: float = 0.0
    handover_pct: float = 0.0
    is_critical_bottleneck: bool = False
    bottleneck_severity: ConstraintSeverity = ConstraintSeverity.UNKNOWN
    acquisition_velocity_ha_per_month: Optional[float] = None
    estimated_months_to_complete: Optional[float] = None
    progress_vs_land_gap_pct: float = 0.0
    is_island_working_risk: bool = False
    disputed_patches_count: int = 0
    pending_stages: Dict[str, float] = field(default_factory=dict)
    findings: List[str] = field(default_factory=list)
    evidence_status: EvidenceStatus = EvidenceStatus.UNVERIFIED_GAP

    def to_dict(self) -> Dict[str, Any]:
        return {
            "required_ha": round(self.required_ha, 2),
            "acquired_ha": round(self.acquired_ha, 2),
            "handed_over_ha": round(self.handed_over_ha, 2),
            "pending_ha": round(self.pending_ha, 2),
            "acquisition_pct": round(self.acquisition_pct, 2),
            "handover_pct": round(self.handover_pct, 2),
            "is_critical_bottleneck": self.is_critical_bottleneck,
            "bottleneck_severity": self.bottleneck_severity.value,
            "acquisition_velocity_ha_per_month": round(self.acquisition_velocity_ha_per_month, 2) if self.acquisition_velocity_ha_per_month is not None else None,
            "estimated_months_to_complete": round(self.estimated_months_to_complete, 1) if self.estimated_months_to_complete is not None else None,
            "progress_vs_land_gap_pct": round(self.progress_vs_land_gap_pct, 2),
            "is_island_working_risk": self.is_island_working_risk,
            "disputed_patches_count": self.disputed_patches_count,
            "pending_stages": self.pending_stages,
            "findings": self.findings,
            "evidence_status": self.evidence_status.value,
        }


@dataclass
class ClearanceItem:
    """Individual statutory clearance record."""
    clearance_type: ClearanceType
    name: str
    status: ClearanceStatus
    applied_date: Optional[str] = None
    approval_date: Optional[str] = None
    pending_days: Optional[int] = None
    critical_path: bool = False
    affected_stretch: Optional[str] = None
    affected_cost_cr: Optional[float] = None
    remarks: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clearance_type": self.clearance_type.value,
            "name": self.name,
            "status": self.status.value,
            "applied_date": self.applied_date,
            "approval_date": self.approval_date,
            "pending_days": self.pending_days,
            "critical_path": self.critical_path,
            "affected_stretch": self.affected_stretch,
            "affected_cost_cr": self.affected_cost_cr,
            "remarks": self.remarks,
        }


@dataclass
class EnvironmentalClearanceAnalysis:
    """Status and impact evaluation of statutory clearances (DSI-06)."""
    clearances: List[ClearanceItem] = field(default_factory=list)
    total_clearances_required: int = 0
    approved_count: int = 0
    pending_count: int = 0
    pending_critical_count: int = 0
    forest_land_diverted_ha: float = 0.0
    tree_felling_pending_count: int = 0
    is_clearance_bottleneck: bool = False
    bottleneck_severity: ConstraintSeverity = ConstraintSeverity.UNKNOWN
    findings: List[str] = field(default_factory=list)
    evidence_status: EvidenceStatus = EvidenceStatus.UNVERIFIED_GAP

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clearances": [c.to_dict() for c in self.clearances],
            "total_clearances_required": self.total_clearances_required,
            "approved_count": self.approved_count,
            "pending_count": self.pending_count,
            "pending_critical_count": self.pending_critical_count,
            "forest_land_diverted_ha": round(self.forest_land_diverted_ha, 2),
            "tree_felling_pending_count": self.tree_felling_pending_count,
            "is_clearance_bottleneck": self.is_clearance_bottleneck,
            "bottleneck_severity": self.bottleneck_severity.value,
            "findings": self.findings,
            "evidence_status": self.evidence_status.value,
        }


@dataclass
class UtilityShiftingItem:
    """Individual utility relocation item."""
    utility_type: UtilityType
    identifier: str
    location: str = ""
    stage: UtilityStage = UtilityStage.IDENTIFIED
    estimate_cr: Optional[float] = None
    deposit_paid: bool = False
    blocks_workfront: bool = False
    agency: str = ""
    remarks: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "utility_type": self.utility_type.value,
            "identifier": self.identifier,
            "location": self.location,
            "stage": self.stage.value,
            "estimate_cr": self.estimate_cr,
            "deposit_paid": self.deposit_paid,
            "blocks_workfront": self.blocks_workfront,
            "agency": self.agency,
            "remarks": self.remarks,
        }


@dataclass
class UtilityShiftingAnalysis:
    """Status and bottleneck evaluation of utility relocations (DSI-07)."""
    utilities: List[UtilityShiftingItem] = field(default_factory=list)
    total_utilities: int = 0
    completed_count: int = 0
    pending_count: int = 0
    blocking_workfront_count: int = 0
    completion_pct: float = 0.0
    deposit_paid_pct: float = 0.0
    is_utility_bottleneck: bool = False
    bottleneck_severity: ConstraintSeverity = ConstraintSeverity.UNKNOWN
    findings: List[str] = field(default_factory=list)
    evidence_status: EvidenceStatus = EvidenceStatus.UNVERIFIED_GAP

    def to_dict(self) -> Dict[str, Any]:
        return {
            "utilities": [u.to_dict() for u in self.utilities],
            "total_utilities": self.total_utilities,
            "completed_count": self.completed_count,
            "pending_count": self.pending_count,
            "blocking_workfront_count": self.blocking_workfront_count,
            "completion_pct": round(self.completion_pct, 2),
            "deposit_paid_pct": round(self.deposit_paid_pct, 2),
            "is_utility_bottleneck": self.is_utility_bottleneck,
            "bottleneck_severity": self.bottleneck_severity.value,
            "findings": self.findings,
            "evidence_status": self.evidence_status.value,
        }


@dataclass
class ProcurementAnalysis:
    """Commercial procurement and contracting model intelligence (DSI-03)."""
    execution_model: ExecutionModel = ExecutionModel.UNKNOWN
    tender_notice_date: Optional[str] = None
    award_date: Optional[str] = None
    tender_duration_months: Optional[float] = None
    retender_count: int = 0
    awarded_cost_cr: Optional[float] = None
    sanctioned_cost_cr: Optional[float] = None
    bid_premium_discount_pct: Optional[float] = None
    is_procurement_risk: bool = False
    risk_severity: ConstraintSeverity = ConstraintSeverity.UNKNOWN
    findings: List[str] = field(default_factory=list)
    evidence_status: EvidenceStatus = EvidenceStatus.UNVERIFIED_GAP

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_model": self.execution_model.value,
            "tender_notice_date": self.tender_notice_date,
            "award_date": self.award_date,
            "tender_duration_months": round(self.tender_duration_months, 1) if self.tender_duration_months is not None else None,
            "retender_count": self.retender_count,
            "awarded_cost_cr": self.awarded_cost_cr,
            "sanctioned_cost_cr": self.sanctioned_cost_cr,
            "bid_premium_discount_pct": round(self.bid_premium_discount_pct, 2) if self.bid_premium_discount_pct is not None else None,
            "is_procurement_risk": self.is_procurement_risk,
            "risk_severity": self.risk_severity.value,
            "findings": self.findings,
            "evidence_status": self.evidence_status.value,
        }


@dataclass
class ContractAnalysis:
    """Contractual variation, extension of time (EOT), and milestone compliance (DSI-04)."""
    original_completion_date: Optional[str] = None
    current_completion_date: Optional[str] = None
    eot_granted_months: float = 0.0
    eot_pending_months: float = 0.0
    eot_count: int = 0
    scope_changes_count: int = 0
    cost_revision_cr: float = 0.0
    penalty_liquidated_damages_invoked: bool = False
    is_contractual_risk: bool = False
    risk_severity: ConstraintSeverity = ConstraintSeverity.UNKNOWN
    findings: List[str] = field(default_factory=list)
    evidence_status: EvidenceStatus = EvidenceStatus.UNVERIFIED_GAP

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_completion_date": self.original_completion_date,
            "current_completion_date": self.current_completion_date,
            "eot_granted_months": round(self.eot_granted_months, 1),
            "eot_pending_months": round(self.eot_pending_months, 1),
            "eot_count": self.eot_count,
            "scope_changes_count": self.scope_changes_count,
            "cost_revision_cr": round(self.cost_revision_cr, 2),
            "penalty_liquidated_damages_invoked": self.penalty_liquidated_damages_invoked,
            "is_contractual_risk": self.is_contractual_risk,
            "risk_severity": self.risk_severity.value,
            "findings": self.findings,
            "evidence_status": self.evidence_status.value,
        }


@dataclass
class PhysicalContextAnalysis:
    """Terrain, geological constraints, and seasonal vulnerability (DSI-08, DSI-09)."""
    terrain: TerrainType = TerrainType.UNKNOWN
    tunnels_km: float = 0.0
    bridges_viaducts_km: float = 0.0
    complex_structures_count: int = 0
    seasonal_monsoon_downtime_months: float = 0.0
    winter_downtime_months: float = 0.0
    working_window_months_per_year: float = 12.0
    geological_surprises: List[str] = field(default_factory=list)
    flood_hazard_level: str = "LOW"
    terrain_difficulty_factor: float = 1.0
    findings: List[str] = field(default_factory=list)
    evidence_status: EvidenceStatus = EvidenceStatus.UNVERIFIED_GAP

    def to_dict(self) -> Dict[str, Any]:
        return {
            "terrain": self.terrain.value,
            "tunnels_km": round(self.tunnels_km, 2),
            "bridges_viaducts_km": round(self.bridges_viaducts_km, 2),
            "complex_structures_count": self.complex_structures_count,
            "seasonal_monsoon_downtime_months": round(self.seasonal_monsoon_downtime_months, 1),
            "winter_downtime_months": round(self.winter_downtime_months, 1),
            "working_window_months_per_year": round(self.working_window_months_per_year, 1),
            "geological_surprises": self.geological_surprises,
            "flood_hazard_level": self.flood_hazard_level,
            "terrain_difficulty_factor": round(self.terrain_difficulty_factor, 2),
            "findings": self.findings,
            "evidence_status": self.evidence_status.value,
        }


@dataclass
class ContractorWorkfrontAnalysis:
    """Contractor execution profile, concentration risk, and linear continuity (DSI-10, DSI-11)."""
    contractor_name: str = ""
    contractor_tier: str = "UNKNOWN"
    concurrent_packages_held: int = 1
    concentration_risk: str = "LOW"
    linear_continuity_ratio: float = 1.0  # 1.0 = single continuous stretch, 0.2 = broken into isolated patches
    broken_workfronts_count: int = 0
    average_continuous_stretch_km: Optional[float] = None
    is_fragmented_workfront: bool = False
    findings: List[str] = field(default_factory=list)
    evidence_status: EvidenceStatus = EvidenceStatus.UNVERIFIED_GAP

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contractor_name": self.contractor_name,
            "contractor_tier": self.contractor_tier,
            "concurrent_packages_held": self.concurrent_packages_held,
            "concentration_risk": self.concentration_risk,
            "linear_continuity_ratio": round(self.linear_continuity_ratio, 2),
            "broken_workfronts_count": self.broken_workfronts_count,
            "average_continuous_stretch_km": round(self.average_continuous_stretch_km, 2) if self.average_continuous_stretch_km is not None else None,
            "is_fragmented_workfront": self.is_fragmented_workfront,
            "findings": self.findings,
            "evidence_status": self.evidence_status.value,
        }


# ==============================================================================
# Dependency Graph Contracts (DSI-13)
# ==============================================================================

@dataclass
class DependencyNode:
    """Node in the execution dependency graph."""
    node_id: str
    node_type: DependencyNodeType
    name: str
    status: DependencyStatus = DependencyStatus.PENDING
    critical_path: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "name": self.name,
            "status": self.status.value,
            "critical_path": self.critical_path,
            "metadata": self.metadata,
        }


@dataclass
class DependencyEdge:
    """Directed dependency relation between nodes (source -> target)."""
    source_id: str
    target_id: str
    relation: str = "PREREQUISITE_FOR"
    is_blocking: bool = True
    lag_days: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation,
            "is_blocking": self.is_blocking,
            "lag_days": self.lag_days,
        }


@dataclass
class DependencyGraphReport:
    """Analytical evaluation of the project dependency graph (DSI-13)."""
    nodes: List[DependencyNode] = field(default_factory=list)
    edges: List[DependencyEdge] = field(default_factory=list)
    total_nodes: int = 0
    total_edges: int = 0
    critical_path_nodes: List[str] = field(default_factory=list)
    blocking_nodes: List[str] = field(default_factory=list)
    blocked_milestones: List[str] = field(default_factory=list)
    bottleneck_summary: str = ""
    graph_complexity: str = "LOW"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "total_nodes": self.total_nodes,
            "total_edges": self.total_edges,
            "critical_path_nodes": self.critical_path_nodes,
            "blocking_nodes": self.blocking_nodes,
            "blocked_milestones": self.blocked_milestones,
            "bottleneck_summary": self.bottleneck_summary,
            "graph_complexity": self.graph_complexity,
        }


# ==============================================================================
# Domain Normalization & Investigation Strategy Contracts (DSI-12, DSI-14)
# ==============================================================================

@dataclass
class DomainNormalizationAdjustment:
    """Adjustment rationale and multiplier for peer comparability (DSI-12)."""
    metric_name: str
    raw_target_value: float
    normalized_target_value: float
    adjustment_factor: float
    adjustment_rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "raw_target_value": round(self.raw_target_value, 2),
            "normalized_target_value": round(self.normalized_target_value, 2),
            "adjustment_factor": round(self.adjustment_factor, 3),
            "adjustment_rationale": self.adjustment_rationale,
        }


@dataclass
class InvestigationStrategyRecommendation:
    """Hypothesis-conditioned investigation recommendation (DSI-14)."""
    target_domain: str
    suggested_tool: str
    priority: str
    rationale: str
    specific_questions: List[str] = field(default_factory=list)
    evidence_gaps_to_fill: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_domain": self.target_domain,
            "suggested_tool": self.suggested_tool,
            "priority": self.priority,
            "rationale": self.rationale,
            "specific_questions": self.specific_questions,
            "evidence_gaps_to_fill": self.evidence_gaps_to_fill,
        }


@dataclass
class DomainEvidenceItem:
    """Structured evidence item conforming strictly to CONTEXTUALIZES semantics."""
    claim: str
    domain_factor: str
    evidence_relation: str = "CONTEXTUALIZES"
    evidence_status: EvidenceStatus = EvidenceStatus.UNVERIFIED_GAP
    source_fields: List[str] = field(default_factory=list)
    severity: ConstraintSeverity = ConstraintSeverity.UNKNOWN
    observation: str = ""
    cautionary_note: str = (
        "Domain context contextualizes the operational execution environment; "
        "it does NOT constitute verified sole root-cause without independent causal proof."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim,
            "domain_factor": self.domain_factor,
            "evidence_relation": self.evidence_relation,
            "evidence_status": self.evidence_status.value,
            "source_fields": self.source_fields,
            "severity": self.severity.value,
            "observation": self.observation,
            "cautionary_note": self.cautionary_note,
        }


@dataclass
class DomainContextReport:
    """Master consolidated domain intelligence report (DSI-01 to DSI-14)."""
    project_code: str
    project_name: str
    profile: ProjectDomainProfile
    land_acquisition: Optional[LandAcquisitionAnalysis] = None
    environmental_clearances: Optional[EnvironmentalClearanceAnalysis] = None
    utility_shifting: Optional[UtilityShiftingAnalysis] = None
    procurement: Optional[ProcurementAnalysis] = None
    contract: Optional[ContractAnalysis] = None
    physical_context: Optional[PhysicalContextAnalysis] = None
    contractor_workfront: Optional[ContractorWorkfrontAnalysis] = None
    dependency_graph: Optional[DependencyGraphReport] = None
    normalizations: List[DomainNormalizationAdjustment] = field(default_factory=list)
    investigation_strategies: List[InvestigationStrategyRecommendation] = field(default_factory=list)
    evidence_items: List[Dict[str, Any]] = field(default_factory=list)
    summary_narrative: str = ""
    key_constraints: List[str] = field(default_factory=list)
    data_gaps: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_code": self.project_code,
            "project_name": self.project_name,
            "profile": self.profile.to_dict(),
            "land_acquisition": self.land_acquisition.to_dict() if self.land_acquisition else None,
            "environmental_clearances": self.environmental_clearances.to_dict() if self.environmental_clearances else None,
            "utility_shifting": self.utility_shifting.to_dict() if self.utility_shifting else None,
            "procurement": self.procurement.to_dict() if self.procurement else None,
            "contract": self.contract.to_dict() if self.contract else None,
            "physical_context": self.physical_context.to_dict() if self.physical_context else None,
            "contractor_workfront": self.contractor_workfront.to_dict() if self.contractor_workfront else None,
            "dependency_graph": self.dependency_graph.to_dict() if self.dependency_graph else None,
            "normalizations": [n.to_dict() for n in self.normalizations],
            "investigation_strategies": [s.to_dict() for s in self.investigation_strategies],
            "evidence_items": self.evidence_items,
            "summary_narrative": self.summary_narrative,
            "key_constraints": self.key_constraints,
            "data_gaps": self.data_gaps,
            "execution_time_ms": round(self.execution_time_ms, 2),
        }
