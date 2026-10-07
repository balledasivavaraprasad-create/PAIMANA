"""Recommendation decision tracing and audit serialization."""
from __future__ import annotations
import logging
from typing import Any
from .candidate import RecommendationCandidate
from .selector import RecommendationDecision

logger = logging.getLogger("paimana_agent.recommendations.trace")


class RecommendationTracer:
    """Audit tracer recording candidate generation, scoring, and selection decisions."""

    def log_decision(self, decision: RecommendationDecision, project_code: str):
        """Emits structured audit log for the recommendation decision."""
        sel = decision.selected_candidate
        if sel:
            logger.info(
                "Recommendation Selected for %s: '%s' (ID: %s, Score: %.3f, Conf: %.3f, Status: %s)",
                project_code, sel.title[:50], sel.id, sel.confidence_adjusted_score, sel.confidence, decision.outcome_status
            )
        else:
            logger.warning(
                "No Recommendation Selected for %s (Status: %s)",
                project_code, decision.outcome_status
            )
