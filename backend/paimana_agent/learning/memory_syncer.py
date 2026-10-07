"""Closed-loop Institutional Memory synchronizer.

Consolidates evaluated empirical outcomes into validated institutional precedents,
updates Laplace-smoothed Bayesian track records, and registers negative warnings.
"""
from __future__ import annotations
import logging
import time
from typing import Optional, Any
from .models import EffectivenessAssessment, OutcomeObservation
from ..memory.precedent_memory import PrecedentMemoryStore
from ..memory.memory_consolidator import MemoryConsolidator
from ..memory.failure_memory import FailureMemoryManager
from ..memory.memory_reliability import MemoryReliabilityManager
from ..memory.models import Precedent, PrecedentProvenance

logger = logging.getLogger("paimana_agent.learning.memory_syncer")


class InstitutionalMemorySyncer:
    """Synchronizes empirical outcome assessments directly into Institutional Memory."""

    def __init__(self, memory_store: PrecedentMemoryStore):
        self.memory_store = memory_store
        self.consolidator = MemoryConsolidator(self.memory_store)

    def sync_outcome_to_precedent(
        self,
        observation: OutcomeObservation,
        assessment: EffectivenessAssessment,
        precedent_id: Optional[str] = None,
        action_title: str = "",
        action_type: str = "PRIMARY_RECOVERY",
        independence_group: Optional[str] = None
    ) -> Precedent:
        """Updates or creates a validated precedent backed by empirical outcome data."""
        precedent = None
        if precedent_id:
            precedent = self.memory_store.get_precedent(precedent_id)

        now = time.time()
        if not precedent:
            # Create a new precedent record
            p_code = observation.project_code
            prec_id = precedent_id or f"PREC-LRN-{p_code}-{int(now * 1000) % 100000:05d}"
            precedent = Precedent(
                id=prec_id,
                title=f"Empirically Validated Action: {action_title[:60]}",
                source_project_id=p_code,
                intervention={
                    "action": action_title,
                    "action_type": action_type,
                },
                intervention_class=action_type,
                provenance=PrecedentProvenance(
                    source_project_codes=[p_code],
                    independence_group_ids=[independence_group or f"proj_{p_code}"]
                ),
                status="VALIDATED",
                application_count=1,
                success_count=1 if assessment.is_success else 0,
                failure_count=1 if assessment.is_failure else 0,
            )

        # Update observed outcome
        precedent.observed_outcome = {
            "evaluation": assessment.to_dict(),
            "recorded_at": now,
            "pre_metrics": observation.pre_metrics,
            "post_metrics": observation.post_metrics,
        }
        precedent.attribution_class = assessment.attribution.value
        precedent.outcome_quality = 1.00
        precedent.intervention_effectiveness = assessment.net_effectiveness_score
        precedent.last_validated_at = now
        precedent.status = "VALIDATED"

        # Reliability and empirical counts updated via MemoryReliabilityManager
        MemoryReliabilityManager.record_application_outcome(
            precedent=precedent,
            success=assessment.is_success,
            independence_group=independence_group or f"group_{observation.project_code}"
        )

        # Index in FailureMemoryManager if failure
        if assessment.is_failure or assessment.attribution.value == "FAILED":
            FailureMemoryManager.index_failure(precedent)
            logger.warning(
                f"Indexed failure precedent '{precedent.id}' in FailureMemoryManager to protect future decisions."
            )

        self.memory_store.add_precedent(precedent)
        logger.info(
            f"Consolidated outcome into Precedent '{precedent.id}': track_record={precedent.track_record:.2f}, "
            f"successes={precedent.success_count}, failures={precedent.failure_count}."
        )
        return precedent
