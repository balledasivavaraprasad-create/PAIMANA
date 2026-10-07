"""Procurement & Contracting Model Intelligence (DSI-03).

Analyzes commercial delivery models (EPC, HAM, BOT), tender-to-award durations,
re-tendering episodes, and aggressive bidding discounts or premiums.
"""
from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from .project_profile import infer_execution_model
from .schemas import ConstraintSeverity, EvidenceStatus, ExecutionModel, ProcurementAnalysis


def parse_date(date_str: Optional[str]) -> Optional[datetime.date]:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%b %Y", "%B %Y"):
        try:
            return datetime.datetime.strptime(str(date_str).strip(), fmt).date()
        except ValueError:
            continue
    return None


class ProcurementAnalyzer:
    """Evaluates procurement timelines and contracting model risks."""

    def analyze(self, project_data: Dict[str, Any]) -> ProcurementAnalysis:
        findings: List[str] = []
        exec_model = infer_execution_model(project_data)

        proc_dict = project_data.get("procurement") or {}
        if not isinstance(proc_dict, dict):
            proc_dict = {}

        t_notice = proc_dict.get("tender_notice_date") or project_data.get("tender_date") or project_data.get("nit_date")
        t_award = proc_dict.get("award_date") or project_data.get("contract_award_date") or project_data.get("date_of_award")
        retenders = int(proc_dict.get("retender_count") or project_data.get("retender_count") or project_data.get("retenders") or 0)

        # Cost comparisons
        awarded_cost = proc_dict.get("awarded_cost_cr") or project_data.get("awarded_cost_cr") or project_data.get("contract_value_cr")
        sanctioned_cost = proc_dict.get("sanctioned_cost_cr") or project_data.get("original_cost_cr") or project_data.get("sanctioned_cost")

        awarded_f = float(awarded_cost) if awarded_cost is not None else None
        sanctioned_f = float(sanctioned_cost) if sanctioned_cost is not None else None

        # Duration
        t_duration_months = None
        d_notice = parse_date(t_notice)
        d_award = parse_date(t_award)
        if d_notice and d_award and d_award >= d_notice:
            days = (d_award - d_notice).days
            t_duration_months = days / 30.4375

        # Bid discount / premium
        bid_diff_pct = None
        if awarded_f and sanctioned_f and sanctioned_f > 0:
            bid_diff_pct = ((awarded_f - sanctioned_f) / sanctioned_f) * 100.0

        has_data = any([
            t_notice, t_award, retenders > 0, awarded_f,
            exec_model != ExecutionModel.UNKNOWN,
        ])

        if not has_data:
            return ProcurementAnalysis(
                execution_model=ExecutionModel.UNKNOWN,
                is_procurement_risk=False,
                risk_severity=ConstraintSeverity.UNKNOWN,
                findings=["No procurement or contracting lifecycle data recorded."],
                evidence_status=EvidenceStatus.UNVERIFIED_GAP,
            )

        # Risk assessment
        severity = ConstraintSeverity.NEGLIGIBLE
        is_risk = False

        findings.append(f"Delivery model identified as {exec_model.value}.")

        if retenders > 1:
            severity = ConstraintSeverity.HIGH
            is_risk = True
            findings.append(f"Repeated re-tendering ({retenders} rounds) caused extensive pre-construction delay.")
        elif retenders == 1:
            severity = ConstraintSeverity.MODERATE
            is_risk = True
            findings.append("Project underwent 1 round of re-tendering prior to award.")

        if t_duration_months and t_duration_months > 18.0:
            if severity != ConstraintSeverity.HIGH:
                severity = ConstraintSeverity.MODERATE
            is_risk = True
            findings.append(f"Extended procurement cycle: {t_duration_months:.1f} months from tender notice to award.")

        if bid_diff_pct is not None:
            if bid_diff_pct < -20.0:
                severity = ConstraintSeverity.HIGH
                is_risk = True
                findings.append(f"High risk of aggressive under-bidding: awarded at {abs(bid_diff_pct):.1f}% below sanctioned estimate.")
            elif bid_diff_pct > 15.0:
                findings.append(f"Bid awarded at a premium of {bid_diff_pct:.1f}% above original sanctioned cost.")

        return ProcurementAnalysis(
            execution_model=exec_model,
            tender_notice_date=str(t_notice) if t_notice else None,
            award_date=str(t_award) if t_award else None,
            tender_duration_months=t_duration_months,
            retender_count=retenders,
            awarded_cost_cr=awarded_f,
            sanctioned_cost_cr=sanctioned_f,
            bid_premium_discount_pct=bid_diff_pct,
            is_procurement_risk=is_risk,
            risk_severity=severity,
            findings=findings,
            evidence_status=EvidenceStatus.VERIFIED if (t_award or awarded_f) else EvidenceStatus.INFERRED,
        )
