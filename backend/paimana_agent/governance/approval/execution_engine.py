"""Execution Engine strictly enforcing:
    APPROVE  ≠  EXECUTE
    RECOMMEND  ≠  EXECUTE  (Autonomous execution completely blocked)

Guarantees that operational actions cannot be dispatched without a valid,
unexpired, cryptographically signed ApprovalRecord and human execution role.
"""
from __future__ import annotations
import logging
import time
from typing import Any, Optional
from .models import (
    Actor,
    Role,
    Permission,
    Stage,
    ApprovalStatus,
    ApprovalRecord,
    ExecutionStatus,
    ExecutionRecord,
    UnauthorizedExecutionError,
    PermissionDeniedError,
    StageViolationError
)
from .stage_boundary import StageBoundaryManager

logger = logging.getLogger("paimana_agent.governance.execution_engine")


class ExecutionEngine:
    """Enforces pre-execution invariants and dispatches approved operational interventions."""

    def __init__(self):
        self.boundary_manager = StageBoundaryManager()

    def validate_for_execution(
        self,
        approval_record: ApprovalRecord,
        executor: Actor,
        project_current_state: Optional[dict[str, Any]] = None,
        verified_conditions: Optional[list[str]] = None
    ) -> bool:
        """Validates all prerequisites before an action can be physically dispatched."""
        # 1. Stage Boundary & Actor Validation
        self.boundary_manager.assert_can_execute(executor)
        self.boundary_manager.validate_transition(Stage.APPROVE, Stage.EXECUTE, actor=executor)

        # 2. Approval Record Structural & Cryptographic Validity
        if not isinstance(approval_record, ApprovalRecord):
            raise UnauthorizedExecutionError("Execution requires a valid ApprovalRecord instance.")

        if not approval_record.is_valid():
            raise UnauthorizedExecutionError(
                f"Tampered or Invalid Approval Signature on record '{approval_record.record_id}'. "
                "Execution aborted due to cryptographic mismatch."
            )

        # 3. Decision Status Check
        decision = approval_record.decision.decision
        if decision not in {ApprovalStatus.APPROVED, ApprovalStatus.CONDITIONAL_APPROVAL}:
            raise UnauthorizedExecutionError(
                f"Cannot execute action with approval status '{decision.value}'. "
                "Only 'APPROVED' or 'CONDITIONAL_APPROVAL' actions can be dispatched."
            )

        # 4. Expiration TTL Check
        now = time.time()
        if now > approval_record.decision.expires_at:
            raise UnauthorizedExecutionError(
                f"Approval record '{approval_record.record_id}' has expired. "
                f"Expired at {approval_record.decision.expires_at:.0f}, current time {now:.0f}."
            )

        # 5. Conditional Approval Verification
        if decision == ApprovalStatus.CONDITIONAL_APPROVAL:
            required_conds = approval_record.decision.conditions
            verified = set(verified_conditions or [])
            missing_conds = [c for c in required_conds if c not in verified]
            if missing_conds:
                raise UnauthorizedExecutionError(
                    f"Conditional approval prerequisites not satisfied: {', '.join(missing_conds)}."
                )

        # 6. Safety Circuit Breaker (Project state sanity)
        if project_current_state:
            status = project_current_state.get("status", "").lower()
            if status in ["terminated", "completed", "abandoned"]:
                raise UnauthorizedExecutionError(
                    f"Execution aborted by circuit breaker: Project status is '{status.upper()}', "
                    "no further operational interventions may be deployed."
                )

        return True

    def execute_approved_action(
        self,
        approval_record: ApprovalRecord,
        executor: Actor,
        store: Optional[Any] = None,
        project_current_state: Optional[dict[str, Any]] = None,
        verified_conditions: Optional[list[str]] = None,
        dispatch_channel: str = "PMIS_DIRECT_DISPATCH"
    ) -> ExecutionRecord:
        """Executes an action backed by an authentic ApprovalRecord."""
        # 1. Run all pre-execution checks
        self.validate_for_execution(
            approval_record=approval_record,
            executor=executor,
            project_current_state=project_current_state,
            verified_conditions=verified_conditions
        )

        req = approval_record.request
        now = time.time()
        exec_id = f"EXEC-{req.project_code}-{int(now * 1000) % 1000000:06d}"

        # 2. Record intervention in store if store is provided
        if store:
            try:
                if hasattr(store, "add_intervention"):
                    action_desc = f"{req.action_title} (Approved by {approval_record.decision.approver.name})"
                    store.add_intervention(req.project_code, action_desc)
                elif hasattr(store, "save_project_history"):
                    hist = getattr(store, "get_project_history")(req.project_code) or {"interventions": []}
                    hist.setdefault("interventions", []).append({
                        "action": req.action_title,
                        "approval_record_id": approval_record.record_id,
                        "timestamp": now,
                    })
                    store.save_project_history(req.project_code, hist)
                logger.info(f"Persisted executed intervention to store for project '{req.project_code}'.")
            except Exception as ex:
                logger.warning(f"Could not persist intervention directly into store: {ex}")

        # 3. Mint ExecutionRecord
        record = ExecutionRecord(
            execution_id=exec_id,
            approval_record_id=approval_record.record_id,
            project_code=req.project_code,
            action_title=req.action_title,
            action_type=req.action_type,
            executor=executor,
            dispatch_channel=dispatch_channel,
            execution_status=ExecutionStatus.COMPLETED,
            result_summary=f"Dispatched '{req.action_title}' via {dispatch_channel} with verified approval {approval_record.record_id}.",
            conditions_verified=list(verified_conditions or []),
            executed_at=now
        )
        logger.info(f"Minted ExecutionRecord '{exec_id}' for project '{req.project_code}'.")
        return record

    def reject_unauthorized_execution(self, raw_candidate: Any, actor: Actor) -> None:
        """Explicit boundary assertion: rejects direct attempts to execute raw recommendations."""
        raise UnauthorizedExecutionError(
            f"Autonomous Execution Blocked! Recommendation '{getattr(raw_candidate, 'title', raw_candidate)}' "
            "cannot be dispatched without formal human APPROVE record. RECOMMEND ≠ EXECUTE."
        )
