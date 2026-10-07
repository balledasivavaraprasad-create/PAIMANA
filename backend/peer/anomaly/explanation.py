"""Anomaly Explanation & Structured Evidence Attribution (DO-11).

Generates non-conflating narrative explanations and Supervisor evidence items
conforming to CONTEXTUALIZES semantics without causal overreach.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .schemas import (
    AnomalySeverity,
    DeviationResult,
    MethodDetectionDetail,
    MetricAnomalyReport,
)


class AnomalyExplainer:
    """Produces explainable summaries and formal Supervisor evidence items."""

    @classmethod
    def generate_explanation(
        cls,
        metric_name: str,
        deviation: DeviationResult,
        method_results: Dict[str, MethodDetectionDetail],
        statistical_status: str,
        severity: AnomalySeverity,
        sample_size: int,
    ) -> str:
        """Formulate a transparent narrative explanation."""
        t_val = deviation.target_value
        p_ref = deviation.peer_reference
        abs_diff = deviation.absolute_deviation
        unit_label = "percentage points" if deviation.is_unit_percentage_points else deviation.unit

        flagged_methods = [
            m for m, r in method_results.items() if r.flagged
        ]

        if statistical_status == "STATISTICAL_OUTLIER":
            expl = (
                f"{metric_name}: STATISTICAL ANOMALY ({severity.value} severity). "
                f"Target ({t_val:.1f}) deviates by {abs_diff:+.1f} {unit_label} from peer median ({p_ref:.1f}). "
                f"Flagged by {len(flagged_methods)}/{len(method_results)} applicable detection methods "
                f"({', '.join(flagged_methods)})."
            )
        elif statistical_status == "MODERATE_DEVIATION":
            expl = (
                f"{metric_name}: Moderate peer divergence ({severity.value} severity). "
                f"Target ({t_val:.1f}) is {abs_diff:+.1f} {unit_label} vs peer median ({p_ref:.1f}). "
                f"Methods agreeing: {', '.join(flagged_methods) if flagged_methods else 'None'}."
            )
        else:
            expl = (
                f"{metric_name}: Normal peer variation. "
                f"Target ({t_val:.1f}) aligns with peer median ({p_ref:.1f}, diff: {abs_diff:+.1f} {unit_label})."
            )

        if sample_size < 10:
            expl += f" (Note: Evaluated against small peer cohort of n={sample_size})."

        return expl

    @classmethod
    def build_supervisor_evidence_item(
        cls,
        report: MetricAnomalyReport,
        target_project_code: str,
    ) -> Dict[str, Any]:
        """Convert a metric anomaly report into a structured Supervisor evidence item."""
        is_outlier = report.statistical_status == "STATISTICAL_OUTLIER" or report.consensus_flagged
        dev = report.deviation

        # Map to Supervisor risk levels
        if report.severity in (AnomalySeverity.HIGH, AnomalySeverity.CRITICAL):
            risk_level = "SIGNIFICANTLY_ABOVE_PEERS"
        elif report.severity == AnomalySeverity.MODERATE:
            risk_level = "MODERATE_DEVIATION"
        else:
            risk_level = "TYPICAL_FOR_PEERS"

        return {
            "source": "peer_anomaly_detection",
            "type": "PEER_ANOMALY_EVALUATION",
            "metric_name": report.metric_name,
            "target_project_code": target_project_code,
            "target_value": dev.target_value,
            "peer_median": dev.peer_reference,
            "absolute_deviation": dev.absolute_deviation,
            "relative_deviation_pct": dev.relative_deviation_pct,
            "statistical_status": report.statistical_status,
            "practical_significance": report.practical_significance.value,
            "severity": report.severity.value,
            "confidence": report.confidence,
            "is_peer_outlier": is_outlier,
            "peer_relative_risk_level": risk_level,
            "agreement_ratio": report.agreement_ratio,
            "relation": "CONTEXTUALIZES",
            "statement": report.explanation,
            "limitations": report.limitations,
        }
