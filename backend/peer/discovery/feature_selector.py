"""Investigation-Specific Feature Selection Engine for PAIMANA Peer Discovery.

Filters candidate attributes down to dimensions explicitly demanded by the
active investigation strategy and evaluates feature completeness.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .strategy_registry import PeerStrategyDefinition


@dataclass
class SelectedFeaturesReport:
    """Report detailing active dimensions, extracted attributes, and completeness."""
    strategy_id: str
    active_dimensions: List[str]
    extracted_features: Dict[str, Any]
    missing_dimensions: List[str]
    completeness_score: float  # 0.0 to 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "active_dimensions": self.active_dimensions,
            "extracted_features": self.extracted_features,
            "missing_dimensions": self.missing_dimensions,
            "completeness_score": round(self.completeness_score, 4),
        }


class FeatureSelector:
    """Selects and extracts only investigation-relevant features from project records."""

    def select_features(
        self,
        project_record: Dict[str, Any],
        strategy: PeerStrategyDefinition,
    ) -> SelectedFeaturesReport:
        """Extracts strategy-required dimensions from a project record."""
        active_dimensions = list(strategy.dimension_weights.keys())
        extracted: Dict[str, Any] = {}
        missing: List[str] = []

        for dim in active_dimensions:
            val = self._extract_dimension_value(project_record, dim)
            if val is not None:
                extracted[dim] = val
            else:
                missing.append(dim)

        total_dims = len(active_dimensions)
        completeness = (total_dims - len(missing)) / total_dims if total_dims > 0 else 1.0

        return SelectedFeaturesReport(
            strategy_id=strategy.strategy_id,
            active_dimensions=active_dimensions,
            extracted_features=extracted,
            missing_dimensions=missing,
            completeness_score=completeness,
        )

    def _extract_dimension_value(self, record: Dict[str, Any], dimension: str) -> Optional[Any]:
        """Resolves dimension value from record across multiple common alias keys."""
        field_alias_map = {
            "original_cost": ["original_cost", "cost", "sanctioned_cost", "estimated_cost"],
            "revised_cost": ["revised_cost", "current_cost", "anticipated_cost"],
            "expenditure": ["expenditure", "cumulative_expenditure", "spent_amount"],
            "physical_progress": ["physical_progress", "progress_pct", "progress"],
            "execution_stage": ["execution_stage", "stage", "status", "physical_progress"],
            "implementing_agency": ["implementing_agency", "agency", "dept", "department"],
            "sector": ["sector", "ministry", "domain"],
            "project_type": ["project_type", "type", "subsector", "category"],
            "state": ["state", "location", "region"],
            "planned_duration": ["planned_duration", "duration_months", "duration"],
        }

        candidates = field_alias_map.get(dimension, [dimension])
        for key in candidates:
            if key in record and record[key] is not None:
                val = record[key]
                if isinstance(val, str) and not val.strip():
                    continue
                return val
        return None
