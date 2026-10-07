"""Tool Failure Classifier.

Categorizes exceptions and tool error payloads into standardized taxonomy codes,
enabling deterministic recovery rather than ad-hoc exception matching.
"""
from __future__ import annotations
import re
from typing import Any, Optional
from .models import ToolResult, ToolResultStatus


class ToolFailureClassifier:
    """Classifies raw exceptions and error payloads into standardized taxonomy codes."""

    TAXONOMY = {
        "TIMEOUT": "TOOL_TIMEOUT",
        "RATE_LIMITED": "TOOL_RATE_LIMITED",
        "AUTH_FAILED": "TOOL_AUTH_FAILED",
        "SOURCE_UNAVAILABLE": "TOOL_SOURCE_UNAVAILABLE",
        "SCHEMA_INVALID": "TOOL_SCHEMA_INVALID",
        "RESULT_INVALID": "TOOL_RESULT_INVALID",
        "RESULT_STALE": "TOOL_RESULT_STALE",
        "RESULT_PARTIAL": "TOOL_RESULT_PARTIAL",
        "DEPENDENCY_UNAVAILABLE": "TOOL_DEPENDENCY_UNAVAILABLE",
        "PERMISSION_DENIED": "TOOL_PERMISSION_DENIED",
        "CIRCUIT_OPEN": "TOOL_CIRCUIT_OPEN",
        "INTERNAL_ERROR": "TOOL_INTERNAL_ERROR",
    }

    RETRYABLE_CODES = {
        "TOOL_TIMEOUT",
        "TOOL_RATE_LIMITED",
        "TOOL_SOURCE_UNAVAILABLE",
    }

    NON_RETRYABLE_CODES = {
        "TOOL_AUTH_FAILED",
        "TOOL_PERMISSION_DENIED",
        "TOOL_SCHEMA_INVALID",
        "TOOL_RESULT_INVALID",
        "TOOL_CIRCUIT_OPEN",
        "TOOL_DEPENDENCY_UNAVAILABLE",
    }

    @classmethod
    def classify(cls, error_or_result: Any) -> tuple[str, bool]:
        """Maps an error string, exception, or ToolResult to (taxonomy_code, is_retryable)."""
        if isinstance(error_or_result, ToolResult):
            st = error_or_result.status
            if st == ToolResultStatus.TIMEOUT.value:
                return "TOOL_TIMEOUT", True
            elif st == ToolResultStatus.RATE_LIMITED.value:
                return "TOOL_RATE_LIMITED", True
            elif st in (ToolResultStatus.AUTH_FAILURE.value, "PERMISSION_DENIED"):
                return "TOOL_AUTH_FAILED", False
            elif st == ToolResultStatus.SOURCE_UNAVAILABLE.value:
                return "TOOL_SOURCE_UNAVAILABLE", True
            elif st == ToolResultStatus.SCHEMA_ERROR.value:
                return "TOOL_SCHEMA_INVALID", False
            elif st == ToolResultStatus.VALIDATION_ERROR.value:
                return "TOOL_RESULT_INVALID", False
            elif st == ToolResultStatus.CIRCUIT_OPEN.value:
                return "TOOL_CIRCUIT_OPEN", False
            elif st == ToolResultStatus.DEPENDENCY_FAILURE.value:
                return "TOOL_DEPENDENCY_UNAVAILABLE", False
            err_msg = str(error_or_result.error or error_or_result.summary or "")
        else:
            err_msg = str(error_or_result)

        err_lower = err_msg.lower()

        if "timeout" in err_lower or "timed out" in err_lower or "deadline exceeded" in err_lower:
            return "TOOL_TIMEOUT", True
        if "rate limit" in err_lower or "too many requests" in err_lower or "429" in err_lower:
            return "TOOL_RATE_LIMITED", True
        if "auth" in err_lower or "forbidden" in err_lower or "unauthorized" in err_lower or "401" in err_lower or "403" in err_lower:
            return "TOOL_AUTH_FAILED", False
        if "unavailable" in err_lower or "connection refused" in err_lower or "503" in err_lower or "502" in err_lower:
            return "TOOL_SOURCE_UNAVAILABLE", True
        if "schema" in err_lower or "parse error" in err_lower or "jsondecode" in err_lower:
            return "TOOL_SCHEMA_INVALID", False
        if "circuit" in err_lower and "open" in err_lower:
            return "TOOL_CIRCUIT_OPEN", False
        if "dependency" in err_lower or "prerequisite" in err_lower or "missing file" in err_lower:
            return "TOOL_DEPENDENCY_UNAVAILABLE", False

        return "TOOL_INTERNAL_ERROR", False
