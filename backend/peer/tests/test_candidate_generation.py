"""Unit tests for Peer Candidate Generation Engine (Phase PD-3)."""
import pytest

from peer.discovery.candidate_generator import CandidateGenerator
from peer.discovery.context import PeerInvestigationContext
from peer.discovery.question_classifier import InvestigationType
from peer.discovery.strategy_registry import PeerStrategyRegistry
from peer.repository import InMemoryProjectRepository


class TestCandidateGenerator:
    def setup_method(self):
        self.projects = [
            {"project_code": "P101", "project_name": "NH-1 Road", "sector": "Roads", "original_cost": 1000.0},
            {"project_code": "P102", "project_name": "NH-2 Road", "sector": "Roads", "original_cost": 1100.0},
            {"project_code": "P103", "project_name": "NH-3 Road", "sector": "Roads", "original_cost": 950.0},
            {"project_code": "P104", "project_name": "NH-4 Road (Mega)", "sector": "Roads", "original_cost": 50000.0},  # Out of cost bounds
            {"project_code": "P105", "project_name": "Railway Line 1", "sector": "Railways", "original_cost": 1200.0},  # Different sector
            {"project_code": "P102-DUP", "project_name": "NH-2 Road", "sector": "Roads", "original_cost": 1100.0},  # Duplicate name
        ]
        self.repo = InMemoryProjectRepository(projects=self.projects)
        self.generator = CandidateGenerator(repository=self.repo)
        self.registry = PeerStrategyRegistry()

    def test_candidate_retrieval_and_deduplication(self):
        target = {"project_code": "P101", "project_name": "NH-1 Road", "sector": "Roads", "original_cost": 1000.0}
        strategy = self.registry.get_strategy(InvestigationType.COST_OVERRUN)

        result = self.generator.generate_candidates(
            target_project=target,
            strategy=strategy,
            max_candidates=10,
            enable_cost_prefilter=True,
        )

        # Target (P101) must be excluded
        codes = [c["project_code"] for c in result.candidates]
        assert "P101" not in codes

        # Railways (P105) excluded by sector
        assert "P105" not in codes

        # Duplicate name (P102-DUP) eliminated
        assert "P102-DUP" not in codes

        # Mega project (P104) eliminated by cost prefilter
        assert "P104" not in codes

        # Eligible candidates P102 and P103 should be present
        assert "P102" in codes
        assert "P103" in codes
        assert result.total_candidates == 2
        assert result.total_scanned >= 2
        assert result.retrieval_duration_ms >= 0

    def test_candidate_limit(self):
        target = {"project_code": "P101", "project_name": "NH-1 Road", "sector": "Roads", "original_cost": 1000.0}
        strategy = self.registry.get_strategy(InvestigationType.COST_OVERRUN)

        # Max candidates set to 1
        result = self.generator.generate_candidates(
            target_project=target,
            strategy=strategy,
            max_candidates=1,
            enable_cost_prefilter=False,
        )
        assert len(result.candidates) == 1
