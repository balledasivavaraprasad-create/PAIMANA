"""Comprehensive Unit & Behavioral Test Suite for Cohort Intelligence (CI-1 through CI-10)."""
import pytest

from peer.intelligence.clustering import CohortClusterAnalyzer
from peer.intelligence.confidence import MetricConfidenceAssessor
from peer.intelligence.distribution import DistributionAnalyzer
from peer.intelligence.diversity import CohortDiversityEvaluator
from peer.intelligence.fragmentation import FragmentationDetector
from peer.intelligence.heterogeneity import CohortHeterogeneityAnalyzer
from peer.intelligence.multimodality import MultimodalityDetector
from peer.intelligence.quality import CohortQualityAssessor
from peer.intelligence.refinement import CohortRefinementEngine
from peer.intelligence.schemas import (
    CohortQualityLevel,
    CohortRefinementAction,
)
from peer.intelligence.service import CohortIntelligenceService
from peer.intelligence.stability import CohortStabilityEvaluator
from peer.intelligence.subgroup import SubgroupDetector
from peer.repository import InMemoryProjectRepository
from peer.schemas import CohortDiscoveryResult, CohortQuality, SimilarityBreakdown
from peer.service import PeerIntelligenceService
from peer.tools_adapter import make_peer_tool_definitions


class TestCohortQualityAndDistribution:
    def setup_method(self):
        self.quality_assessor = CohortQualityAssessor()
        self.dist_analyzer = DistributionAnalyzer()

    def test_multidimensional_quality_tiers(self):
        target = {"project_code": "T1", "original_cost": 1000.0}
        # 10 High similarity peers with complete data
        robust_peers = [
            SimilarityBreakdown(
                peer_code=f"P{i}",
                peer_name=f"Peer {i}",
                overall_similarity=0.82 + (i % 3) * 0.02,
                raw_attributes={
                    "original_cost": 1000.0 + i * 10,
                    "physical_progress": 50.0,
                    "implementing_agency": "NHAI",
                    "snapshot_date": "2024-03-31",
                },
            )
            for i in range(10)
        ]
        q_res = self.quality_assessor.assess_quality(robust_peers, target)
        assert q_res.overall_quality == CohortQualityLevel.HIGH
        assert q_res.overall_score >= 0.75
        assert len(q_res.dimension_details) == 8

        # Corrupted peer data should trigger UNRELIABLE
        corrupted_peers = list(robust_peers)
        corrupted_peers[0].raw_attributes["original_cost"] = -500.0
        q_bad = self.quality_assessor.assess_quality(corrupted_peers, target)
        assert q_bad.overall_quality == CohortQualityLevel.UNRELIABLE

    def test_similarity_distribution_and_fragmentation(self):
        # 4 high similarity (>0.85) and 4 low (<0.50) peers -> fragmented
        frag_peers = [
            SimilarityBreakdown(peer_code=f"H{i}", peer_name=f"H{i}", overall_similarity=0.88) for i in range(4)
        ] + [
            SimilarityBreakdown(peer_code=f"L{i}", peer_name=f"L{i}", overall_similarity=0.45) for i in range(4)
        ]
        res = self.dist_analyzer.analyze_similarity_distribution(frag_peers)
        assert res.overall_distribution.count == 8
        assert res.is_fragmented is True
        assert res.overall_distribution.iqr >= 0.20


class TestHeterogeneityAndSubgroups:
    def setup_method(self):
        self.hetero_analyzer = CohortHeterogeneityAnalyzer()
        self.subgroup_detector = SubgroupDetector()
        self.cluster_analyzer = CohortClusterAnalyzer()

    def test_heterogeneity_numerical_and_categorical(self):
        # Disparate costs and mixed project types
        diverse_peers = [
            SimilarityBreakdown(peer_code="P1", peer_name="P1", overall_similarity=0.8, raw_attributes={"original_cost": 200.0, "project_type": "Road"}),
            SimilarityBreakdown(peer_code="P2", peer_name="P2", overall_similarity=0.8, raw_attributes={"original_cost": 250.0, "project_type": "Road"}),
            SimilarityBreakdown(peer_code="P3", peer_name="P3", overall_similarity=0.7, raw_attributes={"original_cost": 4500.0, "project_type": "Bridge"}),
            SimilarityBreakdown(peer_code="P4", peer_name="P4", overall_similarity=0.7, raw_attributes={"original_cost": 5000.0, "project_type": "Tunnel"}),
        ]
        res = self.hetero_analyzer.analyze_heterogeneity(diverse_peers)
        assert res.overall_level == "HIGH"
        assert res.numerical_variation["cost_cv"] > 0.50

    def test_domain_driven_subgroup_detection(self):
        target = {"project_code": "T1", "procurement_type": "EPC"}
        peers = [
            SimilarityBreakdown(peer_code="E1", peer_name="E1", overall_similarity=0.85, raw_attributes={"procurement_type": "EPC", "original_cost": 1000.0}),
            SimilarityBreakdown(peer_code="E2", peer_name="E2", overall_similarity=0.82, raw_attributes={"procurement_type": "EPC", "original_cost": 1050.0}),
            SimilarityBreakdown(peer_code="H1", peer_name="H1", overall_similarity=0.75, raw_attributes={"procurement_type": "HAM", "original_cost": 1200.0}),
            SimilarityBreakdown(peer_code="H2", peer_name="H2", overall_similarity=0.72, raw_attributes={"procurement_type": "HAM", "original_cost": 1250.0}),
        ]
        res = self.subgroup_detector.detect_subgroups(peers, target)
        assert res.subgroups_detected is True
        assert len(res.subgroups) == 2
        assert res.target_subgroup_id is not None

    def test_cluster_analyzer_separation_validation(self):
        target = {"project_code": "T1"}
        # Extremely similar values where silhouette will be very low or degenerate
        uniform_peers = [
            SimilarityBreakdown(peer_code=f"U{i}", peer_name=f"U{i}", overall_similarity=0.80, raw_attributes={"original_cost": 1000.0 + i, "physical_progress": 50.0})
            for i in range(5)
        ]
        res = self.cluster_analyzer.cluster_cohort(uniform_peers, target)
        # Should cleanly reject clustering because separation is insufficient
        assert res.subgroups_detected is False
        assert "INSUFFICIENT_CLUSTER_SEPARATION" in res.recommendation


