"""Unit tests for Question-Conditioned Peer Discovery Context & Classifier (Phase PD-1)."""
import pytest

from peer.discovery.context import PeerInvestigationContext
from peer.discovery.question_classifier import (
    ClassificationResult,
    InvestigationType,
    QuestionClassifier,
)


class TestPeerInvestigationContext:
    def test_context_creation_and_dict_serialization(self):
        ctx = PeerInvestigationContext(
            target_project_id="HWY-102",
            hypothesis_id="front_loaded_billing",
            investigation_question="Is expenditure progressing disproportionately compared with physical progress?",
            as_of_date="2026-03-31",
            max_peers=8,
            min_similarity=0.60,
        )

        d = ctx.to_dict()
        assert d["target_project_id"] == "HWY-102"
        assert d["hypothesis_id"] == "front_loaded_billing"
        assert d["max_peers"] == 8
        assert d["min_similarity"] == 0.60
        assert d["as_of_date"] == "2026-03-31"

        reconstructed = PeerInvestigationContext.from_dict(d)
        assert reconstructed.target_project_id == ctx.target_project_id
        assert reconstructed.investigation_question == ctx.investigation_question
        assert reconstructed.hypothesis_id == ctx.hypothesis_id
        assert reconstructed.max_peers == ctx.max_peers


class TestQuestionClassifier:
    def setup_method(self):
        self.classifier = QuestionClassifier()

    def test_classify_explicit_type(self):
        ctx = PeerInvestigationContext(
            target_project_id="P1",
            investigation_type="COST_OVERRUN",
        )
        res = self.classifier.classify(ctx)
        assert res.investigation_type == InvestigationType.COST_OVERRUN
        assert res.confidence == 1.0
        assert res.matched_rule == "EXPLICIT_INVESTIGATION_TYPE"
        assert "original_cost" in res.relevant_dimensions

    def test_classify_via_hypothesis_mapping(self):
        ctx_billing = PeerInvestigationContext(
            target_project_id="P1",
            hypothesis_id="front_loaded_billing",
        )
        res_billing = self.classifier.classify(ctx_billing)
        assert res_billing.investigation_type == InvestigationType.EXPENDITURE_PROGRESS_MISMATCH
        assert "expenditure" in res_billing.relevant_metrics

        ctx_delay = PeerInvestigationContext(
            target_project_id="P1",
            hypothesis_id="chronic_schedule_delay",
        )
        res_delay = self.classifier.classify(ctx_delay)
        assert res_delay.investigation_type == InvestigationType.TIME_SLIPPAGE
        assert "schedule_delay_months" in res_delay.relevant_metrics

    def test_classify_via_question_text(self):
        ctx_land = PeerInvestigationContext(
            target_project_id="P1",
            investigation_question="Why is land acquisition delayed in this state?",
        )
        res_land = self.classifier.classify(ctx_land)
        assert res_land.investigation_type == InvestigationType.LAND_ACQUISITION
        assert "state" in res_land.relevant_dimensions

        ctx_env = PeerInvestigationContext(
            target_project_id="P1",
            investigation_question="What is causing statutory environmental clearance delays?",
        )
        res_env = self.classifier.classify(ctx_env)
        assert res_env.investigation_type == InvestigationType.REGULATORY_CLEARANCE

    def test_classify_fallback(self):
        ctx_blank = PeerInvestigationContext(target_project_id="P1")
        res = self.classifier.classify(ctx_blank)
        assert res.investigation_type == InvestigationType.GENERAL_SIMILARITY
        assert res.confidence == 0.50
        assert res.matched_rule == "DEFAULT_GENERAL_FALLBACK"
