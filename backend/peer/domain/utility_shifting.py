"""Utility Shifting & Right-of-Way Obstruction Analyzer (DSI-07).

Tracks electrical, water, gas, and telecom utility relocation stages
and evaluates physical workfront blockages resulting from pending shifting.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .schemas import (
    ConstraintSeverity,
    EvidenceStatus,
    UtilityShiftingAnalysis,
    UtilityShiftingItem,
    UtilityStage,
    UtilityType,
)


def parse_utility_type(raw: str) -> UtilityType:
    r = raw.upper()
    if "HT" in r or "EHT" in r or "TRANSMISSION" in r or "TOWER" in r:
        return UtilityType.ELECTRICAL_HT_EHT
    if "ELECTR" in r or "POLE" in r or "LT" in r:
        return UtilityType.ELECTRICAL_LT_DISTRIBUTION
    if "WATER" in r or "PIPELINE" in r:
        return UtilityType.WATER_SUPPLY_PIPELINE
    if "SEWER" in r or "DRAIN" in r:
        return UtilityType.SEWERAGE_LINE
    if "GAS" in r:
        return UtilityType.GAS_PIPELINE
    if "TELECOM" in r or "OFC" in r or "FIBER" in r or "CABLE" in r:
        return UtilityType.TELECOM_OFC
    return UtilityType.OTHER


def parse_utility_stage(raw: str) -> UtilityStage:
    r = raw.upper()
    if "COMPLETED" in r or "SHIFTED" in r or "CLEARED" in r or "DONE" in r:
        return UtilityStage.SHIFTING_COMPLETED
    if "PROGRESS" in r or "ONGOING" in r or "SHIFTING" in r:
        return UtilityStage.SHIFTING_IN_PROGRESS
    if "AWARDED" in r or "CONTRACTOR" in r:
        return UtilityStage.AGENCY_AWARDED
    if "SUPERVISION" in r or "PAID" in r or "DEPOSIT" in r:
        return UtilityStage.SUPERVISION_PAID
    if "SANCTIONED" in r or "APPROVED" in r:
        return UtilityStage.ESTIMATE_SANCTIONED
    if "ESTIMATE" in r:
        return UtilityStage.ESTIMATE_PREPARED
    if "IDENTIFIED" in r or "SURVEY" in r:
        return UtilityStage.IDENTIFIED
    return UtilityStage.UNKNOWN


class UtilityShiftingAnalyzer:
    """Evaluates utility relocation lifecycle and workfront obstructions."""

    def analyze(self, project_data: Dict[str, Any]) -> UtilityShiftingAnalysis:
        findings: List[str] = []
        utility_items: List[UtilityShiftingItem] = []

        raw_utilities = (
            project_data.get("utilities")
            or project_data.get("utility_shifting")
            or project_data.get("utilities_to_shift")
            or []
        )

        if isinstance(raw_utilities, list) and raw_utilities:
            for item in raw_utilities:
                if isinstance(item, dict):
                    u_type = parse_utility_type(item.get("type") or item.get("utility_type") or "")
                    ident = str(item.get("identifier") or item.get("id") or item.get("description") or u_type.value)
                    stage = parse_utility_stage(item.get("stage") or item.get("status") or "")
                    est = item.get("estimate_cr")
                    est_f = float(est) if est is not None else None
                    dep_paid = bool(item.get("deposit_paid") or stage in (
                        UtilityStage.SUPERVISION_PAID,
                        UtilityStage.AGENCY_AWARDED,
                        UtilityStage.SHIFTING_IN_PROGRESS,
                        UtilityStage.SHIFTING_COMPLETED,
                    ))
                    blocks = bool(item.get("blocks_workfront") or item.get("critical", False))

                    utility_items.append(
                        UtilityShiftingItem(
                            utility_type=u_type,
                            identifier=ident,
                            location=str(item.get("location") or ""),
                            stage=stage,
                            estimate_cr=est_f,
                            deposit_paid=dep_paid,
                            blocks_workfront=blocks,
                            agency=str(item.get("agency") or ""),
                            remarks=str(item.get("remarks") or ""),
                        )
                    )

        # Also inspect summary numbers if list not present
        total_count = len(utility_items)
        if total_count == 0:
            total_sum = project_data.get("total_utilities_count") or project_data.get("utilities_count")
            comp_sum = project_data.get("shifted_utilities_count") or project_data.get("utilities_completed_count")
            if total_sum is not None:
                try:
                    tot_i = int(total_sum)
                    comp_i = int(comp_sum or 0)
                    total_count = tot_i
                    completed_count = comp_i
                    pending_count = max(0, tot_i - comp_i)
                    blocks_count = int(project_data.get("utilities_blocking_count") or 0)
                    pct = (comp_i / tot_i * 100.0) if tot_i > 0 else 0.0

                    severity = ConstraintSeverity.NEGLIGIBLE
                    is_bottleneck = False
                    if blocks_count > 0:
                        severity = ConstraintSeverity.CRITICAL
                        is_bottleneck = True
                        findings.append(f"{blocks_count} utility lines actively obstructing execution workfronts.")
                    elif pending_count > 10:
                        severity = ConstraintSeverity.HIGH
                        is_bottleneck = True
                        findings.append(f"Substantial utility backlog: {pending_count} of {tot_i} utilities pending shifting.")
                    elif pending_count > 0:
                        severity = ConstraintSeverity.MODERATE
                        findings.append(f"{pending_count} utilities pending relocation.")
                    else:
                        findings.append(f"All {tot_i} identified utilities successfully shifted.")

                    return UtilityShiftingAnalysis(
                        utilities=[],
                        total_utilities=tot_i,
                        completed_count=comp_i,
                        pending_count=pending_count,
                        blocking_workfront_count=blocks_count,
                        completion_pct=pct,
                        deposit_paid_pct=100.0 if comp_i > 0 else 0.0,
                        is_utility_bottleneck=is_bottleneck,
                        bottleneck_severity=severity,
                        findings=findings,
                        evidence_status=EvidenceStatus.INFERRED,
                    )
                except (ValueError, TypeError):
                    pass

        if total_count == 0:
            return UtilityShiftingAnalysis(
                utilities=[],
                total_utilities=0,
                completed_count=0,
                pending_count=0,
                blocking_workfront_count=0,
                completion_pct=0.0,
                deposit_paid_pct=0.0,
                is_utility_bottleneck=False,
                bottleneck_severity=ConstraintSeverity.UNKNOWN,
                findings=["No utility shifting or encumbrance records available in project documentation."],
                evidence_status=EvidenceStatus.UNVERIFIED_GAP,
            )

        completed_count = sum(1 for u in utility_items if u.stage == UtilityStage.SHIFTING_COMPLETED)
        pending_count = total_count - completed_count
        blocking_count = sum(1 for u in utility_items if u.blocks_workfront and u.stage != UtilityStage.SHIFTING_COMPLETED)
        deposit_paid_count = sum(1 for u in utility_items if u.deposit_paid)

        comp_pct = (completed_count / total_count * 100.0) if total_count > 0 else 0.0
        dep_pct = (deposit_paid_count / total_count * 100.0) if total_count > 0 else 0.0

        # Severity Assessment
        severity = ConstraintSeverity.NEGLIGIBLE
        is_bottleneck = False

        if blocking_count > 0:
            severity = ConstraintSeverity.CRITICAL
            is_bottleneck = True
            findings.append(f"{blocking_count} utility obstruction(s) blocking critical workfronts.")
        elif comp_pct < 50.0 and total_count > 5:
            severity = ConstraintSeverity.HIGH
            is_bottleneck = True
            findings.append(f"Low utility shifting progress: only {comp_pct:.1f}% shifted ({pending_count} pending).")
        elif pending_count > 0:
            severity = ConstraintSeverity.MODERATE
            findings.append(f"{pending_count} of {total_count} utilities pending completion.")
        else:
            findings.append(f"All {total_count} utilities successfully shifted.")

        if dep_pct < 100.0 and pending_count > 0:
            unpaid = pending_count - (deposit_paid_count - completed_count)
            if unpaid > 0:
                findings.append(f"Supervision charges / shifting deposits unpaid for {unpaid} pending utilities.")

        return UtilityShiftingAnalysis(
            utilities=utility_items,
            total_utilities=total_count,
            completed_count=completed_count,
            pending_count=pending_count,
            blocking_workfront_count=blocking_count,
            completion_pct=comp_pct,
            deposit_paid_pct=dep_pct,
            is_utility_bottleneck=is_bottleneck,
            bottleneck_severity=severity,
            findings=findings,
            evidence_status=EvidenceStatus.VERIFIED,
        )
