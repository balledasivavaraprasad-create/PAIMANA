"""Unit tests for Modular Similarity, Adaptive Selection & Heterogeneity Detection (PD-5, PD-6, PD-7)."""
import pytest

from peer.discovery.adaptive_selection import AdaptiveCohortSelector
from peer.discovery.context import PeerInvestigationContext
from peer.discovery.heterogeneity import CohortHeterogeneityDetector
from peer.discovery.modular_similarity import ModularSimilarityEngine
from peer.discovery.question_classifier import InvestigationType
from peer.discovery.strategy_registry import PeerStrategyRegistry
from peer.schemas import SimilarityBreakdown


class TestModularSimilarityEngine:
    def setup_method(self):
        self.engine = ModularSimilarityEngine()
        self.registry = PeerStrategyRegistry()

    def test_log_scale_cost_similarity(self):
        strat = self.registry.get_strategy(InvestigationType.COST_OVERRUN)
        target = {"original_cost": 200.0, "project_type": "Road", "implementing_agency": "NHAI"}
        cand_close = {"original_cost": 250.0, "project_type": "Road", "implementing_agency": "NHAI"}
        cand_far = {"original_cost": 5000.0, "project_type": "Road", "implementing_agency": "NHAI"}

        sim_close = self.engine.compute_similarity(target, cand_close, strat)
        sim_far = self.engine.compute_similarity(target, cand_far, strat)

        assert sim_close.overall_similarity > sim_far.overall_similarity
        assert sim_close.dimension_scores["original_cost"] > 0.85
        assert sim_far.dimension_scores["original_cost"] < 0.50

    def test_agency_and_state_categorical_matching(self):
        strat = self.registry.get_strategy(InvestigationType.LAND_ACQUISITION)
        target = {"state": "Haryana", "project_type": "Expressway", "implementing_agency": "NHAI", "original_cost": 1000.0}
        cand_same_region = {"state": "Punjab", "project_type": "Expressway", "implementing_agency": "NHAI", "original_cost": 1000.0}
        cand_diff_region = {"state": "Tamil Nadu", "project_type": "Expressway", "implementing_agency": "NHAI", "original_cost": 1000.0}

        sim_region = self.engine.compute_similarity(target, cand_same_region, strat)
        sim_diff = self.engine.compute_similarity(target, cand_diff_region, strat)

        assert sim_region.dimension_scores["state"] > sim_diff.dimension_scores["state"]


class TestAdaptiveCohortSelector:
    def setup_method(self):
        self.selector = AdaptiveCohortSelector()
        self.registry = PeerStrategyRegistry()
        self.strategy = self.registry.get_strategy(InvestigationType.COST_OVERRUN)

    def test_adaptive_relaxation_audit_trail(self):
        # Only 2 candidates above 0.50, but 2 more between 0.40 and 0.50
        candidates = [
            SimilarityBreakdown(peer_code="P1", peer_name="P1", overall_similarity=0.85),
            SimilarityBreakdown(peer_code="P2", peer_name="P2", overall_similarity=0.65),
            SimilarityBreakdown(peer_code="P3", peer_name="P3", overall_similarity=0.52),
            SimilarityBreakdown(peer_code="P4", peer_name="P4", overall_similarity=0.42),
        ]
        ctx = PeerInvestigationContext(target_project_id="TARGET", min_similarity=0.60, allow_relaxation=True)

        result = self.selector.select_cohort(
            scored_candidates=candidates,
            strategy=self.strategy,
            context=ctx,
            min_cohort_size=3,
        )

        assert result.was_relaxed is True
        assert len(result.relaxation_history) > 0
        assert result.final_peer_count >= 3
        step1 = result.relaxation_history[0]
        assert step1.parameter == "min_similarity_threshold"
        assert step1.original_value == 0.60
        assert step1.additional_peers_found >= 1


class TestCohortHeterogeneityDetector:
    def setup_method(self):
        self.detector = CohortHeterogeneityDetector()

    def test_bimodal_scale_detection(self):
        target = {"project_code": "T1", "original_cost": 250.0}
        # 3 small projects (150-300cr) and 3 mega projects (3000-5000cr)
        peers = [
            SimilarityBreakdown(peer_code="S1", peer_name="S1", overall_similarity=0.80, raw_attributes={"original_cost": 200.0}),
            SimilarityBreakdown(peer_code="S2", peer_name="S2", overall_similarity=0.78, raw_attributes={"original_cost": 280.0}),
            SimilarityBreakdown(peer_code="S3", peer_name="S3", overall_similarity=0.75, raw_attributes={"original_cost": 220.0}),
            SimilarityBreakdown(peer_code="M1", peer_name="M1", overall_similarity=0.72, raw_attributes={"original_cost": 3500.0}),
            SimilarityBreakdown(peer_code="M2", peer_name="M2", overall_similarity=0.70, raw_attributes={"original_cost": 4200.0}),
            SimilarityBreakdown(peer_code="M3", peer_name="M3", overall_similarity=0.68, raw_attributes={"original_cost": 3800.0}),
        ]

        res = self.detector.analyze(target, peers)
        assert res.is_heterogeneous is True
        assert res.detected_modality == "BIMODAL"
        assert len(res.subgroups) == 2
        # Target (250cr) should align with small projects cluster
        assert "S1" in res.recommended_peer_codes
        assert "S2" in res.recommended_peer_codes
        assert "M1" not in res.recommended_peer_codes
