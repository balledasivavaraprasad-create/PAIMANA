"""Similarity & Feature Distribution Analysis Engine (CI-02, CI-3).

Computes comprehensive descriptive statistics (mean, median, IQR, CV, percentiles)
across overall similarity and individual dimensional scores to detect cohort fragmentation.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from ..schemas import SimilarityBreakdown
from .schemas import DistributionStats, SimilarityDistributionReport


class DistributionAnalyzer:
    """Computes descriptive statistical distributions for peer metrics and similarities."""

    def analyze_similarity_distribution(
        self,
        peers: List[SimilarityBreakdown],
    ) -> SimilarityDistributionReport:
        """Analyzes overall similarity distribution and individual dimension distributions."""
        if not peers:
            empty_dist = DistributionStats(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
            return SimilarityDistributionReport(
                overall_distribution=empty_dist,
                details="Empty peer cohort.",
            )

        overall_sims = [p.overall_similarity for p in peers]
        overall_stats = self.compute_stats(overall_sims)

        # Dimension-specific distributions
        dimension_vals: Dict[str, List[float]] = {}
        for p in peers:
            for dim, score in p.dimension_scores.items():
                dimension_vals.setdefault(dim, []).append(score)

        dim_stats = {dim: self.compute_stats(vals) for dim, vals in dimension_vals.items()}

        peers_above_75 = sum(1 for s in overall_sims if s >= 0.75)
        peers_above_60 = sum(1 for s in overall_sims if s >= 0.60)

        # Detect similarity fragmentation:
        # e.g., high spread with some very high (>0.85) and some very low (<0.50)
        is_fragmented = False
        if len(overall_sims) >= 4:
            has_high = any(s >= 0.85 for s in overall_sims)
            has_low = any(s < 0.50 for s in overall_sims)
            if has_high and has_low and overall_stats.iqr >= 0.20:
                is_fragmented = True

        details = (
            f"Median similarity {round(overall_stats.median, 2)} (IQR: {round(overall_stats.iqr, 2)}, "
            f"min: {round(overall_stats.min_val, 2)}, max: {round(overall_stats.max_val, 2)}). "
            f"{peers_above_75}/{len(peers)} peers above 0.75 similarity. "
            f"{'Fragmented similarity pattern detected.' if is_fragmented else 'Consistent similarity distribution.'}"
        )

        return SimilarityDistributionReport(
            overall_distribution=overall_stats,
            dimension_distributions=dim_stats,
            peers_above_75_pct=peers_above_75,
            peers_above_60_pct=peers_above_60,
            is_fragmented=is_fragmented,
            details=details,
        )

    def compute_stats(self, values: List[float]) -> DistributionStats:
        """Computes complete descriptive statistics for a series of numbers."""
        n = len(values)
        if n == 0:
            return DistributionStats(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        sorted_v = sorted(values)
        mean_val = sum(sorted_v) / n

        # Median
        median_val = self._percentile(sorted_v, 50.0)

        # Variance & Std Dev
        if n > 1:
            var = sum((x - mean_val) ** 2 for x in sorted_v) / (n - 1)
            std_dev = math.sqrt(var)
        else:
            std_dev = 0.0

        min_val = sorted_v[0]
        max_val = sorted_v[-1]

        q1 = self._percentile(sorted_v, 25.0)
        q3 = self._percentile(sorted_v, 75.0)
        iqr = max_val - min_val if n <= 2 else max(0.0, q3 - q1)

        cv = (std_dev / mean_val) if mean_val > 0 else 0.0

        percentiles = {
            "p10": self._percentile(sorted_v, 10.0),
            "p25": q1,
            "p50": median_val,
            "p75": q3,
            "p90": self._percentile(sorted_v, 90.0),
        }

        return DistributionStats(
            count=n,
            mean=mean_val,
            median=median_val,
            std_dev=std_dev,
            min_val=min_val,
            max_val=max_val,
            q1=q1,
            q3=q3,
            iqr=iqr,
            cv=cv,
            percentiles=percentiles,
        )

    @staticmethod
    def _percentile(sorted_vals: List[float], p: float) -> float:
        """Linear interpolation percentile matching standard numpy style."""
        if not sorted_vals:
            return 0.0
        if len(sorted_vals) == 1:
            return sorted_vals[0]
        k = (len(sorted_vals) - 1) * (p / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_vals[int(k)]
        d0 = sorted_vals[int(f)] * (c - k)
        d1 = sorted_vals[int(c)] * (k - f)
        return d0 + d1
