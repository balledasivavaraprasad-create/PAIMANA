"""Robust Statistical Benchmarking Engine for PAIMANA Peer Cohorts.

Calculates outlier-resistant statistical distributions across peer projects:
- Median, 25th percentile (Q1), 75th percentile (Q3), and Interquartile Range (IQR)
- Arithmetic mean, sample standard deviation, min, max, and observation counts
- Explicit tracking of missing values and metric coverage
- Zero fabrication of synthetic data points
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import numpy as np

from .schemas import (
    CohortDiscoveryResult,
    CohortQuality,
    MetricDistribution,
    PeerBenchmarkResult,
)

# Standard infrastructure metrics monitored in PAIMANA
DEFAULT_BENCHMARK_METRICS = [
    "cost_overrun_pct",
    "schedule_slippage_months",
    "physical_progress_pct",
    "cumulative_expenditure_cr",
    "original_cost_cr",
    "progress_velocity_pct_per_month",
    "burn_rate_ratio",
    "progress_expenditure_gap_pct",
    "risk_score",
]


class PeerBenchmarkEngine:
    """Computes robust statistical baselines across a validated peer cohort."""

    def __init__(self, default_metrics: Optional[List[str]] = None):
        self.default_metrics = default_metrics or DEFAULT_BENCHMARK_METRICS

    def compute_benchmarks(
        self,
        cohort: CohortDiscoveryResult,
        metrics: Optional[List[str]] = None,
    ) -> PeerBenchmarkResult:
        t_code = cohort.target_project_code
        target_metrics = metrics or self.default_metrics

        if not cohort.is_sufficient or cohort.cohort_size == 0:
            return PeerBenchmarkResult(
                target_project_code=t_code,
                cohort_size=cohort.cohort_size,
                cohort_quality=cohort.quality,
                is_sufficient=False,
                distributions={},
                notes=["Cohort is insufficient (< 3 peers); statistical benchmarking suppressed."],
                source_lineage=cohort.source_lineage,
            )

        distributions: Dict[str, MetricDistribution] = {}
        notes: List[str] = []

        # Extract peer raw attributes
        peer_records = [p.raw_attributes for p in cohort.peers if p.raw_attributes]

        for metric in target_metrics:
            vals: List[float] = []
            missing_count = 0

            for rec in peer_records:
                val = _extract_numeric(rec, metric)
                if val is not None:
                    vals.append(val)
                else:
                    missing_count += 1

            if len(vals) < 3:
                notes.append(f"Metric '{metric}' has insufficient peer observations ({len(vals)}/{len(peer_records)}).")
                continue

            arr = np.array(vals, dtype=float)
            q25, med, q75 = np.percentile(arr, [25, 50, 75])
            mean_val = float(np.mean(arr))
            std_val = float(np.std(arr, ddof=1)) if len(vals) > 1 else 0.0

            dist = MetricDistribution(
                metric_name=metric,
                count=len(vals),
                mean=mean_val,
                std=std_val,
                median=float(med),
                p25=float(q25),
                p75=float(q75),
                iqr=float(q75 - q25),
                min_val=float(np.min(arr)),
                max_val=float(np.max(arr)),
                valid_observations=len(vals),
                missing_count=missing_count,
            )
            distributions[metric] = dist

        notes.append(
            f"Computed robust statistics across {len(distributions)} metrics for cohort of {cohort.cohort_size} peers."
        )

        return PeerBenchmarkResult(
            target_project_code=t_code,
            cohort_size=cohort.cohort_size,
            cohort_quality=cohort.quality,
            is_sufficient=len(distributions) > 0,
            distributions=distributions,
            notes=notes,
            source_lineage=cohort.source_lineage,
        )


def _extract_numeric(rec: Dict[str, Any], key: str) -> Optional[float]:
    v = rec.get(key)
    if v is None or v == "" or str(v).strip() in ("(-)", "-", "nan", "None"):
        return None
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None
