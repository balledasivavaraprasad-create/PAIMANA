"""PAIMANA Domain-Specific Intelligence Subsystem (DSI-01 to DSI-14).

Exposes infrastructure taxonomy, multi-attribute project profiling, land acquisition
and right-of-way analysis, statutory clearance tracking, utility relocation monitoring,
commercial procurement/contract variations, physical terrain difficulty, seasonal downtime,
workfront continuity, dependency graph modeling, peer normalizations, and investigation planning.
"""
from __future__ import annotations

from .contract import ContractAnalyzer
from .contractor_workfront import ContractorWorkfrontAnalyzer
from .dependency_graph import DependencyGraphBuilder
from .environmental import EnvironmentalClearanceAnalyzer
from .explanation import DomainExplanationEngine
from .investigation_strategy import InvestigationStrategyPlanner
from .land_acquisition import LandAcquisitionAnalyzer
from .normalization import DomainNormalizationEngine
from .physical_context import PhysicalContextAnalyzer
from .procurement import ProcurementAnalyzer
from .project_profile import ProjectProfileBuilder
from .utility_shifting import UtilityShiftingAnalyzer
from .schemas import (
    ClearanceItem,
    ClearanceStatus,
    ClearanceType,
    ConstraintSeverity,
    ContractAnalysis,
    ContractorWorkfrontAnalysis,
    DependencyEdge,
    DependencyGraphReport,
    DependencyNode,
    DependencyNodeType,
    DependencyStatus,
    DomainContextReport,
    DomainEvidenceItem,
    DomainNormalizationAdjustment,
    EnvironmentalClearanceAnalysis,
    EvidenceStatus,
    ExecutionModel,
    InfrastructureCategory,
    InfrastructureSector,
    InvestigationStrategyRecommendation,
    LandAcquisitionAnalysis,
    LandAcquisitionStage,
    PhysicalContextAnalysis,
    ProcurementAnalysis,
    ProjectDomainProfile,
    TerrainType,
    UtilityShiftingAnalysis,
    UtilityShiftingItem,
    UtilityStage,
    UtilityType,
)
from .service import DomainIntelligenceService
from .taxonomy import classify_sector, is_linear_infrastructure

__all__ = [
    # Master Service
    "DomainIntelligenceService",
    # Profile & Taxonomy
    "ProjectProfileBuilder",
    "classify_sector",
    "is_linear_infrastructure",
    # Domain Analyzers
    "LandAcquisitionAnalyzer",
    "EnvironmentalClearanceAnalyzer",
    "UtilityShiftingAnalyzer",
    "ProcurementAnalyzer",
    "ContractAnalyzer",
    "PhysicalContextAnalyzer",
    "ContractorWorkfrontAnalyzer",
    "DependencyGraphBuilder",
    "DomainNormalizationEngine",
    "InvestigationStrategyPlanner",
    "DomainExplanationEngine",
    # Enums
    "InfrastructureSector",
    "InfrastructureCategory",
    "ExecutionModel",
    "TerrainType",
    "LandAcquisitionStage",
    "ClearanceType",
    "ClearanceStatus",
    "UtilityType",
    "UtilityStage",
    "ConstraintSeverity",
    "EvidenceStatus",
    "DependencyNodeType",
    "DependencyStatus",
    # Data Contracts & Reports
    "ProjectDomainProfile",
    "LandAcquisitionAnalysis",
    "ClearanceItem",
    "EnvironmentalClearanceAnalysis",
    "UtilityShiftingItem",
    "UtilityShiftingAnalysis",
    "ProcurementAnalysis",
    "ContractAnalysis",
    "PhysicalContextAnalysis",
    "ContractorWorkfrontAnalysis",
    "DependencyNode",
    "DependencyEdge",
    "DependencyGraphReport",
    "DomainNormalizationAdjustment",
    "InvestigationStrategyRecommendation",
    "DomainEvidenceItem",
    "DomainContextReport",
]
