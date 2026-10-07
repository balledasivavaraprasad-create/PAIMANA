"""Statistical Benchmarking Master Service (SB-12).

Orchestrates the complete statistical benchmarking pipeline:
- Normalization & metric derivation
- Robust estimators (median, MAD, IQR, trimmed mean)
- Empirical percentiles & target relative ranking
- Non-parametric bootstrap resampling & confidence intervals
- Operational small-sample guardrails
- Distribution shape & tail classification
- Temporal distribution-shift detection
- Leave-one-out sensitivity testing
- Provenance auditing & deterministic reproducibility
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Union

from .schemas import (
    DistributionShape,
    MetricBenchmarkDetail,
    SmallSampleStatus,
    StatisticalBenchmarkResult,
)
from .metric_registry import MetricRegistry
from .normalization import MetricNormalizer
from .small_sample import SmallSampleEvaluator
from .robust_statistics import RobustStatisticsEngine
from .bootstrap import BootstrapEngine
from .distributions import DistributionAnalyzer
from .shift_detection import DistributionShiftDetector
from .sensitivity import SensitivityEngine
from .reproducibility import AuditTrailEngine


DEFAULT_ANALYSIS_METRICS = [
    "cost_overrun_pct",
    "time_slippage_months",
    "physical_progress_pct",
    "expenditure_pct",
    "progress_expenditure_gap_pct",
    "progress_velocity_pct_per_month",
]


class StatisticalBenchmarkingService:
    """Master analytical service for statistical peer benchmarking."""

    def __init__(
        self,
        registry: Optional[MetricRegistry] = None,
        normalizer: Optional[MetricNormalizer] = None,
    ):
        self.registry = registry or MetricRegistry()
        self.normalizer = normalizer or MetricNormalizer(self.registry)

    def benchmark_cohort(
        self,
        target_project: Dict[str, Any],
        cohort: Union[List[Dict[str, Any]], Any],
        metrics: Optional[List[str]] = None,
        reference_cohort: Optional[List[Dict[str, Any]]] = None,
        as_of_date: Optional[str] = None,
        random_seed: int = 42,
        resample_count: int = 2000,
    ) -> StatisticalBenchmarkResult:
        """Run end-to-end statistical benchmarking across peer cohort."""
        start_time = time.time()
        target_code = str(target_project.get("project_code") or target_project.get("id") or "TARGET")

        # Unwrap cohort records if a CohortDiscoveryResult was passed
        peer_records: List[Dict[str, Any]] = []
        cohort_id = "COHORT"
        if hasattr(cohort, "peers"):
            cohort_id = getattr(cohort, "cohort_id", "COHORT")
            for p in cohort.peers:
                if hasattr(p, "raw_attributes") and p.raw_attributes:
                    peer_records.append(p.raw_attributes)
                elif isinstance(p, dict):
                    peer_records.append(p)
        elif isinstance(cohort, list):
            peer_records = cohort

        peer_codes = [
            str(p.get("project_code") or p.get("id") or f"P{idx}")
            for idx, p in enumerate(peer_records)
        ]

        target_metrics = metrics or DEFAULT_ANALYSIS_METRICS
        benchmarks: Dict[str, MetricBenchmarkDetail] = {}
        evidence_items: List[Dict[str, Any]] = []

        for metric_id in target_metrics:
            defn = self.registry.get_metric(metric_id)
            unit = defn.unit if defn else "value"
            direction = defn.direction if defn else RobustStatisticsEngine.MetricDirection.NEUTRAL

            # 1. Extract values
            cohort_vals, stats = self.normalizer.extract_cohort_series(peer_records, metric_id)
            target_val = self.normalizer.extract_metric(target_project, metric_id)

            # 2. Small-sample evaluation
            status, eff_n, warnings = SmallSampleEvaluator.evaluate_sample_size(cohort_vals)

            if not SmallSampleEvaluator.can_compute_benchmarks(status):
                # Insufficient sample: suppress estimations
                detail = MetricBenchmarkDetail(
                    metric_name=metric_id,
                    unit=unit,
                    direction=direction,
                    count=len(cohort_vals),
                    effective_sample_size=eff_n,
                    missing_count=stats["missing_count"],
                    mean=0.0,
                    median=0.0,
                    trimmed_mean=0.0,
                    std=0.0,
                    mad=0.0,
                    iqr=0.0,
                    cv=0.0,
                    skewness=0.0,
                    kurtosis=0.0,
                    distribution_shape=DistributionShape.UNKNOWN,
                    percentiles={"p10": 0.0, "p25": 0.0, "p50": 0.0, "p75": 0.0, "p90": 0.0},
                    confidence_interval=None,
                    bootstrap=None,
                    target_percentile=None,
                    sensitivity=None,
                    small_sample_status=status,
                    warnings=warnings,
                )
                benchmarks[metric_id] = detail
                continue

            # 3. Robust Estimators
            ct = RobustStatisticsEngine.compute_central_tendency(cohort_vals)
            disp = RobustStatisticsEngine.compute_dispersion(cohort_vals)
            pcts = RobustStatisticsEngine.compute_percentiles(cohort_vals)

            # 4. Distribution Shape Analysis
            if SmallSampleEvaluator.can_fit_distribution_shape(status):
                skew_val, kurt_val, shape, _ = DistributionAnalyzer.analyze_distribution(cohort_vals)
            else:
                skew_val, kurt_val, shape = 0.0, 0.0, DistributionShape.UNKNOWN

            # 5. Bootstrap & Analytical Confidence Intervals
            bootstrap_summary = None
            analytical_ci = None
            if SmallSampleEvaluator.can_compute_bootstrap(status):
                bootstrap_summary = BootstrapEngine.compute_bootstrap_interval(
                    cohort_vals,
                    statistic="median",
                    resample_count=resample_count,
                    random_seed=random_seed,
                )
                analytical_ci = BootstrapEngine.compute_analytical_mean_ci(cohort_vals)

            # 6. Target Percentile Ranking
            target_percentile = None
            if target_val is not None:
                target_percentile = RobustStatisticsEngine.evaluate_target_percentile(
                    target_value=target_val,
                    cohort_values=cohort_vals,
                    metric_name=metric_id,
                    direction=direction,
                )

            # 7. Leave-One-Out Sensitivity Testing
            sensitivity_rep = SensitivityEngine.evaluate_sensitivity(
                project_ids=peer_codes,
                values=cohort_vals,
                metric_name=metric_id,
            )

            detail = MetricBenchmarkDetail(
                metric_name=metric_id,
                unit=unit,
                direction=direction,
                count=len(cohort_vals),
                effective_sample_size=eff_n,
                missing_count=stats["missing_count"],
                mean=ct["mean"],
                median=ct["median"],
                trimmed_mean=ct["trimmed_mean"],
                std=disp["std"],
                mad=disp["mad"],
                iqr=disp["iqr"],
                cv=disp["cv"],
                skewness=skew_val,
                kurtosis=kurt_val,
                distribution_shape=shape,
                percentiles=pcts,
                confidence_interval=analytical_ci,
                bootstrap=bootstrap_summary,
                target_percentile=target_percentile,
                sensitivity=sensitivity_rep,
                small_sample_status=status,
                warnings=warnings,
            )
            benchmarks[metric_id] = detail

            # 8. Evidence Item Generation
            if target_percentile is not None:
                is_outlier = target_percentile.interpretation in (
                    "SIGNIFICANTLY_ABOVE",
                    "SIGNIFICANTLY_BELOW",
                )
                if target_percentile.percentile_rank >= 85.0:
                    risk_level = "SIGNIFICANTLY_ABOVE_PEERS"
                elif target_percentile.percentile_rank <= 15.0:
                    risk_level = "SIGNIFICANTLY_BELOW_PEERS"
                elif 40.0 <= target_percentile.percentile_rank <= 60.0:
                    risk_level = "TYPICAL_FOR_PEERS"
                else:
                    risk_level = "MODERATE_DEVIATION"

                evidence = {
                    "source": "statistical_peer_benchmark",
                    "metric_name": metric_id,
                    "target_value": round(target_val, 4),
                    "peer_median": round(ct["median"], 4),
                    "peer_mad": round(disp["mad"], 4),
                    "percentile_rank": round(target_percentile.percentile_rank, 2),
                    "relative_position": target_percentile.interpretation,
                    "is_peer_outlier": is_outlier,
                    "peer_relative_risk_level": risk_level,
                    "sample_size": eff_n,
                    "confidence_interval_median": (
                        bootstrap_summary.confidence_interval.to_dict()
                        if bootstrap_summary
                        else None
                    ),
                }
                evidence_items.append(evidence)

        # 9. Audit Metadata
        audit_meta = AuditTrailEngine.build_audit_metadata(
            target_project_code=target_code,
            peer_codes=peer_codes,
            metric_names=target_metrics,
            random_seed=random_seed,
            resample_count=resample_count,
            start_time=start_time,
            extra_info={"as_of_date": as_of_date, "cohort_id": cohort_id},
        )

        return StatisticalBenchmarkResult(
            target_project_code=target_code,
            cohort_id=cohort_id,
            cohort_size=len(peer_records),
            as_of_date=as_of_date,
            metrics_analyzed=target_metrics,
            benchmarks=benchmarks,
            audit_metadata=audit_meta,
            evidence_items=evidence_items,
        )

    def detect_distribution_shift(
        self,
        current_cohort: List[Dict[str, Any]],
        reference_cohort: List[Dict[str, Any]],
        metric_id: str,
    ) -> Any:
        """Evaluate temporal distribution shift between current and reference cohorts."""
        curr_vals, _ = self.normalizer.extract_cohort_series(current_cohort, metric_id)
        ref_vals, _ = self.normalizer.extract_cohort_series(reference_cohort, metric_id)
        return DistributionShiftDetector.evaluate_shift(
            current_values=curr_vals,
            reference_values=ref_vals,
            metric_name=metric_id,
        )
