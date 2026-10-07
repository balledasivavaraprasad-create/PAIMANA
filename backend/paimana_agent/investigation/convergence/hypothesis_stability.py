"""Hypothesis Stability Evaluator.

Tracks changes in hypothesis support across iterations to verify that convergence
reflects true trajectory stabilization rather than a single ephemeral snapshot.
"""
from __future__ import annotations
from typing import Any, Optional


class HypothesisStabilityEvaluator:
    """Evaluates the stability and variance of hypothesis scores over consecutive steps."""

    @classmethod
    def evaluate_stability(
        cls,
        history: list[dict[str, float]],
        current_scores: Optional[dict[str, float]] = None,
        stability_threshold: float = 0.05,
        required_stable_steps: int = 2
    ) -> dict[str, Any]:
        """Calculates trajectory delta and stability score over the step history."""
        # Append current scores to history window if provided
        all_snapshots = list(history)
        if current_scores:
            all_snapshots.append(current_scores)

        if len(all_snapshots) <= 1:
            # First iteration, no prior history to establish instability or stabilization
            return {
                "hypothesis_stability": 0.50,
                "recent_deltas": [],
                "is_stable": False,
                "consecutive_stable_steps": 0,
                "mean_delta": 0.50,
            }

        deltas: list[float] = []
        for i in range(1, len(all_snapshots)):
            prev = all_snapshots[i - 1]
            curr = all_snapshots[i]
            common_keys = set(prev.keys()) & set(curr.keys())
            if common_keys:
                step_delta = sum(abs(curr.get(k, 0.0) - prev.get(k, 0.0)) for k in common_keys) / len(common_keys)
            else:
                # Key sets are disjoint (e.g. IDs vs names); compare sorted value distributions
                v_prev = sorted(prev.values(), reverse=True)
                v_curr = sorted(curr.values(), reverse=True)
                max_len = max(len(v_prev), len(v_curr))
                step_delta = sum(abs((v_curr[j] if j < len(v_curr) else 0.0) - (v_prev[j] if j < len(v_prev) else 0.0)) for j in range(max_len)) / max(1, max_len)
            deltas.append(step_delta)

        if not deltas:
            return {
                "hypothesis_stability": 0.85,
                "recent_deltas": [],
                "is_stable": True,
                "consecutive_stable_steps": 1,
                "mean_delta": 0.0,
            }

        recent = deltas[-3:]
        mean_recent = sum(recent) / len(recent)

        # Count consecutive steps below stability threshold
        stable_streak = 0
        for d in reversed(deltas):
            if d <= stability_threshold:
                stable_streak += 1
            else:
                break

        # Map mean delta to stability score [0.0, 1.0]
        # Low delta (<= 0.03) -> High stability (0.95)
        # High delta (>= 0.25) -> Low stability (0.25)
        raw_stability = max(0.10, min(1.0, 1.0 - (mean_recent * 3.0)))

        is_stable = stable_streak >= required_stable_steps or (len(deltas) >= 2 and mean_recent <= stability_threshold)

        return {
            "hypothesis_stability": round(raw_stability, 3),
            "recent_deltas": [round(d, 3) for d in recent],
            "is_stable": is_stable,
            "consecutive_stable_steps": stable_streak,
            "mean_delta": round(mean_recent, 3),
        }
