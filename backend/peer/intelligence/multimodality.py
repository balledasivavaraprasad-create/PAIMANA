"""Multimodality Detection Engine for Cohort Metrics (CI-05, CI-7).

Detects distinct peaks and bimodal distributions in project metrics
(e.g., 36-month vs 72-month duration clusters) to prevent misleading single-mean benchmarks.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..schemas import SimilarityBreakdown
from .schemas import MultimodalityReport


class MultimodalityDetector:
    """Analyzes metric distributions for multiple distinct modes/peaks."""

    def analyze_metric(
        self,
        peers: List[SimilarityBreakdown],
        metric_name: str,
        min_peers_for_multimodality: int = 6,
    ) -> MultimodalityReport:
        """Evaluates whether the distribution of metric_name contains multiple distinct peaks."""
        values: List[float] = []
        for p in peers:
            v = p.raw_attributes.get(metric_name)
            if v is not None:
                try:
                    values.append(float(v))
                except (ValueError, TypeError):
                    pass

        if len(values) < min_peers_for_multimodality:
            return MultimodalityReport(
                metric=metric_name,
                is_multimodal=False,
                modes=[sum(values) / len(values)] if values else [],
                confidence="LOW",
                recommended_action="UNIFIED_BASELINE",
            )

        values.sort()
        min_v = values[0]
        max_v = values[-1]
        val_range = max_v - min_v

        if val_range < 1e-4:
            return MultimodalityReport(
                metric=metric_name,
                is_multimodal=False,
                modes=[min_v],
                confidence="HIGH",
                recommended_action="UNIFIED_BASELINE",
            )

        # 6-bin histogram density estimation
        num_bins = 6
        bin_width = val_range / num_bins
        bins = [0] * num_bins
        for val in values:
            idx = min(num_bins - 1, int((val - min_v) / bin_width))
            bins[idx] += 1

        # Peak detection: a peak is a bin that is strictly greater than its neighbors
        # and has at least 2 observations
        peaks = []
        for i in range(num_bins):
            left_ok = (i == 0 or bins[i] > bins[i - 1])
            right_ok = (i == num_bins - 1 or bins[i] > bins[i + 1])
            if left_ok and right_ok and bins[i] >= 2:
                # Mode value is the midpoint of the bin
                mode_val = min_v + (i + 0.5) * bin_width
                peaks.append(mode_val)

        is_multimodal = len(peaks) >= 2
        confidence = "HIGH" if len(values) >= 10 and is_multimodal else ("MEDIUM" if is_multimodal else "HIGH")

        return MultimodalityReport(
            metric=metric_name,
            is_multimodal=is_multimodal,
            modes=peaks if is_multimodal else ([sum(values) / len(values)] if values else []),
            confidence=confidence,
            recommended_action="SUBGROUP_ANALYSIS" if is_multimodal else "UNIFIED_BASELINE",
        )
