"""Outcome Learning Engine closing the 7-stage operational learning loop:
    recommendation
    → approval
    → intervention
    → outcome
    → effectiveness
    → memory
    → recommendation evaluation
"""
from __future__ import annotations
import logging
import time
from typing import Any, Optional
from .models import (
    OutcomeObservation,
    EffectivenessAssessment,
    RecommendationCalibration,
    LearningMilestone,
)
from .effectiveness import EffectivenessAnalyzer
from .memory_syncer import InstitutionalMemorySyncer
from .recommendation_evaluator import RecommendationEvaluator
from ..memory.precedent_memory import PrecedentMemoryStore
from ..tools import _default_precedent_store

logger = logging.getLogger("paimana_agent.learning.outcome_loop")


class OutcomeLearningEngine:
    """Master engine orchestrating the complete closed-loop outcome learning cycle."""

    def __init__(
        self,
        memory_store: Optional[PrecedentMemoryStore] = None,
        effectiveness_analyzer: Optional[EffectivenessAnalyzer] = None,
        recommendation_evaluator: Optional[RecommendationEvaluator] = None
    ):
        self.memory_store = memory_store or _default_precedent_store
        self.effectiveness_analyzer = effectiveness_analyzer or EffectivenessAnalyzer()
        self.memory_syncer = InstitutionalMemorySyncer(self.memory_store)
        self.recommendation_evaluator = recommendation_evaluator or RecommendationEvaluator()
        self._milestones: list[LearningMilestone] = []

    def process_closed_loop(
        self,
        candidate: Any,
        approval_record: Any,
        execution_record: Any,
        pre_metrics: dict[str, float],
        post_metrics: dict[str, float],
        confounders: Optional[list[str]] = None,
        precedent_id: Optional[str] = None,
        independence_group: Optional[str] = None
    ) -> LearningMilestone:
        """Executes the complete 7-stage learning loop from recommendation to dynamic recalibration."""
        now = time.time()
        project_code = getattr(execution_record, "project_code", getattr(approval_record.request, "project_code", "UNKNOWN"))
        act_title = getattr(candidate, "title", getattr(candidate, "action", "Operational Intervention"))
        act_type = getattr(candidate, "action_type", getattr(candidate, "candidate_type", "PRIMARY_RECOVERY"))
        pred_benefit = float(getattr(candidate, "expected_benefit", 0.50))
        pred_rr = float(getattr(candidate, "expected_risk_reduction", 0.50))

        # --------------------------------------------------------------------
        # Stage 4: Empirical Outcome Observation
        # --------------------------------------------------------------------
        obs_id = f"OBS-{project_code}-{int(now * 1000) % 100000:05d}"
        observation = OutcomeObservation(
            observation_id=obs_id,
            project_code=project_code,
            intervention_id=getattr(execution_record, "execution_id", f"EXEC-{project_code}"),
            pre_metrics=dict(pre_metrics),
            post_metrics=dict(post_metrics),
            confounders=list(confounders or []),
            observed_at=now
        )

        # --------------------------------------------------------------------
        # Stage 5: Effectiveness Assessment & Attribution
        # --------------------------------------------------------------------
        assessment = self.effectiveness_analyzer.evaluate_effectiveness(
            observation=observation,
            predicted_benefit=pred_benefit,
            predicted_risk_reduction=pred_rr
        )

        # --------------------------------------------------------------------
        # Stage 6: Institutional Memory Consolidation
        # --------------------------------------------------------------------
        prec = self.memory_syncer.sync_outcome_to_precedent(
            observation=observation,
            assessment=assessment,
            precedent_id=precedent_id,
            action_title=act_title,
            action_type=act_type,
            independence_group=independence_group
        )

        # --------------------------------------------------------------------
        # Stage 7: Recommendation Evaluation & Recalibration
        # --------------------------------------------------------------------
        updated_calib = self.recommendation_evaluator.record_outcome_feedback(
            action_type=act_type,
            predicted_benefit=pred_benefit,
            assessment=assessment
        )

        # Assemble full 7-stage learning milestone
        milestone = LearningMilestone(
            milestone_id=f"MLS-LRN-{project_code}-{int(now * 1000) % 100000:05d}",
            project_code=project_code,
            candidate_id=getattr(candidate, "id", "CAND-01"),
            action_title=act_title,
            action_type=act_type,
            predicted_benefit=pred_benefit,
            approval_record_id=getattr(approval_record, "record_id", "REC-APP-UNKNOWN"),
            approver_name=getattr(approval_record.decision.approver, "name", "Approver"),
            approval_class=getattr(approval_record.request, "approval_class", "managerial"),
            execution_id=getattr(execution_record, "execution_id", "EXEC-UNKNOWN"),
            executed_at=float(getattr(execution_record, "executed_at", now)),
            observation=observation,
            assessment=assessment,
            precedent_id=prec.id,
            precedent_status=prec.status,
            precedent_track_record=prec.track_record,
            updated_calibration=updated_calib,
            created_at=now
        )

        self._milestones.append(milestone)
        logger.info(
            f"Completed closed-loop learning milestone '{milestone.milestone_id}' for '{project_code}'. "
            f"Precedent track_record={prec.track_record:.2f}, Calibration multiplier={updated_calib.calibration_multiplier:.2f}."
        )
        return milestone

    def get_milestones(self, project_code: Optional[str] = None) -> list[LearningMilestone]:
        """Returns all recorded learning milestones, optionally filtered by project_code."""
        if project_code:
            return [m for m in self._milestones if m.project_code == project_code]
        return list(self._milestones)
