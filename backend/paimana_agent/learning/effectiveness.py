"""Empirical Effectiveness Analyzer for post-intervention outcomes."""
from __future__ import annotations
import logging
import time
from typing import Optional
from .models import OutcomeObservation, EffectivenessAssessment, OutcomeAttribution

logger = logging.getLogger("paimana_agent.learning.effectiveness")


class EffectivenessAnalyzer:
    """Evaluates empirical metric changes against expected recommendation benefits."""

    def evaluate_effectiveness(
        self,
        observation: OutcomeObservation,
        predicted_benefit: float = 0.50,
        predicted_risk_reduction: float = 0.50
    ) -> EffectivenessAssessment:
        """Computes empirical effectiveness, attribution class, and calibration error."""
        risk_delta = observation.risk_delta
        gap_delta = observation.gap_delta
        delay_delta = observation.delay_delta
        confounders = observation.confounders

        # 1. Component Contributions
        # Risk score reduction (up to 15 pts mapped to 1.0)
        risk_comp = max(0.0, min(1.0, (-risk_delta) / 15.0)) if risk_delta < 0 else 0.0
        
        # Expenditure-progress gap closure (up to 10% mapped to 1.0)
        gap_comp = max(0.0, min(1.0, (-gap_delta) / 10.0)) if gap_delta < 0 else 0.0
        
        # Schedule slippage halted or reduced
        if delay_delta <= 0:
            delay_comp = 1.0
        else:
            delay_comp = max(0.0, 1.0 - (delay_delta / 6.0))

        raw_score = 0.50 * risk_comp + 0.30 * gap_comp + 0.20 * delay_comp

        # Severe deterioration penalty
        if risk_delta > 5.0 or delay_delta > 3.0:
            raw_score = max(0.0, raw_score - 0.40)

        # 2. Confounder Discounting
        num_conf = len(confounders)
        if num_conf == 0:
            conf_discount = 1.00
        elif num_conf == 1:
            conf_discount = 0.70
        else:
            conf_discount = 0.50

        net_score = round(raw_score * conf_discount, 3)

        # 3. Categorical Attribution
        if risk_delta >= 8.0 or delay_delta >= 4.0:
            attribution = OutcomeAttribution.FAILED
        elif risk_delta > 2.0 or delay_delta > 1.0:
            attribution = OutcomeAttribution.LIKELY_INEFFECTIVE
        elif num_conf > 0:
            attribution = OutcomeAttribution.CONFOUNDED
        elif risk_delta <= -8.0 and delay_delta <= 0.0:
            attribution = OutcomeAttribution.LIKELY_EFFECTIVE
        elif risk_delta < -2.0 or (gap_delta < -3.0 and delay_delta <= 1.0):
            attribution = OutcomeAttribution.POSSIBLY_EFFECTIVE
        else:
            attribution = OutcomeAttribution.INCONCLUSIVE

        is_success = attribution in {OutcomeAttribution.LIKELY_EFFECTIVE, OutcomeAttribution.POSSIBLY_EFFECTIVE}
        is_failure = attribution in {OutcomeAttribution.FAILED, OutcomeAttribution.LIKELY_INEFFECTIVE}

        calib_error = round(abs(predicted_benefit - net_score), 3)

        ass_id = f"ASS-EFF-{observation.project_code}-{int(time.time()*1000)%100000:05d}"
        
        assessment = EffectivenessAssessment(
            assessment_id=ass_id,
            observation_id=observation.observation_id,
            attribution=attribution,
            raw_effectiveness_score=round(raw_score, 3),
            confounder_discount=conf_discount,
            net_effectiveness_score=net_score,
            predicted_benefit=predicted_benefit,
            predicted_risk_reduction=predicted_risk_reduction,
            calibration_error=calib_error,
            component_breakdown={
                "risk_reduction_component": round(risk_comp, 3),
                "gap_closure_component": round(gap_comp, 3),
                "delay_stabilization_component": round(delay_comp, 3),
            },
            is_success=is_success,
            is_failure=is_failure,
            assessed_at=time.time()
        )
        logger.info(
            f"Evaluated effectiveness for '{observation.project_code}': attribution={attribution.value}, "
            f"net_score={net_score:.2f}, calibration_error={calib_error:.2f}"
        )
        return assessment
