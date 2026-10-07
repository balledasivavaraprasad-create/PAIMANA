"""Central Metric Registry & Specification Engine (SB-01).

Defines metric formulas, units, interpretation directions, allowed boundaries,
and derivation specifications for all infrastructure monitoring metrics.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from .schemas import MetricDirection


@dataclass
class MetricDefinition:
    """Formal domain specification of an infrastructure benchmark metric."""
    metric_id: str
    unit: str
    direction: MetricDirection
    description: str
    source_fields: List[str]
    allowed_range: Tuple[Optional[float], Optional[float]] = (None, None)
    is_derived: bool = False
    missing_policy: str = "SUPPRESS"
    stage_sensitive: bool = False
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "unit": self.unit,
            "direction": self.direction.value,
            "description": self.description,
            "source_fields": self.source_fields,
            "allowed_range": list(self.allowed_range),
            "is_derived": self.is_derived,
            "missing_policy": self.missing_policy,
            "stage_sensitive": self.stage_sensitive,
            "version": self.version,
        }


class MetricRegistry:
    """Central repository of standardized metric specifications."""

    def __init__(self):
        self._metrics: Dict[str, MetricDefinition] = {}
        self._load_standard_metrics()

    def register_metric(self, definition: MetricDefinition) -> None:
        self._metrics[definition.metric_id] = definition

    def get_metric(self, metric_id: str) -> Optional[MetricDefinition]:
        return self._metrics.get(metric_id)

    def list_metrics(self) -> List[MetricDefinition]:
        return list(self._metrics.values())

    def _load_standard_metrics(self) -> None:
        # 1. Cost Overrun %
        self.register_metric(
            MetricDefinition(
                metric_id="cost_overrun_pct",
                unit="percentage",
                direction=MetricDirection.HIGHER_IS_WORSE,
                description="Percentage escalation of revised or anticipated cost over original sanctioned budget.",
                source_fields=["revised_cost", "original_cost", "cost_overrun_pct"],
                allowed_range=(-50.0, 500.0),
                is_derived=True,
                stage_sensitive=False,
            )
        )

        # 2. Time Slippage / Schedule Delay Months
        self.register_metric(
            MetricDefinition(
                metric_id="time_slippage_months",
                unit="months",
                direction=MetricDirection.HIGHER_IS_WORSE,
                description="Total schedule delay in months beyond original planned completion date.",
                source_fields=["schedule_delay_months", "time_overrun_pct", "planned_completion_date"],
                allowed_range=(0.0, 240.0),
                is_derived=True,
                stage_sensitive=False,
            )
        )

        # 3. Physical Progress %
        self.register_metric(
            MetricDefinition(
                metric_id="physical_progress_pct",
                unit="percentage",
                direction=MetricDirection.HIGHER_IS_BETTER,
                description="Cumulative physical construction progress achieved to date.",
                source_fields=["physical_progress", "progress_pct"],
                allowed_range=(0.0, 100.0),
                is_derived=False,
                stage_sensitive=True,
            )
        )

        # 4. Expenditure Ratio %
        self.register_metric(
            MetricDefinition(
                metric_id="expenditure_pct",
                unit="percentage",
                direction=MetricDirection.NEUTRAL,
                description="Cumulative financial expenditure as a percentage of original sanctioned cost.",
                source_fields=["expenditure", "original_cost", "financial_progress"],
                allowed_range=(0.0, 300.0),
                is_derived=True,
                stage_sensitive=True,
            )
        )

        # 5. Progress-Expenditure Gap (Financial Mismatch %)
        self.register_metric(
            MetricDefinition(
                metric_id="progress_expenditure_gap_pct",
                unit="percentage",
                direction=MetricDirection.HIGHER_IS_WORSE,
                description="Disparity between financial expenditure ratio and physical completion percentage.",
                source_fields=["financial_progress", "physical_progress", "expenditure", "original_cost"],
                allowed_range=(-100.0, 100.0),
                is_derived=True,
                stage_sensitive=True,
            )
        )

        # 6. Progress Velocity (% per month)
        self.register_metric(
            MetricDefinition(
                metric_id="progress_velocity_pct_per_month",
                unit="percentage_per_month",
                direction=MetricDirection.HIGHER_IS_BETTER,
                description="Average monthly progress realization rate across chronological snapshots.",
                source_fields=["physical_progress", "snapshots"],
                allowed_range=(0.0, 25.0),
                is_derived=True,
                stage_sensitive=True,
            )
        )
