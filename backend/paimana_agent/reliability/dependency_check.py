"""Tool Dependency Checker.

Validates that prerequisite databases, models, features, or external connections
are present before allowing a tool to be selected or executed.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolDependencyStatus:
    """Outcome of dependency verification for a specific tool."""
    tool_name: str
    satisfied: bool
    missing_dependencies: list[str] = field(default_factory=list)
    remediation_hint: Optional[str] = None


class DependencyChecker:
    """Verifies that all prerequisite inputs and services are met for tool execution."""

    @classmethod
    def check_dependencies(
        cls,
        tool_name: str,
        prerequisites: list[str],
        available_context: dict[str, Any],
    ) -> ToolDependencyStatus:
        """Verifies that all required prerequisites are satisfied."""
        missing = []
        for req in prerequisites:
            val = available_context.get(req)
            if val is None:
                missing.append(req)

        satisfied = len(missing) == 0
        hint = None
        if not satisfied:
            hint = f"Ensure required context keys/objects {missing} are provided before dispatching {tool_name}."

        return ToolDependencyStatus(
            tool_name=tool_name,
            satisfied=satisfied,
            missing_dependencies=missing,
            remediation_hint=hint,
        )
