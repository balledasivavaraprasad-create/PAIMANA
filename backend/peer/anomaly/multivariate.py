"""Multivariate Anomaly Detection Engine (DO-07).

Detects multi-metric joint anomalies using regularized Mahalanobis distance
with small-sample dimensionality safeguards and feature contribution attribution.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats

from .schemas import (
    AnomalyMethod,
    AnomalySeverity,
    MultivariateAnomalyReport,
)


DEFAULT_MULTIVARIATE_METRICS = [
    "cost_overrun_pct",
    "schedule_slippage_months",
    "physical_progress_pct",
    "progress_expenditure_gap_pct",
]


class MultivariateDetector:
    """Multivariate anomaly detection using regularized Mahalanobis distance."""

    @classmethod
    def evaluate_multivariate(
        cls,
        target_project: Dict[str, Any],
        cohort_records: List[Dict[str, Any]],
        metrics: Optional[List[str]] = None,
        alpha: float = 0.01,
        regularization: float = 1e-3,
    ) -> MultivariateAnomalyReport:
        """Evaluate multivariate anomaly profile across selected metrics."""
        t_code = str(target_project.get("project_code") or "TARGET")
        eval_metrics = metrics or DEFAULT_MULTIVARIATE_METRICS

        # 1. Extract target feature vector
        target_vec: List[float] = []
        active_metrics: List[str] = []

        for m in eval_metrics:
            val = cls._extract_val(target_project, m)
            if val is not None:
                target_vec.append(val)
                active_metrics.append(m)

        p = len(active_metrics)
        if p < 2:
            return MultivariateAnomalyReport(
                target_project_code=t_code,
                method=AnomalyMethod.MAHALANOBIS,
                distance_or_score=0.0,
                threshold=0.0,
                anomaly_detected=False,
                contributing_metrics=[],
                severity=AnomalySeverity.INFO,
                interpretation="At least 2 valid metric dimensions required for multivariate anomaly detection.",
                limitations=["INSUFFICIENT_FEATURE_DIMENSIONS"],
            )

        # 2. Extract cohort matrix
        cohort_matrix: List[List[float]] = []
        for rec in cohort_records:
            row: List[float] = []
            has_all = True
            for m in active_metrics:
                v = cls._extract_val(rec, m)
                if v is not None:
                    row.append(v)
                else:
                    has_all = False
                    break
            if has_all:
                cohort_matrix.append(row)

        n = len(cohort_matrix)
        limitations: List[str] = []

        # 3. Small-sample vs Dimensionality Safeguard
        # If n <= p + 1, Mahalanobis is structurally underdetermined; fallback to composite distance
        if n <= p + 1:
            limitations.append(f"Cohort sample size (n={n}) is too small for p={p} covariance matrix estimation.")
            return cls._fallback_composite_distance(
                target_code=t_code,
                target_vec=target_vec,
                cohort_matrix=cohort_matrix,
                metrics=active_metrics,
                limitations=limitations,
            )

        X = np.array(cohort_matrix, dtype=float)
        x_target = np.array(target_vec, dtype=float)

        mu = np.mean(X, axis=0)
        cov = np.cov(X, rowvar=False)

        # 4. Regularization to ensure positive definiteness and invertible covariance
        if p == 1:
            cov = np.array([[cov]])
        cov_reg = cov + (regularization * np.eye(p))

        try:
            inv_cov = np.linalg.pinv(cov_reg)
            diff = x_target - mu
            dist_sq = float(np.dot(np.dot(diff, inv_cov), diff.T))
            dist = float(math.sqrt(max(0.0, dist_sq)))
        except Exception:
            limitations.append("Covariance matrix inversion failed; fell back to composite distance.")
            return cls._fallback_composite_distance(
                target_code=t_code,
                target_vec=target_vec,
                cohort_matrix=cohort_matrix,
                metrics=active_metrics,
                limitations=limitations,
            )

        # Critical value from chi-square distribution with p degrees of freedom
        crit_chi2 = float(stats.chi2.ppf(1.0 - alpha, df=p))
        crit_dist = float(math.sqrt(crit_chi2))

        anomaly_detected = dist >= crit_dist

        # Identify contributing metrics (relative standardized deviation from mean)
        contributing: List[str] = []
        std_diag = np.sqrt(np.diag(cov_reg))
        rel_diffs = np.abs(diff) / np.maximum(std_diag, 1e-4)
        for idx, m in enumerate(active_metrics):
            if rel_diffs[idx] >= 1.5:
                contributing.append(m)

        if anomaly_detected:
            severity = AnomalySeverity.HIGH if dist >= 1.3 * crit_dist else AnomalySeverity.MODERATE
            interp = (
                f"Unusual joint multivariate profile detected (Mahalanobis D={dist:.2f} >= threshold {crit_dist:.2f}, p={p}). "
                f"Primary contributing dimensions: {', '.join(contributing) if contributing else 'joint correlation'}."
            )
        else:
            severity = AnomalySeverity.INFO
            interp = f"Joint multivariate metric profile is consistent with peer correlation baseline (D={dist:.2f} < threshold {crit_dist:.2f})."

        return MultivariateAnomalyReport(
            target_project_code=t_code,
            method=AnomalyMethod.MAHALANOBIS,
            distance_or_score=round(dist, 4),
            threshold=round(crit_dist, 4),
            anomaly_detected=anomaly_detected,
            contributing_metrics=contributing,
            severity=severity,
            interpretation=interp,
            limitations=limitations,
        )

    @classmethod
    def _fallback_composite_distance(
        cls,
        target_code: str,
        target_vec: List[float],
        cohort_matrix: List[List[float]],
        metrics: List[str],
        limitations: List[str],
    ) -> MultivariateAnomalyReport:
        """Composite standardized Euclidean distance fallback when sample size is insufficient for covariance."""
        if not cohort_matrix:
            return MultivariateAnomalyReport(
                target_project_code=target_code,
                method=AnomalyMethod.MULTIVARIATE_COMPOSITE,
                distance_or_score=0.0,
                threshold=2.0,
                anomaly_detected=False,
                contributing_metrics=[],
                severity=AnomalySeverity.INFO,
                interpretation="Insufficient peer records for multivariate evaluation.",
                limitations=limitations + ["ZERO_PEER_RECORDS"],
            )

        X = np.array(cohort_matrix, dtype=float)
        x_target = np.array(target_vec, dtype=float)

        medians = np.median(X, axis=0)
        mads = np.median(np.abs(X - medians), axis=0)
        mads = np.where(mads < 1e-4, 1.0, mads)

        # Standardized robust z-score per dimension
        z_scores = 0.6745 * np.abs(x_target - medians) / mads
        composite_score = float(np.mean(z_scores))
        threshold = 2.5

        anomaly_detected = composite_score >= threshold
        contributing = [metrics[i] for i, z in enumerate(z_scores) if z >= 2.0]

        severity = AnomalySeverity.MODERATE if anomaly_detected else AnomalySeverity.INFO
        interp = (
            f"Composite standardized deviation: {composite_score:.2f} ({'ANOMALOUS' if anomaly_detected else 'NORMAL'}). "
            "Evaluated using robust marginal composite due to small cohort sample size."
        )

        return MultivariateAnomalyReport(
            target_project_code=target_code,
            method=AnomalyMethod.MULTIVARIATE_COMPOSITE,
            distance_or_score=round(composite_score, 4),
            threshold=threshold,
            anomaly_detected=anomaly_detected,
            contributing_metrics=contributing,
            severity=severity,
            interpretation=interp,
            limitations=limitations,
        )

    @classmethod
    def _extract_val(cls, p: Dict[str, Any], metric: str) -> Optional[float]:
        from peer.statistical.normalization import MetricNormalizer
        norm = getattr(cls, "_norm_instance", None)
        if norm is None:
            norm = MetricNormalizer()
            cls._norm_instance = norm
        return norm.extract_metric(p, metric)
