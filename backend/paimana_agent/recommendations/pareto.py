"""Pareto frontier filtering for multi-criteria recommendation selection."""
from __future__ import annotations
from typing import Tuple
from .candidate import RecommendationCandidate


def dominates(cand_a: RecommendationCandidate, cand_b: RecommendationCandidate) -> bool:
    """Returns True if cand_a Pareto-dominates cand_b.
    
    A dominates B if A is >= B across all 5 evaluation dimensions,
    and strictly > B on at least one dimension.
    """
    cost_a = max(0.0, 1.0 - cand_a.expected_cost)
    cost_b = max(0.0, 1.0 - cand_b.expected_cost)
    risk_a = cand_a.expected_risk_reduction * (1.0 - cand_a.implementation_risk)
    risk_b = cand_b.expected_risk_reduction * (1.0 - cand_b.implementation_risk)

    dims_a = [cand_a.expected_benefit, cost_a, risk_a, cand_a.evidence_strength, cand_a.authority_score]
    dims_b = [cand_b.expected_benefit, cost_b, risk_b, cand_b.evidence_strength, cand_b.authority_score]

    all_greater_or_equal = all(a >= b - 1e-4 for a, b in zip(dims_a, dims_b))
    at_least_one_strictly_greater = any(a > b + 1e-3 for a, b in zip(dims_a, dims_b))

    return all_greater_or_equal and at_least_one_strictly_greater


def pareto_filter(
    candidates: list[RecommendationCandidate]
) -> Tuple[list[RecommendationCandidate], list[RecommendationCandidate]]:
    """Partitions candidates into non-dominated Pareto frontier and dominated candidates.
    
    Returns:
        (frontier_candidates, dominated_candidates)
    """
    if len(candidates) <= 1:
        return candidates, []

    dominated: set[str] = set()

    for i, a in enumerate(candidates):
        for j, b in enumerate(candidates):
            if i != j and dominates(a, b):
                dominated.add(b.id)
                b.is_dominated = True

    frontier = [c for c in candidates if c.id not in dominated]
    dominated_list = [c for c in candidates if c.id in dominated]

    return frontier, dominated_list
