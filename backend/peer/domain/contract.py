"""Contract Variation & Milestone Tracking Analyzer (DSI-04).

Tracks contractual Extensions of Time (EOT), scope variations, cost revisions,
and formal liquidated damages / penalty invocations.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .schemas import ConstraintSeverity, ContractAnalysis, EvidenceStatus


class ContractAnalyzer:
    """Evaluates contract modifications, EOTs, scope shifts, and commercial disputes."""

    def analyze(self, project_data: Dict[str, Any]) -> ContractAnalysis:
        findings: List[str] = []

        contract_dict = project_data.get("contract") or {}
        if not isinstance(contract_dict, dict):
            contract_dict = {}

        orig_date = contract_dict.get("original_completion_date") or project_data.get("original_date_of_commissioning") or project_data.get("original_completion_date")
        curr_date = contract_dict.get("current_completion_date") or project_data.get("anticipated_date_of_commissioning") or project_data.get("current_completion_date")

        eot_granted = float(contract_dict.get("eot_granted_months") or project_data.get("eot_granted_months") or 0.0)
        eot_pending = float(contract_dict.get("eot_pending_months") or project_data.get("eot_pending_months") or 0.0)
        eot_count = int(contract_dict.get("eot_count") or project_data.get("eot_count") or (1 if eot_granted > 0 else 0))

        scope_changes = int(contract_dict.get("scope_changes_count") or project_data.get("scope_variations_count") or 0)
        cost_revision = float(contract_dict.get("cost_revision_cr") or project_data.get("cost_variation_cr") or 0.0)

        penalty_invoked = bool(
            contract_dict.get("penalty_invoked")
            or project_data.get("liquidated_damages_invoked")
            or project_data.get("ld_invoked")
            or False
        )

        has_data = any([
            orig_date, curr_date, eot_granted > 0, eot_pending > 0,
            scope_changes > 0, cost_revision > 0, penalty_invoked,
        ])

        if not has_data:
            return ContractAnalysis(
                is_contractual_risk=False,
                risk_severity=ConstraintSeverity.UNKNOWN,
                findings=["No contract administration, EOT, or variation records available."],
                evidence_status=EvidenceStatus.UNVERIFIED_GAP,
            )

        # Severity Assessment
        severity = ConstraintSeverity.NEGLIGIBLE
        is_risk = False

        if penalty_invoked:
            severity = ConstraintSeverity.CRITICAL
            is_risk = True
            findings.append("Liquidated damages / contractual penalties have been formally invoked against the contractor.")

        if eot_pending > 6.0:
            if severity != ConstraintSeverity.CRITICAL:
                severity = ConstraintSeverity.HIGH
            is_risk = True
            findings.append(f"Unresolved contractual claims: {eot_pending:.1f} months of EOT applications pending formal determination.")
        elif eot_pending > 0.0:
            if severity == ConstraintSeverity.NEGLIGIBLE:
                severity = ConstraintSeverity.MODERATE
            findings.append(f"{eot_pending:.1f} months of Extension of Time pending decision.")

        if eot_granted > 12.0:
            if severity not in (ConstraintSeverity.CRITICAL, ConstraintSeverity.HIGH):
                severity = ConstraintSeverity.HIGH
            is_risk = True
            findings.append(f"Extensive formal EOT granted: {eot_granted:.1f} months across {eot_count} revision(s).")
        elif eot_granted > 0.0:
            findings.append(f"{eot_granted:.1f} months EOT granted to date.")

        if scope_changes > 2 or cost_revision > 50.0:
            if severity == ConstraintSeverity.NEGLIGIBLE:
                severity = ConstraintSeverity.MODERATE
            is_risk = True
            findings.append(f"Significant scope variations: {scope_changes} variation orders resulting in ₹{cost_revision:.2f} Cr cost revision.")

        return ContractAnalysis(
            original_completion_date=str(orig_date) if orig_date else None,
            current_completion_date=str(curr_date) if curr_date else None,
            eot_granted_months=eot_granted,
            eot_pending_months=eot_pending,
            eot_count=eot_count,
            scope_changes_count=scope_changes,
            cost_revision_cr=cost_revision,
            penalty_liquidated_damages_invoked=penalty_invoked,
            is_contractual_risk=is_risk,
            risk_severity=severity,
            findings=findings,
            evidence_status=EvidenceStatus.VERIFIED if (orig_date and curr_date) else EvidenceStatus.INFERRED,
        )
