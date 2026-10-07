"""Multi-Method Anomaly Ensemble & Agreement Engine (DO-05).

Coordinates complementary detection methods (Modified Z, Ordinary Z, IQR, Percentiles),
evaluates consensus agreement, and isolates robust detection signals.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from .schemas import (
    AnomalyMethod,
    MethodDetectionDetail,
    MethodStatus,
)
from .mad_detector import ModifiedZScoreDetector
from .zscore import OrdinaryZScoreDetector
from .iqr_detector import IQRDetector
from .percentile_detector import PercentileDetector


class EnsembleDetector:
    """Ensemble orchestrator evaluating multi-method detection consensus."""

    @classmethod
    def evaluate_univariate_ensemble(
        cls,
        target_value: float,
        cohort_values: List[float],
        direction_rule: str = "HIGHER_IS_WORSE",
        mod_z_threshold: float = 3.5,
        z_threshold: float = 2.5,
        iqr_multiplier: float = 1.5,
        percentile_threshold: float = 90.0,
    ) -> Tuple[Dict[str, MethodDetectionDetail], float, bool, str]:
        """Run all univariate methods and compute consensus agreement.

        Returns (method_results, agreement_ratio, consensus_flagged, statistical_status).
        """
        results: Dict[str, MethodDetectionDetail] = {}

        # 1. Modified Z-Score
        m_z = ModifiedZScoreDetector.evaluate(
            target_value, cohort_values, threshold=mod_z_threshold
        )
        results[AnomalyMethod.MODIFIED_Z_SCORE.value] = m_z

        # 2. Ordinary Z-Score
        o_z = OrdinaryZScoreDetector.evaluate(
            target_value, cohort_values, threshold=z_threshold
        )
        results[AnomalyMethod.ORDINARY_Z_SCORE.value] = o_z

        # 3. IQR Fences
        iqr_res = IQRDetector.evaluate(
            target_value, cohort_values, multiplier=iqr_multiplier
        )
        results[AnomalyMethod.IQR_FENCE.value] = iqr_res

        # 4. Percentile Band
        pct_res = PercentileDetector.evaluate(
            target_value, cohort_values, direction_rule=direction_rule, upper_threshold=percentile_threshold
        )
        results[AnomalyMethod.PERCENTILE_BAND.value] = pct_res

        # Calculate applicable methods and agreement
        applicable = [
            r for r in results.values()
            if r.status not in (MethodStatus.METHOD_NOT_APPLICABLE, MethodStatus.INSUFFICIENT_DATA, MethodStatus.INSUFFICIENT_DISPERSION)
        ]
        flagged = [r for r in applicable if r.flagged]

        if applicable:
            agreement_ratio = len(flagged) / len(applicable)
        else:
            agreement_ratio = 0.0

        # Consensus rules:
        # If >= 2 methods flag, or if agreement >= 0.50 with >= 2 applicable methods
        consensus_flagged = (len(flagged) >= 2) or (len(applicable) >= 2 and agreement_ratio >= 0.50)

        # Statistical status classification
        if consensus_flagged and (
            (m_z.flagged and m_z.score is not None and abs(m_z.score) >= 3.5)
            or (pct_res.score is not None and pct_res.score >= 95.0 and direction_rule == "HIGHER_IS_WORSE")
            or (pct_res.score is not None and pct_res.score <= 5.0 and direction_rule == "HIGHER_IS_BETTER")
        ):
            statistical_status = "STATISTICAL_OUTLIER"
        elif consensus_flagged or len(flagged) >= 1:
            statistical_status = "MODERATE_DEVIATION"
        else:
            statistical_status = "NORMAL"

        return results, round(agreement_ratio, 2), consensus_flagged, statistical_status
