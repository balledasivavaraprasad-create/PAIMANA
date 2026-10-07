"""Recommendation Evaluator closing the learning loop back to the decision engine.

Dynamically calibrates candidate benefit models, computes portfolio calibration error (MACE),
and scales candidate scoring by empirical historical track records.
"""
from __future__ import annotations
import logging
import time
from typing import Any, Optional
from .models import RecommendationCalibration, EffectivenessAssessment

logger = logging.getLogger("paimana_agent.learning.recommendation_evaluator")


class RecommendationEvaluator:
    """Evaluates recommendation system performance over time and dynamically calibrates generation."""

    def __init__(self):
        self._calibrations: dict[str, RecommendationCalibration] = {}
        self._history: list[dict[str, Any]] = []

    def get_calibration(self, action_type: str) -> RecommendationCalibration:
        """Retrieves or initializes calibration record for an action type."""
        norm_type = action_type.upper()
        if norm_type not in self._calibrations:
            self._calibrations[norm_type] = RecommendationCalibration(action_type=norm_type)
        return self._calibrations[norm_type]

    def record_outcome_feedback(
        self,
        action_type: str,
        predicted_benefit: float,
        assessment: EffectivenessAssessment
    ) -> RecommendationCalibration:
        """Updates calibration metrics with verified post-intervention empirical results."""
        calib = self.get_calibration(action_type)
        calib.update(
            predicted_benefit=predicted_benefit,
            realized_effectiveness=assessment.net_effectiveness_score,
            is_success=assessment.is_success,
            is_failure=assessment.is_failure
        )
        self._history.append({
            "action_type": action_type,
            "predicted_benefit": predicted_benefit,
            "realized_effectiveness": assessment.net_effectiveness_score,
            "calibration_error": assessment.calibration_error,
            "attribution": assessment.attribution.value,
            "timestamp": time.time(),
        })
        logger.info(
            f"Updated calibration for '{action_type}': track_record={calib.track_record:.2f}, "
            f"multiplier={calib.calibration_multiplier:.2f}, MAE={calib.mean_absolute_error:.2f}"
        )
        return calib

    def calibrate_candidate(self, candidate: Any) -> Any:
        """Applies empirical calibration multiplier to a recommendation candidate."""
        act_type = getattr(candidate, "action_type", getattr(candidate, "candidate_type", "GENERAL_ACTION"))
        calib = self.get_calibration(act_type)

        if calib.total_applications > 0:
            # Scale candidate expected benefit by empirical calibration multiplier
            original_benefit = float(getattr(candidate, "expected_benefit", 0.50))
            calibrated_benefit = round(min(1.0, max(0.05, original_benefit * calib.calibration_multiplier)), 3)
            candidate.expected_benefit = calibrated_benefit

            # If action type has demonstrated high failure rate, penalize implementation risk
            if calib.track_record < 0.40 and calib.failure_count > 0:
                cur_risk = float(getattr(candidate, "implementation_risk", 0.20))
                candidate.implementation_risk = round(min(0.95, cur_risk + 0.15), 3)

            # Record calibration provenance on candidate
            if hasattr(candidate, "score_breakdown") and isinstance(candidate.score_breakdown, dict):
                candidate.score_breakdown["empirical_calibration"] = {
                    "action_type": act_type,
                    "calibration_multiplier": calib.calibration_multiplier,
                    "track_record": round(calib.track_record, 3),
                    "original_benefit": original_benefit,
                    "calibrated_benefit": calibrated_benefit,
                }
        return candidate

    def compute_portfolio_metrics(self) -> dict[str, Any]:
        """Calculates system-wide recommendation accuracy and learning metrics."""
        if not self._history:
            return {
                "total_evaluations": 0,
                "mean_absolute_calibration_error": 0.0,
                "portfolio_success_rate": 0.0,
                "portfolio_failure_rate": 0.0,
                "playbook_calibrations": {},
            }

        total = len(self._history)
        mace = sum(h["calibration_error"] for h in self._history) / total
        successes = sum(1 for h in self._history if h["attribution"] in {"LIKELY_EFFECTIVE", "POSSIBLY_EFFECTIVE"})
        failures = sum(1 for h in self._history if h["attribution"] in {"FAILED", "LIKELY_INEFFECTIVE"})

        return {
            "total_evaluations": total,
            "mean_absolute_calibration_error": round(mace, 3),
            "portfolio_success_rate": round(successes / total, 3),
            "portfolio_failure_rate": round(failures / total, 3),
            "playbook_calibrations": {k: v.to_dict() for k, v in self._calibrations.items()},
        }
