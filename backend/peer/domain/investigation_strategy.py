"""Domain-Aware Investigation Planning & Tool Recommendation Engine (DSI-14).

Formulates hypothesis-conditioned investigation workflows, maps detected domain
bottlenecks to targeted investigation tools, and highlights critical evidence gaps.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .schemas import (
    ConstraintSeverity,
    ContractAnalysis,
    EnvironmentalClearanceAnalysis,
    InvestigationStrategyRecommendation,
    LandAcquisitionAnalysis,
    ProjectDomainProfile,
    UtilityShiftingAnalysis,
)


class InvestigationStrategyPlanner:
    """Plans domain-aware investigation strategies conditioned on hypotheses and evidence gaps."""

    def plan_strategy(
        self,
        profile: ProjectDomainProfile,
        question: Optional[str] = None,
        hypothesis: Optional[str] = None,
        land_analysis: Optional[LandAcquisitionAnalysis] = None,
        clearance_analysis: Optional[EnvironmentalClearanceAnalysis] = None,
        utility_analysis: Optional[UtilityShiftingAnalysis] = None,
        contract_analysis: Optional[ContractAnalysis] = None,
    ) -> List[InvestigationStrategyRecommendation]:
        recommendations: List[InvestigationStrategyRecommendation] = []
        q_text = f"{question or ''} {hypothesis or ''}".lower()

        # 1. Land Acquisition Investigation Strategy
        if land_analysis and (land_analysis.is_critical_bottleneck or land_analysis.bottleneck_severity in (ConstraintSeverity.CRITICAL, ConstraintSeverity.HIGH) or "land" in q_text or "delay" in q_text):
            specific_q = [
                f"What is the status of Section 3D and 3G compensation awards for the pending {land_analysis.pending_ha:.1f} ha?",
                "Are non-contiguous land stretches causing contractor mobilization standby claims?",
                "Has state revenue administration conducted joint site measurement for disputed parcels?",
            ]
            gaps = [
                "Detailed parcel-wise land acquisition schedule (3A to 3H)",
                "Competent Authority Land Acquisition (CALA) disbursement records",
            ]
            recommendations.append(
                InvestigationStrategyRecommendation(
                    target_domain="LAND_ACQUISITION",
                    suggested_tool="investigate_land_records",
                    priority="CRITICAL" if land_analysis.is_critical_bottleneck else "HIGH",
                    rationale=(
                        f"Land handover is at {land_analysis.handover_pct:.1f}%, creating an active physical bottleneck. "
                        f"Target project requires verification of CALA compensation deposits and state possession orders."
                    ),
                    specific_questions=specific_q,
                    evidence_gaps_to_fill=gaps,
                )
            )

        # 2. Environmental & Statutory Clearance Strategy
        if clearance_analysis and (clearance_analysis.is_clearance_bottleneck or clearance_analysis.pending_critical_count > 0 or "clearance" in q_text or "forest" in q_text):
            specific_q = [
                f"Which specific stretch/chainage is blocked by pending {clearance_analysis.pending_critical_count} critical clearance(s)?",
                "Has compensatory afforestation land (CA land) been mutated and handed over for Forest Stage-II approval?",
            ]
            gaps = [
                "Ministry of Environment, Forest and Climate Change (MoEF&CC) / Parivesh portal tracking status",
                "State Forest Department tree felling enumerations",
            ]
            recommendations.append(
                InvestigationStrategyRecommendation(
                    target_domain="STATUTORY_CLEARANCES",
                    suggested_tool="query_regulatory_clearance_portal",
                    priority="CRITICAL" if clearance_analysis.pending_critical_count > 0 else "HIGH",
                    rationale=(
                        f"{clearance_analysis.pending_count} clearances pending ({clearance_analysis.pending_critical_count} critical-path). "
                        f"Requires checking statutory file movement and state compliance submissions."
                    ),
                    specific_questions=specific_q,
                    evidence_gaps_to_fill=gaps,
                )
            )

        # 3. Utility Shifting Strategy
        if utility_analysis and (utility_analysis.is_utility_bottleneck or utility_analysis.blocking_workfront_count > 0 or "utility" in q_text or "power" in q_text):
            specific_q = [
                f"What is the physical progress of shifting the {utility_analysis.blocking_workfront_count} workfront-blocking utilities?",
                "Have transmission line shutdown/power block permissions been sanctioned by the power utility?",
            ]
            gaps = [
                "Joint utility shifting inspection minutes",
                "Utility agency estimate sanctions and supervision payment receipts",
            ]
            recommendations.append(
                InvestigationStrategyRecommendation(
                    target_domain="UTILITY_SHIFTING",
                    suggested_tool="inspect_utility_relocation_status",
                    priority="HIGH",
                    rationale=(
                        f"{utility_analysis.blocking_workfront_count} utilities actively obstruct execution frontages. "
                        f"Inter-agency coordination between project authority and line departments must be verified."
                    ),
                    specific_questions=specific_q,
                    evidence_gaps_to_fill=gaps,
                )
            )

        # 4. Commercial, Contract & Scope Variations
        if contract_analysis and (contract_analysis.is_contractual_risk or "cost" in q_text or "overrun" in q_text or "variation" in q_text or "eot" in q_text):
            specific_q = [
                f"What specific scope changes contributed to the ₹{contract_analysis.cost_revision_cr:.2f} Cr cost revision?",
                f"What are the claimed grounds for {contract_analysis.eot_pending_months:.1f} months of pending Extension of Time (EOT)?",
                "Has the Independent Engineer / Authority's Engineer issued formal determination on contractor delay claims?",
            ]
            gaps = [
                "Authority's Engineer EOT recommendation report",
                "Contract Variation Orders (VOs) and Standing Finance Committee (SFC) revised cost sanctions",
            ]
            recommendations.append(
                InvestigationStrategyRecommendation(
                    target_domain="CONTRACT_ADMINISTRATION",
                    suggested_tool="audit_contract_variations_and_eot",
                    priority="HIGH" if contract_analysis.penalty_liquidated_damages_invoked else "MEDIUM",
                    rationale=(
                        f"Significant contract dynamics ({contract_analysis.eot_count} EOT revisions, "
                        f"₹{contract_analysis.cost_revision_cr:.2f} Cr variation). Contractual claims need verification."
                    ),
                    specific_questions=specific_q,
                    evidence_gaps_to_fill=gaps,
                )
            )

        # Fallback baseline recommendation if no acute bottlenecks triggered
        if not recommendations:
            recommendations.append(
                InvestigationStrategyRecommendation(
                    target_domain="GENERAL_EXECUTION",
                    suggested_tool="audit_milestone_schedule",
                    priority="MEDIUM",
                    rationale="Execution environment appears relatively unconstrained; focus on direct contractor productivity and cashflow.",
                    specific_questions=[
                        "What is contractor monthly plant and machinery deployment vs planned mobilization?",
                        "Is billing and running account (RA) payment cycle functioning without liquidity blockage?",
                    ],
                    evidence_gaps_to_fill=["Monthly progress report (MPR) plant deployment schedule"],
                )
            )

        return recommendations
