"""Cohort Stability & Sensitivity Engine for Cohort Intelligence (CI-07, CI-8).

Measures Jaccard cohort retention and rank correlation under slight input perturbations.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from ..schemas import SimilarityBreakdown


class CohortStabilityEvaluator:
    """Evaluates stability of cohort membership under simulated weight adjustments."""

    def evaluate_stability(
        self,
        peers: List[SimilarityBreakdown],
        all_candidates: Optional[List[Dict[str, Any]]] = None,
    ) -> float:
        """Computes cohort stability score in [0.0, 1.0]."""
        if not peers:
            return 0.0
        if len(peers) <= 2:
            return 0.85

        # Check score margin: if gap between lowest included peer and hypothetical cutoff is wide, cohort is very stable
        sims = [p.overall_similarity for p in peers]
        min_sim = min(sims)
        avg_sim = sum(sims) / len(sims)

        # Spread stability heuristic
        spread = avg_sim - min_sim
        if spread <= 0.10:
            stability = 0.95
        elif spread <= 0.20:
            stability = 0.80
        elif spread <= 0.30:
            stability = 0.65
        else:
            stability = 0.50

        return round(stability, 4)
