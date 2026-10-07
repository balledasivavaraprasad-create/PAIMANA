"""Decision Readiness Evaluator.

Assesses whether the investigation has gathered the operational prerequisites
demanded by the recommendation synthesis and candidate validation layer.
"""
from __future__ import annotations
from typing import Any, Optional


class DecisionReadinessEvaluator:
    """Evaluates whether investigation state is mature enough to support recommendations."""

    @classmethod
    def evaluate_readiness(
        cls,
        state: Any,
        causal_support: float = 0.50,
        candidates: Optional[list[Any]] = None
    ) -> dict[str, Any]:
        """Calculates decision readiness score [0.0, 1.0]."""
        evidence_items = getattr(state, "evidence_items", [])
        observations = getattr(state, "observations", {})
        tools_used = set(getattr(state, "tools_used", []))

        # 1. Causal Understanding (35% weight)
        causal_factor = min(1.0, max(0.10, causal_support))

        # 2. Responsible Authority / Stakeholder Identified (25% weight)
        has_financial = (
            "financial_velocity" in observations
            or "financial_velocity" in tools_used
            or any("financial" in getattr(e, "claim", "").lower() for e in evidence_items)
            or any("financial" in getattr(e, "source_tool", "").lower() for e in evidence_items)
        )
        has_milestone = (
            "milestone_audit" in observations
            or "milestone_audit" in tools_used
            or any("milestone" in getattr(e, "claim", "").lower() for e in evidence_items)
            or any("milestone" in getattr(e, "source_tool", "").lower() for e in evidence_items)
        )
        if has_financial and has_milestone:
            authority_factor = 0.90
        elif has_financial or has_milestone:
            authority_factor = 0.70
        else:
            authority_factor = 0.35

        # 3. Action Feasibility & Context Known (20% weight)
        has_precedents = (
            "memory_retrieval" in observations
            or "memory_retrieval" in tools_used
            or bool(getattr(state, "precedent_context", None))
        )
        has_peers = (
            "peer_intelligence" in observations
            or "peer_intelligence" in tools_used
            or any("peer" in getattr(e, "source_tool", "").lower() for e in evidence_items)
        )
        if has_precedents and has_peers:
            feasibility_factor = 0.95
        elif has_precedents or has_peers:
            feasibility_factor = 0.75
        else:
            feasibility_factor = 0.40

        # 4. Cost / Implementation Risk Awareness (20% weight)
        if has_financial:
            cost_factor = 0.90
        else:
            cost_factor = 0.30

        # Composite Decision Readiness
        decision_readiness = (
            0.35 * causal_factor +
            0.25 * authority_factor +
            0.20 * feasibility_factor +
            0.20 * cost_factor
        )

        readiness_score = min(1.0, max(0.05, decision_readiness))

        return {
            "decision_readiness": round(readiness_score, 3),
            "is_decision_ready": readiness_score >= 0.55,
            "readiness_breakdown": {
                "causal_understanding": round(causal_factor, 3),
                "authority_identified": round(authority_factor, 3),
                "action_feasibility": round(feasibility_factor, 3),
                "cost_awareness": round(cost_factor, 3),
            }
        }
