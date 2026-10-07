"""Stability & Sensitivity Analysis Engine for Peer Discovery.

Evaluates whether the selected peer cohort remains robust under minor parameter perturbations
(weight jitter, threshold changes) and flags fragile cohort selections for human review.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

from ..schemas import SimilarityBreakdown
from .strategy_registry import PeerStrategyDefinition


@dataclass
class PerturbationEvaluation:
    """Outcome of cohort comparison under a specific parameter perturbation."""
    perturbation_type: str
    jaccard_overlap: float  # |Base ∩ Perturbed| / |Base ∪ Perturbed|
    retained_peers: List[str]
    dropped_peers: List[str]
    added_peers: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "perturbation_type": self.perturbation_type,
            "jaccard_overlap": round(self.jaccard_overlap, 4),
            "retained_count": len(self.retained_peers),
            "dropped_count": len(self.dropped_peers),
            "added_count": len(self.added_peers),
        }


@dataclass
class StabilityAnalysisResult:
    """Holistic cohort stability report under sensitivity testing."""
    overall_stability_score: float  # 0.0 to 1.0
    is_stable: bool
    evaluations: List[PerturbationEvaluation] = field(default_factory=list)
    warning: Optional[str] = None
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_stability_score": round(self.overall_stability_score, 4),
            "is_stable": self.is_stable,
            "warning": self.warning,
            "summary": self.summary,
            "evaluations": [e.to_dict() for e in self.evaluations],
        }


class PeerStabilityAnalyzer:
    """Tests peer selection invariance under slight weight and threshold changes."""

    def analyze_stability(
        self,
        base_peers: List[SimilarityBreakdown],
        all_candidates: List[Dict[str, Any]],
        target_project: Dict[str, Any],
        strategy: PeerStrategyDefinition,
        similarity_engine: Any,
        top_k: int = 10,
    ) -> StabilityAnalysisResult:
        """Runs sensitivity tests and computes cohort stability score."""
        if not base_peers:
            return StabilityAnalysisResult(
                overall_stability_score=0.0,
                is_stable=False,
                warning="Empty cohort cannot be evaluated for stability.",
                summary="No peers in base cohort.",
            )

        base_codes = {p.peer_code for p in base_peers}
        evaluations: List[PerturbationEvaluation] = []

        # Perturbation 1: Cost weight +10%, other weights normalized
        strat_perturbed_cost = _perturb_strategy_weight(strategy, "original_cost", +0.10)
        p1_peers = _score_and_rank(similarity_engine, target_project, all_candidates, strat_perturbed_cost, top_k)
        evaluations.append(_compute_overlap("COST_WEIGHT_PLUS_10_PCT", base_codes, p1_peers))

        # Perturbation 2: Agency weight -10%, other weights normalized
        strat_perturbed_agency = _perturb_strategy_weight(strategy, "implementing_agency", -0.10)
        p2_peers = _score_and_rank(similarity_engine, target_project, all_candidates, strat_perturbed_agency, top_k)
        evaluations.append(_compute_overlap("AGENCY_WEIGHT_MINUS_10_PCT", base_codes, p2_peers))

        # Overall stability is the average Jaccard overlap
        scores = [e.jaccard_overlap for e in evaluations]
        avg_score = sum(scores) / len(scores) if scores else 1.0

        is_stable = avg_score >= 0.70
        warning = None if is_stable else f"Cohort selection is sensitive to weight adjustments (stability: {round(avg_score, 2)})."
        summary = (
            f"Cohort stability score: {round(avg_score, 2)} ({'STABLE' if is_stable else 'UNSTABLE'}). "
            f"Average peer retention across perturbations is {round(avg_score * 100, 1)}%."
        )

        return StabilityAnalysisResult(
            overall_stability_score=avg_score,
            is_stable=is_stable,
            evaluations=evaluations,
            warning=warning,
            summary=summary,
        )


def _perturb_strategy_weight(strategy: PeerStrategyDefinition, dimension: str, delta: float) -> PeerStrategyDefinition:
    weights = dict(strategy.dimension_weights)
    if dimension in weights:
        weights[dimension] = max(0.05, weights[dimension] + delta)
    total = sum(weights.values())
    norm_weights = {k: round(v / total, 4) for k, v in weights.items()}
    return PeerStrategyDefinition(
        strategy_id=f"{strategy.strategy_id}-PERTURBED",
        version=strategy.version,
        investigation_type=strategy.investigation_type,
        description="Perturbed sensitivity test",
        mandatory_hard_filters=strategy.mandatory_hard_filters,
        dimension_weights=norm_weights,
        relevant_metrics=strategy.relevant_metrics,
        relaxation_hierarchy=strategy.relaxation_hierarchy,
        min_similarity_threshold=strategy.min_similarity_threshold,
    )


def _score_and_rank(similarity_engine: Any, target: Dict[str, Any], candidates: List[Dict[str, Any]], strategy: PeerStrategyDefinition, top_k: int) -> Set[str]:
    scored = [similarity_engine.compute_similarity(target, c, strategy) for c in candidates]
    scored.sort(key=lambda x: x.overall_similarity, reverse=True)
    return {p.peer_code for p in scored[:top_k]}


def _compute_overlap(label: str, base_codes: Set[str], perturbed_codes: Set[str]) -> PerturbationEvaluation:
    intersection = base_codes.intersection(perturbed_codes)
    union = base_codes.union(perturbed_codes)
    jaccard = len(intersection) / len(union) if union else 1.0

    return PerturbationEvaluation(
        perturbation_type=label,
        jaccard_overlap=jaccard,
        retained_peers=list(intersection),
        dropped_peers=list(base_codes - perturbed_codes),
        added_peers=list(perturbed_codes - base_codes),
    )
