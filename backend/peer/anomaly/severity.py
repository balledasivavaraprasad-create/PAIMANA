"""Statistical vs Practical Severity Evaluator (DO-08).

Decouples statistical unusualness (distributional deviation) from practical significance
(real-world operational and financial impact) to produce calibrated anomaly severity.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .schemas import (
    AnomalySeverity,
    DeviationResult,
    PracticalSignificance,
)


class SeverityEvaluator:
    """Evaluates combined operational severity from statistical and practical dimensions."""

    @classmethod
    def evaluate_severity(
        cls,
        metric_name: str,
        deviation: DeviationResult,
        statistical_status: str,
        agreement_ratio: float,
        target_project: Dict[str, Any],
        sample_size: int,
    ) -> tuple[PracticalSignificance, AnomalySeverity, str]:
        """Compute practical significance, overall severity, and evaluation confidence.

        Returns (practical_significance, overall_severity, confidence).
        """
        # 1. Practical Significance Assessment
        abs_dev = abs(deviation.absolute_deviation)
        target_val = deviation.target_value
        prac_sig = PracticalSignificance.NEGLIGIBLE

        if metric_name == "cost_overrun_pct":
            orig_cost = float(target_project.get("original_cost_cr") or target_project.get("original_cost") or 0.0)
            escalation_cr = (abs_dev / 100.0) * orig_cost if orig_cost > 0 else 0.0

            if abs_dev >= 30.0 or escalation_cr >= 250.0:
                prac_sig = PracticalSignificance.CRITICAL
            elif abs_dev >= 15.0 or escalation_cr >= 100.0:
                prac_sig = PracticalSignificance.HIGH
            elif abs_dev >= 8.0:
                prac_sig = PracticalSignificance.MEDIUM
            elif abs_dev >= 3.0:
                prac_sig = PracticalSignificance.LOW
            else:
                prac_sig = PracticalSignificance.NEGLIGIBLE

        elif metric_name in ("schedule_slippage_months", "time_slippage_months"):
            if abs_dev >= 24.0 or target_val >= 36.0:
                prac_sig = PracticalSignificance.CRITICAL
            elif abs_dev >= 12.0 or target_val >= 18.0:
                prac_sig = PracticalSignificance.HIGH
            elif abs_dev >= 6.0:
                prac_sig = PracticalSignificance.MEDIUM
            elif abs_dev >= 2.0:
                prac_sig = PracticalSignificance.LOW
            else:
                prac_sig = PracticalSignificance.NEGLIGIBLE

        elif metric_name in ("progress_expenditure_gap_pct", "expenditure_progress_gap"):
            # Positive gap: expenditure exceeds physical progress
            if deviation.absolute_deviation >= 25.0:
                prac_sig = PracticalSignificance.CRITICAL
            elif deviation.absolute_deviation >= 15.0:
                prac_sig = PracticalSignificance.HIGH
            elif deviation.absolute_deviation >= 8.0:
                prac_sig = PracticalSignificance.MEDIUM
            else:
                prac_sig = PracticalSignificance.LOW

        elif metric_name == "physical_progress_pct":
            # For progress, falling substantially below peers is adverse
            if deviation.deviation_direction.value == "BELOW_PEERS" and abs_dev >= 25.0:
                prac_sig = PracticalSignificance.HIGH
            elif deviation.deviation_direction.value == "BELOW_PEERS" and abs_dev >= 12.0:
                prac_sig = PracticalSignificance.MEDIUM
            else:
                prac_sig = PracticalSignificance.LOW
        else:
            # Generic fallback
            rel_dev = abs(deviation.relative_deviation_pct) if deviation.relative_deviation_pct is not None else 0.0
            if rel_dev >= 100.0:
                prac_sig = PracticalSignificance.HIGH
            elif rel_dev >= 40.0:
                prac_sig = PracticalSignificance.MEDIUM
            else:
                prac_sig = PracticalSignificance.LOW

        # 2. Overall Severity Decision Matrix
        # Reconciles statistical status with practical significance
        if statistical_status == "STATISTICAL_OUTLIER":
            if prac_sig == PracticalSignificance.CRITICAL:
                severity = AnomalySeverity.CRITICAL
            elif prac_sig == PracticalSignificance.HIGH:
                severity = AnomalySeverity.HIGH
            elif prac_sig == PracticalSignificance.MEDIUM:
                severity = AnomalySeverity.MODERATE
            elif prac_sig in (PracticalSignificance.LOW, PracticalSignificance.NEGLIGIBLE):
                # Statistically unusual but negligible real impact
                severity = AnomalySeverity.LOW
            else:
                severity = AnomalySeverity.MODERATE

        elif statistical_status == "MODERATE_DEVIATION":
            if prac_sig == PracticalSignificance.CRITICAL:
                severity = AnomalySeverity.HIGH
            elif prac_sig in (PracticalSignificance.HIGH, PracticalSignificance.MEDIUM):
                severity = AnomalySeverity.MODERATE
            elif prac_sig == PracticalSignificance.LOW:
                severity = AnomalySeverity.LOW
            else:
                severity = AnomalySeverity.INFO

        else:  # NORMAL
            if prac_sig in (PracticalSignificance.CRITICAL, PracticalSignificance.HIGH):
                # High absolute project value but typical for cohort
                severity = AnomalySeverity.LOW
            else:
                severity = AnomalySeverity.INFO

        # 3. Confidence determination
        if sample_size >= 15 and agreement_ratio >= 0.75:
            confidence = "HIGH"
        elif sample_size >= 5 and agreement_ratio >= 0.50:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        return prac_sig, severity, confidence
