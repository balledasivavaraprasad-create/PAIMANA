"""Hypothesis Separation Evaluator.

Measures the discrimination margin between the leading hypothesis and alternatives,
distinguishing CLEARLY_SEPARATED, PARTIALLY_SEPARATED, and HIGHLY_COMPETITIVE states.
"""
from __future__ import annotations
from typing import Any


class HypothesisSeparationEvaluator:
    """Evaluates whether competing explanations have become sufficiently distinguished."""

    @classmethod
    def evaluate_separation(cls, hypotheses: list[Any]) -> dict[str, Any]:
        """Calculates margin and separation score across active hypotheses."""
        if not hypotheses:
            return {
                "hypothesis_separation": 0.0,
                "margin": 0.0,
                "classification": "NO_HYPOTHESES",
                "leading_id": None,
                "leading_support": 0.0,
                "runner_up_id": None,
                "runner_up_support": 0.0,
                "is_clearly_separated": False,
            }

        def _get_score(h: Any) -> float:
            c = getattr(h, "confidence_score", getattr(h, "confidence", 0.0))
            if isinstance(c, str):
                u = c.upper()
                return 0.85 if u == "HIGH" else (0.50 if u == "MEDIUM" else 0.20)
            return float(c)

        # Filter to active or supported hypotheses
        active = [h for h in hypotheses if getattr(h, "status", "active").lower() in ["active", "supported", "primary", "plausible"]]
        if not active:
            active = hypotheses

        # Sort by support descending
        sorted_h = sorted(active, key=_get_score, reverse=True)
        top = sorted_h[0]
        top_score = _get_score(top)
        top_id = getattr(top, "id", getattr(top, "title", "H1"))

        if len(sorted_h) == 1:
            margin = top_score
            runner_up_id = None
            runner_up_score = 0.0
            classification = "CLEARLY_SEPARATED" if top_score >= 0.60 else "PARTIALLY_SEPARATED"
            sep_score = min(1.0, top_score)
        else:
            runner_up = sorted_h[1]
            runner_up_score = _get_score(runner_up)
            runner_up_id = getattr(runner_up, "id", getattr(runner_up, "title", "H2"))
            margin = max(0.0, top_score - runner_up_score)

            if margin >= 0.25 and top_score >= 0.65:
                classification = "CLEARLY_SEPARATED"
                sep_score = min(1.0, 0.70 + margin)
            elif margin >= 0.12:
                classification = "PARTIALLY_SEPARATED"
                sep_score = min(0.75, 0.40 + margin * 1.5)
            else:
                classification = "HIGHLY_COMPETITIVE"
                sep_score = max(0.10, margin * 2.0)

        return {
            "hypothesis_separation": round(sep_score, 3),
            "margin": round(margin, 3),
            "classification": classification,
            "leading_id": str(top_id),
            "leading_support": round(top_score, 3),
            "runner_up_id": str(runner_up_id) if runner_up_id else None,
            "runner_up_support": round(runner_up_score, 3),
            "is_clearly_separated": classification == "CLEARLY_SEPARATED",
            "is_highly_competitive": classification == "HIGHLY_COMPETITIVE",
        }
