"""Stage Boundary Manager enforcing the lockdown:
    INVESTIGATE  ≠  RECOMMEND  ≠  APPROVE  ≠  EXECUTE

Prevents stage bypassing, enforces unidirectional state progression,
and ensures AI agents can never self-approve or autonomously execute actions.
"""
from __future__ import annotations
import logging
from typing import Optional
from .models import (
    Stage,
    Role,
    Actor,
    StageViolationError,
    PermissionDeniedError,
    UnauthorizedExecutionError
)

logger = logging.getLogger("paimana_agent.governance.stage_boundary")


class StageBoundaryManager:
    """Enforces strict structural boundaries between the four operational stages."""

    ALLOWED_TRANSITIONS: dict[Stage, set[Stage]] = {
        Stage.INVESTIGATE: {Stage.RECOMMEND},
        Stage.RECOMMEND: {Stage.APPROVE, Stage.INVESTIGATE},
        Stage.APPROVE: {Stage.EXECUTE, Stage.RECOMMEND, Stage.INVESTIGATE},
        Stage.EXECUTE: set(),  # Terminal stage in the decision lifecycle
    }

    @classmethod
    def validate_transition(
        cls,
        from_stage: Stage,
        to_stage: Stage,
        actor: Optional[Actor] = None
    ) -> bool:
        """Validates that a stage transition is lawful under canonical governance."""
        # 1. Check AI Actor Restrictions
        if actor and actor.is_ai:
            if to_stage in {Stage.APPROVE, Stage.EXECUTE}:
                raise PermissionDeniedError(
                    f"AI Actor '{actor.id}' ({actor.role}) is strictly prohibited from entering stage '{to_stage.value}'. "
                    "Only authorized human institutional stakeholders may approve or execute actions."
                )

        # 2. Check Allowed Transitions
        allowed = cls.ALLOWED_TRANSITIONS.get(from_stage, set())
        if to_stage not in allowed:
            # Detect explicit illegal bypasses
            if from_stage == Stage.INVESTIGATE and to_stage == Stage.EXECUTE:
                raise StageViolationError(
                    "Direct Execution Bypass Detected: Cannot transition directly from 'INVESTIGATE' to 'EXECUTE'. "
                    "All actions must proceed through 'RECOMMEND' and obtain authorized human 'APPROVE'."
                )
            elif from_stage == Stage.RECOMMEND and to_stage == Stage.EXECUTE:
                raise StageViolationError(
                    "Autonomous Execution Bypass Detected: Cannot transition directly from 'RECOMMEND' to 'EXECUTE'. "
                    "Recommendations are advisory proposals and strictly require an independent 'APPROVE' record."
                )
            elif from_stage == Stage.INVESTIGATE and to_stage == Stage.APPROVE:
                raise StageViolationError(
                    "Invalid Stage Transition: Cannot transition directly from 'INVESTIGATE' to 'APPROVE'. "
                    "Candidate options must be generated, validated, and ranked in 'RECOMMEND' first."
                )
            else:
                raise StageViolationError(
                    f"Illegal stage transition from '{from_stage.value}' to '{to_stage.value}'."
                )

        return True

    @classmethod
    def assert_can_investigate(cls, actor: Actor) -> None:
        """Asserts that the actor has permission to conduct an investigation."""
        from .models import Permission
        if not actor.has_permission(Permission.INVESTIGATE):
            raise PermissionDeniedError(f"Actor '{actor.id}' does not have INVESTIGATE permission.")

    @classmethod
    def assert_can_recommend(cls, actor: Actor) -> None:
        """Asserts that the actor has permission to formulate recommendations."""
        from .models import Permission
        if not actor.has_permission(Permission.RECOMMEND):
            raise PermissionDeniedError(f"Actor '{actor.id}' does not have RECOMMEND permission.")

    @classmethod
    def assert_can_approve(cls, actor: Actor) -> None:
        """Asserts that the actor is a human with approval authority."""
        if actor.is_ai:
            raise PermissionDeniedError("AI agents cannot approve recommendations. Human authorization is mandatory.")
        from .models import Permission
        has_any_approval = any(
            actor.has_permission(p) for p in [
                Permission.APPROVE_ROUTINE,
                Permission.APPROVE_MANAGERIAL,
                Permission.APPROVE_EXECUTIVE,
                Permission.APPROVE_STATUTORY
            ]
        )
        if not has_any_approval:
            raise PermissionDeniedError(f"Actor '{actor.id}' ({actor.role}) holds no approval permissions.")

    @classmethod
    def assert_can_execute(cls, actor: Actor) -> None:
        """Asserts that the actor is authorized to dispatch/execute approved interventions."""
        if actor.is_ai:
            raise PermissionDeniedError("AI agents cannot execute operational interventions.")
        from .models import Permission
        if not actor.has_permission(Permission.EXECUTE_ACTION):
            raise PermissionDeniedError(f"Actor '{actor.id}' does not have EXECUTE_ACTION permission.")
