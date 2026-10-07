"""Unit tests for Hard Eligibility Filter Engine (Phase PD-4)."""
import pytest

from peer.discovery.context import PeerInvestigationContext
from peer.discovery.eligibility import (
    HardEligibilityFilter,
    RejectionReason,
)
from peer.discovery.question_classifier import InvestigationType
from peer.discovery.strategy_registry import PeerStrategyRegistry


class TestHardEligibilityFilter:
    def setup_method(self):
        self.filter = HardEligibilityFilter()
        self.registry = PeerStrategyRegistry()
        self.strategy = self.registry.get_strategy(InvestigationType.COST_OVERRUN)
        self.target = {
            "project_code": "HWY-101",
            "project_name": "Golden Corridor Package 1",
            "sector": "Road Transport",
            "implementing_agency": "NHAI",
            "original_cost": 2500.0,
            "aliases": ["GC-PKG1"],
        }

    def test_rejection_same_project_code_and_name(self):
        cand_same_code = {"project_code": "HWY-101", "project_name": "Different Name", "sector": "Road Transport", "original_cost": 2500.0}
        eval_code = self.filter.evaluate_candidate(self.target, cand_same_code, self.strategy)
        assert eval_code.is_eligible is False
        assert RejectionReason.SAME_PROJECT in eval_code.rejection_reasons

        cand_same_name = {"project_code": "DIFF-999", "project_name": "Golden Corridor Package 1", "sector": "Road Transport", "original_cost": 2500.0}
        eval_name = self.filter.evaluate_candidate(self.target, cand_same_name, self.strategy)
        assert eval_name.is_eligible is False
        assert RejectionReason.SAME_PROJECT in eval_name.rejection_reasons

    def test_rejection_duplicate_alias(self):
        cand_alias = {
            "project_code": "GC-PKG1",  # matches target alias
            "project_name": "Package 1 Alias",
            "sector": "Road Transport",
            "original_cost": 2500.0,
        }
        res = self.filter.evaluate_candidate(self.target, cand_alias, self.strategy)
        assert res.is_eligible is False
        assert RejectionReason.DUPLICATE_PROJECT in res.rejection_reasons

    def test_rejection_sector_mismatch(self):
        cand_rail = {
            "project_code": "RLW-202",
            "project_name": "High Speed Rail Track",
            "sector": "Railways",
            "original_cost": 2500.0,
        }
        res = self.filter.evaluate_candidate(self.target, cand_rail, self.strategy)
        assert res.is_eligible is False
        assert RejectionReason.SECTOR_MISMATCH in res.rejection_reasons

    def test_rejection_temporal_ineligibility(self):
        ctx = PeerInvestigationContext(
            target_project_id="HWY-101",
            as_of_date="2025-12-31",
        )
        cand_future = {
            "project_code": "HWY-202",
            "project_name": "Future Highway Package",
            "sector": "Road Transport",
            "original_cost": 2300.0,
            "observation_date": "2026-03-31",  # After as_of_date
        }
        res = self.filter.evaluate_candidate(self.target, cand_future, self.strategy, context=ctx)
        assert res.is_eligible is False
        assert RejectionReason.TEMPORAL_INELIGIBILITY in res.rejection_reasons

    def test_rejection_invalid_snapshot(self):
        cand_negative_cost = {
            "project_code": "HWY-301",
            "project_name": "Corrupted Highway",
            "sector": "Road Transport",
            "original_cost": -500.0,
        }
        res = self.filter.evaluate_candidate(self.target, cand_negative_cost, self.strategy)
        assert res.is_eligible is False
        assert RejectionReason.INVALID_SNAPSHOT in res.rejection_reasons

        cand_bad_progress = {
            "project_code": "HWY-302",
            "project_name": "Impossible Progress",
            "sector": "Road Transport",
            "original_cost": 2000.0,
            "physical_progress": 250.0,
        }
        res_prog = self.filter.evaluate_candidate(self.target, cand_bad_progress, self.strategy)
        assert res_prog.is_eligible is False
        assert RejectionReason.INVALID_SNAPSHOT in res_prog.rejection_reasons

    def test_rejection_insufficient_data(self):
        cand_empty = {
            "project_code": "HWY-EMPTY",
            "project_name": "Empty Highway Record",
            "sector": "Road Transport",
        }
        res = self.filter.evaluate_candidate(self.target, cand_empty, self.strategy)
        assert res.is_eligible is False
        assert RejectionReason.INSUFFICIENT_DATA in res.rejection_reasons

    def test_filter_candidates_batch(self):
        candidates = [
            {"project_code": "HWY-VALID-1", "project_name": "Valid Road 1", "sector": "Road Transport", "original_cost": 2200.0},
            {"project_code": "HWY-101", "project_name": "Same Code", "sector": "Road Transport", "original_cost": 2500.0},
            {"project_code": "HWY-VALID-2", "project_name": "Valid Road 2", "sector": "Road Transport", "original_cost": 2700.0},
            {"project_code": "METRO-1", "project_name": "Metro 1", "sector": "Urban Transport", "original_cost": 2500.0},
        ]
        eligible, evaluations = self.filter.filter_candidates(self.target, candidates, self.strategy)
        assert len(eligible) == 2
        assert [c["project_code"] for c in eligible] == ["HWY-VALID-1", "HWY-VALID-2"]
        assert len(evaluations) == 4
