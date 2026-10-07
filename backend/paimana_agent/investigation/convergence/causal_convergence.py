"""Causal Convergence Evaluator.

Connects investigation convergence directly to verified causal claim levels,
distinguishing CAUSALLY_SUPPORTED, CAUSALLY_PLAUSIBLE, CAUSALLY_COMPETING,
and CAUSALLY_UNRESOLVED states.
"""
from __future__ import annotations
from typing import Any, Optional


class CausalConvergenceEvaluator:
    """Evaluates causal maturity and claim verification status."""

    LEVEL_SCORES = {
        "LEVEL_5_INTERVENTION_SUPPORTED": 1.00,
        "LEVEL_4_STRONG_CAUSAL_SUPPORT": 0.90,
        "LEVEL_3_MECHANISTIC_SUPPORT": 0.70,
        "LEVEL_2_TEMPORAL_ASSOCIATION": 0.45,
        "LEVEL_1_ASSOCIATION": 0.25,
        "LEVEL_0_OBSERVATION": 0.10,
    }

    @classmethod
    def evaluate_causal_convergence(cls, state: Any) -> dict[str, Any]:
        """Calculates causal convergence score based on verified causal claims and mechanisms."""
        claims = getattr(state, "causal_claims", [])
        leading_claim = getattr(state, "leading_causal_claim", None)
        conclusion_status = getattr(state, "causal_conclusion_status", "INSUFFICIENT_EVIDENCE")

        if not claims:
            # Check if hypotheses have causal indicators
            hypotheses = getattr(state, "hypotheses", [])
            active_h = [h for h in hypotheses if getattr(h, "status", "active").lower() in ["active", "supported", "primary"]]
            if active_h:
                top_h = active_h[0]
                conf = getattr(top_h, "confidence_score", getattr(top_h, "confidence", 0.0))
                if isinstance(conf, str):
                    conf = 0.85 if conf == "HIGH" else (0.50 if conf == "MEDIUM" else 0.20)
                # Fallback causal support approximation from hypothesis
                approx_score = min(0.65, float(conf))
                return {
                    "causal_support": round(approx_score, 3),
                    "causal_status": "CAUSALLY_PLAUSIBLE" if approx_score >= 0.50 else "CAUSALLY_UNRESOLVED",
                    "claim_level": "LEVEL_2_TEMPORAL_ASSOCIATION" if approx_score >= 0.50 else "LEVEL_1_ASSOCIATION",
                    "leading_cause": getattr(top_h, "name", getattr(top_h, "statement", "Unknown")),
                    "is_causally_supported": False,
                }
            return {
                "causal_support": 0.10,
                "causal_status": "CAUSALLY_UNRESOLVED",
                "claim_level": "LEVEL_0_OBSERVATION",
                "leading_cause": None,
                "is_causally_supported": False,
            }

        # Sort claims by support score
        sorted_claims = sorted(claims, key=lambda c: getattr(c, "causal_support_score", 0.0), reverse=True)
        top = sorted_claims[0]
        level = getattr(top, "causal_level", "LEVEL_1_ASSOCIATION")
        raw_score = getattr(top, "causal_support_score", 0.0)
        level_score = cls.LEVEL_SCORES.get(level, 0.25)

        # Composite score
        causal_score = min(1.0, 0.60 * raw_score + 0.40 * level_score)

        if conclusion_status == "UNRESOLVED_CAUSAL_CONFLICT":
            causal_status = "CAUSALLY_COMPETING"
        elif level in ["LEVEL_4_STRONG_CAUSAL_SUPPORT", "LEVEL_5_INTERVENTION_SUPPORTED"]:
            causal_status = "CAUSALLY_SUPPORTED"
        elif level == "LEVEL_3_MECHANISTIC_SUPPORT":
            causal_status = "CAUSALLY_PLAUSIBLE"
        else:
            causal_status = "CAUSALLY_UNRESOLVED"

        return {
            "causal_support": round(causal_score, 3),
            "causal_status": causal_status,
            "claim_level": level,
            "leading_cause": getattr(top, "proposed_cause", None),
            "is_causally_supported": causal_status == "CAUSALLY_SUPPORTED",
            "is_competing": causal_status == "CAUSALLY_COMPETING",
        }
