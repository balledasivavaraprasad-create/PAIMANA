"""PAIMANA Peer Intelligence Subsystem.

A deterministic, explainable, and robust peer intelligence foundation for continuous infrastructure monitoring.
"""

from .schemas import (
    CohortDiscoveryResult,
    CohortQuality,
    DeviationDirection,
    MetricDeviation,
    MetricDistribution,
    OutlierMetricEvaluation,
    OutlierSeverity,
    PeerBenchmarkResult,
    PeerDeviationResult,
    PeerOutlierResult,
    PeerTrajectoryResult,
    SimilarityBreakdown,
    TrajectoryMetricComparison,
)
from .repository import (
    InMemoryProjectRepository,
    ProjectRepository,
    SQLiteProjectRepository,
)
from .similarity import ExplainableSimilarityEngine, get_cost_band, get_progress_stage
from .cohort import PeerCohortEngine
from .benchmark import PeerBenchmarkEngine
from .deviation import PeerDeviationEngine
from .trajectory import PeerTrajectoryEngine
from .outlier import PeerOutlierEngine
from .service import PeerIntelligenceService
from .tools_adapter import make_peer_tool_definitions

__all__ = [
    "CohortDiscoveryResult",
    "CohortQuality",
    "DeviationDirection",
    "MetricDeviation",
    "MetricDistribution",
    "OutlierMetricEvaluation",
    "OutlierSeverity",
    "PeerBenchmarkResult",
    "PeerDeviationResult",
    "PeerOutlierResult",
    "PeerTrajectoryResult",
    "SimilarityBreakdown",
    "TrajectoryMetricComparison",
    "ProjectRepository",
    "InMemoryProjectRepository",
    "SQLiteProjectRepository",
    "ExplainableSimilarityEngine",
    "get_cost_band",
    "get_progress_stage",
    "PeerCohortEngine",
    "PeerBenchmarkEngine",
    "PeerDeviationEngine",
    "PeerTrajectoryEngine",
    "PeerOutlierEngine",
    "PeerIntelligenceService",
    "make_peer_tool_definitions",
]
