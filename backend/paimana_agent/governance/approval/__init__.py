"""Human Approval and Governance Lockdown Subpackage.

Enforces:
    INVESTIGATE  ≠  RECOMMEND  ≠  APPROVE  ≠  EXECUTE

With real permissions, approval requirements, policy gates, and audit records.
"""
from .models import (
    Stage,
    Role,
    Permission,
    Actor,
    ApprovalStatus,
    ExecutionStatus,
    ApprovalRequest,
    ApprovalDecision,
    ApprovalRecord,
    ExecutionRecord,
    GovernanceError,
    StageViolationError,
    PermissionDeniedError,
    PolicyGateViolationError,
    CausalGateViolationError,
    UnauthorizedExecutionError,
    DEFAULT_ROLE_PERMISSIONS,
)
from .stage_boundary import StageBoundaryManager
from .policy_gates import PolicyGateEngine
from .approval_engine import ApprovalEngine
from .execution_engine import ExecutionEngine
from .audit_ledger import GovernanceAuditLedger, AuditTrailEntry

__all__ = [
    "Stage",
    "Role",
    "Permission",
    "Actor",
    "ApprovalStatus",
    "ExecutionStatus",
    "ApprovalRequest",
    "ApprovalDecision",
    "ApprovalRecord",
    "ExecutionRecord",
    "GovernanceError",
    "StageViolationError",
    "PermissionDeniedError",
    "PolicyGateViolationError",
    "CausalGateViolationError",
    "UnauthorizedExecutionError",
    "DEFAULT_ROLE_PERMISSIONS",
    "StageBoundaryManager",
    "PolicyGateEngine",
    "ApprovalEngine",
    "ExecutionEngine",
    "GovernanceAuditLedger",
    "AuditTrailEntry",
]
