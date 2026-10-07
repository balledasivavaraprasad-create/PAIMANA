"""Leave-One-Out Sensitivity Analysis Engine (SB-10).

Identifies influential peer projects whose removal causes disproportionate
shifts in cohort benchmark reference values (e.g. median).
"""
from __future__ import annotations

import math
from typing import Dict, List, Tuple
import numpy as np

from .schemas import SensitivityReport


class SensitivityEngine:
    """Performs leave-one-out robustness testing on peer benchmark metrics."""

    @classmethod
    def evaluate_sensitivity(
        cls,
        project_ids: List[str],
        values: List[float],
        metric_name: str,
        relative_threshold: float = 0.15,
    ) -> SensitivityReport:
        """Run leave-one-out analysis over peer metric values."""
        clean_pairs = [
            (pid, val)
            for pid, val in zip(project_ids, values)
            if val is not None and not math.isnan(val) and not math.isinf(val)
        ]

        n = len(clean_pairs)
        if n < 3:
            base_med = float(np.median([p[1] for p in clean_pairs])) if n > 0 else 0.0
            return SensitivityReport(
                metric_name=metric_name,
                base_median=base_med,
                leave_one_out_min=base_med,
                leave_one_out_max=base_med,
                sensitivity_level="LOW",
                influential_peers=[],
            )

        clean_pids = [p[0] for p in clean_pairs]
        clean_vals = np.array([p[1] for p in clean_pairs], dtype=float)

        base_median = float(np.median(clean_vals))
        loo_medians: List[float] = []
        influential_peers: List[str] = []

        denom = abs(base_median) if abs(base_median) > 1e-4 else 1.0

        for i in range(n):
            loo_subset = np.delete(clean_vals, i)
            loo_med = float(np.median(loo_subset))
            loo_medians.append(loo_med)

            shift_pct = abs(loo_med - base_median) / denom
            if shift_pct >= relative_threshold:
                influential_peers.append(clean_pids[i])

        min_loo = float(np.min(loo_medians))
        max_loo = float(np.max(loo_medians))
        max_shift_pct = max(abs(min_loo - base_median), abs(max_loo - base_median)) / denom

        if max_shift_pct >= 0.20 or len(influential_peers) >= 2:
            sensitivity_level = "HIGH"
        elif max_shift_pct >= 0.10 or len(influential_peers) >= 1:
            sensitivity_level = "MEDIUM"
        else:
            sensitivity_level = "LOW"

        return SensitivityReport(
            metric_name=metric_name,
            base_median=round(base_median, 4),
            leave_one_out_min=round(min_loo, 4),
            leave_one_out_max=round(max_loo, 4),
            sensitivity_level=sensitivity_level,
            influential_peers=influential_peers,
        )
