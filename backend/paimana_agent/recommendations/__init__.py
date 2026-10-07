"""Recommendations Subpackage for PAIMANA Agentic Layer.

Implements candidate generation -> validation -> multi-criteria evaluation -> Pareto filtering -> constrained selection.
"""
from .candidate import RecommendationCandidate
from .candidate_generator import CandidateGenerator
from .candidate_validator import CandidateValidator
from .candidate_deduplicator import CandidateDeduplicator
from .ranking_policy import RankingPolicy
from .candidate_scorer import CandidateScorer
from .pareto import pareto_filter, dominates
from .selector import RecommendationSelector, RecommendationDecision
from .benefit_model import BenefitModel
from .cost_model import CostModel
from .risk_model import RiskModel
from .evidence_model import CandidateEvidenceModel
from .authority_model import AuthorityModel

# Backward-compatible class aliases
RecommendationGenerator = CandidateGenerator
RecommendationValidator = CandidateValidator
RecommendationScorer = CandidateScorer

__all__ = [
    "RecommendationCandidate",
    "CandidateGenerator",
    "CandidateValidator",
    "CandidateDeduplicator",
    "CandidateScorer",
    "RankingPolicy",
    "pareto_filter",
    "dominates",
    "RecommendationSelector",
    "RecommendationDecision",
    "BenefitModel",
    "CostModel",
    "RiskModel",
    "CandidateEvidenceModel",
    "AuthorityModel",
    "RecommendationGenerator",
    "RecommendationValidator",
    "RecommendationScorer",
]
