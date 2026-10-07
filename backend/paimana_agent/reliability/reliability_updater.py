"""Reliability Profile Updater.

Applies post-execution updates to tool reliability profiles, calculates degradation
adjustments, and records audit reason codes (e.g. TOOL_RELIABILITY_REDUCED).
"""
from __future__ import annotations
import time
from typing import Any, Optional
from .models import ToolReliabilityProfile, ToolResult, ToolResultStatus


class ReliabilityUpdater:
    """Updates persistent reliability profiles with new operational telemetry."""

    @classmethod
    def update_profile(
        cls,
        profile: ToolReliabilityProfile,
        result: ToolResult,
    ) -> ToolReliabilityProfile:
        """Applies result telemetry to profile and appends explanatory reason codes."""
        prev_composite = profile.composite_reliability
        profile.record_call(result)

        # Check for reason codes
        st = result.status
        if st == ToolResultStatus.TIMEOUT.value:
            if "TOOL_TIMEOUT_EXCEEDED" not in profile.reason_codes:
                profile.reason_codes.append("TOOL_TIMEOUT_EXCEEDED")

        elif st == ToolResultStatus.SCHEMA_ERROR.value:
            if "TOOL_SCHEMA_VIOLATION" not in profile.reason_codes:
                profile.reason_codes.append("TOOL_SCHEMA_VIOLATION")

        elif st == ToolResultStatus.VALIDATION_ERROR.value or (result.is_success and not result.useful_evidence):
            if "FALSE_SUCCESS_DETECTED" not in profile.reason_codes:
                profile.reason_codes.append("FALSE_SUCCESS_DETECTED")

        if result.completeness_score < 0.70:
            if "DATA_COMPLETENESS_DEGRADED" not in profile.reason_codes:
                profile.reason_codes.append("DATA_COMPLETENESS_DEGRADED")

        # Did composite reliability drop significantly?
        if profile.composite_reliability < prev_composite - 0.05:
            if "TOOL_RELIABILITY_REDUCED" not in profile.reason_codes:
                profile.reason_codes.append("TOOL_RELIABILITY_REDUCED")

        return profile
