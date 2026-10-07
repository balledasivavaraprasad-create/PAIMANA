"""Peer Cohort Engine for PAIMANA Infrastructure Monitoring.

Discovers, filters, scores, and assesses peer cohorts:
- Supports question-conditioned discovery (PD-1 through PD-11)
- Enforces hard eligibility constraints before soft similarity scoring
- Applies feature-specific log-distance, stage-distance, and calibrated weights
- Provides adaptive cohort sizing with controlled relaxation audit trails
- Detects cohort scale heterogeneity & bimodal distributions
- Evaluates peer-selection stability under sensitivity perturbations
- Produces comprehensive, auditable selection dossiers
- Fully backwards-compatible with legacy baseline peer discovery
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from .discovery import (
    AdaptiveCohortSelector,
    CandidateGenerator,
    CohortHeterogeneityDetector,
    HardEligibilityFilter,
    InvestigationType,
    ModularSimilarityEngine,
    PeerExplainabilityEngine,
    PeerInvestigationContext,
    PeerRankingEngine,
    PeerStabilityAnalyzer,
    PeerStrategyRegistry,
    QuestionClassifier,
)
from .repository import ProjectRepository
from .schemas import CohortDiscoveryResult, CohortQuality, SimilarityBreakdown
from .similarity import ExplainableSimilarityEngine


class PeerCohortEngine:
    """Discovers and manages peer cohorts for target infrastructure projects."""

    def __init__(
        self,
        repository: ProjectRepository,
        similarity_engine: Optional[ExplainableSimilarityEngine] = None,
        min_similarity_threshold: float = 0.50,
        min_cohort_size: int = 3,
        max_cohort_size: int = 25,
    ):
        self.repository = repository
        self.similarity_engine = similarity_engine or ExplainableSimilarityEngine()
        self.min_similarity_threshold = min_similarity_threshold
        self.min_cohort_size = min_cohort_size
        self.max_cohort_size = max_cohort_size

        # Discovery Subsystem Engines
        self.question_classifier = QuestionClassifier()
        self.strategy_registry = PeerStrategyRegistry()
        self.candidate_generator = CandidateGenerator(repository=self.repository)
        self.hard_eligibility_filter = HardEligibilityFilter()
        self.modular_similarity_engine = ModularSimilarityEngine()
        self.adaptive_selector = AdaptiveCohortSelector()
        self.heterogeneity_detector = CohortHeterogeneityDetector()
        self.ranking_engine = PeerRankingEngine()
        self.stability_analyzer = PeerStabilityAnalyzer()
        self.explainability_engine = PeerExplainabilityEngine()

    def discover_cohort(
        self,
        target_project: Dict[str, Any],
        min_similarity: Optional[float] = None,
        max_peers: Optional[int] = None,
        context: Optional[PeerInvestigationContext] = None,
    ) -> CohortDiscoveryResult:
        """Discovers qualifying peer projects for the target project.
        
        If `context` is provided, executes the complete 10-stage question-conditioned
        discovery pipeline. Otherwise, executes the legacy baseline similarity discovery.
        """
        if context is not None:
            return self._discover_question_conditioned_cohort(
                target_project=target_project,
                context=context,
                min_similarity=min_similarity,
                max_peers=max_peers,
            )

        return self._discover_baseline_cohort(
            target_project=target_project,
            min_similarity=min_similarity,
            max_peers=max_peers,
        )

    def _discover_question_conditioned_cohort(
        self,
        target_project: Dict[str, Any],
        context: PeerInvestigationContext,
        min_similarity: Optional[float] = None,
        max_peers: Optional[int] = None,
    ) -> CohortDiscoveryResult:
        """Full question-conditioned peer discovery pipeline."""
        t_code = str(target_project.get("project_code", context.target_project_id)).strip()
        t_name = str(target_project.get("project_name", t_code)).strip()

        # 1. Classify question & select strategy
        classification = self.question_classifier.classify(context)
        strategy = self.strategy_registry.get_strategy(classification.investigation_type)

        top_k = max_peers or context.max_peers or self.max_cohort_size

        # 2. Candidate generation
        cand_result = self.candidate_generator.generate_candidates(
            target_project=target_project,
            strategy=strategy,
            context=context,
            max_candidates=100,
        )

        # 3. Hard eligibility filtering
        eligible_cands, evaluations = self.hard_eligibility_filter.filter_candidates(
            target_project=target_project,
            candidates=cand_result.candidates,
            strategy=strategy,
            context=context,
        )

        # 4. Modular, calibrated similarity scoring
        scored_peers = [
            self.modular_similarity_engine.compute_similarity(target_project, c, strategy)
            for c in eligible_cands
        ]

        # 5. Adaptive cohort sizing with controlled relaxation
        adaptive_res = self.adaptive_selector.select_cohort(
            scored_candidates=scored_peers,
            strategy=strategy,
            context=context,
            min_cohort_size=self.min_cohort_size,
            target_cohort_size=top_k,
        )

        # 6. Heterogeneity & subgroup detection
        hetero_res = self.heterogeneity_detector.analyze(
            target_project=target_project,
            peers=adaptive_res.selected_peers,
        )

        # 7. Top-K ranking with diversity optimization
        ranking_res = self.ranking_engine.rank_and_select(
            scored_candidates=adaptive_res.selected_peers,
            top_k=top_k,
            enable_diversity=True,
        )

        final_peers = ranking_res.selected_peers

        # 8. Stability analysis
        stability_res = self.stability_analyzer.analyze_stability(
            base_peers=final_peers,
            all_candidates=eligible_cands,
            target_project=target_project,
            strategy=strategy,
            similarity_engine=self.modular_similarity_engine,
            top_k=top_k,
        )

        # 9. Build explainability dossier
        dossier = self.explainability_engine.build_dossier(
            target_project=target_project,
            strategy=strategy,
            selected_peers=final_peers,
            evaluations=evaluations,
            ranked_candidates=ranking_res.ranked_candidates,
            relaxation_history=adaptive_res.relaxation_history,
            heterogeneity=hetero_res,
            stability=stability_res,
        )

        # 10. Quality assessment
        cohort_size = len(final_peers)
        avg_sim = (sum(p.overall_similarity for p in final_peers) / cohort_size) if cohort_size > 0 else 0.0
        quality, is_sufficient, quality_reasons = self._assess_quality(cohort_size, avg_sim, final_peers)

        # Rejection aggregation
        excluded_count = len(cand_result.candidates) - cohort_size
        exclusion_summary = dossier.rejections_summary

        source_lineage = {
            "target_code": t_code,
            "pipeline": "QUESTION_CONDITIONED_DISCOVERY",
            "investigation_type": strategy.investigation_type.value,
            "strategy_id": strategy.strategy_id,
            "candidates_evaluated": len(cand_result.candidates),
            "eligible_candidates": len(eligible_cands),
            "relaxation_applied": adaptive_res.was_relaxed,
            "stability_score": round(stability_res.overall_stability_score, 4),
            "selection_dossier": dossier.to_dict(),
            "timestamp": time.time(),
        }

        return CohortDiscoveryResult(
            target_project_code=t_code,
            target_project_name=t_name,
            cohort_size=cohort_size,
            quality=quality,
            is_sufficient=is_sufficient,
            peers=final_peers,
            excluded_count=excluded_count,
            exclusion_summary=exclusion_summary,
            average_similarity=round(avg_sim, 4),
            quality_reasons=quality_reasons,
            source_lineage=source_lineage,
        )

    def _discover_baseline_cohort(
        self,
        target_project: Dict[str, Any],
        min_similarity: Optional[float] = None,
        max_peers: Optional[int] = None,
    ) -> CohortDiscoveryResult:
        """Legacy baseline similarity cohort discovery."""
        t_code = str(target_project.get("project_code", "TARGET")).strip()
        t_name = str(target_project.get("project_name", "Target Project")).strip()
        t_sector = str(target_project.get("sector") or "").strip()

        threshold = min_similarity if min_similarity is not None else self.min_similarity_threshold
        max_limit = max_peers if max_peers is not None else self.max_cohort_size

        if not t_sector:
            return CohortDiscoveryResult(
                target_project_code=t_code,
                target_project_name=t_name,
                cohort_size=0,
                quality=CohortQuality.INSUFFICIENT,
                is_sufficient=False,
                peers=[],
                excluded_count=0,
                exclusion_summary={"missing_target_sector": 1},
                average_similarity=0.0,
                quality_reasons=["Target project is missing 'sector' attribute; genuine peer discovery impossible."],
                source_lineage={"target_code": t_code, "generated_at": time.time()},
            )

        # Retrieve candidates from repository
        candidates = self.repository.get_candidates(sector=t_sector, exclude_code=t_code)

        qualified_peers: List[SimilarityBreakdown] = []
        excluded_count = 0
        exclusion_summary: Dict[str, int] = {}

        for cand in candidates:
            c_code = str(cand.get("project_code", "")).strip()
            if not c_code or c_code == t_code:
                continue

            breakdown = self.similarity_engine.compute_similarity(target_project, cand)

            if breakdown.overall_similarity >= threshold:
                qualified_peers.append(breakdown)
            else:
                excluded_count += 1
                reason = "below_similarity_threshold"
                if breakdown.exclusion_reasons:
                    reason = breakdown.exclusion_reasons[0].split(":")[0].strip().lower().replace(" ", "_")
                exclusion_summary[reason] = exclusion_summary.get(reason, 0) + 1

        # Sort descending by overall similarity
        qualified_peers.sort(key=lambda p: p.overall_similarity, reverse=True)

        final_peers = qualified_peers[:max_limit]
        cohort_size = len(final_peers)

        avg_sim = (sum(p.overall_similarity for p in final_peers) / cohort_size) if cohort_size > 0 else 0.0
        quality, is_sufficient, quality_reasons = self._assess_quality(cohort_size, avg_sim, final_peers)

        source_lineage = {
            "target_code": t_code,
            "target_sector": t_sector,
            "candidates_evaluated": len(candidates),
            "similarity_threshold": threshold,
            "cohort_bounds": {"min": self.min_cohort_size, "max": max_limit},
            "peer_codes_included": [p.peer_code for p in final_peers],
            "timestamp": time.time(),
        }

        return CohortDiscoveryResult(
            target_project_code=t_code,
            target_project_name=t_name,
            cohort_size=cohort_size,
            quality=quality,
            is_sufficient=is_sufficient,
            peers=final_peers,
            excluded_count=excluded_count,
            exclusion_summary=exclusion_summary,
            average_similarity=round(avg_sim, 4),
            quality_reasons=quality_reasons,
            source_lineage=source_lineage,
        )

    def _assess_quality(
        self, cohort_size: int, avg_sim: float, peers: List[SimilarityBreakdown]
    ) -> Tuple[CohortQuality, bool, List[str]]:
        reasons: List[str] = []

        if cohort_size < self.min_cohort_size:
            reasons.append(
                f"Cohort size ({cohort_size}) is below minimum requirement ({self.min_cohort_size}); insufficient evidence."
            )
            return CohortQuality.INSUFFICIENT, False, reasons

        if avg_sim < 0.45:
            reasons.append(f"Average similarity ({avg_sim:.2f}) is too weak for reliable benchmarking.")
            return CohortQuality.INSUFFICIENT, False, reasons

        if cohort_size >= 10 and avg_sim >= 0.75:
            reasons.append(f"Robust cohort with {cohort_size} high-similarity peers (avg: {avg_sim:.2f}).")
            return CohortQuality.HIGH, True, reasons

        if cohort_size >= 5 and avg_sim >= 0.60:
            reasons.append(f"Adequate cohort with {cohort_size} peers (avg: {avg_sim:.2f}).")
            return CohortQuality.MEDIUM, True, reasons

        reasons.append(f"Marginal cohort with {cohort_size} peers (avg: {avg_sim:.2f}); interpret with caution.")
        return CohortQuality.LOW, True, reasons
