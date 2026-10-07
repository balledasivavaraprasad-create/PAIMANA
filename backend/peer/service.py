"""Unified Peer Intelligence Service for PAIMANA Infrastructure Monitoring.

Exposes the 6 formal peer intelligence capabilities:
1. peer_discovery: multi-dimensional comparable peer identification & filtering
2. peer_benchmark: robust statistical distributions across cohort metrics
3. peer_deviation: target vs peer baseline deviation & directional interpretations
4. peer_trajectory: chronological velocity comparison across historical snapshots
5. peer_outlier: peer-relative anomaly detection separating absolute risk from peer context
6. peer_cohort_health: explicit data completeness, similarity strength, and quality scoring

Includes in-memory snapshot hash caching to prevent redundant computations.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union

from .benchmark import PeerBenchmarkEngine
from .cohort import PeerCohortEngine
from .deviation import PeerDeviationEngine
from .intelligence import CohortIntelligenceResult, CohortIntelligenceService
from .outlier import PeerOutlierEngine
from .repository import ProjectRepository
from .schemas import (
    CohortDiscoveryResult,
    CohortQuality,
    PeerBenchmarkResult,
    PeerDeviationResult,
    PeerOutlierResult,
    PeerTrajectoryResult,
)
from .similarity import ExplainableSimilarityEngine
from .trajectory import (
    PeerTrajectoryEngine,
    TrajectoryIntelligenceService,
    TrajectoryIntelligenceResult,
)
from .statistical import StatisticalBenchmarkingService, StatisticalBenchmarkResult
from .anomaly import DeviationAndOutlierService, ConsolidatedAnomalyResult
from .domain import DomainIntelligenceService, DomainContextReport
from .evidence import (
    Evidence,
    EvidenceAndSemanticSafetyService,
    Claim,
    SemanticSafeReport,
    SemanticSafetyAuditReport,
)

logger = logging.getLogger("paimana.peer.service")


class PeerIntelligenceService:
    """Central service orchestrating all peer intelligence capabilities."""

    def __init__(
        self,
        repository: ProjectRepository,
        similarity_engine: Optional[ExplainableSimilarityEngine] = None,
        cohort_engine: Optional[PeerCohortEngine] = None,
        benchmark_engine: Optional[PeerBenchmarkEngine] = None,
        deviation_engine: Optional[PeerDeviationEngine] = None,
        trajectory_engine: Optional[PeerTrajectoryEngine] = None,
        outlier_engine: Optional[PeerOutlierEngine] = None,
        cohort_intelligence: Optional[CohortIntelligenceService] = None,
        statistical_benchmark_service: Optional[StatisticalBenchmarkingService] = None,
        anomaly_service: Optional[DeviationAndOutlierService] = None,
        trajectory_intelligence_service: Optional[TrajectoryIntelligenceService] = None,
        domain_service: Optional[DomainIntelligenceService] = None,
        evidence_service: Optional[EvidenceAndSemanticSafetyService] = None,
        cache_enabled: bool = True,
    ):
        self.repository = repository
        self.similarity_engine = similarity_engine or ExplainableSimilarityEngine()
        self.cohort_engine = cohort_engine or PeerCohortEngine(
            repository=repository, similarity_engine=self.similarity_engine
        )
        self.benchmark_engine = benchmark_engine or PeerBenchmarkEngine()
        self.deviation_engine = deviation_engine or PeerDeviationEngine()
        self.trajectory_engine = trajectory_engine or PeerTrajectoryEngine(repository=repository)
        self.outlier_engine = outlier_engine or PeerOutlierEngine()
        self.cohort_intelligence = cohort_intelligence or CohortIntelligenceService()
        self.statistical_benchmark_service = (
            statistical_benchmark_service or StatisticalBenchmarkingService()
        )
        self.anomaly_service = anomaly_service or DeviationAndOutlierService()
        self.trajectory_intelligence_service = (
            trajectory_intelligence_service or TrajectoryIntelligenceService()
        )
        self.domain_service = domain_service or DomainIntelligenceService(cache_enabled=cache_enabled)
        self.evidence_service = evidence_service or EvidenceAndSemanticSafetyService()
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, Any] = {}

    # 1. Peer Discovery
    def peer_discovery(
        self,
        target_project: Dict[str, Any],
        min_similarity: Optional[float] = None,
        max_peers: Optional[int] = None,
        context: Optional[Any] = None,
    ) -> CohortDiscoveryResult:
        """Finds comparable peer projects with transparent similarity explanations."""
        return self.cohort_engine.discover_cohort(
            target_project=target_project,
            min_similarity=min_similarity,
            max_peers=max_peers,
            context=context,
        )


    # 2. Peer Benchmark
    def peer_benchmark(
        self,
        target_project: Dict[str, Any],
        metrics: Optional[List[str]] = None,
        cohort: Optional[CohortDiscoveryResult] = None,
    ) -> PeerBenchmarkResult:
        """Calculates robust statistical baselines across the target project's peer cohort."""
        c = cohort or self.peer_discovery(target_project)
        return self.benchmark_engine.compute_benchmarks(cohort=c, metrics=metrics)

    # 2b. Statistical Benchmark (SB-12)
    def statistical_benchmark(
        self,
        target_project: Dict[str, Any],
        cohort: Optional[Union[CohortDiscoveryResult, List[Dict[str, Any]]]] = None,
        metrics: Optional[List[str]] = None,
        reference_cohort: Optional[List[Dict[str, Any]]] = None,
        as_of_date: Optional[str] = None,
        random_seed: int = 42,
        resample_count: int = 2000,
    ) -> StatisticalBenchmarkResult:
        """Calculates non-parametric robust reference profiles, bootstrap CIs, and empirical percentiles."""
        c = cohort or self.peer_discovery(target_project)
        return self.statistical_benchmark_service.benchmark_cohort(
            target_project=target_project,
            cohort=c,
            metrics=metrics,
            reference_cohort=reference_cohort,
            as_of_date=as_of_date,
            random_seed=random_seed,
            resample_count=resample_count,
        )

    # 3. Peer Deviation
    def peer_deviation(
        self,
        target_project: Dict[str, Any],
        metrics: Optional[List[str]] = None,
        cohort: Optional[CohortDiscoveryResult] = None,
        benchmarks: Optional[PeerBenchmarkResult] = None,
    ) -> PeerDeviationResult:
        """Evaluates target-vs-peer deviation, relative gaps, and directional significance."""
        c = cohort or self.peer_discovery(target_project)
        b = benchmarks or self.benchmark_engine.compute_benchmarks(cohort=c, metrics=metrics)
        # Extract raw peer metric pools for exact percentile ranks
        raw_vals: Dict[str, List[float]] = {}
        for p in c.peers:
            if p.raw_attributes:
                for k, v in p.raw_attributes.items():
                    if isinstance(v, (int, float)) and not isinstance(v, bool):
                        raw_vals.setdefault(k, []).append(float(v))
        return self.deviation_engine.analyze_deviations(
            target_project=target_project, benchmarks=b, peer_raw_values=raw_vals
        )

    # 4. Peer Trajectory
    def peer_trajectory(
        self,
        target_project_code: str,
        cohort: Optional[CohortDiscoveryResult] = None,
        window_snapshots: int = 6,
    ) -> PeerTrajectoryResult:
        """Compares chronological rate of change against peer cohort trajectories."""
        t_code = target_project_code.strip()
        if cohort is None:
            target_p = self.repository.get_project(t_code)
            if not target_p:
                return PeerTrajectoryResult(
                    target_project_code=t_code,
                    snapshots_analyzed=0,
                    is_sufficient_history=False,
                    comparisons={},
                    summary=f"Project '{t_code}' not found in repository.",
                    source_lineage={"target_code": t_code},
                )
            cohort = self.peer_discovery(target_p)
        return self.trajectory_engine.analyze_trajectory(
            target_project_code=t_code, cohort=cohort, window_snapshots=window_snapshots
        )

    # 4b. Trajectory Intelligence (TI-14)
    def analyze_trajectory_intelligence(
        self,
        target_project_code: str,
        target_snapshots: Optional[List[Dict[str, Any]]] = None,
        cohort: Optional[CohortDiscoveryResult] = None,
        metrics: Optional[List[str]] = None,
        target_project: Optional[Dict[str, Any]] = None,
        window_snapshots: int = 12,
    ) -> TrajectoryIntelligenceResult:
        """Runs in-depth trajectory intelligence across historical snapshots."""
        t_code = target_project_code.strip()
        t_snaps = target_snapshots
        if not t_snaps:
            t_snaps = self.repository.get_history(t_code, limit=window_snapshots)

        target_p = target_project
        if not target_p:
            target_p = self.repository.get_project(t_code)

        peer_snaps: Dict[str, List[Dict[str, Any]]] = {}
        c = cohort
        if c is None and target_p:
            c = self.peer_discovery(target_p)

        if c and c.peers:
            for p in c.peers:
                p_code = p.peer_code
                p_h = self.repository.get_history(p_code, limit=window_snapshots)
                if p_h:
                    peer_snaps[p_code] = p_h

        return self.trajectory_intelligence_service.analyze_project_trajectory(
            target_project_code=t_code,
            target_snapshots=t_snaps,
            peer_cohort_snapshots=peer_snaps if peer_snaps else None,
            metrics=metrics,
            target_project=target_p,
            cohort_id=getattr(c, "cohort_id", getattr(c, "target_project_code", "COHORT")) if c else "COHORT",
        )

    # 5. Peer Outlier
    def peer_outlier(
        self,
        target_project: Dict[str, Any],
        cohort: Optional[CohortDiscoveryResult] = None,
    ) -> PeerOutlierResult:
        """Determines whether project performance is abnormal relative to peer distribution."""
        c = cohort or self.peer_discovery(target_project)
        return self.outlier_engine.evaluate_outliers(target_project=target_project, cohort=c)

    # 6. Peer Cohort Health
    def peer_cohort_health(
        self,
        target_project: Dict[str, Any],
        cohort: Optional[CohortDiscoveryResult] = None,
    ) -> Dict[str, Any]:
        """Provides an explainable summary of cohort strength, coverage, and reliability."""
        c = cohort or self.peer_discovery(target_project)
        return {
            "target_project_code": c.target_project_code,
            "cohort_size": c.cohort_size,
            "cohort_quality": c.quality.value,
            "is_sufficient": c.is_sufficient,
            "average_similarity": round(c.average_similarity, 4),
            "quality_reasons": c.quality_reasons,
            "excluded_count": c.excluded_count,
            "exclusion_summary": c.exclusion_summary,
            "lineage": c.source_lineage,
        }

    # 7. Cohort Intelligence (CI-10)
    def analyze_cohort_intelligence(
        self,
        target_project: Dict[str, Any],
        cohort: Optional[CohortDiscoveryResult] = None,
        metrics: Optional[List[str]] = None,
        strategy: Optional[Any] = None,
    ) -> CohortIntelligenceResult:
        """Runs in-depth diagnostic health, heterogeneity, subgroup and refinement analysis."""
        c = cohort or self.peer_discovery(target_project)
        return self.cohort_intelligence.analyze_cohort(
            cohort=c, target_project=target_project, metrics=metrics, strategy=strategy
        )

    # 8. Anomaly & Outlier Detection (DO-12)
    def detect_peer_anomalies(
        self,
        target_project: Dict[str, Any],
        cohort: Optional[Union[CohortDiscoveryResult, List[Dict[str, Any]]]] = None,
        metrics: Optional[List[str]] = None,
        historical_snapshots: Optional[List[Dict[str, Any]]] = None,
    ) -> ConsolidatedAnomalyResult:
        """Runs multi-method, contextual, multivariate, and temporal anomaly detection."""
        c = cohort or self.peer_discovery(target_project)
        return self.anomaly_service.detect_anomalies(
            target_project=target_project,
            cohort=c,
            metrics=metrics,
            historical_snapshots=historical_snapshots,
        )

    # 12. Domain-Specific Intelligence (DSI-01 to DSI-14)
    def analyze_domain_context(
        self,
        target_project: Dict[str, Any],
        question: Optional[str] = None,
        hypothesis: Optional[str] = None,
        target_metrics: Optional[Dict[str, float]] = None,
    ) -> DomainContextReport:
        """Analyzes domain-specific operational realities, constraints, and dependencies."""
        return self.domain_service.analyze_domain_context(
            project_data=target_project,
            question=question,
            hypothesis=hypothesis,
            target_metrics=target_metrics,
        )

    # Comprehensive Analytical Report
    def get_comprehensive_peer_intelligence(
        self,
        target_project: Dict[str, Any],
        metrics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Runs the complete peer intelligence pipeline with caching."""
        cache_key = self._compute_cache_key(target_project)
        if self.cache_enabled and cache_key in self._cache:
            return self._cache[cache_key]

        t0 = time.time()
        cohort = self.peer_discovery(target_project)
        benchmarks = self.peer_benchmark(target_project, metrics=metrics, cohort=cohort)
        deviation = self.peer_deviation(target_project, metrics=metrics, cohort=cohort, benchmarks=benchmarks)
        outlier = self.peer_outlier(target_project, cohort=cohort)

        t_code = str(target_project.get("project_code", "")).strip()
        trajectory = self.peer_trajectory(target_project_code=t_code, cohort=cohort)
        domain_ctx = self.analyze_domain_context(target_project)

        res = {
            "target_code": t_code,
            "target_name": str(target_project.get("project_name") or t_code or "Unknown Project").strip(),
            "cohort_health": self.peer_cohort_health(target_project, cohort=cohort),
            "discovery": cohort.to_dict(),
            "benchmarks": benchmarks.to_dict(),
            "deviations": deviation.to_dict(),
            "trajectory": trajectory.to_dict(),
            "outliers": outlier.to_dict(),
            "domain_context": domain_ctx.to_dict(),
            "pipeline_latency_ms": round((time.time() - t0) * 1000.0, 2),
            "generated_at": time.time(),
        }

        if self.cache_enabled and cache_key:
            self._cache[cache_key] = res

        return res

    def _compute_cache_key(self, p: Dict[str, Any]) -> str:
        keys = ["project_code", "sector", "original_cost_cr", "physical_progress_pct", "report_month"]
        sub = {k: p.get(k) for k in keys}
        return hashlib.sha256(json.dumps(sub, sort_keys=True, default=str).encode("utf-8")).hexdigest()

    # Evidence & Semantic Safety Facades (ESS-01 to ESS-10)
    def normalize_evidence_from_pipeline(
        self,
        target_project: Dict[str, Any],
        pipeline_result: Dict[str, Any],
    ) -> List[Evidence]:
        """Normalizes and registers canonical Evidence objects from peer pipeline and domain outputs."""
        p_id = str(target_project.get("project_code", target_project.get("project_id", "TARGET_PROJECT"))).strip()
        ingested: List[Evidence] = []

        if "benchmarks" in pipeline_result:
            ingested.extend(self.evidence_service.ingest_from_peer_intelligence(p_id, pipeline_result["benchmarks"]))
        if "domain_context" in pipeline_result:
            ingested.extend(self.evidence_service.ingest_from_domain_context(p_id, pipeline_result["domain_context"]))

        return ingested

    def audit_investigation_claims(self, candidate_claims: List[Claim]) -> SemanticSafetyAuditReport:
        """Audits candidate analytical claims through pre-report safety gate."""
        return self.evidence_service.audit_claims(candidate_claims)

    def generate_semantic_safe_report(
        self,
        target_project: Dict[str, Any],
        candidate_claims: List[Claim],
        evidence_gaps: Optional[List[str]] = None,
    ) -> SemanticSafeReport:
        """Generates an executive report strictly bounded by registered evidence and safety rules."""
        p_id = str(target_project.get("project_code", target_project.get("project_id", "TARGET_PROJECT"))).strip()
        p_name = target_project.get("project_name", "Target Infrastructure Project")
        return self.evidence_service.generate_safe_report(
            project_id=p_id,
            project_name=p_name,
            candidate_claims=candidate_claims,
            evidence_gaps=evidence_gaps,
        )

