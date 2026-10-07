"""Data models for Phase 13 Outcome Learning.

Supports the canonical 7-stage closed-loop lifecycle:
    recommendation
    → approval
    → intervention
    → outcome
    → effectiveness
    → memory
    → recommendation evaluation
"""
from __future__ import annotations
import enum
import time
from dataclasses import dataclass, field
from typing import Any, Optional


class OutcomeAttribution(str, enum.Enum):
    """Categorical causal attribution for post-intervention trajectory."""
    LIKELY_EFFECTIVE = "LIKELY_EFFECTIVE"
    POSSIBLY_EFFECTIVE = "POSSIBLY_EFFECTIVE"
    INCONCLUSIVE = "INCONCLUSIVE"
    LIKELY_INEFFECTIVE = "LIKELY_INEFFECTIVE"
    FAILED = "FAILED"
    CONFOUNDED = "CONFOUNDED"


@dataclass
class OutcomeObservation:
    """Empirical observations before and after an operational intervention."""
    observation_id: str
    project_code: str
    intervention_id: str
    pre_metrics: dict[str, float]
    post_metrics: dict[str, float]
    confounders: list[str] = field(default_factory=list)
    observed_at: float = field(default_factory=time.time)
    observation_window_days: float = 60.0

    @property
    def risk_delta(self) -> float:
        """Negative is improvement (risk decreased)."""
        return self.post_metrics.get("risk_score", 50.0) - self.pre_metrics.get("risk_score", 50.0)

    @property
    def gap_delta(self) -> float:
        """Negative is improvement (expenditure-progress gap narrowed)."""
        return self.post_metrics.get("progress_expenditure_gap_pct", 0.0) - self.pre_metrics.get("progress_expenditure_gap_pct", 0.0)

    @property
    def delay_delta(self) -> float:
        """Negative is schedule recovery (months slippage reduced)."""
        return self.post_metrics.get("completion_delay_months", 0.0) - self.pre_metrics.get("completion_delay_months", 0.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "project_code": self.project_code,
            "intervention_id": self.intervention_id,
            "pre_metrics": self.pre_metrics,
            "post_metrics": self.post_metrics,
            "risk_delta": round(self.risk_delta, 2),
            "gap_delta": round(self.gap_delta, 2),
            "delay_delta": round(self.delay_delta, 2),
            "confounders": list(self.confounders),
            "observed_at": self.observed_at,
            "observation_window_days": self.observation_window_days,
        }


@dataclass
class EffectivenessAssessment:
    """Rigorous evaluation of empirical effectiveness vs predicted benefit."""
    assessment_id: str
    observation_id: str
    attribution: OutcomeAttribution
    raw_effectiveness_score: float      # 0.0 to 1.0
    confounder_discount: float          # 0.0 to 1.0 (1.0 = no discount)
    net_effectiveness_score: float      # raw * discount
    predicted_benefit: float            # from recommendation candidate
    predicted_risk_reduction: float     # from recommendation candidate
    calibration_error: float            # |predicted - net_effectiveness|
    component_breakdown: dict[str, float] = field(default_factory=dict)
    is_success: bool = False
    is_failure: bool = False
    assessed_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "observation_id": self.observation_id,
            "attribution": self.attribution.value,
            "raw_effectiveness_score": round(self.raw_effectiveness_score, 3),
            "confounder_discount": round(self.confounder_discount, 3),
            "net_effectiveness_score": round(self.net_effectiveness_score, 3),
            "predicted_benefit": round(self.predicted_benefit, 3),
            "predicted_risk_reduction": round(self.predicted_risk_reduction, 3),
            "calibration_error": round(self.calibration_error, 3),
            "component_breakdown": {k: round(v, 3) for k, v in self.component_breakdown.items()},
            "is_success": self.is_success,
            "is_failure": self.is_failure,
            "assessed_at": self.assessed_at,
        }


@dataclass
class RecommendationCalibration:
    """Dynamic calibration tracking for an action type / playbook template."""
    action_type: str
    total_applications: int = 0
    success_count: int = 0
    failure_count: int = 0
    mean_predicted_benefit: float = 0.50
    mean_realized_effectiveness: float = 0.50
    calibration_multiplier: float = 1.00
    mean_absolute_error: float = 0.00
    last_updated: float = field(default_factory=time.time)

    @property
    def track_record(self) -> float:
        """Laplace-smoothed Bayesian success probability."""
        return (self.success_count + 1.0) / (self.total_applications + 2.0)

    def update(self, predicted_benefit: float, realized_effectiveness: float, is_success: bool, is_failure: bool) -> None:
        self.total_applications += 1
        if is_success:
            self.success_count += 1
        elif is_failure:
            self.failure_count += 1

        n = self.total_applications
        self.mean_predicted_benefit += (predicted_benefit - self.mean_predicted_benefit) / n
        self.mean_realized_effectiveness += (realized_effectiveness - self.mean_realized_effectiveness) / n
        
        error = abs(predicted_benefit - realized_effectiveness)
        self.mean_absolute_error += (error - self.mean_absolute_error) / n

        # Calibration multiplier scales around baseline 1.0 based on track record
        # Track record 0.50 -> multiplier 1.00
        # Track record 0.85 -> multiplier 1.35
        # Track record 0.15 -> multiplier 0.65
        self.calibration_multiplier = round(0.50 + (1.00 * self.track_record), 3)
        self.last_updated = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type,
            "total_applications": self.total_applications,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "track_record": round(self.track_record, 3),
            "mean_predicted_benefit": round(self.mean_predicted_benefit, 3),
            "mean_realized_effectiveness": round(self.mean_realized_effectiveness, 3),
            "calibration_multiplier": self.calibration_multiplier,
            "mean_absolute_error": round(self.mean_absolute_error, 3),
            "last_updated": self.last_updated,
        }


@dataclass
class LearningMilestone:
    """Complete, end-to-end closed loop record connecting all 7 stages."""
    milestone_id: str
    project_code: str
    
    # 1. Recommendation
    candidate_id: str
    action_title: str
    action_type: str
    predicted_benefit: float
    
    # 2. Approval
    approval_record_id: str
    approver_name: str
    approval_class: str
    
    # 3. Intervention
    execution_id: str
    executed_at: float
    
    # 4. Outcome
    observation: OutcomeObservation
    
    # 5. Effectiveness
    assessment: EffectivenessAssessment
    
    # 6. Memory
    precedent_id: Optional[str]
    precedent_status: str
    precedent_track_record: float
    
    # 7. Recommendation Evaluation
    updated_calibration: RecommendationCalibration
    
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "milestone_id": self.milestone_id,
            "project_code": self.project_code,
            "lifecycle_stages": {
                "1_recommendation": {
                    "candidate_id": self.candidate_id,
                    "action_title": self.action_title,
                    "action_type": self.action_type,
                    "predicted_benefit": round(self.predicted_benefit, 3),
                },
                "2_approval": {
                    "approval_record_id": self.approval_record_id,
                    "approver_name": self.approver_name,
                    "approval_class": self.approval_class,
                },
                "3_intervention": {
                    "execution_id": self.execution_id,
                    "executed_at": self.executed_at,
                },
                "4_outcome": self.observation.to_dict(),
                "5_effectiveness": self.assessment.to_dict(),
                "6_memory": {
                    "precedent_id": self.precedent_id,
                    "precedent_status": self.precedent_status,
                    "precedent_track_record": round(self.precedent_track_record, 3),
                },
                "7_recommendation_evaluation": self.updated_calibration.to_dict(),
            },
            "created_at": self.created_at,
        }
