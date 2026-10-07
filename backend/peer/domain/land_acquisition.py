"""Land Acquisition Bottleneck & Linear Vulnerability Analyzer (DSI-05).

Evaluates land acquisition lifecycle stages (3A/3D/3G/3H), physical progress vs
handover alignment, acquisition velocity, and non-contiguous island working risks.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .schemas import ConstraintSeverity, EvidenceStatus, LandAcquisitionAnalysis


class LandAcquisitionAnalyzer:
    """Analyzes land acquisition status and operational bottlenecks."""

    def analyze(
        self,
        project_data: Dict[str, Any],
        is_linear: bool = True,
        physical_progress_pct: Optional[float] = None,
    ) -> LandAcquisitionAnalysis:
        findings: List[str] = []
        pending_stages: Dict[str, float] = {}

        # Look for explicit land acquisition records in nested dict or top-level keys
        land_dict = project_data.get("land_acquisition") or {}
        if not isinstance(land_dict, dict):
            land_dict = {}

        req_ha = float(
            land_dict.get("required_ha")
            or project_data.get("land_required_ha")
            or project_data.get("total_land_ha")
            or 0.0
        )
        acq_ha = float(
            land_dict.get("acquired_ha")
            or project_data.get("land_acquired_ha")
            or 0.0
        )
        handover_ha = float(
            land_dict.get("handed_over_ha")
            or project_data.get("land_handed_over_ha")
            or acq_ha  # Fallback: if acquired is given but not handover, assume equal
        )

        acq_pct_input = land_dict.get("acquisition_pct") or project_data.get("land_acquisition_pct")
        handover_pct_input = land_dict.get("handover_pct") or project_data.get("land_handover_pct")

        has_data = req_ha > 0 or acq_pct_input is not None or handover_pct_input is not None

        if not has_data:
            # Absence of record is noted as an explicit gap rather than assuming 100% or 0%
            return LandAcquisitionAnalysis(
                required_ha=0.0,
                acquired_ha=0.0,
                handed_over_ha=0.0,
                pending_ha=0.0,
                acquisition_pct=0.0,
                handover_pct=0.0,
                is_critical_bottleneck=False,
                bottleneck_severity=ConstraintSeverity.UNKNOWN,
                findings=["No land acquisition or right-of-way records present in project documentation."],
                evidence_status=EvidenceStatus.UNVERIFIED_GAP,
            )

        # Compute percentages
        if req_ha > 0:
            acq_pct = (acq_ha / req_ha) * 100.0 if acq_pct_input is None else float(acq_pct_input)
            handover_pct = (handover_ha / req_ha) * 100.0 if handover_pct_input is None else float(handover_pct_input)
            pending_ha = max(0.0, req_ha - handover_ha)
        else:
            acq_pct = float(acq_pct_input or 0.0)
            handover_pct = float(handover_pct_input or acq_pct)
            pending_ha = 0.0

        acq_pct = min(100.0, max(0.0, acq_pct))
        handover_pct = min(100.0, max(0.0, handover_pct))

        # Check stages breakdown if available
        stages = land_dict.get("stages") or project_data.get("land_stages") or {}
        if isinstance(stages, dict):
            for stage_name, ha_val in stages.items():
                try:
                    pending_stages[stage_name] = float(ha_val)
                except (ValueError, TypeError):
                    pass

        # Progress vs Land Handover Alignment
        phys_pct = physical_progress_pct
        if phys_pct is None:
            raw_p = project_data.get("physical_progress_pct") or project_data.get("physical_progress")
            phys_pct = float(raw_p) if raw_p is not None else 0.0

        progress_vs_land_gap = max(0.0, phys_pct - handover_pct)

        # Island working & fragmented handover risk
        disputed = int(land_dict.get("disputed_patches_count") or project_data.get("land_disputes_count") or 0)
        is_island_risk = False
        if is_linear and handover_pct < 90.0 and (handover_pct - acq_pct < -5.0 or disputed > 0 or handover_pct < 75.0):
            is_island_risk = True

        # Velocity & time to complete
        velocity = land_dict.get("acquisition_velocity_ha_per_month") or project_data.get("land_velocity_ha_month")
        months_to_complete = None
        if velocity is not None:
            try:
                v = float(velocity)
                if v > 0 and pending_ha > 0:
                    months_to_complete = pending_ha / v
            except (ValueError, TypeError):
                velocity = None

        # Severity Assessment
        severity = ConstraintSeverity.NEGLIGIBLE
        is_critical = False

        if handover_pct < 60.0:
            severity = ConstraintSeverity.CRITICAL
            is_critical = True
            findings.append(f"Severe land deficit: only {handover_pct:.1f}% handed over (pending {pending_ha:.1f} ha).")
        elif handover_pct < 80.0:
            if is_linear and phys_pct > 50.0:
                severity = ConstraintSeverity.CRITICAL
                is_critical = True
                findings.append(f"Critical linear bottleneck: physical progress ({phys_pct:.1f}%) approaching handed over land boundary ({handover_pct:.1f}%).")
            else:
                severity = ConstraintSeverity.HIGH
                findings.append(f"Substantial pending land: {100.0 - handover_pct:.1f}% pending handover.")
        elif handover_pct < 95.0:
            if progress_vs_land_gap > 0:
                severity = ConstraintSeverity.MODERATE
                findings.append(f"Tight workfront margin: physical progress ({phys_pct:.1f}%) exceeds handed over land ({handover_pct:.1f}%).")
            else:
                severity = ConstraintSeverity.LOW
                findings.append(f"Minor pending land: {100.0 - handover_pct:.1f}% remains to be handed over.")
        else:
            severity = ConstraintSeverity.NEGLIGIBLE
            findings.append(f"Land acquisition substantially complete ({handover_pct:.1f}% handed over).")

        if is_island_risk:
            findings.append("High risk of fragmented 'island' construction stretches due to non-contiguous land possession.")

        if disputed > 0:
            findings.append(f"{disputed} disputed land parcels under active litigation or local opposition.")

        return LandAcquisitionAnalysis(
            required_ha=req_ha,
            acquired_ha=acq_ha,
            handed_over_ha=handover_ha,
            pending_ha=pending_ha,
            acquisition_pct=acq_pct,
            handover_pct=handover_pct,
            is_critical_bottleneck=is_critical,
            bottleneck_severity=severity,
            acquisition_velocity_ha_per_month=float(velocity) if velocity else None,
            estimated_months_to_complete=months_to_complete,
            progress_vs_land_gap_pct=progress_vs_land_gap,
            is_island_working_risk=is_island_risk,
            disputed_patches_count=disputed,
            pending_stages=pending_stages,
            findings=findings,
            evidence_status=EvidenceStatus.VERIFIED if req_ha > 0 else EvidenceStatus.INFERRED,
        )
