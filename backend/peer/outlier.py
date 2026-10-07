"""Peer-Relative Anomaly & Outlier Analysis Engine for PAIMANA Projects.

Isolates whether an observed project pattern is genuinely anomalous relative to comparable peers:
- Strictly decouples absolute project-level risk from peer-relative deviation
- Uses outlier-resistant Modified Z-scores based on Median Absolute Deviation (MAD)
- Distinguishes high-risk-but-cohort-typical projects from moderate-risk-but-abnormal projects
- Prevents false alarms when entire sectors or agency cohorts face systemic headwinds
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .benchmark import _extract_numeric
from .schemas import (
    CohortDiscoveryResult,
    CohortQuality,
    OutlierMetricEvaluation,
    OutlierSeverity,
    PeerOutlierResult,
)

# Standard metrics evaluated for peer-relative anomalies
OUTLIER_EVAL_METRICS = [
    "risk_score",
    "cost_overrun_pct",
    "schedule_slippage_months",
    "progress_expenditure_gap_pct",
]


class PeerOutlierEngine:
    """Detects whether a project's behavior is abnormal relative to its peer cohort."""

    def __init__(self, metrics: Optional[List[str]] = None):
        self.metrics = metrics or OUTLIER_EVAL_METRICS

    def evaluate_outliers(
        self,
        target_project: Dict[str, Any],
        cohort: CohortDiscoveryResult,
    ) -> PeerOutlierResult:
        t_code = cohort.target_project_code

        if not cohort.is_sufficient or cohort.cohort_size < 3:
            return PeerOutlierResult(
                target_project_code=t_code,
                cohort_size=cohort.cohort_size,
                cohort_quality=cohort.quality,
                is_sufficient=False,
                evaluations={},
                is_overall_peer_outlier=False,
                highest_severity=OutlierSeverity.NONE,
                summary="Peer cohort is insufficient; peer-relative anomaly detection suppressed.",
                source_lineage=cohort.source_lineage,
            )

        peer_records = [p.raw_attributes for p in cohort.peers if p.raw_attributes]
        evaluations: Dict[str, OutlierMetricEvaluation] = {}
        highest_severity = OutlierSeverity.NONE
        summary_lines: List[str] = []

        for metric in self.metrics:
            t_val = _extract_numeric(target_project, metric)
            if t_val is None:
                continue

            peer_vals = [_extract_numeric(r, metric) for r in peer_records]
            valid_peer_vals = [v for v in peer_vals if v is not None]

            if len(valid_peer_vals) < 3:
                continue

            arr = np.array(valid_peer_vals, dtype=float)
            med = float(np.median(arr))
            abs_devs = np.abs(arr - med)
            mad = float(np.median(abs_devs))

            # Modified Z-Score: 0.6745 * (x - median) / MAD
            if mad > 0:
                mod_z = float(0.6745 * abs(t_val - med) / mad)
            else:
                # Fallback to IQR if MAD is zero (e.g. many identical values)
                q25, q75 = np.percentile(arr, [25, 75])
                iqr = float(q75 - q25)
                mod_z = float(abs(t_val - med) / max(iqr, 1.0))

            # Determine Outlier Severity
            if mod_z >= 3.5:
                severity = OutlierSeverity.EXTREME
                is_outlier = True
                if highest_severity != OutlierSeverity.EXTREME:
                    highest_severity = OutlierSeverity.EXTREME
            elif mod_z >= 2.2:
                severity = OutlierSeverity.MILD
                is_outlier = True
                if highest_severity == OutlierSeverity.NONE:
                    highest_severity = OutlierSeverity.MILD
            else:
                severity = OutlierSeverity.NONE
                is_outlier = False

            # Absolute Risk Classification
            abs_level = self._classify_absolute_risk(metric, t_val)

            # Peer-Relative Risk Classification
            if severity == OutlierSeverity.EXTREME:
                rel_level = "HIGH_ANOMALY"
            elif severity == OutlierSeverity.MILD:
                rel_level = "MODERATE_ANOMALY"
            else:
                rel_level = "TYPICAL_FOR_PEERS"

            # Formulate Non-Conflating Explanation
            explanation = self._formulate_distinction_explanation(
                metric, t_val, med, mod_z, abs_level, rel_level, severity
            )

            evaluations[metric] = OutlierMetricEvaluation(
                metric_name=metric,
                target_value=t_val,
                peer_median=med,
                peer_mad=mad,
                modified_z_score=mod_z,
                is_peer_outlier=is_outlier,
                severity=severity,
                absolute_risk_level=abs_level,
                peer_relative_risk_level=rel_level,
                distinction_explanation=explanation,
            )

            if is_outlier:
                summary_lines.append(explanation)

        is_overall_outlier = highest_severity != OutlierSeverity.NONE
        summary = (
            "; ".join(summary_lines)
            if summary_lines
            else f"Target project performance is consistent with peer distribution (no statistical peer anomalies detected)."
        )

        return PeerOutlierResult(
            target_project_code=t_code,
            cohort_size=cohort.cohort_size,
            cohort_quality=cohort.quality,
            is_sufficient=len(evaluations) > 0,
            evaluations=evaluations,
            is_overall_peer_outlier=is_overall_outlier,
            highest_severity=highest_severity,
            summary=summary,
            source_lineage=cohort.source_lineage,
        )

    def _classify_absolute_risk(self, metric: str, val: float) -> str:
        if metric == "risk_score":
            return "HIGH" if val >= 75.0 else ("MEDIUM" if val >= 40.0 else "LOW")
        if metric == "cost_overrun_pct":
            return "HIGH" if val >= 20.0 else ("MEDIUM" if val >= 5.0 else "LOW")
        if metric == "schedule_slippage_months":
            return "HIGH" if val >= 24.0 else ("MEDIUM" if val >= 6.0 else "LOW")
        if metric == "progress_expenditure_gap_pct":
            return "HIGH" if val >= 20.0 else ("MEDIUM" if val >= 10.0 else "LOW")
        return "MEDIUM"

    def _formulate_distinction_explanation(
        self,
        metric: str,
        t_val: float,
        med: float,
        mod_z: float,
        abs_level: str,
        rel_level: str,
        severity: OutlierSeverity,
    ) -> str:
        if abs_level == "HIGH" and rel_level == "TYPICAL_FOR_PEERS":
            return (
                f"{metric}: High absolute value ({t_val:.1f}), but TYPICAL for peer cohort "
                f"(peer median {med:.1f}, Modified Z: {mod_z:.2f}). Indicates systemic cohort conditions rather than project-isolated failure."
            )
        if abs_level in ("MEDIUM", "LOW") and rel_level in ("HIGH_ANOMALY", "MODERATE_ANOMALY"):
            return (
                f"{metric}: Moderate/Low absolute value ({t_val:.1f}), but HIGHLY UNUSUAL relative to peers "
                f"(peer median {med:.1f}, Modified Z: {mod_z:.2f}). Deserves early attention before escalating to high absolute tier."
            )
        if abs_level == "HIGH" and rel_level in ("HIGH_ANOMALY", "MODERATE_ANOMALY"):
            return (
                f"{metric}: High absolute value ({t_val:.1f}) AND SIGNIFICANT PEER ANOMALY "
                f"(peer median {med:.1f}, Modified Z: {mod_z:.2f}). Compounded project-specific risk."
            )
        return (
            f"{metric}: Value ({t_val:.1f}) aligns with peer median ({med:.1f}, Modified Z: {mod_z:.2f})."
        )
