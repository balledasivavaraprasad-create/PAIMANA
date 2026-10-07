"""Contractor Execution Profile & Linear Workfront Continuity Analyzer (DSI-10, DSI-11).

Evaluates contractor portfolio concentration risk and assesses linear right-of-way
continuity to detect fragmented "island" construction stretches and broken workfronts.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .schemas import (
    ConstraintSeverity,
    ContractorWorkfrontAnalysis,
    EvidenceStatus,
)


class ContractorWorkfrontAnalyzer:
    """Analyzes contractor concentration and linear workfront continuity."""

    def analyze(
        self,
        project_data: Dict[str, Any],
        is_linear: bool = True,
        length_km: Optional[float] = None,
        handover_pct: float = 100.0,
    ) -> ContractorWorkfrontAnalysis:
        findings: List[str] = []

        wf_dict = project_data.get("contractor_workfront") or {}
        if not isinstance(wf_dict, dict):
            wf_dict = {}

        c_name = str(
            wf_dict.get("contractor_name")
            or project_data.get("contractor")
            or project_data.get("agency_contractor")
            or project_data.get("concessionaire")
            or "UNASSIGNED"
        ).strip()

        c_tier = str(wf_dict.get("contractor_tier") or project_data.get("contractor_tier") or "UNKNOWN").upper()
        packages_held = int(wf_dict.get("concurrent_packages_held") or project_data.get("contractor_active_packages") or 1)

        # Concentration Risk
        if packages_held >= 5:
            conc_risk = "HIGH"
            findings.append(f"High contractor portfolio concentration: contractor holds {packages_held} concurrent packages.")
        elif packages_held >= 3:
            conc_risk = "MODERATE"
            findings.append(f"Moderate contractor exposure across {packages_held} concurrent packages.")
        else:
            conc_risk = "LOW"

        # Linear Continuity & Broken Workfronts
        continuity_ratio = float(wf_dict.get("linear_continuity_ratio") or 1.0)
        broken_count = int(wf_dict.get("broken_workfronts_count") or 0)
        avg_stretch = wf_dict.get("average_continuous_stretch_km")

        if "linear_continuity_ratio" not in wf_dict:
            # Estimate from handover % and linear nature
            if is_linear:
                if handover_pct < 60.0:
                    continuity_ratio = 0.45
                    broken_count = max(4, int(length_km / 15.0) if length_km else 4)
                elif handover_pct < 80.0:
                    continuity_ratio = 0.70
                    broken_count = max(2, int(length_km / 25.0) if length_km else 2)
                elif handover_pct < 95.0:
                    continuity_ratio = 0.88
                    broken_count = 1
                else:
                    continuity_ratio = 1.0
                    broken_count = 0

        avg_stretch_f = float(avg_stretch) if avg_stretch is not None else None
        if avg_stretch_f is None and length_km and broken_count > 0:
            avg_stretch_f = (length_km * (handover_pct / 100.0)) / (broken_count + 1)

        is_fragmented = is_linear and (continuity_ratio < 0.75 or broken_count > 2)

        if is_fragmented:
            findings.append(
                f"Workfront is severely fragmented: continuity ratio is {continuity_ratio:.2f} "
                f"with {broken_count} disconnected execution stretches ('island' construction)."
            )
            findings.append("Frequent equipment mobilization/demobilization cycles inflating plant idle costs.")
        elif is_linear and continuity_ratio < 0.90:
            findings.append(f"Minor workfront discontinuity: continuity ratio is {continuity_ratio:.2f}.")
        else:
            findings.append("Continuous encumbrance-free workfront available for systematic execution.")

        has_data = bool(
            c_name != "UNASSIGNED" or "linear_continuity_ratio" in wf_dict or
            "contractor" in project_data or "contractor_workfront" in project_data
        )

        return ContractorWorkfrontAnalysis(
            contractor_name=c_name,
            contractor_tier=c_tier,
            concurrent_packages_held=packages_held,
            concentration_risk=conc_risk,
            linear_continuity_ratio=round(continuity_ratio, 2),
            broken_workfronts_count=broken_count,
            average_continuous_stretch_km=round(avg_stretch_f, 2) if avg_stretch_f is not None else None,
            is_fragmented_workfront=is_fragmented,
            findings=findings,
            evidence_status=EvidenceStatus.VERIFIED if has_data else EvidenceStatus.INFERRED,
        )
