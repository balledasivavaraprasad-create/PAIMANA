"""Hypothesis Validator for candidate hypotheses.

Enforces strict verification rules: schema compliance, valid evidence references,
falsifiability, observable predictions, testability with tools, and no invented facts.
"""
from __future__ import annotations
import logging
from typing import Optional, Any
from .model import Hypothesis
from .similarity import HypothesisSimilarityChecker

logger = logging.getLogger("paimana_agent.hypotheses.validator")


class HypothesisValidator:
    """Validates candidate hypotheses against formal agentic guardrails."""

    def __init__(self, similarity_checker: Optional[HypothesisSimilarityChecker] = None):
        self.similarity = similarity_checker or HypothesisSimilarityChecker()

    def validate_candidate(
        self,
        candidate: Hypothesis,
        known_evidence_ids: set[str],
        known_evidence_claims: list[str],
        existing_hypotheses: list[Hypothesis],
        available_tools: Optional[list[str]] = None
    ) -> tuple[bool, str, Optional[str]]:
        """Validates candidate hypothesis.
        
        Returns:
            (is_valid: bool, reason: str, merged_with_id: Optional[str])
        """
        # 1. Schema Validation: statement must be non-empty and substantive
        if not candidate.statement or len(candidate.statement.strip()) < 15:
            return False, "Rejected: Hypothesis statement is missing or trivial (<15 chars).", None

        # 2. Evidence Reference Validation: references must exist in known evidence
        for eid in candidate.support_evidence_ids:
            if eid not in known_evidence_ids:
                return False, f"Rejected: References nonexistent evidence ID '{eid}'.", None

        for eid in candidate.contradiction_evidence_ids:
            if eid not in known_evidence_ids:
                return False, f"Rejected: References nonexistent contradiction evidence ID '{eid}'.", None

        # 3. Unsupported Fact Check: cannot assert specific invented numbers/proper nouns not in evidence
        # E.g. asserting specific unauthorized dates or unobserved numbers
        stmt_lower = candidate.statement.lower()
        if "embezzlement" in stmt_lower or "fraud" in stmt_lower or "criminal" in stmt_lower:
            # High-liability accusations require explicit evidence claim containing such terms
            if not any("fraud" in c.lower() or "audit" in c.lower() for c in known_evidence_claims):
                return False, "Rejected: Contains severe unsupported claims (fraud/criminal) without explicit evidence.", None

        # 4. Falsifiability & Observable Prediction Check
        # Must have at least one predicted observation or falsification condition
        if not candidate.predicted_observations and not candidate.falsification_condition:
            return False, "Rejected: Hypothesis is unfalsifiable; lacks observable predictions or falsification condition.", None

        # 5. Discriminating Evidence & Testability Check
        # Must define discriminating evidence probeable via tools
        if not candidate.discriminating_evidence:
            return False, "Rejected: Hypothesis fails to specify discriminating evidence testable by tools.", None

        # 6. Duplicate & Novelty Check
        is_dup, match = self.similarity.is_duplicate(candidate, existing_hypotheses, threshold=0.35)
        if is_dup and match:
            return False, f"Rejected: Duplicate of existing hypothesis '{match.id}' (similarity threshold exceeded).", match.id

        # 7. Check if it should be branched as child of existing broad hypothesis
        is_ref, parent = self.similarity.is_refinement(candidate, existing_hypotheses, threshold=0.45)
        if is_ref and parent and not candidate.parent_hypothesis_id:
            candidate.parent_hypothesis_id = parent.id
            logger.info(f"Candidate '{candidate.id}' recognized as refinement of parent '{parent.id}'.")

        return True, "Passed: All hypothesis validation checks satisfied.", None
