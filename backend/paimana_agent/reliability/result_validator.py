"""Tool Result Quality Validation and False-Success Detection.

Performs deep structural and domain-level validation on tool results,
guaranteeing that technical successes with corrupted, stale, or misattributed
payloads are caught before polluting the evidence graph.
"""
from __future__ import annotations
import time
from enum import Enum
from typing import Any, Optional
from .models import ToolResult, ToolResultStatus


class ValidationVerdict(str, Enum):
    """Categorical verdict from post-execution result validation."""
    VALID = "VALID"
    VALID_WITH_WARNINGS = "VALID_WITH_WARNINGS"
    PARTIAL = "PARTIAL"
    INVALID = "INVALID"


class ToolResultValidator:
    """Post-execution validator for specialist tool outputs."""

    @classmethod
    def validate_result(
        cls,
        result: ToolResult,
        expected_project_code: Optional[str] = None,
        max_staleness_days: float = 120.0,
    ) -> tuple[ValidationVerdict, ToolResult]:
        """Validates tool result correctness, detecting false successes and schema flaws."""
        warnings: list[str] = []

        # 1. Non-success statuses do not need domain validation
        if not result.is_success:
            return ValidationVerdict.INVALID, result

        data = result.data or {}

        # 2. False Success Check A: Completely empty data payload returned as success
        if not data and not result.evidence_items:
            result.status = ToolResultStatus.EMPTY_RESULT.value
            result.useful_evidence = False
            result.empty_reason = result.empty_reason or "NO_DATA_RETURNED"
            result.warnings.append("False Success: Function completed with completely empty payload.")
            return ValidationVerdict.INVALID, result

        # 3. False Success Check B: Project Code Mismatch (misattribution)
        payload_code = data.get("project_code") or data.get("code")
        if expected_project_code and payload_code:
            if str(payload_code).strip().upper() != str(expected_project_code).strip().upper():
                result.status = ToolResultStatus.VALIDATION_ERROR.value
                result.useful_evidence = False
                result.error = f"Project code mismatch: expected '{expected_project_code}', got '{payload_code}'."
                result.warnings.append("False Success: Data misattributed to incorrect project.")
                return ValidationVerdict.INVALID, result

        # 4. False Success Check C: All-null values across primary metrics
        non_null_vals = [v for k, v in data.items() if v is not None and not (isinstance(v, (list, dict)) and len(v) == 0)]
        if len(data) > 2 and len(non_null_vals) == 0:
            result.status = ToolResultStatus.VALIDATION_ERROR.value
            result.useful_evidence = False
            result.error = "All payload fields returned null."
            result.warnings.append("False Success: Payload returned null across all fields.")
            return ValidationVerdict.INVALID, result

        # 5. Freshness / Staleness Check
        obs_time = result.observed_at or result.retrieved_at
        age_days = max(0.0, (time.time() - obs_time) / 86400.0)
        if age_days > max_staleness_days:
            result.status = ToolResultStatus.STALE_RESULT.value
            result.freshness_score = round(max(0.1, 1.0 - (age_days / (max_staleness_days * 2))), 3)
            result.warnings.append(f"Stale result: Observation is {age_days:.1f} days old (exceeds {max_staleness_days}d threshold).")
            warnings.append("Result flagged as STALE.")

        # 6. Completeness calculation
        expected_keys = len(data)
        present_keys = sum(1 for v in data.values() if v is not None)
        completeness = present_keys / max(1, expected_keys)
        result.completeness_score = round(completeness, 3)

        if completeness < 0.70:
            result.status = ToolResultStatus.PARTIAL_SUCCESS.value
            result.warnings.append(f"Partial data: only {completeness*100:.0f}% of fields populated.")
            return ValidationVerdict.PARTIAL, result

        if warnings or result.warnings:
            return ValidationVerdict.VALID_WITH_WARNINGS, result

        return ValidationVerdict.VALID, result
