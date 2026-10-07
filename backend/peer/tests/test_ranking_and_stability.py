"""Unit tests for Ranking, Diversity, Stability, and Explainability (PD-8, PD-9, PD-10)."""
import pytest

from peer.discovery.explainability import PeerExplainabilityEngine
from peer.discovery.modular_similarity import ModularSimilarityEngine
from peer.discovery.question_classifier import InvestigationType
from peer.discovery.ranking import PeerRankingEngine
from peer.discovery.stability import PeerStabilityAnalyzer
from peer.discovery.strategy_registry import PeerStrategyRegistry
from peer.schemas import SimilarityBreakdown


class TestPeerRankingAndDiversity:
    def setup_method(self):
        self.ranking_engine = PeerRankingEngine()

    def test_diversity_concentration_guardrail(self):
        # 6 projects from NHAI, 2 from BRO, 2 from State PWD
        candidates = []
        for i in range(6):
            candidates.append(
                SimilarityBreakdown(
                    peer_code=f"NHAI-{i}",
                    peer_name=f"NHAI Project {i}",
                    overall_similarity=0.90 - i * 0.01,
                    raw_attributes={"implementing_agency": "NHAI", "state": "Delhi"},
                )
            )
        for i in range(2):
            candidates.append(
                SimilarityBreakdown(
                    peer_code=f"BRO-{i}",
                    peer_name=f"BRO Project {i}",
                    overall_similarity=0.82 - i * 0.01,
                    raw_attributes={"implementing_agency": "BRO", "state": "Uttarakhand"},
                )
            )

        # Top 5 selection with max 50% agency fraction (max 2 per agency in top 5)
        res = self.ranking_engine.rank_and_select(candidates, top_k=4, enable_diversity=True, max_agency_fraction=0.50)
        assert len(res.selected_peers) == 4
        # NHAI should be capped at 2
        assert res.agency_distribution["NHAI"] <= 2
        # BRO should be included via diversity
        assert "BRO" in res.agency_distribution
        assert res.diversity_adjustments_made > 0


class TestStabilityAndExplainability:
    def setup_method(self):
        self.stability_analyzer = PeerStabilityAnalyzer()
        self.explainability_engine = PeerExplainabilityEngine()
        self.similarity_engine = ModularSimilarityEngine()
        self.registry = PeerStrategyRegistry()
        self.strategy = self.registry.get_strategy(InvestigationType.COST_OVERRUN)

    def test_stability_analysis(self):
        target = {"project_code": "T1", "original_cost": 1000.0, "project_type": "Road", "implementing_agency": "NHAI"}
        all_candidates = [
            {"project_code": "P1", "original_cost": 1050.0, "project_type": "Road", "implementing_agency": "NHAI"},
            {"project_code": "P2", "original_cost": 980.0, "project_type": "Road", "implementing_agency": "NHAI"},
            {"project_code": "P3", "original_cost": 1100.0, "project_type": "Road", "implementing_agency": "NHAI"},
            {"project_code": "P4", "original_cost": 3000.0, "project_type": "Road", "implementing_agency": "NHAI"},
        ]
        base_peers = [
            SimilarityBreakdown(peer_code="P1", peer_name="P1", overall_similarity=0.92),
            SimilarityBreakdown(peer_code="P2", peer_name="P2", overall_similarity=0.90),
            SimilarityBreakdown(peer_code="P3", peer_name="P3", overall_similarity=0.85),
        ]

        res = self.stability_analyzer.analyze_stability(
            base_peers=base_peers,
            all_candidates=all_candidates,
            target_project=target,
            strategy=self.strategy,
            similarity_engine=self.similarity_engine,
            top_k=3,
        )

        assert res.overall_stability_score > 0.70
        assert res.is_stable is True
        assert len(res.evaluations) == 2

    def test_explainability_dossier_generation(self):
        target = {"project_code": "T1", "project_name": "Target Highway"}
        peers = [SimilarityBreakdown(peer_code="P1", peer_name="P1", overall_similarity=0.90, dimension_scores={"original_cost": 0.95})]
        dossier = self.explainability_engine.build_dossier(
            target_project=target,
            strategy=self.strategy,
            selected_peers=peers,
            evaluations=[],
            ranked_candidates=[],
            relaxation_history=[],
        )

        d = dossier.to_dict()
        assert d["target_project_code"] == "T1"
        assert d["strategy_id"] == "STRAT-COST-OVERRUN"
        assert d["selected_peer_count"] == 1
        assert "narrative_explanation" in d
        assert len(d["narrative_explanation"]) > 20
