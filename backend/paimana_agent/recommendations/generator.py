"""[LEGACY ADAPTER] Recommendation Generator for PAIMANA Agentic Layer.

NOTE: This is a legacy compatibility module. The canonical recommendation candidate generator
is `CandidateGenerator` in `paimana_agent.recommendations.candidate_generator`.
"""
from __future__ import annotations
import logging
from typing import Any, Optional
from ..state import RecommendationCandidate

logger = logging.getLogger("paimana_agent.recommendations.generator")


class RecommendationGenerator:
    """[LEGACY ADAPTER] Generates candidate recommendations calibrated to evidentiary support.
    
    Replaced by CandidateGenerator in candidate_generator.py.
    """

    def generate_candidates(
        self,
        leading_hypotheses: list[Any],
        investigation_outcome: str,
        project: dict,
        feats: dict,
        precedents: dict
    ) -> list[RecommendationCandidate]:
        """Generates candidate recommendations adhering to safety boundaries."""
        cost = float(project.get("original_cost_cr", 0.0))
        is_mega = cost >= 1000.0 or feats.get("is_mega_project", False)
        succ = precedents.get("successful_precedents", [])
        candidates: list[RecommendationCandidate] = []

        # 1. Precedent-Validated Recovery Action (if positive precedent exists and matches leading hypothesis)
        if succ and leading_hypotheses and leading_hypotheses[0].confidence >= 0.50:
            p_action = succ[0].get("action", "")
            p_outcome = succ[0].get("outcome", "")
            candidates.append(RecommendationCandidate(
                action=f"Implement verified recovery measure: '{p_action[:60]}'. (Validated by prior positive outcome: '{p_outcome[:70]}').",
                responsible_stakeholder="Project Director & Ministry Infrastructure Monitoring Division",
                urgency="HIGH",
                justification=f"Directly informed by historical success on project {succ[0].get('project_code')} where this action resolved similar anomalies.",
                supporting_evidence=[f"Past precedent outcome: {p_outcome}"],
                candidate_type="PRIMARY_RECOVERY",
                tradeoffs="Requires dedicated monitoring overhead; execution contingent on implementing agency adherence.",
                risks="Potential coordination resistance from field contractors during initial transition.",
                uncertainty="LOW",
                precedent_outcome=p_outcome,
                expected_impact="High probability of operational recovery based on empirical historical success"
            ))

        # Check top hypothesis status
        top_h = leading_hypotheses[0] if leading_hypotheses else None
        top_id = getattr(top_h, "id", getattr(top_h, "name", "")).lower() if top_h else ""
        top_conf = getattr(top_h, "confidence", 0.0)
        top_status = getattr(top_h, "status", "").lower()

        # 2. Outcome-Calibrated Recommendations
        if investigation_outcome == "INSUFFICIENT_EVIDENCE" or (top_conf < 0.35 and top_status != "supported"):
            # Exploratory verification rather than operational action!
            candidates.append(RecommendationCandidate(
                action="Deploy Joint Fact-Finding Technical Inspection to collect targeted on-site measurements and resolve open evidence gaps.",
                responsible_stakeholder="Superintending Engineer & PMU Technical Auditor",
                urgency="MEDIUM",
                justification="Current observations are insufficient to confirm a single dominant root cause; independent on-site ground data required.",
                supporting_evidence=[f"Top hypothesis '{top_id}' confidence is preliminary ({top_conf:.2f})."],
                candidate_type="FORENSIC_AUDIT",
                tradeoffs="Defers major contract interventions by 15-20 days pending physical site audit.",
                risks="Slight administrative delay in executing punitive contractual measures.",
                uncertainty="HIGH",
                expected_impact="Eliminates diagnostic ambiguity and prevents premature or wrongful contractual penalties"
            ))
        elif investigation_outcome == "MULTIPLE_PLAUSIBLE_CAUSES":
            candidates.append(RecommendationCandidate(
                action="Convene Multi-Disciplinary Steering Committee to address compound execution and statutory bottlenecks simultaneously.",
                responsible_stakeholder="Joint Secretary (Infrastructure) & Chief Engineer",
                urgency="HIGH",
                justification="Project exhibits compound risk drivers across multiple independent operational dimensions.",
                supporting_evidence=[h.statement for h in leading_hypotheses[:2]],
                candidate_type="PRIMARY_RECOVERY",
                tradeoffs="Requires coordinated multi-agency alignment across distinct ministry departments.",
                risks="Diffusion of immediate accountability across working groups.",
                uncertainty="MEDIUM",
                expected_impact="Establishes unified inter-departmental taskforce to unblock overlapping constraints"
            ))
        else:
            # Domain-Specific Calibrated Recovery
            if "billing" in top_id or "decoupling" in top_id:
                candidates.append(RecommendationCandidate(
                    action="Establish Joint Financial-Physical Audit Taskforce to reconcile certified physical milestones against contractor mobilization invoices prior to next installment release.",
                    responsible_stakeholder="Ministry Financial Advisor & Chief Engineer" if is_mega else "Project Director & Superintending Engineer",
                    urgency="CRITICAL" if is_mega else "HIGH",
                    justification="Sanctioned disbursements are advancing significantly faster than certified on-site works.",
                    supporting_evidence=[f"Spend leads certified physical execution (confidence: {top_conf:.2f})."],
                    candidate_type="FORENSIC_AUDIT",
                    tradeoffs="Freezes interim contractor disbursements until reconciliation; may create short-term mobilization pause.",
                    risks="Contractor claim for equipment idle charges if reconciliation exceeds 30 calendar days.",
                    uncertainty="LOW",
                    expected_impact="Freezes unverified expenditure and ensures strict milestone linkage"
                ))

            if "delay" in top_id or "schedule" in top_id or "procurement" in top_id:
                candidates.append(RecommendationCandidate(
                    action="Require executing agency to submit a resource-loaded Catch-Up Schedule with fortnightly milestone check-ins.",
                    responsible_stakeholder="Executive Director (Projects) & Chief Engineer",
                    urgency="HIGH",
                    justification="Critical path execution slippage exceeds contractual milestones.",
                    supporting_evidence=[f"Schedule delay confirmed on critical path (confidence: {top_conf:.2f})."],
                    candidate_type="INTERIM_MITIGATION",
                    tradeoffs="Focuses solely on existing contractor resources without capital infusion or scope reduction.",
                    risks="Superficial schedule re-baselining without addressing structural labor or supply shortages.",
                    uncertainty="MEDIUM",
                    expected_impact="Re-establishes milestone accountability and clears contractor bottlenecks"
                ))

            if "clearance" in top_id or "land" in top_id or "regulatory" in top_id:
                candidates.append(RecommendationCandidate(
                    action="Escalate RoW encumbrances and pending statutory environmental approvals to State Chief Secretary Apex Committee.",
                    responsible_stakeholder="Ministry Nodal Officer & State Infrastructure Secretary",
                    urgency="HIGH",
                    justification="Statutory Stage-2 environmental clearances or RoW land handovers are holding up site mobilization.",
                    supporting_evidence=[f"Statutory clearance bottleneck identified (confidence: {top_conf:.2f})."],
                    candidate_type="PRIMARY_RECOVERY",
                    tradeoffs="Requires state-level executive intervention outside project implementing agency.",
                    risks="State political negotiation delays.",
                    uncertainty="LOW",
                    expected_impact="Resolves land handover blocks and unlocks encumbrance-free construction fronts"
                ))

        # Baseline PMU review candidate as standard baseline fallback
        candidates.append(RecommendationCandidate(
            action="Conduct comprehensive inter-ministerial review to assess project risk drivers and establish revised monitoring baselines.",
            responsible_stakeholder="Project Monitoring Unit (PMU)",
            urgency="MEDIUM",
            justification="Composite risk metrics elevated across multiple operational indicators.",
            supporting_evidence=["Multi-metric composite risk escalation observed."],
            candidate_type="BASELINE_REVIEW",
            tradeoffs="Requires multi-ministry convening and inter-departmental consensus, taking 30-45 days.",
            risks="Administrative inertia and delayed decisive on-site intervention.",
            uncertainty="HIGH",
            expected_impact="Identifies root-cause bottlenecks and resets monitoring trajectory"
        ))

        return candidates
