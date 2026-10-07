"""Specialized Failure Memory and Negative Experience Warning Engine.

Indexes past failed interventions and identifies recurring anti-patterns.
Provides warnings to recommendation and hypothesis engines to prevent
repeating institutional mistakes.
"""
from __future__ import annotations
from typing import Any, Optional
from .models import Precedent, PatternFingerprint


class FailureMemoryManager:
    """Manages cautionary failure precedents and generates negative warnings."""

    @classmethod
    def index_failure(cls, precedent: Precedent) -> bool:
        """Determines if a precedent qualifies as a cautionary failure precedent."""
        return (
            precedent.status in {"VALIDATED", "PROVISIONAL"} and
            (precedent.attribution_class in {"FAILED", "LIKELY_INEFFECTIVE"} or
             precedent.failure_count > precedent.success_count)
        )

    @classmethod
    def check_negative_warnings(cls, failed_precedents: list[Precedent],
                                candidate_action: str,
                                pattern: Optional[PatternFingerprint] = None) -> list[str]:
        """Checks if a proposed candidate action matches known historical failure precedents."""
        warnings = []
        action_lower = candidate_action.lower()

        for fp in failed_precedents:
            int_action = str(fp.intervention.get("action", "") or fp.intervention.get("template_id", "")).lower()
            if not int_action:
                continue

            # Check action overlap
            matched = False
            for term in ["penalty", "show-cause", "liquidated damages", "termination", "bank guarantee", "freeze"]:
                if term in action_lower and term in int_action:
                    matched = True
                    break

            if matched or (int_action in action_lower or action_lower in int_action):
                reason = fp.observed_outcome.get("notes") or fp.why_relevant or "resulted in escalation or delays"
                warnings.append(
                    f"Caution: Similar intervention '{int_action}' failed in project {fp.source_project_id or 'precedent ' + fp.id} "
                    f"({reason}). Ensure mitigating prerequisites are satisfied before proceeding."
                )

        return warnings
