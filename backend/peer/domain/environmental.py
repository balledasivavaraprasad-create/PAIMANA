"""Environmental, Forest & Statutory Clearance Analyzer (DSI-06).

Tracks regulatory clearance lifecycles (EC, Forest Stage-I/II, Wildlife, CRZ, Tree Felling)
and evaluates workfront blockages resulting from pending approvals.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .schemas import (
    ClearanceItem,
    ClearanceStatus,
    ClearanceType,
    ConstraintSeverity,
    EnvironmentalClearanceAnalysis,
    EvidenceStatus,
)


def parse_clearance_type(raw: str) -> ClearanceType:
    r = raw.upper()
    if "FOREST" in r:
        if "STAGE II" in r or "STAGE 2" in r or "FINAL" in r:
            return ClearanceType.FOREST_STAGE_2
        return ClearanceType.FOREST_STAGE_1
    if "WILDLIFE" in r or "NBWL" in r:
        return ClearanceType.WILDLIFE
    if "CRZ" in r or "COASTAL" in r:
        return ClearanceType.COASTAL_REGULATION_ZONE
    if "TREE" in r:
        return ClearanceType.TREE_FELLING
    if "RAILWAY" in r or "CRS" in r or "GAD" in r:
        return ClearanceType.RAILWAY_SAFETY
    if "DEFENSE" in r or "MOD" in r:
        return ClearanceType.DEFENSE
    if "ARCHAEOLOGICAL" in r or "ASI" in r:
        return ClearanceType.ARCHAEOLOGICAL
    if "WATER" in r or "CANAL" in r or "RIVER" in r:
        return ClearanceType.WATER_BODIES
    if "ENVIRONMENT" in r or "EC" in r:
        return ClearanceType.ENVIRONMENTAL
    return ClearanceType.OTHER


def parse_clearance_status(raw: str) -> ClearanceStatus:
    r = raw.upper().replace("_", " ").replace("-", " ")
    if "REJECTED" in r:
        return ClearanceStatus.REJECTED
    if "EXEMPTED" in r:
        return ClearanceStatus.EXEMPTED
    if "STAGE 1" in r or "STAGE I" in r or "IN PRINCIPLE" in r:
        return ClearanceStatus.IN_PRINCIPLE_APPROVED
    if "COMPLIANCE" in r:
        return ClearanceStatus.PENDING_COMPLIANCE
    if "FINAL" in r or "APPROVED" in r or "GRANTED" in r or "CLEARED" in r:
        return ClearanceStatus.FINAL_APPROVED
    if "SUBMITTED" in r or "PENDING" in r or "UNDER PROCESS" in r or "APPLIED" in r:
        return ClearanceStatus.SUBMITTED
    if "NOT APPLIED" in r:
        return ClearanceStatus.NOT_APPLIED
    return ClearanceStatus.UNKNOWN


class EnvironmentalClearanceAnalyzer:
    """Evaluates statutory clearance compliance and identifies approval bottlenecks."""

    def analyze(self, project_data: Dict[str, Any]) -> EnvironmentalClearanceAnalysis:
        findings: List[str] = []
        clearance_items: List[ClearanceItem] = []

        raw_clearances = (
            project_data.get("clearances")
            or project_data.get("statutory_clearances")
            or project_data.get("environmental_clearances")
            or []
        )

        forest_diverted_ha = float(project_data.get("forest_land_ha") or 0.0)
        tree_felling_pending = int(project_data.get("pending_tree_felling_count") or 0)

        if isinstance(raw_clearances, list) and raw_clearances:
            for item in raw_clearances:
                if isinstance(item, dict):
                    c_type = parse_clearance_type(item.get("type") or item.get("clearance_type") or "")
                    c_name = str(item.get("name") or c_type.value)
                    c_status = parse_clearance_status(item.get("status") or "")
                    c_crit = bool(item.get("critical_path") or item.get("is_critical", False))
                    p_days = item.get("pending_days")
                    try:
                        p_days_int = int(p_days) if p_days is not None else None
                    except (ValueError, TypeError):
                        p_days_int = None

                    clearance_items.append(
                        ClearanceItem(
                            clearance_type=c_type,
                            name=c_name,
                            status=c_status,
                            applied_date=item.get("applied_date"),
                            approval_date=item.get("approval_date"),
                            pending_days=p_days_int,
                            critical_path=c_crit,
                            affected_stretch=item.get("affected_stretch"),
                            affected_cost_cr=item.get("affected_cost_cr"),
                            remarks=item.get("remarks", ""),
                        )
                    )

        # Also inspect top-level clearance fields if not captured in list
        if not clearance_items:
            for c_field, c_type in [
                ("environmental_clearance", ClearanceType.ENVIRONMENTAL),
                ("forest_clearance", ClearanceType.FOREST_STAGE_1),
                ("wildlife_clearance", ClearanceType.WILDLIFE),
                ("crz_clearance", ClearanceType.COASTAL_REGULATION_ZONE),
            ]:
                if c_field in project_data:
                    val = str(project_data[c_field])
                    status = parse_clearance_status(val)
                    clearance_items.append(
                        ClearanceItem(
                            clearance_type=c_type,
                            name=c_field.replace("_", " ").title(),
                            status=status,
                            critical_path=True,
                            remarks=val,
                        )
                    )

        if not clearance_items and forest_diverted_ha == 0.0 and tree_felling_pending == 0:
            return EnvironmentalClearanceAnalysis(
                clearances=[],
                total_clearances_required=0,
                approved_count=0,
                pending_count=0,
                pending_critical_count=0,
                forest_land_diverted_ha=0.0,
                tree_felling_pending_count=0,
                is_clearance_bottleneck=False,
                bottleneck_severity=ConstraintSeverity.UNKNOWN,
                findings=["No statutory or environmental clearance records available in project documentation."],
                evidence_status=EvidenceStatus.UNVERIFIED_GAP,
            )

        total_req = len(clearance_items)
        approved = sum(1 for c in clearance_items if c.status in (ClearanceStatus.FINAL_APPROVED, ClearanceStatus.EXEMPTED))
        pending = sum(1 for c in clearance_items if c.status in (ClearanceStatus.SUBMITTED, ClearanceStatus.STAGE_1_APPROVED, ClearanceStatus.IN_PRINCIPLE_APPROVED, ClearanceStatus.PENDING_COMPLIANCE, ClearanceStatus.NOT_APPLIED))
        pending_critical = sum(1 for c in clearance_items if c.critical_path and c.status not in (ClearanceStatus.FINAL_APPROVED, ClearanceStatus.EXEMPTED))

        # Severity Assessment
        severity = ConstraintSeverity.NEGLIGIBLE
        is_bottleneck = False

        if pending_critical > 0:
            severity = ConstraintSeverity.CRITICAL
            is_bottleneck = True
            findings.append(f"{pending_critical} critical-path statutory clearance(s) pending approval.")
        elif pending > 2:
            severity = ConstraintSeverity.HIGH
            is_bottleneck = True
            findings.append(f"{pending} of {total_req} statutory clearances remain pending.")
        elif pending > 0:
            severity = ConstraintSeverity.MODERATE
            findings.append(f"{pending} statutory clearance(s) pending resolution.")
        else:
            findings.append(f"All {total_req} required statutory clearances granted.")

        if forest_diverted_ha > 0:
            findings.append(f"Forest diversion required: {forest_diverted_ha:.2f} ha.")

        if tree_felling_pending > 0:
            findings.append(f"Tree felling permissions pending for {tree_felling_pending} trees/clusters.")

        return EnvironmentalClearanceAnalysis(
            clearances=clearance_items,
            total_clearances_required=total_req,
            approved_count=approved,
            pending_count=pending,
            pending_critical_count=pending_critical,
            forest_land_diverted_ha=forest_diverted_ha,
            tree_felling_pending_count=tree_felling_pending,
            is_clearance_bottleneck=is_bottleneck,
            bottleneck_severity=severity,
            findings=findings,
            evidence_status=EvidenceStatus.VERIFIED if clearance_items else EvidenceStatus.INCOMPLETE,
        )
