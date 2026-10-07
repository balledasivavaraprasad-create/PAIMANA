"""Master Deviation & Outlier Analysis Service (DO-12).

Orchestrates univariate, contextual, multivariate, and temporal anomaly detection
to produce actionable, non-conflating peer intelligence evidence for PAIMANA investigations.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Union

from .schemas import (
    AnomalySeverity,
    ConsolidatedAnomalyResult,
    MetricAnomalyReport,
    MultivariateAnomalyReport,
    TemporalDeviationReport,
)
from .deviation_metrics import DeviationCalculator
from .contextual import ContextualDetector
from .ensemble import EnsembleDetector
from .multivariate import MultivariateDetector
from .severity import SeverityEvaluator
from .temporal import TemporalAnomalyDetector
from .explanation import AnomalyExplainer
from peer.statistical.normalization import MetricNormalizer
from peer.statistical.metric_registry import MetricRegistry


DEFAULT_ANOMALY_METRICS = [
    "cost_overrun_pct",
    "schedule_slippage_months",
    "physical_progress_pct",
    "progress_expenditure_gap_pct",
]


class DeviationAndOutlierService:
    """Master service executing end-to-end deviation and outlier analysis."""

    def __init__(
        self,
        normalizer: Optional[MetricNormalizer] = None,
        registry: Optional[MetricRegistry] = None,
    ):
        self.registry = registry or MetricRegistry()
        self.normalizer = normalizer or MetricNormalizer(self.registry)

    def detect_anomalies(
        self,
        target_project: Dict[str, Any],
        cohort: Union[List[Dict[str, Any]], Any],
        metrics: Optional[List[str]] = None,
        historical_snapshots: Optional[List[Dict[str, Any]]] = None,
    ) -> ConsolidatedAnomalyResult:
        """Run complete univariate, contextual, and multivariate anomaly detection."""
        t_code = str(target_project.get("project_code") or target_project.get("id") or "TARGET")

        # Unwrap cohort records
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

        eval_metrics = metrics or DEFAULT_ANOMALY_METRICS
        univariate_reports: Dict[str, MetricAnomalyReport] = {}
        evidence_items: List[Dict[str, Any]] = []
        overall_severity = AnomalySeverity.INFO
        any_outlier = False
        limitations: List[str] = []

        if len(peer_records) < 3:
            limitations.append(f"Insufficient peer cohort size (n={len(peer_records)}). Minimum 3 required.")

        for metric_id in eval_metrics:
            defn = self.registry.get_metric(metric_id)
            direction_rule = defn.direction.value if defn else "HIGHER_IS_WORSE"
            unit = defn.unit if defn else "value"

            target_val = self.normalizer.extract_metric(target_project, metric_id)
            cohort_vals, stats = self.normalizer.extract_cohort_series(peer_records, metric_id)

            if target_val is None or len(cohort_vals) < 3:
                continue

            peer_ref = float(np.median(cohort_vals)) if cohort_vals else 0.0

            # 1. Absolute and relative deviation
            deviation = DeviationCalculator.compute_deviation(
                target_value=target_val,
                peer_reference=peer_ref,
                metric_name=metric_id,
                direction_rule=direction_rule,
                unit=unit,
            )

            # 2. Contextual Threshold Adaptation
            ctx_profile = ContextualDetector.get_contextual_profile(metric_id, target_project)

            # 3. Multi-Method Ensemble
            method_results, agreement_ratio, consensus_flagged, stat_status = (
                EnsembleDetector.evaluate_univariate_ensemble(
                    target_value=target_val,
                    cohort_values=cohort_vals,
                    direction_rule=direction_rule,
                    mod_z_threshold=ctx_profile.modified_z_threshold,
                    iqr_multiplier=ctx_profile.iqr_multiplier,
                    percentile_threshold=ctx_profile.percentile_threshold,
                )
            )

            # 4. Statistical vs Practical Severity
            prac_sig, severity, confidence = SeverityEvaluator.evaluate_severity(
                metric_name=metric_id,
                deviation=deviation,
                statistical_status=stat_status,
                agreement_ratio=agreement_ratio,
                target_project=target_project,
                sample_size=len(cohort_vals),
            )

            # 5. Narrative Explanation
            explanation = AnomalyExplainer.generate_explanation(
                metric_name=metric_id,
                deviation=deviation,
                method_results=method_results,
                statistical_status=stat_status,
                severity=severity,
                sample_size=len(cohort_vals),
            )

            # Assemble metric anomaly report
            metric_report = MetricAnomalyReport(
                metric_name=metric_id,
                deviation=deviation,
                method_results=method_results,
                agreement_ratio=agreement_ratio,
                consensus_flagged=consensus_flagged,
                statistical_status=stat_status,
                practical_significance=prac_sig,
                severity=severity,
                confidence=confidence,
                explanation=explanation,
                limitations=[],
            )
            univariate_reports[metric_id] = metric_report

            # Track overall severity
            if severity == AnomalySeverity.CRITICAL:
                overall_severity = AnomalySeverity.CRITICAL
                any_outlier = True
            elif severity == AnomalySeverity.HIGH and overall_severity != AnomalySeverity.CRITICAL:
                overall_severity = AnomalySeverity.HIGH
                any_outlier = True
            elif severity == AnomalySeverity.MODERATE and overall_severity not in (AnomalySeverity.HIGH, AnomalySeverity.CRITICAL):
                overall_severity = AnomalySeverity.MODERATE

            # Evidence item
            ev_item = AnomalyExplainer.build_supervisor_evidence_item(metric_report, t_code)
            evidence_items.append(ev_item)

        # 6. Multivariate Anomaly Detection
        multivariate_report = None
        if len(peer_records) >= 3:
            multivariate_report = MultivariateDetector.evaluate_multivariate(
                target_project=target_project,
                cohort_records=peer_records,
                metrics=eval_metrics,
            )
            if multivariate_report.anomaly_detected and overall_severity not in (AnomalySeverity.HIGH, AnomalySeverity.CRITICAL):
                overall_severity = AnomalySeverity.HIGH
                any_outlier = True

        # 7. Temporal Deviation Analysis (if history provided)
        temporal_reports: Dict[str, TemporalDeviationReport] = {}
        if historical_snapshots and len(historical_snapshots) >= 2:
            for metric_id in eval_metrics:
                hist_devs: List[Dict[str, Any]] = []
                for s in historical_snapshots:
                    s_t = self.normalizer.extract_metric(s, metric_id)
                    if s_t is not None:
                        hist_devs.append({"absolute_deviation": s_t})
                if len(hist_devs) >= 2:
                    t_rep = TemporalAnomalyDetector.evaluate_temporal_deviation(
                        target_project_code=t_code,
                        metric_name=metric_id,
                        historical_deviations=hist_devs,
                    )
                    temporal_reports[metric_id] = t_rep

        # 8. Executive Summary
        if any_outlier:
            flagged_metrics = [m for m, r in univariate_reports.items() if r.consensus_flagged]
            exec_summary = (
                f"Project {t_code} exhibits statistically significant deviations in: {', '.join(flagged_metrics)}. "
                f"Overall Severity: {overall_severity.value}. Contextualized investigation recommended."
            )
        else:
            exec_summary = f"Project {t_code} metrics are generally aligned with peer baseline distribution (Severity: {overall_severity.value})."

        return ConsolidatedAnomalyResult(
            target_project_code=t_code,
            cohort_id=cohort_id,
            cohort_size=len(peer_records),
            metrics_evaluated=eval_metrics,
            univariate_anomalies=univariate_reports,
            multivariate_anomaly=multivariate_report,
            temporal_anomalies=temporal_reports,
            overall_severity=overall_severity,
            overall_is_outlier=any_outlier,
            executive_summary=exec_summary,
            evidence_items=evidence_items,
            limitations=limitations,
        )


import numpy as np
