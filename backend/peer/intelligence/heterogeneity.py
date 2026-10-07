"""Cohort Heterogeneity & Feature Variation Analysis Engine (CI-03, CI-4).

Quantifies within-cohort divergence across numerical variation (CV, IQR)
and categorical entropy (normalized Shannon entropy) conditioned on the active investigation.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from ..discovery.strategy_registry import PeerStrategyDefinition
from ..schemas import SimilarityBreakdown
from .schemas import HeterogeneityReport


class CohortHeterogeneityAnalyzer:
    """Analyzes variance, entropy, and cross-peer divergence within a cohort."""

    def analyze_heterogeneity(
        self,
        peers: List[SimilarityBreakdown],
        strategy: Optional[PeerStrategyDefinition] = None,
    ) -> HeterogeneityReport:
        """Evaluates heterogeneity across relevant numerical and categorical dimensions."""
        if len(peers) < 2:
            return HeterogeneityReport(
                overall_level="LOW",
                important_dimensions=[],
                numerical_variation={},
                categorical_entropy={},
                summary="Cohort has fewer than 2 peers; heterogeneity analysis not applicable.",
            )

        important_dims = (
            list(strategy.dimension_weights.keys())
            if strategy
            else ["original_cost", "project_type", "implementing_agency", "state", "execution_stage"]
        )

        num_variation: Dict[str, float] = {}
        cat_entropy: Dict[str, float] = {}
        affected_peers: List[str] = []

        # 1. Numerical variation
        # Cost CV
        costs = [float(p.raw_attributes.get("original_cost") or p.raw_attributes.get("cost") or 0) for p in peers]
        costs = [c for c in costs if c > 0]
        if len(costs) >= 2:
            mean_c = sum(costs) / len(costs)
            var_c = sum((c - mean_c) ** 2 for c in costs) / (len(costs) - 1)
            std_c = math.sqrt(var_c)
            cost_cv = std_c / mean_c if mean_c > 0 else 0.0
            num_variation["cost_cv"] = round(cost_cv, 4)
            # Check for scale outliers (> 3x mean)
            for p in peers:
                val = float(p.raw_attributes.get("original_cost") or p.raw_attributes.get("cost") or 0)
                if val > 0 and (val > 3.0 * mean_c or val < 0.25 * mean_c):
                    if p.peer_code not in affected_peers:
                        affected_peers.append(p.peer_code)

        # Progress IQR
        progs = [float(p.raw_attributes.get("physical_progress") or p.raw_attributes.get("progress") or 0) for p in peers]
        if len(progs) >= 2:
            sorted_p = sorted(progs)
            p_iqr = sorted_p[int(len(sorted_p) * 0.75)] - sorted_p[int(len(sorted_p) * 0.25)]
            num_variation["progress_iqr"] = round(p_iqr, 2)

        # 2. Categorical entropy
        cat_fields = ["project_type", "implementing_agency", "state", "procurement_type"]
        for field_name in cat_fields:
            vals = [str(p.raw_attributes.get(field_name, "")).strip().lower() for p in peers]
            vals = [v for v in vals if v]
            if vals:
                cat_entropy[field_name] = round(self._normalized_entropy(vals), 4)

        # 3. Overall Heterogeneity Level Assessment
        # High cost CV (> 0.60) or high category entropy (> 0.75 in multiple key fields)
        cost_high = num_variation.get("cost_cv", 0.0) >= 0.55
        high_entropy_count = sum(1 for e in cat_entropy.values() if e >= 0.75)

        if cost_high or high_entropy_count >= 2:
            overall_level = "HIGH"
            summary = (
                f"HIGH heterogeneity detected: significant divergence in cost scale (CV: {num_variation.get('cost_cv', 0)}) "
                f"and categorical entropy across {high_entropy_count} dimensions. Subgroup benchmarking recommended."
            )
        elif num_variation.get("cost_cv", 0.0) >= 0.35 or high_entropy_count >= 1:
            overall_level = "MODERATE"
            summary = f"MODERATE heterogeneity: balanced peer cohort with moderate variation across {len(important_dims)} dimensions."
        else:
            overall_level = "LOW"
            summary = "LOW heterogeneity: peer cohort is tightly grouped and statistically homogeneous."

        return HeterogeneityReport(
            overall_level=overall_level,
            important_dimensions=important_dims,
            numerical_variation=num_variation,
            categorical_entropy=cat_entropy,
            affected_peer_codes=affected_peers,
            summary=summary,
        )

    @staticmethod
    def _normalized_entropy(categories: List[str]) -> float:
        """Calculates normalized Shannon entropy H / ln(k) in [0.0, 1.0]."""
        n = len(categories)
        if n <= 1:
            return 0.0
        counts: Dict[str, int] = {}
        for c in categories:
            counts[c] = counts.get(c, 0) + 1

        k = len(counts)
        if k <= 1:
            return 0.0

        h = 0.0
        for cnt in counts.values():
            p_i = cnt / n
            h -= p_i * math.log(p_i)

        max_h = math.log(k)
        return min(1.0, max(0.0, h / max_h)) if max_h > 0 else 0.0
