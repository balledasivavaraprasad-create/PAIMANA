"""First-class Governance and Human Approval Data Models for PAIMANA Agentic Layer.

Enforces strict separation of duties across the four canonical operational stages:
    INVESTIGATE  ≠  RECOMMEND  ≠  APPROVE  ≠  EXECUTE

Captures roles, permissions, approval requests, immutable approval records with
cryptographic HMAC signatures, policy gate evaluations, and execution records.
"""
from __future__ import annotations
import enum
import hashlib
import hmac
import time
from dataclasses import dataclass, field
from typing import Any, Optional


# ----------------------------------------------------------------------------
# 1. Operational Stages
# ----------------------------------------------------------------------------
class Stage(str, enum.Enum):
    """The four strictly decoupled operational stages."""
    INVESTIGATE = "INVESTIGATE"
    RECOMMEND = "RECOMMEND"
    APPROVE = "APPROVE"
    EXECUTE = "EXECUTE"


# ----------------------------------------------------------------------------
# 2. Roles & Permissions
# ----------------------------------------------------------------------------
class Role(str, enum.Enum):
    """Institutional stakeholders and system agent roles."""
    # Institutional Human Roles
    FIELD_ENGINEER = "FIELD_ENGINEER"
    PROJECT_DIRECTOR = "PROJECT_DIRECTOR"
    SUPERINTENDING_ENGINEER = "SUPERINTENDING_ENGINEER"
    CHIEF_ENGINEER = "CHIEF_ENGINEER"
    MINISTRY_SECRETARY = "MINISTRY_SECRETARY"
    APEX_COMMITTEE = "APEX_COMMITTEE"

    # AI Agentic System Roles (Explicitly restricted from approving or executing)
    AI_INVESTIGATOR = "AI_INVESTIGATOR"
    AI_RECOMMENDER = "AI_RECOMMENDER"


class Permission(str, enum.Enum):
    """Fine-grained operational permissions."""
    INVESTIGATE = "INVESTIGATE"
    RECOMMEND = "RECOMMEND"
    APPROVE_ROUTINE = "APPROVE_ROUTINE"
    APPROVE_MANAGERIAL = "APPROVE_MANAGERIAL"
    APPROVE_EXECUTIVE = "APPROVE_EXECUTIVE"
    APPROVE_STATUTORY = "APPROVE_STATUTORY"
    EXECUTE_ACTION = "EXECUTE_ACTION"
    OVERRIDE_POLICY = "OVERRIDE_POLICY"


# Default role-to-permission mappings
DEFAULT_ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.AI_INVESTIGATOR: {Permission.INVESTIGATE},
    Role.AI_RECOMMENDER: {Permission.RECOMMEND},
    Role.FIELD_ENGINEER: {
        Permission.INVESTIGATE,
        Permission.APPROVE_ROUTINE,
        Permission.EXECUTE_ACTION
    },
    Role.PROJECT_DIRECTOR: {
        Permission.INVESTIGATE,
        Permission.RECOMMEND,
        Permission.APPROVE_ROUTINE,
        Permission.APPROVE_MANAGERIAL,
        Permission.EXECUTE_ACTION
    },
    Role.SUPERINTENDING_ENGINEER: {
        Permission.INVESTIGATE,
        Permission.APPROVE_ROUTINE,
        Permission.APPROVE_MANAGERIAL,
        Permission.EXECUTE_ACTION
    },
    Role.CHIEF_ENGINEER: {
        Permission.APPROVE_ROUTINE,
        Permission.APPROVE_MANAGERIAL,
        Permission.APPROVE_EXECUTIVE,
        Permission.EXECUTE_ACTION
    },
    Role.MINISTRY_SECRETARY: {
        Permission.APPROVE_ROUTINE,
        Permission.APPROVE_MANAGERIAL,
        Permission.APPROVE_EXECUTIVE,
        Permission.APPROVE_STATUTORY,
        Permission.EXECUTE_ACTION,
        Permission.OVERRIDE_POLICY
    },
    Role.APEX_COMMITTEE: {
        Permission.APPROVE_ROUTINE,
        Permission.APPROVE_MANAGERIAL,
        Permission.APPROVE_EXECUTIVE,
        Permission.APPROVE_STATUTORY,
        Permission.EXECUTE_ACTION,
        Permission.OVERRIDE_POLICY
    },
}


@dataclass
class Actor:
    """An authorized human or system actor."""
    id: str
    name: str
    role: Role
    department: str = "Infrastructure Monitoring Division"
    max_financial_limit_cr: float = 50.0  # Max project/action financial authority
    risk_tolerance_ceiling: float = 0.50  # Max implementation risk they can approve
    permissions: set[Permission] = field(default_factory=set)

    def __post_init__(self):
        if not self.permissions and self.role in DEFAULT_ROLE_PERMISSIONS:
            self.permissions = set(DEFAULT_ROLE_PERMISSIONS[self.role])

    @property
    def is_ai(self) -> bool:
        return self.role in {Role.AI_INVESTIGATOR, Role.AI_RECOMMENDER}

    def has_permission(self, permission: Permission) -> bool:
        return permission in self.permissions

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role.value if isinstance(self.role, Role) else str(self.role),
            "department": self.department,
            "max_financial_limit_cr": self.max_financial_limit_cr,
            "risk_tolerance_ceiling": self.risk_tolerance_ceiling,
            "permissions": [p.value for p in self.permissions],
            "is_ai": self.is_ai,
        }


