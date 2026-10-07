"""Versioned Strategy Registry for Question-Conditioned Peer Selection.

Maintains formal domain strategies detailing mandatory eligibility rules,
question-specific dimension weights, metric focuses, and relaxation hierarchies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .question_classifier import InvestigationType


@dataclass
class PeerStrategyDefinition:
    """Explicit domain specification for discovering peers for a given investigation type."""
    strategy_id: str
    version: str
    investigation_type: InvestigationType
    description: str
    mandatory_hard_filters: List[str]
    dimension_weights: Dict[str, float]
    relevant_metrics: List[str]
    relaxation_hierarchy: List[str]
    cost_tolerance_ratio: float = 0.60  # Initial cost boundary [1 - ratio, 1 + ratio]
    min_similarity_threshold: float = 0.50
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        total = sum(self.dimension_weights.values())
        if abs(total - 1.0) > 1e-4 and total > 0:
            # Normalize weights to sum exactly to 1.0
            self.dimension_weights = {k: round(v / total, 4) for k, v in self.dimension_weights.items()}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "version": self.version,
            "investigation_type": self.investigation_type.value,
            "description": self.description,
            "mandatory_hard_filters": self.mandatory_hard_filters,
            "dimension_weights": self.dimension_weights,
            "relevant_metrics": self.relevant_metrics,
            "relaxation_hierarchy": self.relaxation_hierarchy,
            "cost_tolerance_ratio": self.cost_tolerance_ratio,
            "min_similarity_threshold": self.min_similarity_threshold,
            "metadata": self.metadata,
        }


class PeerStrategyRegistry:
    """Central registry of versioned peer discovery strategies."""

    CURRENT_VERSION = "1.0.0"

    def __init__(self) -> None:
        self._strategies: Dict[InvestigationType, PeerStrategyDefinition] = {}
        self._load_default_strategies()

    def register_strategy(self, strategy: PeerStrategyDefinition) -> None:
        """Register or overwrite an investigation strategy."""
        self._strategies[strategy.investigation_type] = strategy

    def get_strategy(self, inv_type: InvestigationType | str) -> PeerStrategyDefinition:
        """Retrieves the strategy definition for a specific investigation type."""
        if isinstance(inv_type, str):
            try:
                inv_type = InvestigationType(inv_type)
            except ValueError:
                inv_type = InvestigationType.GENERAL_SIMILARITY

        if inv_type in self._strategies:
            return self._strategies[inv_type]
        return self._strategies[InvestigationType.GENERAL_SIMILARITY]

    def _load_default_strategies(self) -> None:
        """Loads domain-calibrated default strategies."""
        # 1. Expenditure vs Progress Mismatch (e.g. front_loaded_billing)
        self.register_strategy(
            PeerStrategyDefinition(
                strategy_id="STRAT-EXPENDITURE-MISMATCH",
                version=self.CURRENT_VERSION,
                investigation_type=InvestigationType.EXPENDITURE_PROGRESS_MISMATCH,
                description="Focuses on scale, stage, and physical progress alignment to evaluate billing curve consistency.",
                mandatory_hard_filters=["SAME_PROJECT", "SECTOR_MISMATCH", "TEMPORAL_ELIGIBILITY"],
                dimension_weights={
                    "original_cost": 0.30,
                    "execution_stage": 0.30,
                    "project_type": 0.20,
                    "implementing_agency": 0.20,
                },
                relevant_metrics=["expenditure", "physical_progress", "cost_overrun_pct"],
                relaxation_hierarchy=["cost_tolerance", "agency_strictness"],
                cost_tolerance_ratio=0.50,
                min_similarity_threshold=0.55,
            )
        )

        # 2. Cost Overrun (budget escalation, cost spikes)
        self.register_strategy(
            PeerStrategyDefinition(
                strategy_id="STRAT-COST-OVERRUN",
                version=self.CURRENT_VERSION,
                investigation_type=InvestigationType.COST_OVERRUN,
                description="Prioritizes project scale, procurement, agency track record, and execution stage.",
                mandatory_hard_filters=["SAME_PROJECT", "SECTOR_MISMATCH", "TEMPORAL_ELIGIBILITY"],
                dimension_weights={
                    "original_cost": 0.35,
                    "project_type": 0.25,
                    "implementing_agency": 0.25,
                    "execution_stage": 0.15,
                },
                relevant_metrics=["revised_cost", "cost_overrun_pct", "expenditure"],
                relaxation_hierarchy=["cost_tolerance", "agency_strictness"],
                cost_tolerance_ratio=0.50,
                min_similarity_threshold=0.50,
            )
        )

        # 3. Time Slippage (schedule delays, deadline overruns)
        self.register_strategy(
            PeerStrategyDefinition(
                strategy_id="STRAT-TIME-SLIPPAGE",
                version=self.CURRENT_VERSION,
                investigation_type=InvestigationType.TIME_SLIPPAGE,
                description="Emphasizes project duration, regional state context, and execution stage.",
                mandatory_hard_filters=["SAME_PROJECT", "SECTOR_MISMATCH", "TEMPORAL_ELIGIBILITY"],
                dimension_weights={
                    "planned_duration": 0.35,
                    "project_type": 0.25,
                    "state": 0.20,
                    "execution_stage": 0.20,
                },
                relevant_metrics=["time_overrun_pct", "schedule_delay_months", "physical_progress"],
                relaxation_hierarchy=["duration_tolerance", "state_strictness"],
                cost_tolerance_ratio=0.70,
                min_similarity_threshold=0.50,
            )
        )

        # 4. Land Acquisition (ROW delays, local resistance, disputes)
        self.register_strategy(
            PeerStrategyDefinition(
                strategy_id="STRAT-LAND-ACQUISITION",
                version=self.CURRENT_VERSION,
                investigation_type=InvestigationType.LAND_ACQUISITION,
                description="Prioritizes geographical jurisdiction (State) and linear project footprint over cost scale.",
                mandatory_hard_filters=["SAME_PROJECT", "SECTOR_MISMATCH", "TEMPORAL_ELIGIBILITY"],
                dimension_weights={
                    "state": 0.45,
                    "project_type": 0.25,
                    "implementing_agency": 0.20,
                    "original_cost": 0.10,
                },
                relevant_metrics=["schedule_delay_months", "time_overrun_pct"],
                relaxation_hierarchy=["agency_strictness", "cost_tolerance"],
                cost_tolerance_ratio=0.80,
                min_similarity_threshold=0.50,
            )
        )

        # 5. Regulatory Clearance (Forest, Wildlife, Environmental)
        self.register_strategy(
            PeerStrategyDefinition(
                strategy_id="STRAT-REGULATORY-CLEARANCE",
                version=self.CURRENT_VERSION,
                investigation_type=InvestigationType.REGULATORY_CLEARANCE,
                description="Heavily weights state jurisdiction and ecological exposure over financial parameters.",
                mandatory_hard_filters=["SAME_PROJECT", "SECTOR_MISMATCH", "TEMPORAL_ELIGIBILITY"],
                dimension_weights={
                    "state": 0.50,
                    "project_type": 0.30,
                    "implementing_agency": 0.20,
                },
                relevant_metrics=["schedule_delay_months", "time_overrun_pct"],
                relaxation_hierarchy=["agency_strictness"],
                cost_tolerance_ratio=1.00,
                min_similarity_threshold=0.50,
            )
        )

        # 6. Physical Progress Delay
        self.register_strategy(
            PeerStrategyDefinition(
                strategy_id="STRAT-PHYSICAL-PROGRESS",
                version=self.CURRENT_VERSION,
                investigation_type=InvestigationType.PHYSICAL_PROGRESS_DELAY,
                description="Weights stage of execution, contractor/agency, and project type.",
                mandatory_hard_filters=["SAME_PROJECT", "SECTOR_MISMATCH", "TEMPORAL_ELIGIBILITY"],
                dimension_weights={
                    "execution_stage": 0.40,
                    "project_type": 0.30,
                    "implementing_agency": 0.20,
                    "original_cost": 0.10,
                },
                relevant_metrics=["physical_progress", "schedule_delay_months"],
                relaxation_hierarchy=["agency_strictness", "cost_tolerance"],
                cost_tolerance_ratio=0.60,
                min_similarity_threshold=0.50,
            )
        )

        # 7. General Similarity (Standard Baseline Fallback)
        self.register_strategy(
            PeerStrategyDefinition(
                strategy_id="STRAT-GENERAL-BASELINE",
                version=self.CURRENT_VERSION,
                investigation_type=InvestigationType.GENERAL_SIMILARITY,
                description="Balanced baseline strategy when no specific investigation hypothesis is indicated.",
                mandatory_hard_filters=["SAME_PROJECT", "SECTOR_MISMATCH", "TEMPORAL_ELIGIBILITY"],
                dimension_weights={
                    "implementing_agency": 0.25,
                    "original_cost": 0.20,
                    "execution_stage": 0.20,
                    "state": 0.15,
                    "planned_duration": 0.10,
                    "project_type": 0.10,
                },
                relevant_metrics=["cost_overrun_pct", "time_overrun_pct", "schedule_delay_months"],
                relaxation_hierarchy=["cost_tolerance", "state_strictness", "agency_strictness"],
                cost_tolerance_ratio=0.60,
                min_similarity_threshold=0.50,
            )
        )