class TestAdvancedAnalyticsAndRefinement:
    def setup_method(self):
        self.multimodal_detector = MultimodalityDetector()
        self.frag_detector = FragmentationDetector()
        self.confidence_assessor = MetricConfidenceAssessor()
        self.refinement_engine = CohortRefinementEngine()

    def test_multimodality_detection(self):
        # Durations clustered around 36 months and 72 months
        durations = [34, 36, 35, 37, 36, 68, 72, 70, 74, 71]
        peers = [
            SimilarityBreakdown(peer_code=f"D{i}", peer_name=f"D{i}", overall_similarity=0.8, raw_attributes={"planned_duration": d})
            for i, d in enumerate(durations)
        ]
        res = self.multimodal_detector.analyze_metric(peers, "planned_duration")
        assert res.is_multimodal is True
        assert len(res.modes) >= 2
        assert res.recommended_action == "SUBGROUP_ANALYSIS"

    def test_fragmentation_detection(self):
        # 3 peers connected by NHAI, 1 isolated peer from Railways with completely different similarity
        peers = [
            SimilarityBreakdown(peer_code="P1", peer_name="P1", overall_similarity=0.85, raw_attributes={"implementing_agency": "NHAI", "sector": "Roads"}),
            SimilarityBreakdown(peer_code="P2", peer_name="P2", overall_similarity=0.82, raw_attributes={"implementing_agency": "NHAI", "sector": "Roads"}),
            SimilarityBreakdown(peer_code="P3", peer_name="P3", overall_similarity=0.80, raw_attributes={"implementing_agency": "NHAI", "sector": "Roads"}),
            SimilarityBreakdown(peer_code="ISO_1", peer_name="Isolated", overall_similarity=0.45, raw_attributes={"implementing_agency": "IRCON", "sector": "Railways"}),
        ]
        res = self.frag_detector.analyze_fragmentation(peers)
        assert res.fragmentation_detected is True
        assert "ISO_1" in res.isolated_peers

    def test_metric_specific_confidence(self):
        peers = [
            SimilarityBreakdown(
                peer_code=f"P{i}",
                peer_name=f"P{i}",
                overall_similarity=0.8,
                raw_attributes={
                    "cost_overrun_pct": 10.0,
                    # contractor_performance only on 1 peer
                    "contractor_score": 90.0 if i == 0 else None,
                },
            )
            for i in range(8)
        ]
        conf = self.confidence_assessor.assess_metric_confidence(peers, metrics=["cost_overrun_pct", "contractor_score"])
        assert conf["cost_overrun_pct"] == "HIGH"
        assert conf["contractor_score"] == "LOW"


class TestCohortIntelligenceEndToEnd:
    def setup_method(self):
        self.projects = [
            {"project_code": "T1", "project_name": "Target Link", "sector": "Roads", "original_cost": 1000.0, "procurement_type": "EPC"},
            {"project_code": "P1", "project_name": "P1", "sector": "Roads", "original_cost": 1050.0, "procurement_type": "EPC", "physical_progress": 55.0},
            {"project_code": "P2", "project_name": "P2", "sector": "Roads", "original_cost": 980.0, "procurement_type": "EPC", "physical_progress": 52.0},
            {"project_code": "P3", "project_name": "P3", "sector": "Roads", "original_cost": 1100.0, "procurement_type": "HAM", "physical_progress": 48.0},
            {"project_code": "P4", "project_name": "P4", "sector": "Roads", "original_cost": 1150.0, "procurement_type": "HAM", "physical_progress": 45.0},
        ]
        self.repo = InMemoryProjectRepository(projects=self.projects)
        self.service = PeerIntelligenceService(repository=self.repo)

    def test_service_analyze_cohort_intelligence(self):
        target = self.projects[0]
        cohort = self.service.peer_discovery(target)

        intel_res = self.service.analyze_cohort_intelligence(target, cohort=cohort)
        assert intel_res.cohort_id == "COHORT-INTEL-T1"
        assert intel_res.quality.overall_quality in (CohortQualityLevel.LOW, CohortQualityLevel.MEDIUM, CohortQualityLevel.HIGH)
        assert intel_res.recommendation in (CohortRefinementAction.ACCEPT, CohortRefinementAction.ACCEPT_WITH_WARNINGS, CohortRefinementAction.SPLIT_INTO_SUBGROUPS)
        assert len(intel_res.evidence) >= 1
        assert intel_res.evidence[0]["type"] == "COHORT_INTELLIGENCE"

    def test_tool_adapter_cohort_intelligence(self):
        tools = make_peer_tool_definitions(self.service)
        intel_tool = next(t for t in tools if t.name == "cohort_intelligence")

        result = intel_tool.execute(p=self.projects[0])
        assert result.status == "SUCCESS"
        assert "Cohort Intelligence:" in result.summary
        assert len(result.evidence_items) >= 1
