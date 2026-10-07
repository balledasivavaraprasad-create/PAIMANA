"""Preflight Health Checker.

Performs fast, non-blocking operational and authorization preflight checks
prior to tool dispatch to avoid wasted cycles and timeouts on known offline sources.
"""
from __future__ import annotations
from typing import Any, Callable, Optional


class PreflightHealthChecker:
    """Performs lightweight operational preflight checks before specialist tool dispatch."""

    def __init__(self):
        self._custom_checks: dict[str, Callable[[dict], tuple[bool, Optional[str]]]] = {}

    def register_check(self, tool_name: str, check_fn: Callable[[dict], tuple[bool, Optional[str]]]):
        """Registers a custom preflight health check for a specific tool."""
        self._custom_checks[tool_name.lower()] = check_fn

    def check(self, tool_name: str, context: Optional[dict] = None) -> tuple[bool, Optional[str]]:
        """Evaluates tool preflight health. Returns (is_healthy, error_or_reason)."""
        clean_name = tool_name.replace("tool_", "").lower()
        context = context or {}

        # 1. Evaluate custom registered check if present
        if clean_name in self._custom_checks:
            try:
                ok, reason = self._custom_checks[clean_name](context)
                if not ok:
                    return False, reason or f"Preflight check failed for tool '{tool_name}'"
            except Exception as e:
                return False, f"Preflight check exception: {e}"

        # 2. Authorization / Scope check
        required_auth = context.get("required_auth", "read_only")
        caller_auth = context.get("caller_auth", "read_only")
        if required_auth == "privileged" and caller_auth != "privileged":
            return False, f"Permission Denied: tool requires '{required_auth}' scope, caller has '{caller_auth}'"

        # 3. Endpoint / Source availability flag check
        offline_sources = context.get("offline_sources", set())
        if clean_name in offline_sources:
            return False, f"Source Unavailable: Tool '{tool_name}' endpoint is flagged offline in preflight."

        return True, None
