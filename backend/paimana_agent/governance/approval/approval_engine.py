"""Approval Engine managing the formal human approval lifecycle and immutable audit records.

Enforces:
    RECOMMEND  ≠  APPROVE

Converts recommendation candidates into structured approval requests,
runs policy gates, processes human decisions, and mints tamper-evident
HMAC-signed ApprovalRecords.
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
    ApprovalRequest,
    ApprovalDecision,
    ApprovalRecord,
    ApprovalStatus,
    GovernanceError,
    PermissionDeniedError,
    PolicyGateViolationError,
)
from .stage_boundary import StageBoundaryManager
from .policy_gates import PolicyGateEngine

logger = logging.getLogger("paimana_agent.governance.approval_engine")


class ApprovalEngine:
    """Orchestrates human review, policy gate enforcement, and approval record minting."""

    def __init__(self, policy_gates: Optional[PolicyGateEngine] = None):
        self.policy_gates = policy_gates or PolicyGateEngine()
        self.boundary_manager = StageBoundaryManager()

    def create_request_from_recommendation(
        self,
        candidate: Any,
        project: dict[str, Any],
        state: Optional[Any] = None,
        proposer: Optional[Actor] = None
    ) -> ApprovalRequest:
        """Converts an advisory recommendation candidate into a formal ApprovalRequest."""
        # Validate that we are moving from RECOMMEND to APPROVE
        proposer_actor = proposer or Actor(
            id="paimana_ai_recommender",
            name="PAIMANA AI Recommender Engine",
            role=Role.AI_RECOMMENDER
        )

        cost = float(project.get("original_cost_cr", 0.0) or project.get("revised_cost_cr", 0.0))
        is_mega = cost >= 1000.0 or project.get("is_mega_project", False)

        # Extract causal claim attributes if present
        causal_level = "LEVEL_0_OBSERVATION"
        causal_score = 0.0
        if state:
            leading_causal = getattr(state, "leading_causal_claim", None)
            if isinstance(leading_causal, dict):
                causal_level = leading_causal.get("causal_level", "LEVEL_0_OBSERVATION")
                causal_score = float(leading_causal.get("causal_support_score", 0.0))
            elif leading_causal:
                causal_level = getattr(leading_causal, "causal_level", "LEVEL_0_OBSERVATION")
                causal_score = float(getattr(leading_causal, "causal_support_score", 0.0))

        # Estimate intervention monetary cost (approx 5-10% of project cost or candidate expected cost)
        cand_cost_factor = getattr(candidate, "expected_cost", 0.20)
        action_cost_cr = round(cost * (0.02 + 0.05 * cand_cost_factor), 2) if cost > 0 else 5.0

        req_id = f"REQ-APP-{getattr(candidate, 'id', 'CAND')}-{int(time.time()*1000)%100000:05d}"
        
        request = ApprovalRequest(
            request_id=req_id,
            project_code=project.get("project_code", getattr(state, "project_code", "UNKNOWN")),
            candidate_id=getattr(candidate, "id", "CAND-01"),
            action_title=getattr(candidate, "title", getattr(candidate, "action", "Proposed Action")),
            action_type=getattr(candidate, "action_type", getattr(candidate, "candidate_type", "PRIMARY_RECOVERY")),
            approval_class=getattr(candidate, "approval_class", "managerial"),
            urgency=getattr(candidate, "urgency", "MEDIUM"),
            proposed_by=proposer_actor,
            justification=getattr(candidate, "rationale", getattr(candidate, "justification", "")),
            evidence_ids=list(getattr(candidate, "evidence_ids", getattr(candidate, "supporting_evidence", []))),
            hypothesis_ids=list(getattr(candidate, "hypothesis_ids", [])),
            causal_level=causal_level,
            causal_support_score=causal_score,
            cost_cr=action_cost_cr,
            implementation_risk=float(getattr(candidate, "implementation_risk", 0.20)),
            is_mega_project=is_mega,
            status=ApprovalStatus.PENDING,
            metadata={
                "utility_score": getattr(candidate, "utility_score", 0.5),
                "confidence_adjusted_score": getattr(candidate, "confidence_adjusted_score", 0.5),
                "tradeoffs": getattr(candidate, "tradeoffs", ""),
                "responsible_stakeholder": getattr(candidate, "responsible_stakeholder", "PMU"),
            }
        )
        logger.info(f"Created formal ApprovalRequest '{req_id}' for candidate '{request.action_title}'.")
        return request

    def process_decision(
        self,
        request: ApprovalRequest,
        approver: Actor,
        decision: ApprovalStatus,
        justification: str,
        conditions: Optional[list[str]] = None,
        override_policy: bool = False,
        override_justification: str = ""
    ) -> ApprovalRecord:
        """Processes a human decision, enforces gates, and issues an immutable ApprovalRecord."""
        # 1. Stage Boundary Validation: Cannot approve if AI or not in APPROVE stage
        self.boundary_manager.assert_can_approve(approver)
        self.boundary_manager.validate_transition(Stage.RECOMMEND, Stage.APPROVE, actor=approver)

        conditions_list = conditions or []

        # 2. Policy Gate Evaluation (only enforced on approvals; rejections are always permitted)
        if decision in {ApprovalStatus.APPROVED, ApprovalStatus.CONDITIONAL_APPROVAL}:
            gate_results = self.policy_gates.assert_can_approve(
                request=request,
                approver=approver,
                override_policy=override_policy,
                override_justification=override_justification
            )
        else:
            # Rejections or evidence requests don't require passing gates
            _, gate_results, _ = self.policy_gates.evaluate_gates(request=request, approver=approver)

        now = time.time()
        # 3. Cryptographic Signature Token
        sig = ApprovalRecord.compute_signature(
            request_id=request.request_id,
            approver_id=approver.id,
            decision=decision.value,
            timestamp=now
        )

        approval_decision = ApprovalDecision(
            decision=decision,
            approver=approver,
            justification=justification,
            conditions=conditions_list,
            timestamp=now,
            expires_at=now + (30 * 86400)
        )

        rec_id = f"REC-APP-{request.request_id.replace('REQ-APP-', '')}"
        record = ApprovalRecord(
            record_id=rec_id,
            request=request,
            decision=approval_decision,
            gate_evaluations=gate_results,
            signature_token=sig,
            created_at=now
        )

        # Update request status
        request.status = decision
        logger.info(f"Minted ApprovalRecord '{rec_id}' with decision '{decision.value}' by '{approver.name}'.")
        return record

    def escalate(
        self,
        request: ApprovalRequest,
        current_actor: Actor,
        target_role: Role,
        reason: str
    ) -> ApprovalRecord:
        """Escalates request to higher authority tier."""
        self.boundary_manager.assert_can_approve(current_actor)
        request.status = ApprovalStatus.ESCALATED
        now = time.time()
        sig = ApprovalRecord.compute_signature(
            request_id=request.request_id,
            approver_id=current_actor.id,
            decision=ApprovalStatus.ESCALATED.value,
            timestamp=now
        )
        record = ApprovalRecord(
            record_id=f"REC-ESC-{request.request_id.replace('REQ-APP-', '')}",
            request=request,
            decision=ApprovalDecision(
                decision=ApprovalStatus.ESCALATED,
                approver=current_actor,
                justification=f"Escalated to {target_role.value}: {reason}",
                timestamp=now
            ),
            gate_evaluations={"escalated": True},
            signature_token=sig,
            created_at=now
        )
        return record

    def request_additional_evidence(
        self,
        request: ApprovalRequest,
        approver: Actor,
        evidence_gap_query: str
    ) -> ApprovalRecord:
        """Returns request back to INVESTIGATE stage for missing evidence."""
        self.boundary_manager.assert_can_approve(approver)
        request.status = ApprovalStatus.REQUEST_ADDITIONAL_EVIDENCE
        now = time.time()
        sig = ApprovalRecord.compute_signature(
            request_id=request.request_id,
            approver_id=approver.id,
            decision=ApprovalStatus.REQUEST_ADDITIONAL_EVIDENCE.value,
            timestamp=now
        )
        record = ApprovalRecord(
            record_id=f"REC-REV-{request.request_id.replace('REQ-APP-', '')}",
            request=request,
            decision=ApprovalDecision(
                decision=ApprovalStatus.REQUEST_ADDITIONAL_EVIDENCE,
                approver=approver,
                justification=f"Additional evidence required: {evidence_gap_query}",
                timestamp=now
            ),
            gate_evaluations={"evidence_requested": True},
            signature_token=sig,
            created_at=now
        )
        return record
