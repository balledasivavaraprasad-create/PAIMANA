"""Policy Gates Engine for human approval governance.

Enforces pre-approval hard policy gates:
  1. Separation of Duties (Proposer ≠ Approver; AI ≠ Approver)
  2. Role & Approval Class Authority (routine, managerial, executive, statutory)
  3. Causal Support Invariant (Punitive actions strictly require Level 4 Causal Support)
  4. Mega-Project Governance Rules (≥ 1,000 Cr scrutiny and ministry-level clearance)
  5. Financial Authority Limits (Cost cannot exceed approver limit)
  6. Risk Ceiling & Tolerance Limits (Risk cannot exceed clearance without policy override)
"""
from __future__ import annotations
import logging
from typing import Any, Tuple
from .models import (
    Actor,
    Role,
    Permission,
    ApprovalRequest,
    PolicyGateViolationError,
    CausalGateViolationError,
    PermissionDeniedError,
)

logger = logging.getLogger("paimana_agent.governance.policy_gates")


class PolicyGateEngine:
    """Evaluates mandatory policy gates before any approval decision can be enacted."""

    PUNITIVE_KEYWORDS = {
        "liquidated damages",
        "contract termination",
        "forfeit bank guarantee",
        "penalize contractor",
        "blacklisting",
        "freeze escrow",
        "debarment",
    }

    CLASS_PERMISSION_MAP: dict[str, Permission] = {
        "routine": Permission.APPROVE_ROUTINE,
        "managerial": Permission.APPROVE_MANAGERIAL,
        "executive": Permission.APPROVE_EXECUTIVE,
        "statutory": Permission.APPROVE_STATUTORY,
    }

    def evaluate_gates(
        self,
        request: ApprovalRequest,
        approver: Actor,
        override_policy: bool = False,
        override_justification: str = ""
    ) -> Tuple[bool, dict[str, bool], list[str]]:
        """Evaluates all policy gates for an approval request.
        
        Returns:
            (all_passed, gate_results_dict, failure_reasons)
        """
        gate_results: dict[str, bool] = {}
        failure_reasons: list[str] = []

        # --------------------------------------------------------------------
        # Gate 1: Separation of Duties
        # --------------------------------------------------------------------
        # 1A: AI cannot approve
        if approver.is_ai:
            gate_results["separation_of_duties_ai"] = False
            failure_reasons.append("Gate 1 Failed: AI agents cannot approve recommendations. Human approval required.")
        else:
            gate_results["separation_of_duties_ai"] = True

        # 1B: Proposer cannot be the sole approver
        if request.proposed_by.id == approver.id:
            gate_results["separation_of_duties_proposer"] = False
            failure_reasons.append(
                f"Gate 1 Failed: Separation of Duties Violation. Submitter '{request.proposed_by.name}' "
                "cannot self-approve their own recommendation proposal."
            )
        else:
            gate_results["separation_of_duties_proposer"] = True

        # --------------------------------------------------------------------
        # Gate 2: Approval Class & Role Authority
        # --------------------------------------------------------------------
        req_perm = self.CLASS_PERMISSION_MAP.get(request.approval_class.lower(), Permission.APPROVE_ROUTINE)
        if not approver.has_permission(req_perm):
            gate_results["role_authority"] = False
            failure_reasons.append(
                f"Gate 2 Failed: Approver '{approver.name}' ({approver.role}) lacks permission '{req_perm.value}' "
                f"required for '{request.approval_class}' approval class."
            )
        else:
            gate_results["role_authority"] = True

        # --------------------------------------------------------------------
        # Gate 3: Causal Support Invariant (Causal Calibration)
        # --------------------------------------------------------------------
        is_punitive = any(
            kw in request.action_title.lower() or kw in request.justification.lower()
            for kw in self.PUNITIVE_KEYWORDS
        )
        if is_punitive:
            level = str(request.causal_level).upper()
            score = float(request.causal_support_score)
            is_level_4 = ("LEVEL_4" in level) or ("COUNTERFACTUAL" in level) or (score >= 0.60)
            if not is_level_4:
                gate_results["causal_support_calibration"] = False
                failure_reasons.append(
                    f"Gate 3 Failed: Causal Support Invariant Violation. Action '{request.action_title}' is a punitive "
                    f"contractual escalation requiring Level 4 Strong Causal Support. Current evidence only established "
                    f"{request.causal_level} (support_score={score:.2f})."
                )
            else:
                gate_results["causal_support_calibration"] = True
        else:
            gate_results["causal_support_calibration"] = True

        # --------------------------------------------------------------------
        # Gate 4: Mega-Project Governance Gate
        # --------------------------------------------------------------------
        if request.is_mega_project and request.urgency in ["HIGH", "CRITICAL"]:
            is_high_auth = (
                approver.has_permission(Permission.APPROVE_EXECUTIVE) or
                approver.has_permission(Permission.APPROVE_STATUTORY) or
                approver.role in {Role.CHIEF_ENGINEER, Role.MINISTRY_SECRETARY, Role.APEX_COMMITTEE}
            )
            if not is_high_auth:
                gate_results["mega_project_governance"] = False
                failure_reasons.append(
                    "Gate 4 Failed: Mega-project (≥ 1,000 Cr) high-urgency actions must be approved by "
                    "Chief Engineer, Ministry Secretary, or Apex Committee."
                )
            else:
                gate_results["mega_project_governance"] = True
        else:
            gate_results["mega_project_governance"] = True

        # --------------------------------------------------------------------
        # Gate 5: Financial Authority Limits
        # --------------------------------------------------------------------
        if request.cost_cr > approver.max_financial_limit_cr:
            gate_results["financial_authority"] = False
            failure_reasons.append(
                f"Gate 5 Failed: Action financial commitment (₹{request.cost_cr:.2f} Cr) exceeds approver's "
                f"sanctioned threshold (₹{approver.max_financial_limit_cr:.2f} Cr)."
            )
        else:
            gate_results["financial_authority"] = True

        # --------------------------------------------------------------------
        # Gate 6: Risk Tolerance & Implementation Risk Ceiling
        # --------------------------------------------------------------------
        if request.implementation_risk > approver.risk_tolerance_ceiling:
            if override_policy and approver.has_permission(Permission.OVERRIDE_POLICY):
                gate_results["risk_tolerance"] = True
                logger.warning(
                    f"Gate 6 Overridden: Implementation risk ({request.implementation_risk:.2f}) exceeded ceiling "
                    f"({approver.risk_tolerance_ceiling:.2f}), overridden by {approver.name}: '{override_justification}'."
                )
            else:
                gate_results["risk_tolerance"] = False
                failure_reasons.append(
                    f"Gate 6 Failed: Implementation risk ({request.implementation_risk:.2f}) exceeds approver's "
                    f"clearance ceiling ({approver.risk_tolerance_ceiling:.2f})."
                )
        else:
            gate_results["risk_tolerance"] = True

        all_passed = all(gate_results.values())
        return all_passed, gate_results, failure_reasons

    def assert_can_approve(
        self,
        request: ApprovalRequest,
        approver: Actor,
        override_policy: bool = False,
        override_justification: str = ""
    ) -> dict[str, bool]:
        """Asserts that all gates pass, raising specific policy exceptions if violated."""
        passed, gate_results, reasons = self.evaluate_gates(
            request=request,
            approver=approver,
            override_policy=override_policy,
            override_justification=override_justification
        )
        if not passed:
            if not gate_results.get("causal_support_calibration", True):
                raise CausalGateViolationError("; ".join(reasons))
            elif not gate_results.get("separation_of_duties_ai", True) or not gate_results.get("separation_of_duties_proposer", True):
                raise PermissionDeniedError("; ".join(reasons))
            else:
                raise PolicyGateViolationError("; ".join(reasons))
        return gate_results
