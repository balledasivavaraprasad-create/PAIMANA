"""Explainability and Audit Trail Generation for Peer Discovery.

Generates transparent, government-grade explanation dossiers detailing why peers
were selected, why candidates were excluded, relaxation history, and cohort validity.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..schemas import CohortDiscoveryResult, SimilarityBreakdown
from .adaptive_selection import RelaxationStep
from .eligibility import EligibilityEvaluation
from .heterogeneity import HeterogeneityAnalysisResult
from .ranking import RankedCandidate
from .stability import StabilityAnalysisResult
from .strategy_registry import PeerStrategyDefinition


@dataclass
class PeerSelectionDossier:
    """Comprehensive, auditable explanation of a peer selection execution."""
    target_project_code: str
    target_project_name: str
    investigation_type: str
    strategy_id: str
    strategy_version: str
    selected_peer_count: int
    selected_peers: List[Dict[str, Any]]
    rejections_summary: Dict[str, int]
    detailed_rejections: List[Dict[str, Any]]
    relaxation_applied: bool
    relaxation_steps: List[Dict[str, Any]]
    heterogeneity: Dict[str, Any]
    stability: Dict[str, Any]
    narrative_explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_project_code": self.target_project_code,
            "target_project_name": self.target_project_name,
            "investigation_type": self.investigation_type,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "selected_peer_count": self.selected_peer_count,
            "selected_peers": self.selected_peers,
            "rejections_summary": self.rejections_summary,
            "detailed_rejections": self.detailed_rejections,
            "relaxation_applied": self.relaxation_applied,
            "relaxation_steps": self.relaxation_steps,
            "heterogeneity": self.heterogeneity,
            "stability": self.stability,
            "narrative_explanation": self.narrative_explanation,
        }


class PeerExplainabilityEngine:
    """Builds auditable dossiers explaining every decision made during peer discovery."""

    def build_dossier(
        self,
        target_project: Dict[str, Any],
        strategy: PeerStrategyDefinition,
        selected_peers: List[SimilarityBreakdown],
        evaluations: List[EligibilityEvaluation],
        ranked_candidates: List[RankedCandidate],
        relaxation_history: List[RelaxationStep],
        heterogeneity: Optional[HeterogeneityAnalysisResult] = None,
        stability: Optional[StabilityAnalysisResult] = None,
    ) -> PeerSelectionDossier:
        """Constructs an auditable explainability dossier."""
        t_code = str(target_project.get("project_code") or target_project.get("canonical_project_id", "")).strip()
        t_name = str(target_project.get("project_name", "")).strip()

        # Rejection aggregation
        rejections_summary: Dict[str, int] = {}
        detailed_rejections: List[Dict[str, Any]] = []

        for ev in evaluations:
            if not ev.is_eligible:
                for r in ev.rejection_reasons:
                    rejections_summary[r.value] = rejections_summary.get(r.value, 0) + 1
                detailed_rejections.append({
                    "candidate_code": ev.candidate_code,
                    "candidate_name": ev.candidate_name,
                    "decision": "DISQUALIFIED_BY_HARD_FILTER",
                    "reasons": [r.value for r in ev.rejection_reasons],
                    "diagnostics": ev.diagnostics,
                })

        for rk in ranked_candidates:
            if rk.decision != "SELECTED":
                detailed_rejections.append({
                    "candidate_code": rk.peer_code,
                    "candidate_name": rk.peer_name,
                    "decision": rk.decision,
                    "reasons": [rk.selection_reason],
                    "similarity_score": round(rk.similarity_score, 4),
                })

        # Selected peers summary
        selected_summaries = []
        for p in selected_peers:
            selected_summaries.append({
                "peer_code": p.peer_code,
                "peer_name": p.peer_name,
                "overall_similarity": round(p.overall_similarity, 4),
                "dimension_scores": {k: round(v, 4) for k, v in p.dimension_scores.items()},
                "key_strengths": p.inclusion_reasons[:3],
                "divergences": p.exclusion_reasons[:2],
            })

        # Build narrative
        narrative = self._generate_narrative(
            t_name=t_name,
            t_code=t_code,
            strategy=strategy,
            selected_count=len(selected_peers),
            rejection_count=len(detailed_rejections),
            was_relaxed=len(relaxation_history) > 0,
            heterogeneity=heterogeneity,
            stability=stability,
        )

        return PeerSelectionDossier(
            target_project_code=t_code,
            target_project_name=t_name,
            investigation_type=strategy.investigation_type.value,
            strategy_id=strategy.strategy_id,
            strategy_version=strategy.version,
            selected_peer_count=len(selected_peers),
            selected_peers=selected_summaries,
            rejections_summary=rejections_summary,
            detailed_rejections=detailed_rejections,
            relaxation_applied=len(relaxation_history) > 0,
            relaxation_steps=[r.to_dict() for r in relaxation_history],
            heterogeneity=heterogeneity.to_dict() if heterogeneity else {},
            stability=stability.to_dict() if stability else {},
            narrative_explanation=narrative,
        )

    def _generate_narrative(
        self,
        t_name: str,
        t_code: str,
        strategy: PeerStrategyDefinition,
        selected_count: int,
        rejection_count: int,
        was_relaxed: bool,
        heterogeneity: Optional[HeterogeneityAnalysisResult],
        stability: Optional[StabilityAnalysisResult],
    ) -> str:
        parts = [
            f"Peer cohort discovery for '{t_name}' ({t_code}) was executed under strategy '{strategy.strategy_id}' "
            f"(investigation type: {strategy.investigation_type.value}).",
            f"{selected_count} comparable peer(s) were selected after evaluating {selected_count + rejection_count} candidate(s).",
        ]
        if was_relaxed:
            parts.append("Controlled threshold relaxation was applied to ensure statistical cohort viability.")
        if heterogeneity and heterogeneity.is_heterogeneous:
            parts.append(f"Cohort scale heterogeneity detected: {heterogeneity.explanation}")
        if stability:
            parts.append(f"Stability verification: {stability.summary}")
        return " ".join(parts)
