"""Hypothesis Oscillation Detector.

Detects unstable reasoning loops where the leading hypothesis identity alternates
repeatedly with narrow margins, indicating genuine ambiguity requiring a targeted
discriminating tool rather than premature convergence.
"""
from __future__ import annotations
from typing import Any


class HypothesisOscillationDetector:
    """Detects alternating dominance between closely contested hypotheses."""

    @classmethod
    def detect_oscillation(
        cls,
        leader_history: list[str],
        margin_history: list[float],
        min_flips: int = 2,
        narrow_margin_threshold: float = 0.15
    ) -> dict[str, Any]:
        """Examines leader identity flips across steps:

        Example: ['H_contractor', 'H_approval', 'H_contractor'] -> 2 flips with narrow margins.
        """
        if len(leader_history) < 3:
            return {
                "is_oscillating": False,
                "flip_count": 0,
                "contested_hypotheses": list(set(leader_history)),
                "status": "STABLE",
            }

        flips = 0
        for i in range(1, len(leader_history)):
            if leader_history[i] != leader_history[i - 1]:
                flips += 1

        # Check average margin during switches
        recent_margins = margin_history[-len(leader_history):]
        mean_margin = (sum(recent_margins) / len(recent_margins)) if recent_margins else 0.50

        # Oscillation confirmed if >= min_flips occur with narrow margins
        is_oscillating = (flips >= min_flips and mean_margin <= narrow_margin_threshold)

        return {
            "is_oscillating": is_oscillating,
            "flip_count": flips,
            "mean_margin": round(mean_margin, 3),
            "contested_hypotheses": list(set(leader_history)),
            "status": "UNSTABLE_OSCILLATION" if is_oscillating else "STABLE",
            "action_required": "DISCRIMINATING_EVIDENCE_NEEDED" if is_oscillating else "PROCEED",
        }
