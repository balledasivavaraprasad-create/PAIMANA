"""Unified Cohort Intelligence Service for PAIMANA (CI-10).

Orchestrates all cohort intelligence analyses:
- Multidimensional quality assessment
- Similarity and feature distributions
- Within-cohort heterogeneity & entropy
- Subgroup and cluster detection
- Multimodality and fragmentation detection
- Stability and diversity evaluation
- Metric-specific confidence and actionable refinement directives
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from ..discovery.strategy_registry import PeerStrategyDefinition
from ..schemas import CohortDiscoveryResult, SimilarityBreakdown
from .clustering import CohortClusterAnalyzer
from .confidence import MetricConfidenceAssessor
from .distribution import DistributionAnalyzer
from .diversity import CohortDiversityEvaluator
from .fragmentation import FragmentationDetector
from .heterogeneity import CohortHeterogeneityAnalyzer
from .multimodality import MultimodalityDetector
from .quality import CohortQualityAssessor
from .refinement import CohortRefinementEngine
from .schemas import CohortIntelligenceResult, MultimodalityReport
from .stability import CohortStabilityEvaluator
from .subgroup import SubgroupDetector


class CohortIntelligenceService:
    """Master service providing in-depth intelligence and diagnostic health for peer cohorts."""

    def __init__(self):
        self.quality_assessor = CohortQualityAssessor()
        self.distribution_analyzer = DistributionAnalyzer()
        self.heterogeneity_analyzer = CohortHeterogeneityAnalyzer()
        self.subgroup_detector = SubgroupDetector()
        self.cluster_analyzer = CohortClusterAnalyzer()
        self.multimodality_detector = MultimodalityDetector()
        self.fragmentation_detector = FragmentationDetector()
        self.stability_evaluator = CohortStabilityEvaluator()
        self.diversity_evaluator = CohortDiversityEvaluator()
        self.confidence_assessor = MetricConfidenceAssessor()
        self.refinement_engine = CohortRefinementEngine()

    def analyze_cohort(
        self,
        cohort: CohortDiscoveryResult,
        target_project: Dict[str, Any],
        metrics: Optional[List[str]] = None,
        strategy: Optional[PeerStrategyDefinition] = None,
    ) -> CohortIntelligenceResult:
        """Executes full diagnostic cohort intelligence evaluation."""
        peers = cohort.peers
        target_code = str(target_project.get("project_code") or cohort.target_project_code).strip()

        # 1. Quality Assessment
        quality_res = self.quality_assessor.assess_quality(peers, target_project, required_metrics=metrics)

        # 2. Distribution Analysis
        dist_res = self.distribution_analyzer.analyze_similarity_distribution(peers)

        # 3. Heterogeneity Analysis
        hetero_res = self.heterogeneity_analyzer.analyze_heterogeneity(peers, strategy=strategy)

        # 4. Subgroup Detection (Domain-driven with hierarchical fallback)
        subgroup_res = self.subgroup_detector.detect_subgroups(peers, target_project)
        if not subgroup_res.subgroups_detected and len(peers) >= 6:
            # Attempt algorithmic clustering fallback
            cluster_res = self.cluster_analyzer.cluster_cohort(peers, target_project)
            if cluster_res.subgroups_detected:
                subgroup_res = cluster_res

        # 5. Multimodality Detection
        multimodal_reports: Dict[str, MultimodalityReport] = {}
        eval_metrics = metrics or ["original_cost", "physical_progress", "planned_duration"]
        for m in eval_metrics:
            m_rep = self.multimodality_detector.analyze_metric(peers, m)
            if m_rep.is_multimodal:
                multimodal_reports[m] = m_rep

        # 6. Fragmentation Detection
        frag_res = self.fragmentation_detector.analyze_fragmentation(peers)

        # 7. Stability & Diversity
        stability_score = self.stability_evaluator.evaluate_stability(peers)
        diversity_score = self.diversity_evaluator.evaluate_diversity(peers)

        # 8. Metric-Specific Confidence
        confidence_map = self.confidence_assessor.assess_metric_confidence(peers, metrics=metrics)

        # 9. Cohort Refinement Decision
        recommendation, warnings = self.refinement_engine.determine_recommendation(
            quality=quality_res,
            heterogeneity=hetero_res,
            subgroups=subgroup_res,
            fragmentation=frag_res,
            stability_score=stability_score,
        )

        # 10. Structured Evidence Items
        evidence = self._build_evidence_items(
            target_code=target_code,
            quality_res=quality_res,
            hetero_res=hetero_res,
            subgroup_res=subgroup_res,
            recommendation=recommendation,
            warnings=warnings,
        )

        return CohortIntelligenceResult(
            cohort_id=f"COHORT-INTEL-{target_code}",
            target_project_code=target_code,
            quality=quality_res,
            similarity_distribution=dist_res,
            heterogeneity=hetero_res,
            subgroups=subgroup_res,
            multimodality=multimodal_reports,
            fragmentation=frag_res,
            stability_score=stability_score,
            diversity_score=diversity_score,
            confidence_by_metric=confidence_map,
            recommendation=recommendation,
            warnings=warnings,
            evidence=evidence,
        )

    def _build_evidence_items(
        self,
        target_code: str,
        quality_res: Any,
        hetero_res: Any,
        subgroup_res: Any,
        recommendation: Any,
        warnings: List[str],
    ) -> List[Dict[str, Any]]:
        evidence = []
        # Main quality evidence
        evidence.append({
            "type": "COHORT_INTELLIGENCE",
            "subject": target_code,
            "statement": (
                f"Cohort Intelligence assessment: Quality is {quality_res.overall_quality.value} "
                f"(score: {round(quality_res.overall_score, 2)}). Recommendation: {recommendation.value}."
            ),
            "relation": "CONTEXTUALIZES",
            "confidence": "HIGH",
            "source": "cohort_intelligence",
            "limitations": list(warnings),
        })

        if subgroup_res.subgroups_detected:
            evidence.append({
                "type": "COHORT_SUBGROUPS_DETECTED",
                "subject": target_code,
                "statement": (
                    f"Identified {len(subgroup_res.subgroups)} distinct subgroups in peer cohort. "
                    f"Target aligns with subgroup '{subgroup_res.target_subgroup_id or 'UNKNOWN'}'."
                ),
                "relation": "CONTEXTUALIZES",
                "confidence": "HIGH",
                "source": "cohort_intelligence",
            })

        return evidence
