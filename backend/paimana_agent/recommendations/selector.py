"""Recommendation Selector executing constrained ranking, Pareto selection, and deterministic explanation generation."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
from .candidate import RecommendationCandidate
from .ranking_policy import RankingPolicy


@dataclass
class RecommendationDecision:
    """Complete, auditable decision package produced by the recommendation selection engine."""
    selected_candidate: Optional[RecommendationCandidate]
    alternatives: list[RecommendationCandidate] = field(default_factory=list)
    rejected_candidates: list[RecommendationCandidate] = field(default_factory=list)
    outcome_status: str = "RECOMMENDATION_SELECTED" # RECOMMENDATION_SELECTED, MULTIPLE_CANDIDATES_REQUIRE_REVIEW, INSUFFICIENT_EVIDENCE, NO_ELIGIBLE_CANDIDATE, HIGH_ACTION_RISK, AUTHORITY_INSUFFICIENT, CONFLICTING_EVIDENCE
    selection_reason: dict[str, Any] = field(default_factory=dict)
    policy_version: str = "v4.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_candidate_id": self.selected_candidate.id if self.selected_candidate else None,
            "selected_action": self.selected_candidate.title if self.selected_candidate else "No action selected.",
            "outcome_status": self.outcome_status,
            "alternatives": [c.to_dict() for c in self.alternatives],
            "rejected_candidates": [c.to_dict() for c in self.rejected_candidates],
            "ranking": [
                {
                    "candidate_id": c.id,
                    "title": c.title,
                    "rank": c.rank,
                    "utility_score": round(c.utility_score, 3),
                    "confidence_adjusted_score": round(c.confidence_adjusted_score, 3),
                    "confidence": round(c.confidence, 3),
                }
                for c in ([self.selected_candidate] if self.selected_candidate else []) + self.alternatives
            ],
            "selection_reason": self.selection_reason,
            "policy_version": self.policy_version,
        }


class RecommendationSelector:
    """Ranks eligible Pareto-frontier candidates and produces an auditable RecommendationDecision."""

    def select(
        self,
        frontier_candidates: list[RecommendationCandidate],
        all_candidates: list[RecommendationCandidate],
        state: Any,
        policy: Optional[RankingPolicy] = None
    ) -> RecommendationDecision:
        """Selects the top-ranked candidate and formulates a deterministic decision trace."""
        active_policy = policy or RankingPolicy()
        policy_ver = active_policy.policy_version

        # Separate validated/eligible candidates from rejected
        eligible = [c for c in frontier_candidates if c.validation_status == "VALID" and not c.is_dominated]
        rejected = [c for c in all_candidates if c.validation_status != "VALID" or c.is_dominated]

        # --------------------------------------------------------------------
        # Terminal State Check 1: No Eligible Candidates
        # --------------------------------------------------------------------
        if not eligible:
            # Check reasons
            if any(c.validation_status == "HIGH_RISK_ACTION" for c in all_candidates):
                status = "HIGH_ACTION_RISK"
            elif any(c.validation_status == "REQUIRES_HIGHER_AUTHORITY" for c in all_candidates):
                status = "AUTHORITY_INSUFFICIENT"
            elif any(c.validation_status == "INSUFFICIENT_EVIDENCE" for c in all_candidates):
                status = "INSUFFICIENT_EVIDENCE"
            else:
                status = "NO_ELIGIBLE_CANDIDATE"

            return RecommendationDecision(
                selected_candidate=None,
                alternatives=[],
                rejected_candidates=rejected,
                outcome_status=status,
                selection_reason={
                    "dominant_factors": ["All candidate interventions failed pre-scoring validation gates or safety constraints."],
                    "tradeoffs": "System withheld autonomous recommendation to preserve governance integrity.",
                    "why_alternatives_not_selected": [{"id": c.id, "reasons": c.validation_reasons} for c in all_candidates],
                },
                policy_version=policy_ver
            )

        # --------------------------------------------------------------------
        # Constraint Gate Checks on Eligible Candidates
        # --------------------------------------------------------------------
        constrained_eligible: list[RecommendationCandidate] = []
        for c in eligible:
            fails_constraints = []
            if c.evidence_strength < active_policy.min_evidence_strength:
                fails_constraints.append(f"Evidence strength ({c.evidence_strength:.2f}) below threshold ({active_policy.min_evidence_strength:.2f})")
            if c.implementation_risk > active_policy.max_implementation_risk:
                fails_constraints.append(f"Implementation risk ({c.implementation_risk:.2f}) above ceiling ({active_policy.max_implementation_risk:.2f})")
            if c.authority_score < active_policy.min_authority_score:
                fails_constraints.append(f"Authority score ({c.authority_score:.2f}) below threshold ({active_policy.min_authority_score:.2f})")

            if fails_constraints:
                c.validation_status = "REJECTED"
                c.validation_reasons.extend(fails_constraints)
                rejected.append(c)
            else:
                constrained_eligible.append(c)

        if not constrained_eligible:
            return RecommendationDecision(
                selected_candidate=None,
                alternatives=[],
                rejected_candidates=rejected,
                outcome_status="NO_ELIGIBLE_CANDIDATE",
                selection_reason={
                    "dominant_factors": ["Candidates passed structural validation but failed runtime policy constraint thresholds."],
                    "tradeoffs": "Prevented low-authority or high-risk intervention from execution.",
                },
                policy_version=policy_ver
            )

        # --------------------------------------------------------------------
        # Sort by confidence_adjusted_score descending
        # --------------------------------------------------------------------
        constrained_eligible.sort(key=lambda c: c.confidence_adjusted_score, reverse=True)

        for rank_idx, c in enumerate(constrained_eligible, start=1):
            c.rank = rank_idx

        winner = constrained_eligible[0]
        alternatives = constrained_eligible[1:]

        # --------------------------------------------------------------------
        # Determine Outcome Status (e.g. Tie / Review Required)
        # --------------------------------------------------------------------
        outcome_status = "RECOMMENDATION_SELECTED"
        if alternatives:
            delta = winner.confidence_adjusted_score - alternatives[0].confidence_adjusted_score
            if delta < 0.025:
                outcome_status = "MULTIPLE_CANDIDATES_REQUIRE_REVIEW"

        # Check for conflicting evidence
        if getattr(state, "contradictions", []) and len(getattr(state, "contradictions", [])) >= 2:
            outcome_status = "CONFLICTING_EVIDENCE"

        # --------------------------------------------------------------------
        # Deterministic Explanation Formulation
        # --------------------------------------------------------------------
        dominant_factors = []
        if winner.score_breakdown.get("evidence", {}).get("independence_groups", 0) >= 2:
            dominant_factors.append("Strong independent evidence corroboration across distinct source groups")
        if winner.expected_risk_reduction >= 0.75:
            dominant_factors.append(f"High expected risk reduction ({winner.expected_risk_reduction:.2f})")
        if winner.implementation_risk <= 0.25:
            dominant_factors.append(f"Low implementation risk ({winner.implementation_risk:.2f})")
        if winner.authority_score >= 0.85:
            dominant_factors.append(f"High source and institutional authority match ({winner.authority_score:.2f})")
        if winner.precedent_outcome:
            dominant_factors.append("Validated by positive historical intervention precedent")

        why_alt_list = []
        for alt in alternatives[:3]:
            alt_reasons = []
            if alt.confidence_adjusted_score < winner.confidence_adjusted_score:
                alt_reasons.append(f"Lower confidence-adjusted utility score ({alt.confidence_adjusted_score:.2f} vs {winner.confidence_adjusted_score:.2f})")
            if alt.implementation_risk > winner.implementation_risk:
                alt_reasons.append(f"Higher implementation risk ({alt.implementation_risk:.2f} vs {winner.implementation_risk:.2f})")
            if alt.evidence_strength < winner.evidence_strength:
                alt_reasons.append(f"Weaker supporting evidence strength ({alt.evidence_strength:.2f} vs {winner.evidence_strength:.2f})")
            why_alt_list.append({
                "candidate_id": alt.id,
                "title": alt.title,
                "score": alt.confidence_adjusted_score,
                "reasons": alt_reasons,
            })

        selection_reason = {
            "dominant_factors": dominant_factors or ["Optimal composite balance across benefit, risk, and evidence utility."],
            "tradeoffs": winner.tradeoffs or "Requires diligent administrative coordination and ongoing milestone monitoring.",
            "why_alternatives_not_selected": why_alt_list,
        }

        return RecommendationDecision(
            selected_candidate=winner,
            alternatives=alternatives,
            rejected_candidates=rejected,
            outcome_status=outcome_status,
            selection_reason=selection_reason,
            policy_version=policy_ver
        )
