"""Cohort Diversity & Representativeness Engine (CI-08).

Measures coverage across agencies, geographies, and procurement models
using normalized Shannon entropy without compromising mandatory comparability.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from ..schemas import SimilarityBreakdown


class CohortDiversityEvaluator:
    """Computes multidimensional representativeness and categorical entropy."""

    def evaluate_diversity(
        self,
        peers: List[SimilarityBreakdown],
    ) -> float:
        """Computes aggregate normalized diversity score in [0.0, 1.0]."""
        if len(peers) <= 1:
            return 0.0

        dimensions = ["implementing_agency", "state", "project_type", "procurement_type"]
        entropies: List[float] = []

        for dim in dimensions:
            vals = [str(p.raw_attributes.get(dim, "")).strip().lower() for p in peers]
            vals = [v for v in vals if v]
            if len(vals) >= 2:
                entropies.append(self._normalized_entropy(vals))

        if not entropies:
            return 0.50

        return round(sum(entropies) / len(entropies), 4)

    @staticmethod
    def _normalized_entropy(categories: List[str]) -> float:
        n = len(categories)
        if n <= 1:
            return 0.0
        counts: Dict[str, int] = {}
        for c in categories:
            counts[c] = counts.get(c, 0) + 1

        k = len(counts)
        if k <= 1:
            return 0.0

        h = sum(-(cnt / n) * math.log(cnt / n) for cnt in counts.values())
        max_h = math.log(k)
        return min(1.0, max(0.0, h / max_h)) if max_h > 0 else 0.0
