"""Non-Conflating Domain Narrative & Evidence Attribution Generator (DSI-14).

Synthesizes multi-domain analysis into clear, non-conflating executive summaries
and structured evidence items conforming strictly to CONTEXTUALIZES semantics.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .schemas import (
    ConstraintSeverity,
    ContractAnalysis,
    DependencyGraphReport,
    DomainEvidenceItem,
    EnvironmentalClearanceAnalysis,
    EvidenceStatus,
    LandAcquisitionAnalysis,
    PhysicalContextAnalysis,
    ProcurementAnalysis,
    ProjectDomainProfile,
    UtilityShiftingAnalysis,
)


class DomainExplanationEngine:
    """Generates rigorous narratives and supervisor evidence items adhering to CONTEXTUALIZES semantics."""

    def generate_evidence_items(
        self,
        profile: ProjectDomainProfile,
        land: Optional[LandAcquisitionAnalysis] = None,
        clearances: Optional[EnvironmentalClearanceAnalysis] = None,
        utilities: Optional[UtilityShiftingAnalysis] = None,
        procurement: Optional[ProcurementAnalysis] = None,
        contract: Optional[ContractAnalysis] = None,
        physical: Optional[PhysicalContextAnalysis] = None,
    ) -> List[Dict[str, Any]]:
        evidence: List[DomainEvidenceItem] = []

        # 1. Land Evidence
        if land and land.evidence_status != EvidenceStatus.UNVERIFIED_GAP:
            if land.bottleneck_severity in (ConstraintSeverity.CRITICAL, ConstraintSeverity.HIGH, ConstraintSeverity.MODERATE):
                evidence.append(
                    DomainEvidenceItem(
                        claim=f"Right-of-way handover deficit of {land.pending_ha:.1f} ha ({100.0 - land.handover_pct:.1f}% unhanded)",
                        domain_factor="LAND_ACQUISITION",
                        evidence_relation="CONTEXTUALIZES",
                        evidence_status=land.evidence_status,
                        source_fields=["land_acquisition.handed_over_ha", "land_acquisition.required_ha"],
                        severity=land.bottleneck_severity,
                        observation=(
                            f"Land possession stands at {land.handover_pct:.1f}%. "
                            f"{'Linear fragmentation risk is acute.' if land.is_island_working_risk else 'Workfront frontage is constrained.'}"
                        ),
                    )
                )

        # 2. Environmental Clearances Evidence
        if clearances and clearances.evidence_status != EvidenceStatus.UNVERIFIED_GAP:
            if clearances.pending_count > 0:
                evidence.append(
                    DomainEvidenceItem(
                        claim=f"{clearances.pending_count} statutory clearance(s) pending ({clearances.pending_critical_count} on critical path)",
                        domain_factor="STATUTORY_CLEARANCES",
                        evidence_relation="CONTEXTUALIZES",
                        evidence_status=clearances.evidence_status,
                        source_fields=["statutory_clearances", "clearances"],
                        severity=clearances.bottleneck_severity,
                        observation=(
                            f"Approved: {clearances.approved_count}/{clearances.total_clearances_required}. "
                            f"Critical approvals pending on active sections."
                        ),
                    )
                )

        # 3. Utilities Evidence
        if utilities and utilities.evidence_status != EvidenceStatus.UNVERIFIED_GAP:
            if utilities.blocking_workfront_count > 0 or utilities.pending_count > 0:
                evidence.append(
                    DomainEvidenceItem(
                        claim=f"{utilities.blocking_workfront_count} utilities actively blocking civil workfronts ({utilities.pending_count} total pending)",
                        domain_factor="UTILITY_SHIFTING",
                        evidence_relation="CONTEXTUALIZES",
                        evidence_status=utilities.evidence_status,
                        source_fields=["utility_shifting.utilities"],
                        severity=utilities.bottleneck_severity,
                        observation=f"Utility shifting completion is {utilities.completion_pct:.1f}%. Relocation delays hinder unencumbered possession.",
                    )
                )

        # 4. Procurement Evidence
        if procurement and procurement.evidence_status != EvidenceStatus.UNVERIFIED_GAP:
            if procurement.is_procurement_risk:
                evidence.append(
                    DomainEvidenceItem(
                        claim=f"Procurement risk under {procurement.execution_model.value}: {procurement.retender_count} retender(s)",
                        domain_factor="PROCUREMENT_COMMERCIAL",
                        evidence_relation="CONTEXTUALIZES",
                        evidence_status=procurement.evidence_status,
                        source_fields=["procurement.retender_count", "procurement.tender_duration_months"],
                        severity=procurement.risk_severity,
                        observation=f"Tender duration spanned {procurement.tender_duration_months or 0.0:.1f} months.",
                    )
                )

        # 5. Contractual Evidence
        if contract and contract.evidence_status != EvidenceStatus.UNVERIFIED_GAP:
            if contract.is_contractual_risk:
                evidence.append(
                    DomainEvidenceItem(
                        claim=f"Contractual strain: {contract.eot_granted_months:.1f}m EOT granted, {contract.eot_pending_months:.1f}m pending",
                        domain_factor="CONTRACT_ADMINISTRATION",
                        evidence_relation="CONTEXTUALIZES",
                        evidence_status=contract.evidence_status,
                        source_fields=["contract.eot_granted_months", "contract.eot_pending_months"],
                        severity=contract.risk_severity,
                        observation=(
                            f"Scope variations count: {contract.scope_changes_count} (₹{contract.cost_revision_cr:.2f} Cr). "
                            f"{'Liquidated damages invoked.' if contract.penalty_liquidated_damages_invoked else ''}"
                        ),
                    )
                )

        # 6. Physical Terrain & Weather Evidence
        if physical and physical.evidence_status != EvidenceStatus.UNVERIFIED_GAP:
            if physical.terrain_difficulty_factor > 1.2 or physical.working_window_months_per_year < 10.0:
                evidence.append(
                    DomainEvidenceItem(
                        claim=f"Topological & seasonal constraints: {physical.terrain.value} terrain, {physical.working_window_months_per_year:.1f}m working window",
                        domain_factor="PHYSICAL_ENVIRONMENT",
                        evidence_relation="CONTEXTUALIZES",
                        evidence_status=physical.evidence_status,
                        source_fields=["physical_context.terrain", "physical_context.seasonal_monsoon_downtime_months"],
                        severity=ConstraintSeverity.MODERATE,
                        observation=(
                            f"Terrain difficulty index is {physical.terrain_difficulty_factor:.2f}x. "
                            f"Annual downtime: {12.0 - physical.working_window_months_per_year:.1f} months."
                        ),
                    )
                )

        return [e.to_dict() for e in evidence]

    def build_narrative(
        self,
        profile: ProjectDomainProfile,
        land: Optional[LandAcquisitionAnalysis],
        clearances: Optional[EnvironmentalClearanceAnalysis],
        utilities: Optional[UtilityShiftingAnalysis],
        procurement: Optional[ProcurementAnalysis],
        contract: Optional[ContractAnalysis],
        physical: Optional[PhysicalContextAnalysis],
        graph: Optional[DependencyGraphReport],
        key_constraints: List[str],
        data_gaps: List[str],
    ) -> str:
        lines: List[str] = []
        lines.append(f"### Domain-Specific Operational Context: {profile.project_name} ({profile.project_code})")
        lines.append(
            f"**Sector:** {profile.sector.value} ({profile.category.value}) | "
            f"**Subsector:** {profile.subsector} | "
            f"**Delivery Model:** {profile.execution_model.value} | "
            f"**Terrain:** {profile.terrain.value}"
        )
        lines.append("")

        if key_constraints:
            lines.append("**Key Operational Constraints Identified:**")
            for c in key_constraints:
                lines.append(f"- {c}")
            lines.append("")
        else:
            lines.append("No critical physical or regulatory execution bottlenecks currently recorded.")
            lines.append("")

        if graph and graph.blocking_nodes:
            lines.append(f"**Critical Path Dependency:** {graph.bottleneck_summary}")
            lines.append("")

        if data_gaps:
            lines.append("**Domain Data Provenance Gaps:**")
            for g in data_gaps:
                lines.append(f"- *Gap:* {g}")
            lines.append("")

        lines.append(
            "> [!NOTE]\n"
            "> **Causal Attribution Precaution:** The domain operational constraints detailed above provide essential "
            "environmental and execution context under `CONTEXTUALIZES` semantics. They establish where physical and "
            "statutory frictions exist, but do not automatically excuse contractor inefficiencies or substitute for direct causal proof."
        )

        return "\n".join(lines)