# ----------------------------------------------------------------------------
# 3. Status Enums
# ----------------------------------------------------------------------------
class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CONDITIONAL_APPROVAL = "CONDITIONAL_APPROVAL"
    ESCALATED = "ESCALATED"
    REQUEST_ADDITIONAL_EVIDENCE = "REQUEST_ADDITIONAL_EVIDENCE"


class ExecutionStatus(str, enum.Enum):
    PENDING = "PENDING"
    DISPATCHED = "DISPATCHED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    BLOCKED = "BLOCKED"


# ----------------------------------------------------------------------------
# 4. Request, Approval, and Execution Entities
# ----------------------------------------------------------------------------
@dataclass
class ApprovalRequest:
    """Formal request submitted to human governance for review and sign-off."""
    request_id: str
    project_code: str
    candidate_id: str
    action_title: str
    action_type: str
    approval_class: str             # routine, managerial, executive, statutory
    urgency: str                    # LOW, MEDIUM, HIGH, CRITICAL
    proposed_by: Actor
    
    # Context & Evidence
    justification: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    hypothesis_ids: list[str] = field(default_factory=list)
    causal_level: str = "LEVEL_0_OBSERVATION"
    causal_support_score: float = 0.0
    
    # Financial & Risk Parameters
    cost_cr: float = 0.0
    implementation_risk: float = 0.20
    is_mega_project: bool = False
    
    # Operational Lifecycle
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "project_code": self.project_code,
            "candidate_id": self.candidate_id,
            "action_title": self.action_title,
            "action_type": self.action_type,
            "approval_class": self.approval_class,
            "urgency": self.urgency,
            "proposed_by": self.proposed_by.to_dict(),
            "justification": self.justification,
            "evidence_ids": list(self.evidence_ids),
            "hypothesis_ids": list(self.hypothesis_ids),
            "causal_level": self.causal_level,
            "causal_support_score": round(self.causal_support_score, 3),
            "cost_cr": self.cost_cr,
            "implementation_risk": round(self.implementation_risk, 3),
            "is_mega_project": self.is_mega_project,
            "status": self.status.value,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


@dataclass
class ApprovalDecision:
    """Evaluated decision returned by the human approver."""
    decision: ApprovalStatus
    approver: Actor
    justification: str
    conditions: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + (30 * 86400))  # 30-day default TTL

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "approver": self.approver.to_dict(),
            "justification": self.justification,
            "conditions": list(self.conditions),
            "timestamp": self.timestamp,
            "expires_at": self.expires_at,
        }


@dataclass
class ApprovalRecord:
    """Immutable audit record linking request, policy gate evaluation, and decision."""
    record_id: str
    request: ApprovalRequest
    decision: ApprovalDecision
    gate_evaluations: dict[str, bool]
    signature_token: str
    created_at: float = field(default_factory=time.time)

    def is_valid(self) -> bool:
        """Verifies cryptographic signature token against content."""
        expected = self.compute_signature(
            request_id=self.request.request_id,
            approver_id=self.decision.approver.id,
            decision=self.decision.decision.value,
            timestamp=self.decision.timestamp
        )
        return hmac.compare_digest(self.signature_token, expected)

    @classmethod
    def compute_signature(cls, request_id: str, approver_id: str, decision: str, timestamp: float) -> str:
        secret = b"PAIMANA_GOVERNANCE_SECRET_KEY_V4"
        payload = f"{request_id}:{approver_id}:{decision}:{timestamp:.2f}".encode("utf-8")
        return hmac.new(secret, payload, hashlib.sha256).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "request": self.request.to_dict(),
            "decision": self.decision.to_dict(),
            "gate_evaluations": self.gate_evaluations,
            "signature_token": self.signature_token,
            "is_valid": self.is_valid(),
            "created_at": self.created_at,
        }


@dataclass
class ExecutionRecord:
    """Immutable audit record logging the dispatch and completion of an approved action."""
    execution_id: str
    approval_record_id: str
    project_code: str
    action_title: str
    action_type: str
    executor: Actor
    dispatch_channel: str
    execution_status: ExecutionStatus
    result_summary: str = ""
    conditions_verified: list[str] = field(default_factory=list)
    audit_hash: str = ""
    executed_at: float = field(default_factory=time.time)

    def __post_init__(self):
        if not self.audit_hash:
            payload = f"{self.execution_id}:{self.approval_record_id}:{self.project_code}:{self.executor.id}:{self.executed_at}".encode("utf-8")
            self.audit_hash = hashlib.sha256(payload).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "approval_record_id": self.approval_record_id,
            "project_code": self.project_code,
            "action_title": self.action_title,
            "action_type": self.action_type,
            "executor": self.executor.to_dict(),
            "dispatch_channel": self.dispatch_channel,
            "execution_status": self.execution_status.value,
            "result_summary": self.result_summary,
            "conditions_verified": list(self.conditions_verified),
            "audit_hash": self.audit_hash,
            "executed_at": self.executed_at,
        }


# ----------------------------------------------------------------------------
# 5. Governance Exceptions
# ----------------------------------------------------------------------------
class GovernanceError(Exception):
    """Base exception for all governance and approval violations."""
    pass


class StageViolationError(GovernanceError):
    """Raised when an operation attempts to bypass or violate lifecycle boundaries."""
    pass


class PermissionDeniedError(GovernanceError):
    """Raised when an actor attempts an action outside their role or clearance."""
    pass


class PolicyGateViolationError(GovernanceError):
    """Raised when an approval request fails mandatory policy gates."""
    pass


class CausalGateViolationError(PolicyGateViolationError):
    """Raised when punitive contractual escalation lacks required Level 4 Causal Support."""
    pass


class UnauthorizedExecutionError(GovernanceError):
    """Raised when an action is dispatched without prior valid human approval."""
    pass
