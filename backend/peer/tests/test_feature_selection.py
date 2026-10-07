"""Unit tests for Peer Feature Selection and Strategy Registry (Phase PD-2)."""
import pytest

from peer.discovery.feature_selector import FeatureSelector
from peer.discovery.question_classifier import InvestigationType
from peer.discovery.strategy_registry import (
    PeerStrategyDefinition,
    PeerStrategyRegistry,
)


class TestPeerStrategyRegistry:
    def setup_method(self):
        self.registry = PeerStrategyRegistry()

    def test_default_strategies_registered_and_normalized(self):
        for inv_type in InvestigationType:
            strategy = self.registry.get_strategy(inv_type)
            assert strategy is not None
            assert strategy.strategy_id.startswith("STRAT-")
            # Dimension weights must sum to 1.0 (with floating point tolerance)
            total_weight = sum(strategy.dimension_weights.values())
            assert abs(total_weight - 1.0) < 1e-3
            assert len(strategy.mandatory_hard_filters) > 0
            assert len(strategy.relevant_metrics) > 0

    def test_strategy_serialization(self):
        strat = self.registry.get_strategy(InvestigationType.COST_OVERRUN)
        d = strat.to_dict()
        assert d["strategy_id"] == "STRAT-COST-OVERRUN"
        assert d["investigation_type"] == "COST_OVERRUN"
        assert "original_cost" in d["dimension_weights"]

    def test_custom_strategy_registration(self):
        custom = PeerStrategyDefinition(
            strategy_id="STRAT-CUSTOM-01",
            version="1.0.0",
            investigation_type=InvestigationType.GENERAL_SIMILARITY,
            description="Custom test strategy",
            mandatory_hard_filters=["SAME_PROJECT"],
            dimension_weights={"original_cost": 0.5, "state": 0.5},
            relevant_metrics=["cost_overrun_pct"],
            relaxation_hierarchy=["cost_tolerance"],
        )
        self.registry.register_strategy(custom)
        retrieved = self.registry.get_strategy(InvestigationType.GENERAL_SIMILARITY)
        assert retrieved.strategy_id == "STRAT-CUSTOM-01"


class TestFeatureSelector:
    def setup_method(self):
        self.selector = FeatureSelector()
        self.registry = PeerStrategyRegistry()

    def test_feature_selection_with_complete_data(self):
        strategy = self.registry.get_strategy(InvestigationType.COST_OVERRUN)
        record = {
            "project_code": "PRJ-001",
            "original_cost": 1500.0,
            "project_type": "Expressway",
            "implementing_agency": "NHAI",
            "execution_stage": "Construction",
            "state": "Haryana",
        }

        report = self.selector.select_features(record, strategy)
        assert report.completeness_score == 1.0
        assert len(report.missing_dimensions) == 0
        assert report.extracted_features["original_cost"] == 1500.0
        assert report.extracted_features["implementing_agency"] == "NHAI"

    def test_feature_selection_with_missing_and_aliased_fields(self):
        strategy = self.registry.get_strategy(InvestigationType.COST_OVERRUN)
        # Uses alias 'cost' instead of 'original_cost', and missing 'execution_stage'
        record = {
            "project_code": "PRJ-002",
            "cost": 850.0,
            "subsector": "Bridge",  # alias for project_type
            "agency": "State PWD",  # alias for implementing_agency
        }

        report = self.selector.select_features(record, strategy)
        assert "execution_stage" in report.missing_dimensions
        assert report.extracted_features["original_cost"] == 850.0
        assert report.extracted_features["project_type"] == "Bridge"
        assert report.extracted_features["implementing_agency"] == "State PWD"
        assert report.completeness_score < 1.0
        assert report.completeness_score > 0.0
