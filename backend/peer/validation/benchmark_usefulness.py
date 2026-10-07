"""Benchmark Usefulness and Discriminative Power Validation Engine.

Provides quantitative empirical evidence that peer cohort benchmarks are useful:
1. Variance Reduction Ratio (VRR): Var(Cohort) / Var(Sector) < 0.60
2. Information Gain / Relative Entropy: KL divergence D_KL(P_cohort || P_sector)
3. False Alarm Reduction: Disentangling sector-wide friction from idiosyncratic project fault
4. Contextual Outlier Separation: Verifying high discriminative power for investigations
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np

from ..service import PeerIntelligenceService


@dataclass
class MetricUsefulnessResult:
    """Quantitative usefulness evaluation for an individual benchmarked metric."""
    metric_name: str
    cohort_variance: float
    sector_variance: float
    variance_reduction_ratio: float  # Var(Cohort) / Var(Sector)
    variance_reduction_pct: float
    kl_information_gain_nats: float
    is_useful: bool
    interpretation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "cohort_variance": round(self.cohort_variance, 4),
            "sector_variance": round(self.sector_variance, 4),
            "variance_reduction_ratio": round(self.variance_reduction_ratio, 4),
            "variance_reduction_pct": round(self.variance_reduction_pct, 2),
            "kl_information_gain_nats": round(self.kl_information_gain_nats, 4),
            "is_useful": self.is_useful,
            "interpretation": self.interpretation,
        }


@dataclass
class BenchmarkUsefulnessReport:
    """Consolidated empirical proof of benchmark utility."""
    target_project_code: str
    target_sector: str
    cohort_size: int
    metrics_evaluated: Dict[str, MetricUsefulnessResult]
    mean_variance_reduction_pct: float
    false_alarm_reduction_count: int
    false_alarm_reduction_pct: float
    is_benchmark_empirically_useful: bool
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_project_code": self.target_project_code,
            "target_sector": self.target_sector,
            "cohort_size": self.cohort_size,
            "metrics_evaluated": {k: v.to_dict() for k, v in self.metrics_evaluated.items()},
            "mean_variance_reduction_pct": round(self.mean_variance_reduction_pct, 2),
            "false_alarm_reduction_count": self.false_alarm_reduction_count,
            "false_alarm_reduction_pct": round(self.false_alarm_reduction_pct, 2),
            "is_benchmark_empirically_useful": self.is_benchmark_empirically_useful,
            "summary": self.summary,
        }


class BenchmarkUsefulnessValidator:
    """Validates the empirical discriminative utility of peer benchmarks."""

    def __init__(self, service: PeerIntelligenceService):
        self.service = service
        self.repository = service.repository

    def evaluate_usefulness(
        self,
        target_project: Dict[str, Any],
        metrics: Optional[List[str]] = None,
    ) -> BenchmarkUsefulnessReport:
        t_code = str(target_project.get("project_code", "")).strip()
        t_sector = str(target_project.get("sector", "")).strip()

        target_metrics = metrics or [
            "cost_overrun_pct",
            "schedule_slippage_months",
            "physical_progress_pct",
        ]

        # 1. Discover cohort
        cohort = self.service.peer_discovery(target_project)
        cohort_records = [p.raw_attributes for p in cohort.peers if p.raw_attributes]

        # 2. Retrieve all sector projects
        sector_candidates = self.repository.get_candidates(sector=t_sector, exclude_code=t_code)

        results: Dict[str, MetricUsefulnessResult] = {}
        var_reductions: List[float] = []
        false_alarm_count = 0

        for m in target_metrics:
            c_vals = [_extract_numeric(r, m) for r in cohort_records if _extract_numeric(r, m) is not None]
            s_vals = [_extract_numeric(r, m) for r in sector_candidates if _extract_numeric(r, m) is not None]

            if len(c_vals) < 3 or len(s_vals) < 3:
                continue

            c_arr = np.array(c_vals, dtype=float)
            s_arr = np.array(s_vals, dtype=float)

            var_c = float(np.var(c_arr, ddof=1)) if len(c_vals) > 1 else 0.0
            var_s = float(np.var(s_arr, ddof=1)) if len(s_vals) > 1 else 1.0

            # Guard against zero variance in synthetic tests
            var_s_effective = max(var_s, 1e-4)
            var_c_effective = max(var_c, 1e-4)

            vrr = var_c_effective / var_s_effective
            var_red_pct = max(0.0, (1.0 - vrr) * 100.0)

            # Approximate KL divergence between Gaussian approximations
            # D_KL = 0.5 * ( ln(var_s / var_c) + (var_c + (mu_c - mu_s)^2) / var_s - 1 )
            mu_c = float(np.mean(c_arr))
            mu_s = float(np.mean(s_arr))
            ratio = var_s_effective / var_c_effective
            kl_div = 0.5 * (math.log(ratio) + (var_c_effective + (mu_c - mu_s)**2) / var_s_effective - 1.0)
            kl_div = max(0.0, kl_div)

            # Check usefulness: VRR <= 0.65 or variance reduction >= 35%
            is_useful = vrr <= 0.65 or var_red_pct >= 35.0 or kl_div >= 0.15

            interp = (
                f"Peer cohort tightened dispersion by {var_red_pct:.1f}% vs broader {t_sector} sector "
                f"(VRR: {vrr:.2f}, Information Gain: {kl_div:.3f} nats)."
            )

            results[m] = MetricUsefulnessResult(
                metric_name=m,
                cohort_variance=var_c,
                sector_variance=var_s,
                variance_reduction_ratio=vrr,
                variance_reduction_pct=var_red_pct,
                kl_information_gain_nats=kl_div,
                is_useful=is_useful,
                interpretation=interp,
            )
            var_reductions.append(var_red_pct)

            # Check false alarm reduction on target
            t_val = _extract_numeric(target_project, m)
            if t_val is not None:
                # If target exceeds global/sector threshold, but is within 1 IQR of cohort median
                med_c = float(np.median(c_arr))
                iqr_c = float(np.percentile(c_arr, 75) - np.percentile(c_arr, 25))
                med_s = float(np.median(s_arr))
                if abs(t_val - med_s) > 10.0 and abs(t_val - med_c) <= max(iqr_c, 5.0):
                    false_alarm_count += 1

        mean_var_red = float(np.mean(var_reductions)) if var_reductions else 0.0
        total_metrics = len(results)
        false_alarm_pct = (false_alarm_count / total_metrics * 100.0) if total_metrics > 0 else 0.0
        empirically_useful = mean_var_red >= 25.0 or any(r.is_useful for r in results.values())

        summary = (
            f"Benchmark Usefulness: Evaluated {total_metrics} metrics for {t_code}. "
            f"Mean variance reduction: {mean_var_red:.1f}%. False alarm contextualization: {false_alarm_count}/{total_metrics}. "
            f"Empirical benchmark usefulness: {empirically_useful}."
        )

        return BenchmarkUsefulnessReport(
            target_project_code=t_code,
            target_sector=t_sector,
            cohort_size=cohort.cohort_size,
            metrics_evaluated=results,
            mean_variance_reduction_pct=mean_var_red,
            false_alarm_reduction_count=false_alarm_count,
            false_alarm_reduction_pct=false_alarm_pct,
            is_benchmark_empirically_useful=empirically_useful,
            summary=summary,
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
