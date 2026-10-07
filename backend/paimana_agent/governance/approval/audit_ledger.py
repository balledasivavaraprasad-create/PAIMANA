"""Governance Audit Ledger maintaining immutable, cryptographically chained audit trails.

Links:
    INVESTIGATE (InvestigationState / Report)
         ↓
    RECOMMEND (RecommendationCandidate / Decision)
         ↓
    APPROVE (ApprovalRequest / ApprovalRecord)
         ↓
    EXECUTE (ExecutionRecord)

Provides tamper-evident verification across all institutional decisions.
"""
from __future__ import annotations
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional
from .models import (
    ApprovalRequest,
    ApprovalRecord,
    ExecutionRecord,
    Stage,
)

logger = logging.getLogger("paimana_agent.governance.audit_ledger")


@dataclass
class AuditTrailEntry:
    """An individual linked node in the governance audit ledger."""
    entry_id: str
    project_code: str
    stage: Stage
    actor_id: str
    actor_role: str
    action_type: str
    action_details: dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    previous_hash: str = "GENESIS_BLOCK"
    entry_hash: str = ""

    def __post_init__(self):
        if not self.entry_hash:
            self.entry_hash = self.compute_hash()

    def compute_hash(self) -> str:
        payload = (
            f"{self.entry_id}:{self.project_code}:{self.stage.value}:{self.actor_id}:"
            f"{self.actor_role}:{self.action_type}:{json.dumps(self.action_details, sort_keys=True)}:"
            f"{self.timestamp:.3f}:{self.previous_hash}"
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "project_code": self.project_code,
            "stage": self.stage.value,
            "actor_id": self.actor_id,
            "actor_role": self.actor_role,
            "action_type": self.action_type,
            "action_details": self.action_details,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash,
        }


class GovernanceAuditLedger:
    """In-memory and persistent cryptographic audit ledger for institutional oversight."""

    def __init__(self):
        self._entries: list[AuditTrailEntry] = []
        self._project_index: dict[str, list[AuditTrailEntry]] = {}

    def append_investigation(
        self,
        project_code: str,
        investigator_id: str,
        investigator_role: str,
        findings_summary: dict[str, Any]
    ) -> AuditTrailEntry:
        """Records an INVESTIGATE stage milestone."""
        return self._append_entry(
            project_code=project_code,
            stage=Stage.INVESTIGATE,
            actor_id=investigator_id,
            actor_role=investigator_role,
            action_type="INVESTIGATION_COMPLETED",
            action_details=findings_summary
        )

    def append_recommendation(
        self,
        project_code: str,
        recommender_id: str,
        recommender_role: str,
        recommendation_decision: dict[str, Any]
    ) -> AuditTrailEntry:
        """Records a RECOMMEND stage milestone."""
        return self._append_entry(
            project_code=project_code,
            stage=Stage.RECOMMEND,
            actor_id=recommender_id,
            actor_role=recommender_role,
            action_type="RECOMMENDATION_FORMULATED",
            action_details=recommendation_decision
        )

    def append_approval(
        self,
        approval_record: ApprovalRecord
    ) -> AuditTrailEntry:
        """Records an APPROVE stage milestone."""
        return self._append_entry(
            project_code=approval_record.request.project_code,
            stage=Stage.APPROVE,
            actor_id=approval_record.decision.approver.id,
            actor_role=approval_record.decision.approver.role.value if hasattr(approval_record.decision.approver.role, "value") else str(approval_record.decision.approver.role),
            action_type=f"APPROVAL_{approval_record.decision.decision.value}",
            action_details={
                "record_id": approval_record.record_id,
                "request_id": approval_record.request.request_id,
                "candidate_id": approval_record.request.candidate_id,
                "decision": approval_record.decision.decision.value,
                "signature_token": approval_record.signature_token,
                "gate_evaluations": approval_record.gate_evaluations,
            }
        )

    def append_execution(
        self,
        execution_record: ExecutionRecord
    ) -> AuditTrailEntry:
        """Records an EXECUTE stage milestone."""
        return self._append_entry(
            project_code=execution_record.project_code,
            stage=Stage.EXECUTE,
            actor_id=execution_record.executor.id,
            actor_role=execution_record.executor.role.value if hasattr(execution_record.executor.role, "value") else str(execution_record.executor.role),
            action_type="ACTION_EXECUTED",
            action_details={
                "execution_id": execution_record.execution_id,
                "approval_record_id": execution_record.approval_record_id,
                "action_title": execution_record.action_title,
                "dispatch_channel": execution_record.dispatch_channel,
                "execution_status": execution_record.execution_status.value,
                "audit_hash": execution_record.audit_hash,
            }
        )

    def _append_entry(
        self,
        project_code: str,
        stage: Stage,
        actor_id: str,
        actor_role: str,
        action_type: str,
        action_details: dict[str, Any]
    ) -> AuditTrailEntry:
        prev_hash = self._entries[-1].entry_hash if self._entries else "GENESIS_BLOCK"
        entry_id = f"AUD-{len(self._entries)+1:06d}"
        
        entry = AuditTrailEntry(
            entry_id=entry_id,
            project_code=project_code,
            stage=stage,
            actor_id=actor_id,
            actor_role=actor_role,
            action_type=action_type,
            action_details=action_details,
            previous_hash=prev_hash
        )
        self._entries.append(entry)
        self._project_index.setdefault(project_code, []).append(entry)
        return entry

    def verify_ledger_integrity(self) -> bool:
        """Verifies the unbroken cryptographic chain across all ledger entries."""
        for i, entry in enumerate(self._entries):
            expected_prev = self._entries[i-1].entry_hash if i > 0 else "GENESIS_BLOCK"
            if entry.previous_hash != expected_prev:
                logger.error(f"Ledger Tampering Detected at entry {entry.entry_id}: previous_hash mismatch.")
                return False
            if entry.entry_hash != entry.compute_hash():
                logger.error(f"Ledger Tampering Detected at entry {entry.entry_id}: entry_hash mismatch.")
                return False
        return True

    def get_project_trail(self, project_code: str) -> list[AuditTrailEntry]:
        """Returns the chronological audit trail for a specific project."""
        return list(self._project_index.get(project_code, []))

    def export_full_trace(self, project_code: str) -> dict[str, Any]:
        """Exports an auditable trace dictionary for reporting and dashboards."""
        trail = self.get_project_trail(project_code)
        stages_covered = {e.stage.value for e in trail}
        return {
            "project_code": project_code,
            "total_audit_entries": len(trail),
            "stages_covered": list(stages_covered),
            "ledger_verified": self.verify_ledger_integrity(),
            "timeline": [e.to_dict() for e in trail],
        }
