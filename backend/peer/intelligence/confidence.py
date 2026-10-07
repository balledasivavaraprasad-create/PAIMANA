"""Metric-Specific Confidence Assessment Engine (CI-09).

Calculates independent statistical confidence levels for each individual metric
(cost overrun, time slippage, physical progress, expenditure) based on data availability and cohort spread.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..schemas import SimilarityBreakdown


class MetricConfidenceAssessor:
    """Evaluates metric-specific data reliability and statistical confidence."""

    def assess_metric_confidence(
        self,
        peers: List[SimilarityBreakdown],
        metrics: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """Calculates confidence tier (HIGH, MEDIUM, LOW) for each metric individually."""
        target_metrics = metrics or [
            "cost_overrun_pct",
            "time_overrun_pct",
            "schedule_delay_months",
            "physical_progress",
            "expenditure",
        ]

        n = len(peers)
        confidence_map: Dict[str, str] = {}

        for m in target_metrics:
            valid_vals = []
            for p in peers:
                val = p.raw_attributes.get(m)
                if val is not None:
                    try:
                        valid_vals.append(float(val))
                    except (ValueError, TypeError):
                        pass

            pop_count = len(valid_vals)
            pop_ratio = pop_count / n if n > 0 else 0.0

            if pop_count >= 8 and pop_ratio >= 0.80:
                conf = "HIGH"
            elif pop_count >= 4 and pop_ratio >= 0.50:
                conf = "MEDIUM"
            else:
                conf = "LOW"

            confidence_map[m] = conf

        return confidence_map
