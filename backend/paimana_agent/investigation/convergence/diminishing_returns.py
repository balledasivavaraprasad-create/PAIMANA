"""Diminishing Returns Detector.

Analyzes the trajectory of realized information gains across steps to detect
when further tool calls have entered a zone of flat diminishing returns.
"""
from __future__ import annotations
from typing import Any


class DiminishingReturnsDetector:
    """Detects when incremental investigation steps cease to provide meaningful information."""

    @classmethod
    def evaluate_trend(
        cls,
        gain_history: list[float],
        window: int = 3,
        threshold: float = 0.03
    ) -> dict[str, Any]:
        """Analyzes realized information gain trajectory:

        GAINS: [0.31, 0.19, 0.11, 0.06, 0.03, 0.02]
        Trends: GAIN_DECLINING, GAIN_STABLE_LOW, GAIN_REBOUNDING
        """
        if not gain_history:
            return {
                "trend": "INITIAL",
                "has_diminishing_returns": False,
                "mean_recent_gain": 0.50,
                "consecutive_low_gain_steps": 0,
            }

        recent = gain_history[-window:]
        mean_recent = sum(recent) / len(recent)

        # Count consecutive low gain steps
        low_count = 0
        for g in reversed(gain_history):
            if g <= threshold:
                low_count += 1
            else:
                break

        # Check trajectory trend
        if len(gain_history) >= 2:
            last = gain_history[-1]
            penultimate = gain_history[-2]
            if last < penultimate:
                trend = "GAIN_DECLINING"
            elif abs(last - penultimate) <= 0.015:
                trend = "GAIN_STABLE_LOW" if last <= threshold else "GAIN_STABLE"
            else:
                trend = "GAIN_REBOUNDING"
        else:
            trend = "INITIAL"

        # Diminishing returns confirmed if last window steps all stay below threshold
        has_diminishing = (len(recent) >= window and mean_recent <= threshold) or (low_count >= window)

        return {
            "trend": trend,
            "has_diminishing_returns": has_diminishing,
            "mean_recent_gain": round(mean_recent, 3),
            "consecutive_low_gain_steps": low_count,
            "recent_gains": [round(g, 3) for g in recent],
        }
