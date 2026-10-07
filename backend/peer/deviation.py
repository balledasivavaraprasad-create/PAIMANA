"""Target-vs-Peer Deviation Analysis Engine for PAIMANA Projects.

Exposes analytical signals comparing target project performance against peer baselines:
- Absolute and percentage differences against peer median & IQR boundaries
- Percentile rank of target project within the peer cohort
- Directional classification (AHEAD, LAGGING, HIGHER, LOWER, ALIGNED)
- Significance thresholding without automatically triggering alerts
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import numpy as np

from .benchmark import _extract_numeric
from .schemas import (
    DeviationDirection,
    MetricDeviation,
    PeerBenchmarkResult,
    PeerDeviationResult,
)

# Metrics where a higher value indicates worse project performance
ADVERSE_WHEN_HIGH = {
    "cost_overrun_pct",
    "schedule_slippage_months",
    "progress_expenditure_gap_pct",
    "risk_score",
    "burn_rate_ratio",
}

# Metrics where a higher value indicates better project performance
FAVORABLE_WHEN_HIGH = {
    "physical_progress_pct",
    "progress_velocity_pct_per_month",
}


class PeerDeviationEngine:
    """Calculates granular deviations of a target project against peer cohort benchmarks."""

    def analyze_deviations(
        self,
        target_project: Dict[str, Any],
        benchmarks: PeerBenchmarkResult,
        peer_raw_values: Optional[Dict[str, List[float]]] = None,
    ) -> PeerDeviationResult:
        t_code = benchmarks.target_project_code

        if not benchmarks.is_sufficient or not benchmarks.distributions:
            return PeerDeviationResult(
                target_project_code=t_code,
                cohort_size=benchmarks.cohort_size,
                cohort_quality=benchmarks.cohort_quality,
                is_sufficient=False,
                deviations={},
                summary="Insufficient peer benchmark data; target deviation analysis cannot be performed.",
                source_lineage=benchmarks.source_lineage,
            )

        deviations: Dict[str, MetricDeviation] = {}
        summary_points: List[str] = []

        for metric, dist in benchmarks.distributions.items():
            t_val = _extract_numeric(target_project, metric)

            if t_val is None:
                deviations[metric] = MetricDeviation(
                    metric_name=metric,
                    target_value=None,
                    peer_median=dist.median,
                    peer_p25=dist.p25,
                    peer_p75=dist.p75,
                    absolute_difference=None,
                    relative_difference=None,
                    percentile_rank=None,
                    direction=DeviationDirection.INCONCLUSIVE,
                    is_significant=False,
                    interpretation=f"Target project lacks observation for '{metric}'.",
                )
                continue

            abs_diff = t_val - dist.median
            rel_diff = abs_diff / max(abs(dist.median), 1.0)

            # Compute target's percentile rank within peer distribution
            pct_rank = 0.5
            if peer_raw_values and metric in peer_raw_values and peer_raw_values[metric]:
                raw_list = sorted(peer_raw_values[metric])
                pct_rank = float(np.searchsorted(raw_list, t_val, side="right") / len(raw_list))
            else:
                # Approximation from median & IQR if raw values not provided
                if dist.iqr > 0:
                    pct_rank = float(np.clip(0.5 + ((t_val - dist.median) / (2.0 * dist.iqr)), 0.0, 1.0))
                else:
                    pct_rank = 1.0 if t_val > dist.median else (0.0 if t_val < dist.median else 0.5)

            # Classify Direction and Significance
            direction, is_sig, interp = self._classify_deviation(metric, t_val, dist, abs_diff, rel_diff)

            deviations[metric] = MetricDeviation(
                metric_name=metric,
                target_value=t_val,
                peer_median=dist.median,
                peer_p25=dist.p25,
                peer_p75=dist.p75,
                absolute_difference=abs_diff,
                relative_difference=rel_diff,
                percentile_rank=pct_rank,
                direction=direction,
                is_significant=is_sig,
                interpretation=interp,
            )

            if is_sig:
                summary_points.append(interp)

        summary = (
            "; ".join(summary_points)
            if summary_points
            else f"Target project performance is closely aligned with peer cohort median across monitored metrics."
        )

        return PeerDeviationResult(
            target_project_code=t_code,
            cohort_size=benchmarks.cohort_size,
            cohort_quality=benchmarks.cohort_quality,
            is_sufficient=True,
            deviations=deviations,
            summary=summary,
            source_lineage=benchmarks.source_lineage,
        )

    def _classify_deviation(
        self, metric: str, t_val: float, dist: Any, abs_diff: float, rel_diff: float
    ) -> Tuple[DeviationDirection, bool, str]:
        # High is adverse: cost overrun, slippage, expenditure gap, risk
        if metric in ADVERSE_WHEN_HIGH:
            if t_val > dist.p75:
                direction = DeviationDirection.SIGNIFICANTLY_ABOVE_PEERS
                is_sig = True
                interp = f"Exceeds 75th percentile of peers in {metric} ({t_val:.1f} vs peer median {dist.median:.1f})"
            elif t_val > dist.median:
                direction = DeviationDirection.HIGHER_THAN_PEERS
                is_sig = abs(rel_diff) >= 0.20
                interp = f"Moderately above peer median in {metric} ({t_val:.1f} vs {dist.median:.1f})"
            elif t_val < dist.p25:
                direction = DeviationDirection.SIGNIFICANTLY_BELOW_PEERS
                is_sig = True
                interp = f"Favorable: Below 25th percentile of peers in {metric} ({t_val:.1f} vs {dist.median:.1f})"
            else:
                direction = DeviationDirection.ALIGNED_WITH_PEERS
                is_sig = False
                interp = f"Aligned with peer median in {metric} ({t_val:.1f} vs {dist.median:.1f})"
            return direction, is_sig, interp

        # High is favorable: physical progress, velocity
        if metric in FAVORABLE_WHEN_HIGH:
            if t_val < dist.p25:
                direction = DeviationDirection.LAGGING_PEERS
                is_sig = True
                interp = f"Lagging peers: Below 25th percentile in {metric} ({t_val:.1f}% vs peer median {dist.median:.1f}%)"
            elif t_val > dist.p75:
                direction = DeviationDirection.AHEAD_OF_PEERS
                is_sig = True
                interp = f"Ahead of peers: Exceeds 75th percentile in {metric} ({t_val:.1f}% vs peer median {dist.median:.1f}%)"
            else:
                direction = DeviationDirection.ALIGNED_WITH_PEERS
                is_sig = False
                interp = f"Aligned with peer baseline in {metric} ({t_val:.1f}% vs {dist.median:.1f}%)"
            return direction, is_sig, interp

        # Neutral metrics (e.g. original cost, expenditure)
        if abs(rel_diff) >= 0.30:
            direction = (
                DeviationDirection.HIGHER_THAN_PEERS
                if abs_diff > 0
                else DeviationDirection.LOWER_THAN_PEERS
            )
            is_sig = True
            interp = f"Distinct from peer median in {metric} ({t_val:.1f} vs {dist.median:.1f})"
        else:
            direction = DeviationDirection.ALIGNED_WITH_PEERS
            is_sig = False
            interp = f"Comparable to peer scale in {metric} ({t_val:.1f} vs {dist.median:.1f})"

        return direction, is_sig, interp
