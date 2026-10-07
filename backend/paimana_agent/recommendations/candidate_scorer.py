"""Multi-criteria Candidate Scorer applying explicit dimensional models and confidence adjustment."""
from __future__ import annotations
from typing import Any, Optional
from .candidate import RecommendationCandidate
from .ranking_policy import RankingPolicy
from .benefit_model import BenefitModel
from .cost_model import CostModel
from .risk_model import RiskModel
from .evidence_model import CandidateEvidenceModel
from .authority_model import AuthorityModel


class CandidateScorer:
    """Multi-criteria scoring engine evaluating candidates across 5 explicit dimensions."""

    def __init__(self):
        self.benefit_model = BenefitModel()
        self.cost_model = CostModel()
        self.risk_model = RiskModel()
        self.evidence_model = CandidateEvidenceModel()
        self.authority_model = AuthorityModel()

    def score_candidate(
        self,
        candidate: RecommendationCandidate,
        state: Any,
        policy: RankingPolicy,
        is_mega_project: bool = False
    ) -> RecommendationCandidate:
        """Scores an individual candidate and attaches a full auditable score breakdown."""
        # 1. Benefit Dimension
        b_score, b_breakdown = self.benefit_model.compute_benefit_score(
            candidate_benefit=candidate.expected_benefit,
            risk_reduction=candidate.expected_risk_reduction,
        )

        # 2. Cost Dimension
        c_score, c_breakdown = self.cost_model.compute_cost_score(
            candidate_cost=candidate.expected_cost,
        )

        # 3. Risk Dimension
        r_score, r_breakdown = self.risk_model.compute_risk_score(
            risk_reduction=candidate.expected_risk_reduction,
            implementation_risk=candidate.implementation_risk,
        )

        # 4. Evidence Strength Dimension (Lineage-aware)
        ev_items = getattr(state, "evidence_items", [])
        contra_count = len(getattr(state, "contradictions", []))
        if candidate.evidence_ids and ev_items:
            e_score, e_breakdown = self.evidence_model.compute_evidence_strength(
                candidate_evidence_ids=candidate.evidence_ids,
                state_evidence_items=ev_items,
                contradictions_count=contra_count,
            )
        else:
            e_score = candidate.evidence_strength
            e_breakdown = {
                "score": e_score,
                "independence_groups": 1,
                "contradictions": contra_count,
                "freshness": 1.0,
                "source_authority": candidate.authority_score,
                "corroboration_boost": 0.0,
            }

        # 5. Authority Dimension
        if candidate.evidence_ids and ev_items:
            mean_auth = e_breakdown.get("source_authority", 0.80)
            a_score, a_breakdown = self.authority_model.compute_authority_score(
                cited_evidence_authority=mean_auth,
                approval_class=candidate.approval_class,
                responsible_stakeholder=candidate.responsible_stakeholder,
                is_mega_project=is_mega_project,
            )
        else:
            a_score = candidate.authority_score
            a_breakdown = {
                "score": a_score,
                "source_authority": a_score,
                "institutional_fit": a_score,
                "approval_class": candidate.approval_class,
                "responsible_stakeholder": candidate.responsible_stakeholder,
            }

        # Weighted Multi-Criteria Utility
        utility = (
            policy.w_benefit * b_score
            + policy.w_cost * c_score
            + policy.w_risk * r_score
            + policy.w_evidence * e_score
            + policy.w_authority * a_score
        )
        utility = round(max(0.01, min(1.0, utility)), 3)

        # Decision Confidence Factor (reflects data freshness, independence, and completeness)
        freshness = e_breakdown.get("freshness", 1.0)
        indep_groups = e_breakdown.get("independence_groups", 1)
        indep_factor = min(1.0, 0.40 + 0.30 * indep_groups)
        decision_conf = round(max(0.10, min(1.0, 0.40 * e_score + 0.30 * freshness + 0.30 * indep_factor)), 3)

        # Confidence-Adjusted Utility
        conf_factor = 0.50 + (0.50 * decision_conf)
        adjusted_score = round(utility * conf_factor, 3)

        candidate.expected_benefit = b_score
        candidate.expected_cost = c_breakdown["normalized_burden"]
        candidate.expected_risk_reduction = r_breakdown["risk_reduction"]
        candidate.implementation_risk = r_breakdown["implementation_risk"]
        candidate.evidence_strength = e_score
        candidate.authority_score = a_score
        candidate.confidence = decision_conf
        candidate.utility_score = utility
        candidate.confidence_adjusted_score = adjusted_score

        candidate.score_breakdown = {
            "benefit": b_breakdown,
            "cost": c_breakdown,
            "risk": r_breakdown,
            "evidence": e_breakdown,
            "authority": a_breakdown,
            "weights": {
                "benefit": round(policy.w_benefit, 3),
                "cost": round(policy.w_cost, 3),
                "risk": round(policy.w_risk, 3),
                "evidence": round(policy.w_evidence, 3),
                "authority": round(policy.w_authority, 3),
            },
            "utility_score": utility,
            "decision_confidence": decision_conf,
            "confidence_factor": round(conf_factor, 3),
            "final_score": adjusted_score,
            "policy_version": policy.policy_version,
        }
        return candidate

    def score_all(
        self,
        candidates: list[RecommendationCandidate],
        state: Any,
        policy: Optional[RankingPolicy] = None,
        is_mega_project: bool = False
    ) -> list[RecommendationCandidate]:
        """Scores all candidates using the specified policy."""
        active_policy = policy or RankingPolicy()
        scored: list[RecommendationCandidate] = []
        for cand in candidates:
            scored.append(self.score_candidate(cand, state, active_policy, is_mega_project))
        return scored
