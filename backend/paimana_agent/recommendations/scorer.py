"""[LEGACY ADAPTER] Recommendation Scorer for computing separated recommendation confidence.

NOTE: This is a legacy compatibility module. The canonical candidate scoring engine
is `CandidateScorer` in `paimana_agent.recommendations.candidate_scorer`.
"""
from __future__ import annotations
from typing import Optional


class RecommendationScorer:
    """[LEGACY ADAPTER] Computes independent recommendation confidence based on precedents, root cause, and authority fit.
    
    Replaced by CandidateScorer in candidate_scorer.py.
    """

    def compute_recommendation_confidence(
        self,
        root_cause_confidence: float,
        has_positive_precedent: bool,
        has_confidence_boost: bool,
        authority_match: float = 0.85
    ) -> float:
        """Calculates operational intervention confidence score (0.0 to 1.0)."""
        precedent_factor = 0.85 if has_positive_precedent else (0.50 if has_confidence_boost else 0.30)
        rec_conf = (0.35 * precedent_factor) + (0.35 * root_cause_confidence) + (0.30 * authority_match)
        return round(max(0.10, min(1.0, rec_conf)), 3)
