"""Deterministic Domain Question Classifier for Question-Conditioned Peer Discovery.

Analyzes natural language questions and hypothesis IDs to classify the investigation
into explicit categories and extract the required peer comparison dimensions.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .context import PeerInvestigationContext


class InvestigationType(str, Enum):
    """Standardized taxonomy of investigation questions."""
    COST_OVERRUN = "COST_OVERRUN"
    TIME_SLIPPAGE = "TIME_SLIPPAGE"
    LAND_ACQUISITION = "LAND_ACQUISITION"
    EXPENDITURE_PROGRESS_MISMATCH = "EXPENDITURE_PROGRESS_MISMATCH"
    PHYSICAL_PROGRESS_DELAY = "PHYSICAL_PROGRESS_DELAY"
    REGULATORY_CLEARANCE = "REGULATORY_CLEARANCE"
    GENERAL_SIMILARITY = "GENERAL_SIMILARITY"


@dataclass
class ClassificationResult:
    """Outcome of question classification containing target dimensions and metrics."""
    investigation_type: InvestigationType
    confidence: float
    matched_rule: str
    relevant_dimensions: List[str] = field(default_factory=list)
    relevant_metrics: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "investigation_type": self.investigation_type.value,
            "confidence": round(self.confidence, 4),
            "matched_rule": self.matched_rule,
            "relevant_dimensions": self.relevant_dimensions,
            "relevant_metrics": self.relevant_metrics,
        }


class QuestionClassifier:
    """Classifies investigation context deterministically against PAIMANA domain rules."""

    HYPOTHESIS_MAPPING: Dict[str, InvestigationType] = {
        "front_loaded_billing": InvestigationType.EXPENDITURE_PROGRESS_MISMATCH,
        "chronic_schedule_delay": InvestigationType.TIME_SLIPPAGE,
        "regulatory_land_clearance": InvestigationType.LAND_ACQUISITION,
        "cost_escalation": InvestigationType.COST_OVERRUN,
        "contractor_abandonment": InvestigationType.PHYSICAL_PROGRESS_DELAY,
    }

    KEYWORD_PATTERNS: List[tuple[re.Pattern, InvestigationType, float]] = [
        # Expenditure mismatch
        (
            re.compile(r"\b(expenditure|spending|disproportionate|front[- ]loaded|billing|financial progress)\b", re.IGNORECASE),
            InvestigationType.EXPENDITURE_PROGRESS_MISMATCH,
            0.95,
        ),
        # Land acquisition
        (
            re.compile(r"\b(land|acquisition|compensation|right of way|row|encroachment|possession)\b", re.IGNORECASE),
            InvestigationType.LAND_ACQUISITION,
            0.95,
        ),
        # Environmental / Regulatory
        (
            re.compile(r"\b(clearance|environment|forest|wildlife|coastal|statutory|approval)\b", re.IGNORECASE),
            InvestigationType.REGULATORY_CLEARANCE,
            0.90,
        ),
        # Cost overrun
        (
            re.compile(r"\b(cost overrun|budget|revised cost|cost increase|escalation|expensive)\b", re.IGNORECASE),
            InvestigationType.COST_OVERRUN,
            0.90,
        ),
        # Time slippage / Schedule delay
        (
            re.compile(r"\b(time overrun|delay|slippage|schedule|behind schedule|deadline|completion date)\b", re.IGNORECASE),
            InvestigationType.TIME_SLIPPAGE,
            0.90,
        ),
        # Physical progress delay
        (
            re.compile(r"\b(physical progress|milestone|civil work|construction slow|execution)\b", re.IGNORECASE),
            InvestigationType.PHYSICAL_PROGRESS_DELAY,
            0.85,
        ),
    ]

    def classify(self, context: PeerInvestigationContext) -> ClassificationResult:
        """Classifies the given context into an InvestigationType with dimensions and metrics."""
        # 1. Explicit investigation_type provided
        if context.investigation_type:
            try:
                inv_type = InvestigationType(context.investigation_type)
                return self._build_result(inv_type, confidence=1.0, rule="EXPLICIT_INVESTIGATION_TYPE")
            except ValueError:
                pass

        # 2. Map via known hypothesis_id
        if context.hypothesis_id and context.hypothesis_id in self.HYPOTHESIS_MAPPING:
            inv_type = self.HYPOTHESIS_MAPPING[context.hypothesis_id]
            return self._build_result(inv_type, confidence=0.98, rule=f"HYPOTHESIS_MAP:{context.hypothesis_id}")

        # 3. Match against question text
        question_text = (context.investigation_question or "").strip()
        if question_text:
            for pattern, inv_type, conf in self.KEYWORD_PATTERNS:
                if pattern.search(question_text):
                    return self._build_result(inv_type, confidence=conf, rule=f"KEYWORD_REGEX:{pattern.pattern}")

        # 4. Fallback to general similarity
        return self._build_result(
            InvestigationType.GENERAL_SIMILARITY,
            confidence=0.50,
            rule="DEFAULT_GENERAL_FALLBACK",
        )

    def _build_result(
        self,
        inv_type: InvestigationType,
        confidence: float,
        rule: str,
    ) -> ClassificationResult:
        dimensions, metrics = self._get_default_dimensions_and_metrics(inv_type)
        return ClassificationResult(
            investigation_type=inv_type,
            confidence=confidence,
            matched_rule=rule,
            relevant_dimensions=dimensions,
            relevant_metrics=metrics,
        )

    @staticmethod
    def _get_default_dimensions_and_metrics(
        inv_type: InvestigationType,
    ) -> tuple[List[str], List[str]]:
        """Maps investigation types to essential comparison dimensions and metrics."""
        mapping = {
            InvestigationType.EXPENDITURE_PROGRESS_MISMATCH: (
                ["sector", "project_type", "original_cost", "execution_stage", "physical_progress"],
                ["expenditure", "physical_progress", "cost_overrun_pct"],
            ),
            InvestigationType.COST_OVERRUN: (
                ["sector", "project_type", "original_cost", "implementing_agency", "execution_stage"],
                ["revised_cost", "cost_overrun_pct", "expenditure"],
            ),
            InvestigationType.TIME_SLIPPAGE: (
                ["sector", "project_type", "planned_duration", "state", "execution_stage"],
                ["time_overrun_pct", "schedule_delay_months", "physical_progress"],
            ),
            InvestigationType.LAND_ACQUISITION: (
                ["state", "sector", "project_type", "implementing_agency"],
                ["schedule_delay_months", "time_overrun_pct"],
            ),
            InvestigationType.REGULATORY_CLEARANCE: (
                ["state", "sector", "project_type"],
                ["schedule_delay_months", "time_overrun_pct"],
            ),
            InvestigationType.PHYSICAL_PROGRESS_DELAY: (
                ["sector", "project_type", "execution_stage", "implementing_agency"],
                ["physical_progress", "schedule_delay_months"],
            ),
            InvestigationType.GENERAL_SIMILARITY: (
                ["sector", "project_type", "original_cost", "implementing_agency", "state"],
                ["cost_overrun_pct", "time_overrun_pct", "schedule_delay_months"],
            ),
        }
        return mapping.get(inv_type, mapping[InvestigationType.GENERAL_SIMILARITY])
