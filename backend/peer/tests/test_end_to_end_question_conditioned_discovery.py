"""End-to-End Evaluation of Question-Conditioned Peer Discovery (PD-11, PD-12)."""
import pytest

from peer.discovery.context import PeerInvestigationContext
from peer.repository import InMemoryProjectRepository
from peer.service import PeerIntelligenceService
from peer.tools_adapter import make_peer_tool_definitions


class TestEndToEndQuestionConditionedDiscovery:
    def setup_method(self):
        # Target project in Haryana with 1500cr cost
        self.target = {
            "project_code": "HWY-TARGET",
            "project_name": "Haryana Golden Link",
            "sector": "Roads",
            "project_type": "Expressway",
            "implementing_agency": "NHAI",
            "state": "Haryana",
            "original_cost": 1500.0,
            "physical_progress": 40.0,
        }

        # Candidate universe:
        # P_COST_MATCH: In Kerala (far away), but identical cost (1500cr)
        # P_STATE_MATCH: In Haryana (same state), but very different cost (600cr)
        # P_BALANCED: In Punjab (neighboring state), cost 1400cr
        self.universe = [
            {
                "project_code": "P_COST_MATCH",
                "project_name": "Kerala Coastal Bypass",
                "sector": "Roads",
                "project_type": "Expressway",
                "implementing_agency": "NHAI",
                "state": "Kerala",
                "original_cost": 1500.0,
                "physical_progress": 42.0,
            },
            {
                "project_code": "P_STATE_MATCH",
                "project_name": "Haryana Ring Road",
                "sector": "Roads",
                "project_type": "Expressway",
                "implementing_agency": "NHAI",
                "state": "Haryana",
                "original_cost": 850.0,
                "physical_progress": 38.0,
            },
            {
                "project_code": "P_BALANCED",
                "project_name": "Punjab Border Corridor",
                "sector": "Roads",
                "project_type": "Expressway",
                "implementing_agency": "NHAI",
                "state": "Punjab",
                "original_cost": 1400.0,
                "physical_progress": 41.0,
            },
            {
                "project_code": "P_DIFFERENT_SECTOR",
                "project_name": "Metro Line",
                "sector": "Railways",
                "original_cost": 1500.0,
            },
        ]

        self.repo = InMemoryProjectRepository(projects=self.universe)
        self.service = PeerIntelligenceService(repository=self.repo)

    def test_different_questions_produce_different_rankings(self):
        # Question 1: Cost overrun focus
        ctx_cost = PeerInvestigationContext(
            target_project_id="HWY-TARGET",
            investigation_question="Why is project cost increasing and exceeding budget?",
            investigation_type="COST_OVERRUN",
        )
        res_cost = self.service.peer_discovery(self.target, context=ctx_cost)

        # Question 2: Land acquisition focus (state is heavily weighted)
        ctx_land = PeerInvestigationContext(
            target_project_id="HWY-TARGET",
            investigation_question="Why is land acquisition delayed in this state?",
            investigation_type="LAND_ACQUISITION",
        )
        res_land = self.service.peer_discovery(self.target, context=ctx_land)

        # Under Cost Overrun, P_COST_MATCH (identical cost) ranks higher than P_STATE_MATCH (600cr)
        cost_peer_codes = [p.peer_code for p in res_cost.peers]
        assert "P_COST_MATCH" in cost_peer_codes
        idx_cost_match_in_cost_q = cost_peer_codes.index("P_COST_MATCH")
        idx_state_match_in_cost_q = cost_peer_codes.index("P_STATE_MATCH")
        assert idx_cost_match_in_cost_q < idx_state_match_in_cost_q

        # Under Land Acquisition, P_STATE_MATCH (same state) ranks higher than P_COST_MATCH (Kerala)
        land_peer_codes = [p.peer_code for p in res_land.peers]
        assert "P_STATE_MATCH" in land_peer_codes
        idx_state_match_in_land_q = land_peer_codes.index("P_STATE_MATCH")
        idx_cost_match_in_land_q = land_peer_codes.index("P_COST_MATCH")
        assert idx_state_match_in_land_q < idx_cost_match_in_land_q

        # Verify cross-sector project is strictly eliminated
        assert "P_DIFFERENT_SECTOR" not in cost_peer_codes
        assert "P_DIFFERENT_SECTOR" not in land_peer_codes

        # Verify Selection Dossier is attached
        assert "selection_dossier" in res_cost.source_lineage
        assert "selection_dossier" in res_land.source_lineage
        dossier_cost = res_cost.source_lineage["selection_dossier"]
        assert dossier_cost["strategy_id"] == "STRAT-COST-OVERRUN"

    def test_tool_adapter_with_question_conditioned_context(self):
        tools = make_peer_tool_definitions(self.service)
        discovery_tool = next(t for t in tools if t.name == "peer_discovery")

        # Invoke tool with question context kwargs
        result = discovery_tool.execute(
            p=self.target,
            investigation_question="Is expenditure progressing disproportionately compared with physical progress?",
            hypothesis_id="front_loaded_billing",
        )

        assert result.status == "SUCCESS"
        assert len(result.evidence_items) >= 2
        strategy_ev = next((e for e in result.evidence_items if e["type"] == "PEER_DISCOVERY_STRATEGY"), None)
        assert strategy_ev is not None
        assert "STRAT-EXPENDITURE-MISMATCH" in strategy_ev["statement"]
